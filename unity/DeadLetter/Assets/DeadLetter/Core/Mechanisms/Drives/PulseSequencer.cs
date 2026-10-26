using System;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Drives
{
    public enum PulseState
    {
        /// <summary>Every lamp is dark.</summary>
        Dark,
        /// <summary>At least one lamp is lit.</summary>
        Pulsing,
    }

    public enum PulseEvent
    {
        /// <summary>A lamp came on (the relay's click: the opening CUES L1585–L1588 and the pulse L8511–L8516 fall on these). Index = lamp, Value = the set's strength.</summary>
        LampLit,
    }

    /// <summary>A pulse schedule. Times are in <see cref="UnitsPerSecond"/> (DL-01 is authored in 24 fps frames).</summary>
    public sealed class PulseParams
    {
        public double UnitsPerSecond = 1;
        /// <summary>Per lamp: when it lights and when it goes off, after a set's start.</summary>
        public double[] OnAt, OffAt;
        /// <summary>Linear fade after OffAt.</summary>
        public double Fade;
        /// <summary>One-off sets: start and strength.</summary>
        public double[] SetStarts = new double[0], SetStrengths = new double[0];
        /// <summary>Then a set of strength 1 every <see cref="RepeatEvery"/> from <see cref="RepeatFrom"/>, for good.</summary>
        public double RepeatFrom = double.PositiveInfinity, RepeatEvery;
        /// <summary>Reset puts the clock at least here (<c>sceneTime = max(sceneTime, OPENING_FRAMES / FPS)</c>, L8095).</summary>
        public double ResetFloor;
        /// <summary>Calm: each lamp is a soft sine bump over CalmWindow at CalmGain instead of the hard on/off (L1541).</summary>
        public bool SoftWhenCalm;
        public double CalmWindow = 40, CalmGain = 0.7;
        /// <summary>Optional: while this is engaged, lamp <see cref="BlinkLamp"/> also blinks at <see cref="BlinkRate"/> rad/s (L6320).</summary>
        public MechanismId BlinkWhile;
        public int BlinkLamp = -1;
        public double BlinkRate = 6;

        /// <summary>DL-01: the three-lamp relay (L332, L1534–L1548, L8511–L8516). Lamp i lights at start + 12i, all go off at start + 30, fade over 10.</summary>
        public static PulseParams Dl01Relay() => new PulseParams
        {
            UnitsPerSecond = 24,                                      // FPS, L268
            OnAt = new double[] { 0, 12, 24 }, OffAt = new double[] { 30, 30, 30 }, Fade = 10,
            SetStarts = new double[] { 120, 168, 336 }, SetStrengths = new double[] { 0.55, 1.0, 1.0 },   // RELAY_SETS, L332
            RepeatFrom = 480, RepeatEvery = 144,                      // OPENING_FRAMES L269; every 6 s, L1536
            ResetFloor = 480,
            SoftWhenCalm = true,
        };

        /// <summary>
        /// The present-day service line (chapter 1): four pilot lamps, a 7 s cycle each, phases 2.3 s apart, lit for 0.25 s;
        /// DL-17's pump relay blinks while the tank refills (L5163–L5166, L6316–L6325).
        /// </summary>
        public static PulseParams AttRelays()
        {
            var on = new double[4];
            var off = new double[4];
            for (int i = 0; i < 4; i++)
            {
                on[i] = (7 - (i * 2.3) % 7) % 7;                     // lit while (clock + 2.3i) % 7 < 0.25
                off[i] = on[i] + 0.25;
            }
            return new PulseParams { OnAt = on, OffAt = off, RepeatFrom = 0, RepeatEvery = 7, BlinkWhile = "dl17.pump", BlinkLamp = 3 };
        }
    }

    /// <summary>
    /// Relay lamps on a schedule (§4.13e): fixed sets, then a set every period, each lamp lit over its window then
    /// fading. A pure function of its own clock, so replays and reloads land on the same phase. The clock survives
    /// respawns (Reset only raises it to <see cref="PulseParams.ResetFloor"/>); the opening calls <see cref="SetClock"/>.
    /// Signals: none (Runtime reads <see cref="Value"/>; D-17's answering lamps read <see cref="ValueAtUnits"/> 4 frames back, L1560).
    /// </summary>
    public sealed class PulseSequencer : Mechanism
    {
        private readonly PulseParams _p;
        private readonly double[] _values;
        private readonly double _span;
        private IEngageable _blink;
        private double _t;

        public PulseSequencer(MechanismId id, PulseParams p) : base(id)
        {
            if (p.OnAt == null || p.OffAt == null || p.OnAt.Length != p.OffAt.Length) throw new ArgumentException("OnAt and OffAt need one entry per lamp.");
            if (p.SetStarts.Length != p.SetStrengths.Length) throw new ArgumentException("One strength per set.");
            _p = p;
            _values = new double[p.OnAt.Length];
            for (int i = 0; i < p.OnAt.Length; i++) _span = Math.Max(_span, Math.Max(p.OffAt[i] + p.Fade, p.SoftWhenCalm ? p.OnAt[i] + p.CalmWindow : 0));
        }

        public PulseState State => (PulseState)StateCode;
        public int LampCount => _values.Length;
        /// <summary>The clock in schedule units (DL-01: frames since the opening began, <c>game.frame</c>).</summary>
        public double Units => _t * _p.UnitsPerSecond;
        public double Seconds => _t;
        /// <summary>Lamp brightness this step, 0..strength.</summary>
        public double Value(int lamp) => _values[lamp];

        /// <summary>Restart the clock (the opening: <c>sceneTime = 0</c>, L8061).</summary>
        public void SetClock(double units) => _t = units / _p.UnitsPerSecond;

        public override void Link(MechanismLinker link) => _blink = link.Read<IEngageable>(_p.BlinkWhile);

        public override void Reset(in Checkpoint cp)
        {
            _t = Math.Max(_t, _p.ResetFloor / _p.UnitsPerSecond);
            Evaluate(false);
            Init((int)(AnyLit() ? PulseState.Pulsing : PulseState.Dark));
        }

        public override void Step(in StepContext ctx)
        {
            double prev = Units;
            _t += ctx.Dt;
            double f = Units;
            for (int i = 0; i < _values.Length; i++) EmitLit(ctx, i, prev, f);
            Evaluate(ctx.Calm);
            Enter(ctx, (int)(AnyLit() ? PulseState.Pulsing : PulseState.Dark));
        }

        /// <summary>Lamp <paramref name="lamp"/>'s brightness at clock <paramref name="f"/> (units): <c>relayValue</c>, L1538–L1548.</summary>
        public double ValueAtUnits(int lamp, double f, bool calm = false)
        {
            bool soft = calm && _p.SoftWhenCalm;
            double v = 0;
            for (int s = 0; s < _p.SetStarts.Length; s++) v = Math.Max(v, LampValue(lamp, f, _p.SetStarts[s], _p.SetStrengths[s], soft));
            if (_p.RepeatEvery > 0 && f >= _p.RepeatFrom)
            {
                for (long k = (long)Math.Floor((f - _p.RepeatFrom) / _p.RepeatEvery); k >= 0; k--)
                {
                    double start = _p.RepeatFrom + k * _p.RepeatEvery;
                    if (start + _span <= f) break;
                    v = Math.Max(v, LampValue(lamp, f, start, 1.0, soft));
                }
            }
            return v;
        }

        private double LampValue(int i, double f, double start, double strength, bool soft)
        {
            double on = start + _p.OnAt[i], off = start + _p.OffAt[i];
            if (soft) return f >= on && f < on + _p.CalmWindow ? strength * _p.CalmGain * Math.Max(0, Math.Sin(Math.PI * (f - on) / _p.CalmWindow)) : 0;
            if (f >= on && f < off) return strength;
            if (f >= off && f < off + _p.Fade) return strength * (1 - (f - off) / _p.Fade);
            return 0;
        }

        private void Evaluate(bool calm)
        {
            double f = Units;
            bool blink = _blink != null && _blink.Engaged && Math.Sin(_t * _p.BlinkRate) > 0;
            for (int i = 0; i < _values.Length; i++)
            {
                double v = ValueAtUnits(i, f, calm);
                _values[i] = blink && i == _p.BlinkLamp ? Math.Max(v, 1) : v;
            }
        }

        private bool AnyLit()
        {
            for (int i = 0; i < _values.Length; i++) if (_values[i] > 0) return true;
            return false;
        }

        /// <summary>LampLit for every set whose lamp-on time falls in (prev, f].</summary>
        private void EmitLit(in StepContext ctx, int i, double prev, double f)
        {
            for (int s = 0; s < _p.SetStarts.Length; s++)
            {
                double on = _p.SetStarts[s] + _p.OnAt[i];
                if (prev < on && on <= f) Emit(ctx, (int)PulseEvent.LampLit, i, _p.SetStrengths[s]);
            }
            if (_p.RepeatEvery <= 0 || double.IsInfinity(_p.RepeatFrom)) return;
            double base0 = _p.RepeatFrom + _p.OnAt[i];
            long lo = Math.Max(0, (long)Math.Floor((prev - base0) / _p.RepeatEvery) + 1);
            long hi = (long)Math.Floor((f - base0) / _p.RepeatEvery);
            for (long k = lo; k <= hi; k++) Emit(ctx, (int)PulseEvent.LampLit, i, 1.0);
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("t", _t);
            for (int i = 0; i < _values.Length; i++) w.WriteDouble("lamp" + i, _values[i]);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            _t = r.ReadDouble("t");
            for (int i = 0; i < _values.Length; i++) _values[i] = r.ReadDouble("lamp" + i);
        }
    }
}
