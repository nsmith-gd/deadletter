using System;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Scenes
{
    /// <summary>
    /// Something D-17 does that the motor has no act for (the prototype's <c>game.act</c> kinds outside U-11's verbs:
    /// quirks, the latch's flinch, the crank's wait to turn back, a scripted transit, being stuck in a trench). While one
    /// runs, <see cref="SceneSim"/> gives the motor no input (he stands; his yaw and clip clock run on), or, when
    /// <see cref="OwnsPose"/>, does not step the motor at all and reports the act's pose. The prototype ran these inside
    /// <c>updatePlayer</c> (#4), and they took the place of free movement, as here.
    /// <para>These are the workaround for U-11 gaps (issue #22): a station cannot chain a follow-up clip, there is no
    /// quirk act, no scripted path act, and no way to move him without <see cref="D17Motor.Place"/>.</para>
    /// </summary>
    public abstract class SceneAct
    {
        protected SceneAct(string kind, string phase)
        {
            Kind = kind ?? throw new ArgumentNullException(nameof(kind));
            Phase = phase;
        }

        /// <summary>What the act is about: a mechanism ID (<c>dl01.latch</c>) or a kind (<c>quirk</c>, <c>transit</c>).</summary>
        public string Kind { get; protected set; }
        /// <summary>Its phase or clip, e.g. "Flinch", "CheckLabel", "0".</summary>
        public string Phase { get; protected set; }
        /// <summary>Seconds of the act's own clock (the prototype's <c>a.t</c> or the clip's time), advanced by the act.</summary>
        public double T { get; protected set; }

        /// <summary>True: the act places D-17 itself (<see cref="X"/>, <see cref="Y"/>, <see cref="Z"/>, <see cref="Yaw"/>); the motor is not stepped.</summary>
        public virtual bool OwnsPose => false;
        public double X { get; protected set; }
        public double Y { get; protected set; }
        /// <summary>Depth, Unity sign (+ into the set).</summary>
        public double Z { get; protected set; }
        public double Yaw { get; protected set; }

        /// <summary>He stays crouched while it runs (the motor gets <see cref="MotorInput.CrouchHeld"/>).</summary>
        public bool Crouch { get; protected set; }

        /// <summary>The act to run after this one ends (or null).</summary>
        public SceneAct Next { get; protected set; }

        /// <summary>One step (§3.1 #4). Return false when the act is over; that step is still the act's.</summary>
        public abstract bool Step(SceneSim sim, in MotorInput input, double dt);
    }

    /// <summary>He holds still for <paramref name="seconds"/> (a clip that only has to play out: DL-01's Flinch after the latch, L1875–L1876).</summary>
    public sealed class HoldAct : SceneAct
    {
        private readonly double _seconds;

        /// <param name="crouch">Keep him crouched meanwhile (the latch's flinch: <c>crouched</c> is cleared only when it ends, L1876).</param>
        public HoldAct(string kind, string phase, double seconds, bool crouch = false) : base(kind, phase) { _seconds = seconds; Crouch = crouch; }

        public override bool Step(SceneSim sim, in MotorInput input, double dt)
        {
            T += dt;                                     // the clip's time: the mixer advances it before updatePlayer reads it
            return !(T >= _seconds);
        }
    }

    /// <summary>
    /// A quirk (<c>playQuirk</c>/<c>updateQuirk</c>, L3841–L3857): a short clip that plays where he stands. A player's
    /// move (axis, left, right or jump) ends it after 0.3 s when it is cancellable (<paramref name="cancel"/>, or once
    /// <paramref name="cancelAfter"/> seconds of the game clock have passed since it started); otherwise it ends 0.05 s
    /// before the clip does, and CheckLabel holds a further <paramref name="holdFor"/> seconds so the label can be read.
    /// </summary>
    public sealed class QuirkAct : SceneAct
    {
        private readonly double _duration, _cancelAfter, _holdFor, _start;
        private readonly bool _cancel;
        private bool _fresh;
        private double _endAt = double.NaN;

        /// <param name="clipSeconds">The clip's length (<see cref="ClipSeconds"/>).</param>
        /// <param name="startClock">The game clock when it started (<c>a.start = game.clock</c>, L8108).</param>
        /// <param name="startsThisStep">True when created before #4 of the step it starts in (it then ignores that step, as the prototype's first <c>updateQuirk</c> sees time 0).</param>
        public QuirkAct(string clip, double clipSeconds, bool cancel, double startClock, double cancelAfter = 0, double holdFor = 0.8,
            bool startsThisStep = false) : base("quirk", clip)
        {
            _duration = clipSeconds; _cancel = cancel; _cancelAfter = cancelAfter; _holdFor = holdFor; _start = startClock;
            _fresh = startsThisStep;
        }

        public override bool Step(SceneSim sim, in MotorInput input, double dt)
        {
            if (_fresh) { _fresh = false; return true; }
            T += dt;
            bool moving = input.Move != 0 || input.JumpPressed;                                      // L3849
            bool cancel = _cancel || (_cancelAfter > 0 && sim.Clock - _start > _cancelAfter);        // L3850
            if (cancel && moving && T > 0.3) return false;                                            // L3851
            if (T >= _duration - 0.05)                                                                // L3852
            {
                if (Phase == "CheckLabel")
                {
                    if (double.IsNaN(_endAt)) _endAt = sim.Clock;                                     // a.endAt ??= game.clock
                    if (sim.Clock - _endAt < _holdFor) return true;                                   // L3853
                }
                return false;
            }
            return true;
        }

        /// <summary>
        /// A clip's length in seconds as three.js reads it from d17.glb: the last key time, a float32 in glTF, so 40 frames
        /// is 1.6666666269… s, not 1.6666…7. Quirks end on it (<c>dur − 0.05</c>).
        /// </summary>
        public static double ClipSeconds(string clip)
        {
            if (!ClipTimings.TryGet(clip, out var c)) throw new ArgumentException("Unknown clip '" + clip + "'.");
            return (float)(c.Frames / 24.0);
        }
    }
}
