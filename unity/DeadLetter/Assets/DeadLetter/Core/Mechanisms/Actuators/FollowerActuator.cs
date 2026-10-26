using System;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Actuators
{
    public enum FollowerState { Still, Rising, Falling }

    public enum FollowerEvent
    {
        /// <summary>The winding ratchet ticks every <see cref="FollowerParams.TickStep"/> of rise (L2382).</summary>
        Tick,
        /// <summary>It landed falling faster than <see cref="FollowerParams.SlamSpeed"/>; Value = impact speed, m/s (L2385–L2386).</summary>
        Slam,
        /// <summary>The slam startled D-17: he was within <see cref="FollowerParams.StartleRadius"/> and not in an act (L2387).</summary>
        Startle,
    }

    public sealed class FollowerParams
    {
        /// <summary>What it follows (an <see cref="ILoad"/>): target height = min(1, load) · <see cref="OpenHeight"/>.</summary>
        public MechanismId Source;
        /// <summary>Lane x of the gate (for the head guard and the startle).</summary>
        public double X;
        public double OpenHeight;
        public double RiseSpeed = 0.55, FallAccel = 9, FallMax = 3.2, SlamSpeed = 0.8;
        /// <summary>Ratchet tick spacing while rising; 0 = silent.</summary>
        public double TickStep = 0.05;
        /// <summary>Startle radius on a slam; 0 = never.</summary>
        public double StartleRadius = 2.8;
        /// <summary>"Never onto him": within GuardHalf of X it stays above his head + HeadGap (HALF + 0.06, L2392).</summary>
        public double GuardHalf = 0.17 + 0.06, StandHeight = 0.76, CrouchHeight = 0.58, HeadGap = 0.03;   // HALF, STAND_H, CROUCH_H L309–L310

        /// <summary>DL-03: the plate's gate, opening = load × 1.2 (L323–L324, L2380–L2392).</summary>
        public static FollowerParams Dl03Gate() => new FollowerParams
        {
            Source = "dl03.plate", X = 13 + 17.6, OpenHeight = 1.2,                   // GATE_X = OFF2 + 17.6, GATE_OPEN_H
        };

        /// <summary>DL-12: the register gate, 1.3 m when someone is on the strip and the coat is on peg 7 (L5400–L5406).</summary>
        public static FollowerParams Dl12Gate() => new FollowerParams
        {
            Source = "dl12.strip", X = 209.4, OpenHeight = 1.3,                       // ATT.gate, L287
            RiseSpeed = 0.5, FallAccel = 8, FallMax = 3, TickStep = 0, StartleRadius = 0,
        };
    }

    /// <summary>
    /// A gate that follows a load: it winds up slowly, drops fast and slams, and never comes down onto D-17
    /// (§4.13a "Follower gates"; DL-03 L2380–L2392, DL-12 L5400–L5406). Signals: <see cref="Position"/> = height, metres.
    /// </summary>
    public sealed class FollowerActuator : Mechanism, IPositionSource
    {
        private readonly FollowerParams _p;
        private ILoad _source;
        private double _ticked;

        public FollowerActuator(MechanismId id, FollowerParams p) : base(id) { _p = p; }

        public FollowerState State => (FollowerState)StateCode;
        /// <summary>Gate height, metres.</summary>
        public double Position { get; private set; }
        /// <summary>Fall speed, m/s (0 while rising or still).</summary>
        public double Velocity { get; private set; }

        public double Target => Math.Min(1, _source.Load) * _p.OpenHeight;

        public override void Link(MechanismLinker link) => _source = link.Read<ILoad>(_p.Source)
            ?? throw new InvalidOperationException(Id + " needs a Source.");

        /// <summary>Starts at the source's target, as <c>gate.y = load · GATE_OPEN_H</c> (L8030).</summary>
        public override void Reset(in Checkpoint cp)
        {
            Position = _ticked = Target;
            Velocity = 0;
            Init((int)FollowerState.Still);
        }

        public override void Step(in StepContext ctx)
        {
            double want = Target, prev = Position, y = Position, dt = ctx.Dt;
            if (want > y)
            {
                Velocity = 0;
                y = Math.Min(want, y + _p.RiseSpeed * dt);
                if (_p.TickStep > 0 && Math.Abs(y - _ticked) > _p.TickStep) { _ticked = y; Emit(ctx, (int)FollowerEvent.Tick); }
            }
            else if (want < y)
            {
                Velocity = Math.Min(_p.FallMax, Velocity + _p.FallAccel * dt);
                y = Math.Max(want, y - Velocity * dt);
                if (y <= want + 1e-4 && Velocity > _p.SlamSpeed)
                {
                    Emit(ctx, (int)FollowerEvent.Slam, 0, Velocity);
                    var pl = ctx.Player;
                    if (_p.StartleRadius > 0 && Math.Abs(pl.X - _p.X) < _p.StartleRadius && !pl.Busy) Emit(ctx, (int)FollowerEvent.Startle);
                    Velocity = 0;
                }
                _ticked = y;
            }

            var p = ctx.Player;
            if (Math.Abs(p.X - _p.X) < _p.GuardHalf)                                                         // L2392
                y = Math.Max(y, Math.Min(prev, p.Y + (p.Crouched ? _p.CrouchHeight : _p.StandHeight) + _p.HeadGap));

            Position = y;
            Enter(ctx, (int)(y > prev ? FollowerState.Rising : y < prev ? FollowerState.Falling : FollowerState.Still));
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("y", Position);
            w.WriteDouble("v", Velocity);
            w.WriteDouble("ticked", _ticked);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            Position = r.ReadDouble("y");
            Velocity = r.ReadDouble("v");
            _ticked = r.ReadDouble("ticked");
        }
    }
}
