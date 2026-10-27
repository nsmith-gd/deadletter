using System;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Cycles
{
    public enum CycleClockState
    {
        /// <summary>Not running, every track at rest.</summary>
        Off,
        /// <summary>The phase advances; tracks follow the timeline.</summary>
        Running,
        /// <summary>The brake holds the phase and every track where they are.</summary>
        Braked,
        /// <summary>Stopped at <see cref="CycleClockParams.HoldAt"/> while the gate (and HoldWhile) hold; tracks stay put.</summary>
        Held,
        /// <summary>Stopped (gate dropped or reversed); tracks are going home at their return rates.</summary>
        Returning,
    }

    public enum CycleClockEvent
    {
        /// <summary>The cycle started from 0 (DL-13: the lesson bell, L5411). Index 1 = a restart after a reverse.</summary>
        Started,
        /// <summary>The phase passed 0: a new lap, including the first step (DL-13: bell and voice, L5419).</summary>
        Lap,
        /// <summary>The phase passed a named cue; Index = its index in <see cref="CycleClockParams.Cues"/>, Value = its time.</summary>
        Cue,
        /// <summary>A track crossed its threshold upward while running (DL-13: a step clacks out, L5424). Index = track.</summary>
        TrackUp,
        /// <summary>A track crossed its threshold downward while running (DL-13: a step thuds home). Index = track.</summary>
        TrackDown,
        /// <summary>It stopped: Index 0 = the gate dropped, 1 = reversed (something in the way). Tracks then go home.</summary>
        Stopped,
    }

    /// <summary>What <see cref="CycleClock.Engaged"/> reports.</summary>
    public enum CycleEngagedMode
    {
        /// <summary>The cycle is on (running, braked or held): the prototype's <c>lesson.on</c>, which <c>CycleBrake.Running</c> reads.</summary>
        On,
        /// <summary>A track is at or below <see cref="CycleClockParams.EngagedThreshold"/> and <see cref="CycleClockParams.EngagedAlso"/> holds (DL-14a: dark).</summary>
        TrackAtOrBelow,
    }

    public sealed class CycleClockParams
    {
        /// <summary>Seconds per lap.</summary>
        public double Period;
        /// <summary>Named moments on the timeline (see <see cref="CycleClockEvent.Cue"/>).</summary>
        public CycleCue[] Cues = Array.Empty<CycleCue>();
        /// <summary>Outputs (see <see cref="CycleTrack"/>).</summary>
        public CycleTrack[] Tracks = Array.Empty<CycleTrack>();

        /// <summary>Optional: runs only while this holds (an <see cref="IEngageable"/>). Unwired = always on (DL-14a).</summary>
        public MechanismId Gate;
        /// <summary>Optional: a <c>Catches/CycleBrake</c> (any <see cref="IEngageable"/>): engaged freezes phase and tracks. Must step first.</summary>
        public MechanismId Brake;
        /// <summary>
        /// Optional: while this holds and the cycle runs unbraked, it reverses to rest (DL-21: something on the table top).
        /// It does not start again until this has been clear for <see cref="ClearFor"/> seconds.
        /// </summary>
        public MechanismId Reverse;
        public double ClearFor;
        /// <summary>A (re)start waits until every track is home (DL-21: "all home, then ..."). DL-13 restarts at once.</summary>
        public bool RestartAtRest;
        /// <summary>
        /// Phase where it stops and holds while the gate holds (and <see cref="HoldWhile"/>, if wired): DL-23's table
        /// "holds at 0.75 while both stay lit". NaN = never.
        /// </summary>
        public double HoldAt = double.NaN;
        public MechanismId HoldWhile;

        /// <summary>Phase on reset; <see cref="SolvedPhase"/> from <see cref="SolvedAfter"/> on.</summary>
        public double ResetPhase, SolvedPhase;
        public string SolvedAfter;
        /// <summary>A gated cycle starts on (mid-lap at the phase) from this checkpoint on (DL-13: <c>lesson.on = p('gallery13')</c>).</summary>
        public string OnAfter;

        public CycleEngagedMode EngagedMode = CycleEngagedMode.On;
        public int EngagedTrack;
        public double EngagedThreshold;
        /// <summary>Optional: TrackAtOrBelow also needs this (DL-14a: both blinds down).</summary>
        public MechanismId EngagedAlso;

        /// <summary>
        /// DL-13: the repeated lesson (L291, L5409–L5436): 12 s while a pupil sits in the front seat (219.4 ± 0.06; the
        /// seat is the gate). Steps out at 1.0/2.6/4.2 and fold at 5.6/6.2/6.8, each moving at 1/0.35 per second; solid
        /// at 0.95 (L5243); they clack out and thud home through 0.5 (L5424). The tree grows 6.8–10.4, shrinks to 11.6;
        /// off, it shrinks at 1 per second (L5427–L5428). Past <c>gallery13</c> it resets on, braked, at 4.9 (L5236).
        /// Tracks: 0–2 the steps, 3 the tree.
        /// </summary>
        public static CycleClockParams Dl13Lesson()
        {
            double[] outAt = { 1.0, 2.6, 4.2 }, foldAt = { 5.6, 6.2, 6.8 };      // ATT.cycle, L291
            var tracks = new CycleTrack[4];
            for (int i = 0; i < 3; i++)
            {
                tracks[i] = CycleTrack.Window("step" + (i + 1), outAt[i], foldAt[i]);
                tracks[i].Slew = tracks[i].ReturnRate = 1 / 0.35;                 // dt / 0.35, L5423, L5428
                tracks[i].Threshold = 0.5;                                         // L5424
                tracks[i].OutAt = 0.95;                                            // attOut, L5243
            }
            tracks[3] = CycleTrack.Keys("tree", 0, 0, 6.8, 0, 10.4, 1, 11.6, 0);  // L5426
            tracks[3].ReturnRate = 1;                                              // tree − dt, L5428
            return new CycleClockParams
            {
                Period = 12, Tracks = tracks,
                Gate = "dl13.seat", Brake = "dl13.brake",
                SolvedPhase = 4.9, SolvedAfter = "gallery13", OnAfter = "gallery13",
            };
        }

        /// <summary>
        /// DL-14a: the night-light (L5896, L5931–L5932, L6219–L6228): 10 s, always on; the sun is bright 0–3, dims 3–4.5, dark
        /// 4.5–8, brightens 8–10. Engaged = the room is DARK: sun ≤ 0.05 and both blinds down (the blind drive's
        /// <see cref="IEngageable"/>, L6222), which <c>DoorParams.Dl14aDoor</c> reads. Past <c>corridor</c> it resets at 6
        /// (L5913–L5914). Track 0 is the sun.
        /// </summary>
        public static CycleClockParams Dl14aNightLight() => new CycleClockParams
        {
            Period = 10,                                                                // ATT3.cycle, L5896
            Tracks = new[] { CycleTrack.Keys("sun", 0, 1, 3, 1, 4.5, 0, 8, 0, 10, 1) },  // sun14a, L5931
            Brake = "dl14a.brake",
            SolvedPhase = 6, SolvedAfter = "corridor",
            EngagedMode = CycleEngagedMode.TrackAtOrBelow, EngagedTrack = 0, EngagedThreshold = 0.05,
            EngagedAlso = "dl14a.blinds",
        };

        /// <summary>
        /// DL-21 (chapter 2, no prototype; <c>docs/chapter2_plan.md</c> §4 "The evening routine",
        /// <c>docs/scenes/DL-21_the_evening_cycle.md</c> §11): the lower flat's 14 s routine while both places are loaded,
        /// braked by the table brake, reversed to rest by anything on the table top and restarted from 0 once the top has
        /// been clear for 1 s and everything is home. Tracks: 0 table height (0.3 ↔ 0.75), 1 hatch shutter bottom
        /// (1.85 ↔ 1.3), 2 ledge out (0..1, snaps up in 0.3 s). The table and shutter go home at their own speeds (0.45 m
        /// and 0.55 m in 2 s).
        /// </summary>
        public static CycleClockParams Dl21Evening(string places = "dl21.places", string brake = "dl21.brake", string tableTop = "dl21.tableTop")
        {
            var table = CycleTrack.Keys("table", 0, 0.3, 0.5, 0.3, 2.5, 0.75, 10, 0.75, 12, 0.3);
            table.Rest = 0.3; table.ReturnRate = 0.45 / 2; table.OutAt = 0.75;
            var shutter = CycleTrack.Keys("shutter", 0, 1.85, 2.5, 1.85, 4.5, 1.3, 7.5, 1.3, 9.5, 1.85);
            shutter.Rest = 1.85; shutter.ReturnRate = 0.55 / 2;
            var ledge = CycleTrack.Keys("ledge", 0, 0, 4.5, 0, 4.5, 1, 7.5, 1, 7.8, 0);
            ledge.ReturnRate = 1 / 0.3; ledge.OutAt = 1;
            return new CycleClockParams
            {
                Period = 14,
                Cues = new[]
                {
                    new CycleCue("chime", 0), new CycleCue("bowl1Lift", 1.8), new CycleCue("bowl1Set", 3.0),
                    new CycleCue("bowl2Lift", 3.8), new CycleCue("ledgeOut", 4.5), new CycleCue("bowl2Set", 5.0),
                    new CycleCue("windowEnd", 7.5), new CycleCue("takeBack", 7.6), new CycleCue("armClear", 9.5),
                    new CycleCue("tableDown", 10), new CycleCue("cock", 12),
                },
                Tracks = new[] { table, shutter, ledge },
                Gate = places, Brake = brake, Reverse = tableTop, ClearFor = 1, RestartAtRest = true,
            };
        }

        /// <summary>
        /// DL-23 (chapter 2, no prototype; <c>docs/scenes/DL-23_the_second_place.md</c> §11): with both dock lamps lit the
        /// table rises 1.2–3.2 s and the arm serves; bowl 2 lands at 14.4 and from 17.5 the routine holds while both stay lit.
        /// Lamp 2 off: the table goes home in 2 s. Track 0 is the table height.
        /// </summary>
        public static CycleClockParams Dl23Serving(string lamps = "dl23.lamps", string tableTop = "dl23.tableTop")
        {
            var table = CycleTrack.Keys("table", 0, 0.3, 1.2, 0.3, 3.2, 0.75);
            table.Rest = 0.3; table.ReturnRate = 0.45 / 2;
            return new CycleClockParams
            {
                Period = 17.5, HoldAt = 17.5,
                Cues = new[]
                {
                    new CycleCue("armRun", 0.2), new CycleCue("chimeHer", 0.6), new CycleCue("chimeHis", 1.1),
                    new CycleCue("armDown", 7.2), new CycleCue("bowl1Set", 9.2), new CycleCue("bowl2Take", 11.4),
                    new CycleCue("bowl2Set", 14.4), new CycleCue("served", 17.5),
                },
                Tracks = new[] { table },
                Gate = lamps, Reverse = tableTop, RestartAtRest = true,
            };
        }
    }

    /// <summary>
    /// The cycle driver (§4.13k "Cycle clocks"; chapter2_plan §7 "Cycle driver"): a phase that runs round a fixed period,
    /// a named timeline of cues, and tracks that follow it. It can be gated (runs only while a condition holds), braked
    /// (<c>Catches/CycleBrake</c>: phase and tracks freeze where they are), held at a point, and reversed to rest. Per step:
    /// <list type="number">
    /// <item>start: off, gate on, not braked, the reverse input clear for <see cref="CycleClockParams.ClearFor"/> (and every
    /// track home if <see cref="CycleClockParams.RestartAtRest"/>) → phase 0, <see cref="CycleClockEvent.Started"/> (L5411);</item>
    /// <item>stop: on and not braked, and the gate dropped (L5412) or the reverse input holds while running → off;</item>
    /// <item>advance (on, not braked, not held): phase += dt, wrapping at the period (L5417–L5418); cues and laps passed in
    /// [previous, new) are logged; tracks follow the timeline at the new phase (L5420–L5426);</item>
    /// <item>off: tracks go home at their return rates (L5428). Braked or held: nothing moves.</item>
    /// </list>
    /// DL-13's lesson and DL-14a's night-light are ported exactly; DL-21 and DL-23 are chapter 2 data (no prototype).
    /// The phase while off stays where it stopped (the dial hand, L5431). Signals: <see cref="Position"/> = phase, seconds;
    /// <see cref="Engaged"/> per <see cref="CycleEngagedMode"/>. Step order: gate, brake, reverse and EngagedAlso first.
    /// </summary>
    public sealed class CycleClock : Mechanism, IPositionSource, IEngageable
    {
        private const double Eps = 1e-9;
        private static readonly string[] TrackKeys = { "v0", "v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8", "v9", "v10", "v11" };

        private readonly CycleClockParams _p;
        private readonly double[] _v;
        private IEngageable _gate, _brake, _reverse, _holdWhile, _also;
        private bool _on, _reversed;
        private double _t, _clear;

        public CycleClock(MechanismId id, CycleClockParams p) : base(id)
        {
            _p = p;
            if (!(p.Period > 0)) throw new ArgumentException(id + " needs a period.");
            if (p.Tracks.Length > TrackKeys.Length) throw new ArgumentException(id + ": at most " + TrackKeys.Length + " tracks.");
            _v = new double[p.Tracks.Length];
        }

        public CycleClockState State => (CycleClockState)StateCode;
        /// <summary>Phase, seconds in [0, period).</summary>
        public double Position => _t;
        public double Phase => _t;
        /// <summary>The dial hand: phase / period, 0..1 (L5431, L6273).</summary>
        public double Dial => _t / _p.Period;
        /// <summary>On (running, braked or held): the prototype's <c>lesson.on</c>.</summary>
        public bool On => _on;
        public bool Engaged => _p.EngagedMode == CycleEngagedMode.On
            ? _on
            : _v[_p.EngagedTrack] <= _p.EngagedThreshold && (_also == null || _also.Engaged);
        public CycleClockParams Params => _p;
        public int TrackCount => _v.Length;
        public double Value(int track) => _v[track];
        /// <summary>The track is out (solid) at its <see cref="CycleTrack.OutAt"/>.</summary>
        public bool IsOut(int track) => _v[track] >= _p.Tracks[track].OutAt;
        /// <summary>Seconds the reverse input has been clear (capped).</summary>
        public double ClearTime => _clear;

        public int TrackIndex(string name)
        {
            for (int i = 0; i < _p.Tracks.Length; i++) if (_p.Tracks[i].Name == name) return i;
            throw new ArgumentException(Id + " has no track '" + name + "'.");
        }

        public int CueIndex(string name)
        {
            for (int i = 0; i < _p.Cues.Length; i++) if (_p.Cues[i].Name == name) return i;
            throw new ArgumentException(Id + " has no cue '" + name + "'.");
        }

        public override void Link(MechanismLinker link)
        {
            _gate = link.Read<IEngageable>(_p.Gate);
            _brake = link.Read<IEngageable>(_p.Brake);
            _reverse = link.Read<IEngageable>(_p.Reverse);
            _holdWhile = link.Read<IEngageable>(_p.HoldWhile);
            _also = link.Read<IEngageable>(_p.EngagedAlso);
        }

        /// <summary>Derived from the checkpoint and from the brake (already reset): DL-13 L5236, DL-14a L5913–L5914.</summary>
        public override void Reset(in Checkpoint cp)
        {
            _t = cp.Past(_p.SolvedAfter) ? _p.SolvedPhase : _p.ResetPhase;
            _on = _gate == null || cp.Past(_p.OnAfter);
            _reversed = false;
            _clear = 0;
            for (int i = 0; i < _v.Length; i++) _v[i] = _on ? _p.Tracks[i].At(_t) : _p.Tracks[i].Rest;
            Init((int)Classify(Braked(), HoldingAt()));
        }

        public override void Step(in StepContext ctx)
        {
            double dt = ctx.Dt;
            bool gate = _gate == null || _gate.Engaged, braked = Braked(), blocked = _reverse != null && _reverse.Engaged;
            _clear = blocked ? 0 : Math.Min(_clear + dt, 1e6);

            if (!_on && gate && !braked && !blocked && _clear >= _p.ClearFor - Eps && (!_p.RestartAtRest || AllHome()))
            {
                _on = true;                                                                     // L5411
                _t = 0;
                Emit(ctx, (int)CycleClockEvent.Started, _reversed ? 1 : 0);
                _reversed = false;
            }

            if (_on && !braked)
            {
                if (!gate) Stop(ctx, 0);                                                        // L5412
                else if (blocked && !HoldingAt()) { _reversed = true; Stop(ctx, 1); }
            }

            if (_on && !braked && !HoldingAt()) Advance(ctx, dt);
            else if (!_on)
                for (int i = 0; i < _v.Length; i++)                                             // L5428
                {
                    var tr = _p.Tracks[i];
                    _v[i] = tr.ReturnRate > 0 ? Home(_v[i], tr.Rest, tr.ReturnRate * dt) : tr.Rest;
                }

            Enter(ctx, (int)Classify(braked, HoldingAt()));
        }

        private void Advance(in StepContext ctx, double dt)
        {
            double prev = _t, t = _t + dt;                                                      // L5417
            bool hold = HoldEnabled() && t >= _p.HoldAt - Eps;
            if (hold) t = _p.HoldAt;
            bool wrapped = false, fromHold = prev == _p.HoldAt;                                 // leaving a hold: its cue has fired
            if (t >= _p.Period && !hold) { t -= _p.Period; wrapped = true; }                    // L5418
            _t = t;

            if (prev == 0 || wrapped) Emit(ctx, (int)CycleClockEvent.Lap);                      // L5419
            for (int c = 0; c < _p.Cues.Length; c++)
            {
                double at = _p.Cues[c].At;
                bool after = at > prev || at == prev && !fromHold;
                bool passed = wrapped ? after || at < t : after && (at < t || hold && at <= t);
                if (passed) Emit(ctx, (int)CycleClockEvent.Cue, c, at);
            }

            for (int i = 0; i < _v.Length; i++)                                                 // L5420–L5426
            {
                var tr = _p.Tracks[i];
                double was = _v[i], want = tr.At(t);
                double v = tr.Slew > 0 ? Smooth.MoveTowards(was, want, tr.Slew * dt) : want;
                _v[i] = v;
                if (was < tr.Threshold && v >= tr.Threshold) Emit(ctx, (int)CycleClockEvent.TrackUp, i);       // L5424
                else if (was > tr.Threshold && v <= tr.Threshold) Emit(ctx, (int)CycleClockEvent.TrackDown, i);
            }
        }

        /// <summary>Toward rest by at most <paramref name="max"/>, landing on it exactly (<c>max(0, v − dt / 0.35)</c>, L5428).</summary>
        private static double Home(double v, double rest, double max)
        {
            double d = rest - v;
            return d > max ? v + max : d < -max ? v - max : rest;
        }

        private void Stop(in StepContext ctx, int why)
        {
            _on = false;
            Emit(ctx, (int)CycleClockEvent.Stopped, why);
        }

        private bool Braked() => _brake != null && _brake.Engaged;
        private bool HoldEnabled() => !double.IsNaN(_p.HoldAt) && (_holdWhile == null || _holdWhile.Engaged);
        private bool HoldingAt() => _on && HoldEnabled() && _t >= _p.HoldAt - Eps;

        private bool AllHome()
        {
            for (int i = 0; i < _v.Length; i++) if (_v[i] != _p.Tracks[i].Rest) return false;
            return true;
        }

        private CycleClockState Classify(bool braked, bool held)
            => _on ? (braked ? CycleClockState.Braked : held ? CycleClockState.Held : CycleClockState.Running)
                : AllHome() ? CycleClockState.Off : CycleClockState.Returning;

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("t", _t);
            w.WriteBool("on", _on);
            w.WriteBool("reversed", _reversed);
            w.WriteDouble("clear", _clear);
            for (int i = 0; i < _v.Length; i++) w.WriteDouble(TrackKeys[i], _v[i]);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            _t = r.ReadDouble("t");
            _on = r.ReadBool("on");
            _reversed = r.ReadBool("reversed");
            _clear = r.ReadDouble("clear");
            for (int i = 0; i < _v.Length; i++) _v[i] = r.ReadDouble(TrackKeys[i]);
        }
    }
}
