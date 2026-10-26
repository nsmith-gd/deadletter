using System;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Cues
{
    /// <summary>Who has D-17 during a moment.</summary>
    public enum MomentControl
    {
        /// <summary>No moment, or control has come back.</summary>
        Player,
        /// <summary>Before <c>lock</c>: input is ignored.</summary>
        Locked,
        /// <summary>From <c>lock</c>: input is still withheld, but any input cuts the hold and hands control back.</summary>
        Cuttable,
    }

    /// <summary>
    /// The directed-moment state machine around a <see cref="CueClock"/> (index.html <c>startMoment</c>, <c>momentShot</c>,
    /// <c>momentFree</c>, <c>voicesHeld</c>, L950–L958; reset L8017). It gates the motor's input: while a moment holds
    /// him, <see cref="GateInput"/> returns <see cref="MotorInput.None"/>; on the step control returns it reports
    /// <see cref="ControlReturned"/> (the act ends; that step's input is consumed, as the prototype's act update returns),
    /// and from the next step the raw input passes.
    /// </summary>
    public sealed class MomentDirector
    {
        private readonly CueClock _clock;
        private bool _released;

        public MomentDirector(IMusicClock music, double prime = 0)
        {
            _clock = new CueClock(music, prime);
        }

        public CueClock Clock => _clock;
        public DirectedMoment Current { get; private set; }
        /// <summary><c>game.momentCut</c>: the player cut the hold short after <c>lock</c>.</summary>
        public bool Cut { get; private set; }
        /// <summary>True on the step control came back (cleared by the next <see cref="GateInput"/>).</summary>
        public bool ControlReturned { get; private set; }
        /// <summary>Moment time at which control came back (for the ring C light's switch-off, L4606), or null.</summary>
        public double? ReturnedAt { get; private set; }

        /// <summary><c>startMoment(name)</c>, L950. Runtime then schedules the cue and calls <c>Clock.Scheduled</c>.</summary>
        public void Start(DirectedMoment moment, double simTime, bool musicAvailable)
        {
            Current = moment ?? throw new ArgumentNullException(nameof(moment));
            Cut = false;
            _released = false;
            ControlReturned = false;
            ReturnedAt = null;
            _clock.Begin(moment.Name, simTime, musicAvailable);
        }

        /// <summary>Checkpoint reset (L8017).</summary>
        public void End()
        {
            _clock.End();
            Current = null;
            Cut = false;
            _released = false;
            ControlReturned = false;
            ReturnedAt = null;
        }

        /// <summary>The current moment's time, or null.</summary>
        public double? Time(double simTime) => Current == null ? null : _clock.Time(Current.Name, simTime);

        /// <summary><c>momentShot</c>: the moment's time while its shot holds; null once it lets go or was cut.</summary>
        public double? ShotTime(string name, double simTime)
        {
            double? t = _clock.Time(name, simTime);
            DirectedMoment m = PrologueMoments.Find(name) ?? (Current != null && Current.Name == name ? Current : null);
            return t.HasValue && m != null && !Cut && t.Value < m.Release ? t : null;
        }

        /// <summary><c>voicesHeld()</c>: voices, tannoys and distant clanks wait while a moment's shot holds (L958).</summary>
        public bool VoicesHeld(double simTime) => Current != null && ShotTime(Current.Name, simTime) != null;

        /// <summary>
        /// <c>momentFree(name, t)</c>, L953–L957: true when control may return now. After <c>lock</c>, any input cuts the
        /// hold (<see cref="Cut"/>). <see cref="DirectedMoment.ActLetsGoAt"/> applies the awe act's own limit.
        /// </summary>
        public bool Free(DirectedMoment m, double? t, bool anyInput)
        {
            if (t == null || t.Value >= m.FreeAt) return true;
            if (t.Value >= m.Lock && anyInput) { Cut = true; return true; }
            return false;
        }

        /// <summary>Who has him at moment time <paramref name="t"/> (null = no moment).</summary>
        public MomentControl ControlAt(double? t)
        {
            if (Current == null || _released || t == null) return MomentControl.Player;
            if (t.Value >= Current.FreeAt) return MomentControl.Player;
            return t.Value >= Current.Lock ? MomentControl.Cuttable : MomentControl.Locked;
        }

        /// <summary>The prototype's "a touch of the controls" (L955): left/right/stick, use or jump pressed.</summary>
        public static bool AnyInput(in MotorInput i) => i.Move != 0 || i.UsePressed || i.JumpPressed;

        /// <summary>
        /// Gate one step's motor input. <paramref name="actReady"/> is the moment's act condition before it consults
        /// <c>momentFree</c>: kin's realise act has gone idle (clip frame ≥ 155 and t &gt; 9.5, L2313); refuge's awe clip is
        /// done (L3389); ringc's car has gone (L4606). The window moment never frees: the ending sequence owns him until
        /// <see cref="End"/>.
        /// </summary>
        public MotorInput GateInput(in MotorInput raw, double simTime, bool actReady = true)
        {
            ControlReturned = false;
            if (Current == null || _released) return raw;
            double? t = Time(simTime);
            if (actReady && Current.ReturnsControl && Free(Current, t, AnyInput(raw)))
            {
                _released = true;
                ControlReturned = true;
                ReturnedAt = t;
            }
            return MotorInput.None;
        }

        /// <summary>True while the moment still holds him (input is withheld).</summary>
        public bool Holding => Current != null && !_released;
    }
}
