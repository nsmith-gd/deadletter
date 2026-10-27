using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Scenes
{
    /// <summary>
    /// Something D-17 does that the motor's acts cannot do exactly (the prototype's <c>game.act</c> kinds beyond them: a
    /// scripted transit, DL-03's set-down, the realisation, a hold a rule ends, a quirk started after the motor's step).
    /// While one runs, <see cref="ChapterSim"/> gives the motor no input (he stands; his yaw and clip clock run on), or,
    /// when <see cref="OwnsPose"/>, does not step the motor at all and reports the act's pose. The prototype ran these
    /// inside <c>updatePlayer</c> (#4), and they took the place of free movement, as here.
    /// <para>Prefer the motor's own acts where they reproduce the prototype (<see cref="D17Motor.Die"/> through
    /// <see cref="ChapterSim.Die"/>, <see cref="D17Motor.BeginStuck"/>, <see cref="D17Motor.PlayQuirk"/> from inside #4);
    /// each scene act here is a motor gap, named where it is used (#28).</para>
    /// </summary>
    public abstract class SceneAct
    {
        protected SceneAct(ActId kind, ActId phase)
        {
            if (kind.IsNone) throw new ArgumentException("A scene act needs a kind.", nameof(kind));
            Kind = kind;
            Phase = phase;
        }

        /// <summary>
        /// What the act is about: a mechanism (<c>dl06.scanner</c>, <see cref="ActId.Of(Mechanisms.MechanismId)"/>) or a kind
        /// (<see cref="ActIds.Quirk"/>, <see cref="ActIds.Transit"/>). <see cref="ChapterSim.SceneActKind"/> reports it.
        /// </summary>
        public ActId Kind { get; }
        /// <summary>Its phase or clip, e.g. "Check", "CheckLabel", "0", interned (<see cref="ChapterSim.SceneActPhase"/>); set at its transitions.</summary>
        public ActId Phase { get; protected set; }
        /// <summary>Seconds of the act's own clock (the prototype's <c>a.t</c> or the clip's time), advanced by the act.</summary>
        public double T { get; protected set; }

        /// <summary>True: the act places D-17 itself (<see cref="X"/>, <see cref="Y"/>, <see cref="Z"/>, <see cref="Yaw"/>); the motor is not stepped.</summary>
        public virtual bool OwnsPose => false;
        public double X { get; protected set; }
        public double Y { get; protected set; }
        /// <summary>Depth, Unity sign (+ into the set).</summary>
        public double Z { get; protected set; }
        public double Yaw { get; protected set; }
        /// <summary>Whether he is on a support while the act owns his pose (default true; a death mid-air keeps <c>game.grounded</c> false).</summary>
        public virtual bool PoseGrounded => true;

        /// <summary>He stays crouched while it runs (the motor gets <see cref="MotorInput.CrouchHeld"/>).</summary>
        public bool Crouch { get; protected set; }

        /// <summary>The act to run after this one ends (or null).</summary>
        public SceneAct Next { get; protected set; }

        /// <summary>One step (§3.1 #4). Return false when the act is over; that step is still the act's.</summary>
        public abstract bool Step(ChapterSim sim, in MotorInput input, double dt);
    }

    /// <summary>
    /// He holds still for <paramref name="seconds"/>, or until a rule ends it (<see cref="ChapterSim.EndAct"/>: DL-06's label
    /// check, which the scanner ends, L2808–L2812; the motor's quirk cannot be ended from outside, #28).
    /// </summary>
    public sealed class HoldAct : SceneAct
    {
        private readonly double _seconds;

        /// <param name="crouch">Keep him crouched meanwhile (the latch's flinch: <c>crouched</c> is cleared only when it ends, L1876).</param>
        public HoldAct(ActId kind, ActId phase, double seconds, bool crouch = false) : base(kind, phase) { _seconds = seconds; Crouch = crouch; }

        public override bool Step(ChapterSim sim, in MotorInput input, double dt)
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
        private static readonly ActId CheckLabel = ActIds.Clip(ClipNames.CheckLabel);
        private readonly double _duration, _cancelAfter, _holdFor, _start;
        private readonly bool _cancel;
        private bool _fresh;
        private double _endAt = double.NaN;

        /// <param name="clipSeconds">The clip's length (<see cref="ClipSeconds"/>).</param>
        /// <param name="startClock">The game clock when it started (<c>a.start = game.clock</c>, L8108).</param>
        /// <param name="startsThisStep">True when created before #4 of the step it starts in (it then ignores that step, as the prototype's first <c>updateQuirk</c> sees time 0).</param>
        public QuirkAct(string clip, double clipSeconds, bool cancel, double startClock, double cancelAfter = 0, double holdFor = 0.8,
            bool startsThisStep = false) : base(ActIds.Quirk, ActIds.Clip(clip))
        {
            _duration = clipSeconds; _cancel = cancel; _cancelAfter = cancelAfter; _holdFor = holdFor; _start = startClock;
            _fresh = startsThisStep;
        }

        public override bool Step(ChapterSim sim, in MotorInput input, double dt)
        {
            if (_fresh) { _fresh = false; return true; }
            T += dt;
            bool moving = input.Move != 0 || input.JumpPressed;                                      // L3849
            bool cancel = _cancel || (_cancelAfter > 0 && sim.Clock - _start > _cancelAfter);        // L3850
            if (cancel && moving && T > 0.3) return false;                                            // L3851
            if (T >= _duration - 0.05)                                                                // L3852
            {
                if (Phase == CheckLabel)
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

namespace DeadLetter.Core.Scenes
{
    /// <summary>
    /// <c>playQuirk(clip, cancel)</c> (L3841–L3845) for a rule that starts one after the motor's step (#4's tail, #6, #7):
    /// a short clip where he stands, which stops him. One place for the conditions and the start, for every scene.
    /// <para>It is a <see cref="QuirkAct"/>, not the motor's quirk (#28): <see cref="D17Motor.PlayQuirk"/> resets the clip
    /// clock to 0 for the next step's #4, where the prototype's mixer has already advanced it by a step (it updates before
    /// <c>updatePlayer</c>), so a quirk started after the motor's step runs a step long (DL-05's label at #10038, DL-06's
    /// Proud at #13876). The motor's quirk is exact only when started inside #4 before the motor steps (DL-01's Proud, from
    /// <c>CrankDoneAct</c>).</para>
    /// </summary>
    public static class SceneQuirk
    {
        /// <summary><c>playQuirk</c>'s own conditions (L3842): no act (scene or motor), no hold, not riding or mantling, on the ground.</summary>
        public static bool CanStart(ChapterSim sim)
        {
            var m = sim.Motor;
            return !sim.Busy && m.Hold == HoldKind.None && m.Ride == null && !m.IsMantling && m.Grounded;
        }

        /// <summary>Starts <paramref name="clip"/> if <see cref="CanStart"/> (it plays from the next step's #4); returns whether it did.</summary>
        public static bool Start(ChapterSim sim, string clip, bool cancel)
        {
            if (!CanStart(sim)) return false;
            Stop(sim);
            sim.StartAct(new QuirkAct(clip, QuirkAct.ClipSeconds(clip), cancel, startClock: sim.Clock));
            return true;
        }

        /// <summary><c>game.vx = 0</c> (<see cref="D17Motor.Stop"/>): his yaw, clip, crouch and hands stay.</summary>
        public static void Stop(ChapterSim sim) => sim.Motor.Stop();
    }
}
