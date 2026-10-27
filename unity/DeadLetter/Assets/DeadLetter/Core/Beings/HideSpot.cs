using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Beings
{
    public sealed class HideSpotParams
    {
        /// <summary>The recess along the lane; Use answers inside it, inset by <see cref="Inset"/> each side (L5980).</summary>
        public double X0, X1, Inset = 0.15;
        /// <summary>Unity z he backs in to (<c>ATT3.hideZ</c> −0.62 negated, L5898).</summary>
        public double HideZ = 0.62;
        /// <summary>He must be on the floor: y &lt; 0.05 (L5980).</summary>
        public double MaxY = 0.05;
        /// <summary>Optional: it is open only while this <see cref="IEngageable"/> is engaged (the bay, once the figure is out of it).</summary>
        public MechanismId OpenWhen;

        /// <summary>DL-14b niche A, 263.6–264.5 (<c>ATT3.nicheA</c>, L5898, L5980).</summary>
        public static HideSpotParams Dl14bNicheA() => new HideSpotParams { X0 = 263.6, X1 = 264.5 };

        /// <summary>DL-14b's bay, 269.4–270.4, once the figure has been nudged out of it (<c>ATT3.bay</c>, L5898, L5980).</summary>
        public static HideSpotParams Dl14bBay(MechanismId figureOut) => new HideSpotParams { X0 = 269.4, X1 = 270.4, OpenWhen = figureOut };
    }

    /// <summary>
    /// A recess D-17 can hide in from a beam (DL-14b, L5973, L5980, L6011, L6111–L6125): Use inside it walks him to its
    /// middle (keeping his facing), and the motor's hide act backs him in to <see cref="HideSpotParams.HideZ"/> and crouches
    /// him there; <c>PlayerPose.Hiding</c> and his z tell a beam he is hidden (EscortTrolley: z &gt; 0.4). No state of its own.
    /// </summary>
    public sealed class HideSpot : Mechanism, IHideSpot
    {
        private readonly HideSpotParams _p;
        private IEngageable _open;

        public HideSpot(MechanismId id, HideSpotParams p) : base(id)
        {
            _p = p ?? throw new ArgumentNullException(nameof(p));
        }

        public InteractionCategory Category => InteractionCategory.Fixed;
        public double HideZ => _p.HideZ;
        public double CentreX => (_p.X0 + _p.X1) / 2;

        public override void Link(MechanismLinker link) => _open = link.ReadAnyOrder<IEngageable>(_p.OpenWhen);

        /// <summary><c>'att:hide'</c>, L5980: on the floor, inside the recess (inset 0.15), and open.</summary>
        public bool Offer(in InteractionQuery q, out StationPose pose)
        {
            pose = default;
            if (!(q.Y < _p.MaxY) || !(q.X > _p.X0 + _p.Inset && q.X < _p.X1 - _p.Inset)) return false;
            if (_open != null && !_open.Engaged) return false;
            pose = new StationPose(CentreX, q.Facing, 0, CentreX);                                   // L6011
            return true;
        }

        public bool IsAvailable(in InteractionQuery q) => Offer(q, out _);

        public override void Reset(in Checkpoint cp) { }
        public override void Step(in StepContext ctx) { }
        protected override void WriteFields(ISnapshotWriter w) { }
        protected override void ReadFields(ISnapshotReader r) { }
    }
}
