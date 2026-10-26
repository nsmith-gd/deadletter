using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Folding
{
    public enum FoldingLeafState
    {
        /// <summary>Stowed on its frame or in its recess.</summary>
        Folded,
        /// <summary>Swinging down toward its stop.</summary>
        Unfolding,
        /// <summary>Down on its stop: a fixed, standable surface.</summary>
        Down,
        /// <summary>Swinging up toward its frame.</summary>
        Folding,
        /// <summary>Came down onto another leaf or object and rests on it; stays there (counterbalanced) until Use sends it back.</summary>
        Propped,
        /// <summary>
        /// Stopped against D-17 (either way), or against something resting on it while folding; carries on by itself once
        /// the way is clear (it never crushes, and never lifts what rests on it).
        /// </summary>
        Waiting,
    }

    public enum FoldingLeafEvent
    {
        /// <summary>It met something and stopped: Index 0 = another volume (the quilt's soft thump), 1 = D-17. Value = angle, degrees.</summary>
        Met,
    }

    public sealed class FoldingLeafParams
    {
        /// <summary>Where he uses its handle.</summary>
        public Station Station;
        public ActProfile Profile = new ActProfile("Pull");
        /// <summary>The Use takes effect at this clip frame (Pull f31, as the latch, L1874) and the act ends at <see cref="EndFrame"/>.</summary>
        public double ToggleFrame = ClipTimings.PullEvents.Release, EndFrame = ClipTimings.PullEvents.Flinch;

        /// <summary>Seconds for a full swing either way (it moves only on input and is counterbalanced: it stays wherever it stops).</summary>
        public double Travel = 1.4;
        /// <summary>The hinge in the cross-section (depth from the back wall, height) and the leaf's angle folded and down, degrees from level (counter-clockwise, depth → height).</summary>
        public double HingeD, HingeY, FoldedDeg = 90, DownDeg;
        /// <summary>Its swept volume, in its own frame.</summary>
        public LeafBox[] Boxes = Array.Empty<LeafBox>();
        /// <summary>
        /// Fully folded it lies in its recess or flat on its frame, out of the shared space, and blocks nothing (DL-18: the
        /// bed "folds into its recess", the bench is "a vertical leaf on the frame").
        /// </summary>
        public bool StowedClear = true;
        /// <summary>The free edge's point in the leaf's frame (for the view and for "free edge at about 0.82", DL-18 §3).</summary>
        public double EdgeU, EdgeV;
        /// <summary>What it stops against (each an <see cref="ISweptVolume"/>; leaves on one frame name each other).</summary>
        public MechanismId[] Blockers = Array.Empty<MechanismId>();

        /// <summary>D-17's body for "stops and waits": half-width (HALF, L310), heights (STAND_H, CROUCH_H, L309) and the lane depth he fills.</summary>
        public double BodyHalf = 0.17, StandHeight = 0.76, CrouchHeight = 0.58, BodyD0 = 0.10, BodyD1 = 0.44;
        public double Margin = 1e-6;

        /// <summary>Down at the start; from <see cref="SolvedAfter"/> on it resets to <see cref="SolvedDown"/> (solved states persist).</summary>
        public bool StartsDown;
        public string SolvedAfter;
        public bool SolvedDown;

        // DL-18 Room for One: docs/scenes/DL-18_room_for_one.md §3 (layout, "The two leaves"), §11 (grey-box). No prototype.

        /// <summary>
        /// DL-18: the fold bed, 351.9–353.9, 0.55 deep and 0.45 high, hinged on the floor at its back edge, folding up into its
        /// recess in 1.4 s; the quilt heaped at its foot to 0.7. Down at the start, folded once past <c>terrace</c>. Use at
        /// the foot rail (353.9) from the floor at 353.6–354.15, from beyond the bed's foot.
        /// </summary>
        public static FoldingLeafParams Dl18Bed() => new FoldingLeafParams
        {
            Station = new Station(standX: 354.0, reach: 0.275, face: -1, reachX: 353.875),
            Travel = 1.4,
            HingeD = 0, HingeY = 0,
            Boxes = new[]
            {
                new LeafBox(351.9, 353.9, 0, 0.55, 0, 0.45),      // the bed
                new LeafBox(353.3, 353.9, 0.25, 0.55, 0.45, 0.7), // the quilt heaped at the foot, to 0.7, on the bed's front half
            },
            EdgeU = 0.55, EdgeV = 0.45,
            Blockers = new MechanismId[] { "dl18.bench" },
            StartsDown = true, SolvedAfter = "terrace", SolvedDown = false,
        };

        /// <summary>
        /// DL-18: the fold bench, 353.4–354.2, a 0.45 leaf hinged along its back edge at 0.6: folded vertical (0.6–1.05),
        /// down to its stop as a seat at 0.6 in 1.2 s. Use at the strap (353.45) from the floor or the bed: a tug (Tug f19,
        /// the act over at f43). Folded at the start, down once past <c>terrace</c>.
        /// </summary>
        public static FoldingLeafParams Dl18Bench() => new FoldingLeafParams
        {
            Station = new Station(standX: 353.45, reach: 0.3, face: +1, floorY: 0.45),
            Profile = new ActProfile("Tug"),
            ToggleFrame = ClipTimings.TugEvents.Click, EndFrame = ClipTimings.TugEvents.Done,
            Travel = 1.2,
            HingeD = 0, HingeY = 0.6,
            Boxes = new[] { new LeafBox(353.4, 354.2, 0, 0.45, -0.04, 0) },  // seat top at 0.6; its underside clears the folded bed (0.55)
            EdgeU = 0.45, EdgeV = 0,
            Blockers = new MechanismId[] { "dl18.bed" },
            StartsDown = false, SolvedAfter = "terrace", SolvedDown = true,
        };
    }

    /// <summary>
    /// A hinged leaf (fold bed, fold bench, workbench; chapter2_plan §7 "Folding furniture", DL-18 §3–§4, §11). It moves
    /// only on Use, at a steady rate, and is counterbalanced: it stays wherever it stops. Each step it swings toward its
    /// target unless its swept volume would meet another <see cref="ISweptVolume"/> on its frame (it stops there as
    /// <see cref="FoldingLeafState.Propped"/> if it was coming down, or waits if it was folding) or D-17 (it stops as
    /// <see cref="FoldingLeafState.Waiting"/> and resumes once he is clear): it never crushes. Use reverses it from any state. Contact is found by bisection, so a leaf rests touching
    /// what stopped it. No prototype exists; the type is new for chapter 2. Signals: <see cref="Position"/> = 0 folded .. 1
    /// down, <see cref="Engaged"/> = down on its stop (standable).
    /// </summary>
    public sealed class FoldingLeaf : StationMechanism, ISweptVolume, IPositionSource, IEngageable
    {
        private const int BisectSteps = 24;

        private readonly FoldingLeafParams _p;
        private readonly ISweptVolume[] _blockers;
        private ActInput _act;
        private bool _done;
        private double _target;

        public FoldingLeaf(MechanismId id, FoldingLeafParams p) : base(id, p.Station)
        {
            _p = p;
            if (!(p.Travel > 0)) throw new ArgumentException(id + " needs a travel time.");
            _blockers = new ISweptVolume[p.Blockers.Length];
        }

        public FoldingLeafState State => (FoldingLeafState)StateCode;
        /// <summary>0 folded .. 1 down.</summary>
        public double Position { get; private set; }
        /// <summary>Down on its stop: a fixed step. Propped, it is not standable (DL-18: he slides off).</summary>
        public bool Engaged => State == FoldingLeafState.Down;
        public bool Standable => Engaged;
        /// <summary>Where it is going: 0 folded, 1 down.</summary>
        public double Target => _target;
        /// <summary>Its angle from level, degrees.</summary>
        public double AngleDeg => AngleAt(Position);
        public override ActProfile Profile => _p.Profile;

        /// <summary>The free edge in the cross-section (depth, height).</summary>
        public void FreeEdge(out double d, out double y)
        {
            double a = AngleDeg * Math.PI / 180, c = Math.Cos(a), s = Math.Sin(a);
            d = _p.HingeD + _p.EdgeU * c - _p.EdgeV * s;
            y = _p.HingeY + _p.EdgeU * s + _p.EdgeV * c;
        }

        public int VolumeCount => _p.StowedClear && Position <= 0 ? 0 : _p.Boxes.Length;
        public SweptBox Volume(int i) => BoxAt(i, Position);

        public override void Link(MechanismLinker link)
        {
            for (int i = 0; i < _blockers.Length; i++)
                _blockers[i] = link.ReadAnyOrder<ISweptVolume>(_p.Blockers[i])                 // leaves block each other: either order
                    ?? throw new InvalidOperationException(Id + ": blocker " + i + " is unwired.");
        }

        public override void Reset(in Checkpoint cp)
        {
            bool down = cp.Past(_p.SolvedAfter) ? _p.SolvedDown : _p.StartsDown;
            Position = _target = down ? 1 : 0;
            Init((int)(down ? FoldingLeafState.Down : FoldingLeafState.Folded));
            _done = false;
            _act.Clear();
        }

        protected override bool CanUse(in InteractionQuery q) => true;

        public override bool OnActFrame(in ActFrame f)
        {
            _act.Receive(f);
            return ClipClock.Reached(f.Frame, _p.EndFrame);
        }

        public override void Step(in StepContext ctx)
        {
            _act.Take();
            if (_act.Active)
            {
                if (_act.Started) _done = false;
                if (!_done && ClipClock.Reached(_act.Frame, _p.ToggleFrame))
                {
                    _done = true;
                    _target = _target > 0.5 ? 0 : 1;
                    Enter(ctx, (int)(_target > 0.5 ? FoldingLeafState.Unfolding : FoldingLeafState.Folding));
                }
            }

            var st = State;
            if (st != FoldingLeafState.Unfolding && st != FoldingLeafState.Folding && st != FoldingLeafState.Waiting) return;

            double p = Position, next = Smooth.MoveTowards(p, _target, ctx.Dt / _p.Travel);
            int hit = Hit(next, ctx.Player);
            if (hit == 0)
            {
                Position = next;
                Enter(ctx, (int)(next == _target ? (_target > 0.5 ? FoldingLeafState.Down : FoldingLeafState.Folded)
                    : _target > 0.5 ? FoldingLeafState.Unfolding : FoldingLeafState.Folding));
                return;
            }

            if (Hit(p, ctx.Player) == 0)                                                       // creep up to the contact
            {
                double lo = p, hi = next;
                for (int k = 0; k < BisectSteps; k++)
                {
                    double mid = (lo + hi) / 2;
                    if (Hit(mid, ctx.Player) == 0) lo = mid; else hi = mid;
                }
                Position = lo;
            }
            var stop = hit == 1 && _target > 0.5 ? FoldingLeafState.Propped : FoldingLeafState.Waiting;
            if (st != stop) Emit(ctx, (int)FoldingLeafEvent.Met, hit == 2 ? 1 : 0, AngleDeg);
            Enter(ctx, (int)stop);
        }

        /// <summary>0 = free at <paramref name="pos"/>, 1 = meets a blocker's volume, 2 = meets D-17.</summary>
        private int Hit(double pos, in PlayerPose pl)
        {
            int n = _p.StowedClear && pos <= 0 ? 0 : _p.Boxes.Length;
            if (n == 0) return 0;
            var body = SweptBox.Aligned(pl.X - _p.BodyHalf, pl.X + _p.BodyHalf, _p.BodyD0, _p.BodyD1,
                pl.Y, pl.Y + (pl.Crouched ? _p.CrouchHeight : _p.StandHeight));
            for (int i = 0; i < n; i++)
            {
                var mine = BoxAt(i, pos);
                if (SweptBox.Overlap(mine, body, _p.Margin)) return 2;
                for (int b = 0; b < _blockers.Length; b++)
                {
                    var other = _blockers[b];
                    for (int j = 0, m = other.VolumeCount; j < m; j++)
                        if (SweptBox.Overlap(mine, other.Volume(j), _p.Margin)) return 1;
                }
            }
            return 0;
        }

        private double AngleAt(double pos) => _p.FoldedDeg + (_p.DownDeg - _p.FoldedDeg) * pos;

        private SweptBox BoxAt(int i, double pos)
        {
            var b = _p.Boxes[i];
            double a = AngleAt(pos) * Math.PI / 180, c = Math.Cos(a), s = Math.Sin(a);
            double uc = (b.U0 + b.U1) / 2, vc = (b.V0 + b.V1) / 2;
            return new SweptBox(b.X0, b.X1, _p.HingeD + uc * c - vc * s, _p.HingeY + uc * s + vc * c, c, s,
                (b.U1 - b.U0) / 2, (b.V1 - b.V0) / 2);
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("p", Position);
            w.WriteDouble("target", _target);
            w.WriteBool("done", _done);
            _act.Write(w);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            Position = r.ReadDouble("p");
            _target = r.ReadDouble("target");
            _done = r.ReadBool("done");
            _act.Read(r);
        }
    }
}
