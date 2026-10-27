using System;
using DeadLetter.Core.Interaction;

namespace DeadLetter.Core.Push
{
    /// <summary>
    /// The other face of a <see cref="Pushable"/> (pass 10's twins, L4287–L4295; DL-03's trolley has a push bar at each
    /// end, <c>grabL</c>/<c>grabR</c>, L2255–L2258): he grabs it from the opposite side and moves the same thing. Everything
    /// is the base's except <see cref="Side"/> and, optionally, the grip reach (<c>bodyAlt.fwd = 0.06</c>, L4295). It is
    /// not a mechanism: register it with the resolver beside the base (<c>SceneDef.Interactables</c>).
    /// </summary>
    public sealed class PushTwin : IPushable
    {
        private readonly double _forwardReach, _backReach;

        /// <param name="forwardReach">This face's grip reach in front of its stand point (NaN = the base's).</param>
        /// <param name="backReach">Behind it (NaN = the base's).</param>
        public PushTwin(Pushable of, double forwardReach = double.NaN, double backReach = double.NaN)
        {
            Base = of ?? throw new ArgumentNullException(nameof(of));
            if (of.TipsIntoPit) throw new ArgumentException(of.Id + " tips into a pit: it is only pushed one way (L4286).");
            _forwardReach = forwardReach; _backReach = backReach;
        }

        /// <summary>The pushable this is a face of: the one state both faces share.</summary>
        public Pushable Base { get; }

        public InteractionCategory Category => InteractionCategory.Push;
        public bool IsAvailable(in InteractionQuery q) => Base.IsAvailableFrom(Side, q);

        public double X => Base.X;
        public int Side => -Base.Side;
        public double Gap => Base.Gap;
        public double Speed => Base.Speed;
        public double Accel => Base.Accel;
        public bool LetGoAtMax => Base.LetGoAtMax;
        public double Min => Base.Min;
        public double Max => Base.Max;
        public double FloorY => Base.FloorY;
        public double Z => Base.Z;
        public double ForwardReach => double.IsNaN(_forwardReach) ? Base.ForwardReach : _forwardReach;
        public double BackReach => double.IsNaN(_backReach) ? Base.BackReach : _backReach;
        public bool TipsIntoPit => false;
        public bool HasDetents => Base.HasDetents;

        public void MoveTo(double x, double velocity) => Base.MoveTo(x, velocity);
        public void SetAtLip(bool atLip) => Base.SetAtLip(atLip);
        public void OnReleased(bool atLip) => Base.OnReleased(atLip);
        public void OnShoved() => Base.OnShoved();
        public void OnTravelEnd() => Base.OnTravelEnd();

        public override string ToString() => "PushTwin " + Base.Id;
    }
}
