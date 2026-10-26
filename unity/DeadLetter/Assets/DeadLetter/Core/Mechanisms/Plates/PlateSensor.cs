using System;

namespace DeadLetter.Core.Mechanisms.Plates
{
    /// <summary>Where a loose thing rests, as the prototype's item and pushable <c>state</c> strings say.</summary>
    public enum BodySupport
    {
        /// <summary>Not in the lane (stored on a hook, gone down a chute): weighs on nothing.</summary>
        Away,
        /// <summary>On the floor (<c>'floor'</c>, <c>'free'</c>).</summary>
        Floor,
        /// <summary>On the floor, in his hands (<c>game.hold === 'push'</c>): weighs as on the floor.</summary>
        Pushed,
        /// <summary>Riding something that moves (<c>'trolley'</c>): weighs where its carrier is (<see cref="IPlateBody.SupportX"/>).</summary>
        Carrier,
        /// <summary>Lifted by D-17 (<c>'carried'</c>): weighs with him.</summary>
        Carried,
        /// <summary>Set into its receiver (<c>'tray'</c>, <c>'car'</c>, <c>'peg'</c>).</summary>
        Placed,
    }

    /// <summary>
    /// A loose thing a plate can weigh: an item (U-12 Carry) or a pushable (Push). This is the Plates family's input
    /// signal; it lives here until the Carry/Push families land and can move to Signals.cs.
    /// </summary>
    public interface IPlateBody
    {
        /// <summary>Lane x of its centre, metres.</summary>
        double X { get; }
        /// <summary>Lane x of what it rests on (its carrier's x when <see cref="Support"/> is Carrier; otherwise <see cref="X"/>).</summary>
        double SupportX { get; }
        BodySupport Support { get; }
    }

    public enum PlateTermKind
    {
        /// <summary>Its full share while its support x is inside the plate (± margin); carried, while he counts (DL-03, L2232–L2238).</summary>
        Inside,
        /// <summary>Share × the fraction of its width [x − Half, x + Half] over the plate (DL-05, L4889).</summary>
        Overlap,
        /// <summary>Share × clamp((x − From) / Width, 0, 1): it rolls on gradually (DL-08 <c>panTrolleyK</c>, L3022–L3025).</summary>
        Ramp,
        /// <summary>Its full share while |x − At| &lt; Half (DL-12 figure on the strip, L5383).</summary>
        Near,
        /// <summary>Its full share while it is placed in its receiver (DL-09 tray, DL-10 car, DL-16a car; L5016, L4560, L5938).</summary>
        Placed,
    }

    /// <summary>One weighed thing: which body, how, and its share (in the prototype's load units).</summary>
    public readonly struct PlateTerm
    {
        public readonly MechanismId Body;
        public readonly PlateTermKind Kind;
        public readonly double Share, Half, At, Width;

        private PlateTerm(MechanismId body, PlateTermKind kind, double share, double half = 0, double at = 0, double width = 0)
        {
            Body = body; Kind = kind; Share = share; Half = half; At = at; Width = width;
        }

        public static PlateTerm Inside(MechanismId body, double share) => new PlateTerm(body, PlateTermKind.Inside, share);
        public static PlateTerm Overlap(MechanismId body, double half, double share) => new PlateTerm(body, PlateTermKind.Overlap, share, half);
        public static PlateTerm Ramp(MechanismId body, double from, double width, double share) => new PlateTerm(body, PlateTermKind.Ramp, share, 0, from, width);
        public static PlateTerm Near(MechanismId body, double at, double half, double share) => new PlateTerm(body, PlateTermKind.Near, share, half, at);
        public static PlateTerm Placed(MechanismId body, double share) => new PlateTerm(body, PlateTermKind.Placed, share);
    }

    /// <summary>What a plate feels: D-17 inside an x interval below a height, and a list of <see cref="PlateTerm"/>s.</summary>
    public sealed class PlateSensorParams
    {
        /// <summary>The plate's extent for Inside (widened by <see cref="Margin"/>) and Overlap terms.</summary>
        public double X0, X1, Margin;
        /// <summary>He is on when PlayerX0 &lt; x &lt; PlayerX1 and y &lt; PlayerMaxY. PlayerShare 0 = he is not weighed.</summary>
        public double PlayerX0, PlayerX1, PlayerMaxY, PlayerShare;
        public PlateTerm[] Terms = Array.Empty<PlateTerm>();
    }

    /// <summary>
    /// Evaluates a <see cref="PlateSensorParams"/> against the bodies and D-17's pose: the shared core of
    /// <see cref="LoadPlate"/>, <see cref="WeighScale"/> and <see cref="PresenceStrip"/>. Resolved once in Link; no
    /// allocation per evaluation.
    /// </summary>
    public sealed class PlateSensor
    {
        private readonly PlateSensorParams _p;
        private IPlateBody[] _bodies;

        public PlateSensor(PlateSensorParams p) { _p = p ?? throw new ArgumentNullException(nameof(p)); }

        public PlateSensorParams Params => _p;

        public void Link(MechanismLinker link)
        {
            _bodies = new IPlateBody[_p.Terms.Length];
            for (int i = 0; i < _bodies.Length; i++)
                _bodies[i] = link.Read<IPlateBody>(_p.Terms[i].Body) ?? throw new InvalidOperationException("A plate term needs a Body.");
        }

        /// <summary>D-17 stands on it this step.</summary>
        public bool PlayerOn(in PlayerPose pl) => _p.PlayerShare > 0 && pl.X > _p.PlayerX0 && pl.X < _p.PlayerX1 && pl.Y < _p.PlayerMaxY;

        /// <summary>The sum of the shares on it. <paramref name="playerOn"/>: weigh him (and what he carries).</summary>
        public double Load(bool playerOn)
        {
            double load = playerOn ? _p.PlayerShare : 0;
            for (int i = 0; i < _bodies.Length; i++) load += Share(in _p.Terms[i], _bodies[i], playerOn);
            return load;
        }

        private double Share(in PlateTerm t, IPlateBody b, bool playerOn)
        {
            var s = b.Support;
            if (t.Kind == PlateTermKind.Placed) return s == BodySupport.Placed ? t.Share : 0;
            if (s == BodySupport.Away || s == BodySupport.Placed) return 0;
            if (s == BodySupport.Carried) return t.Kind == PlateTermKind.Inside && playerOn ? t.Share : 0;   // L2236
            double x = s == BodySupport.Carrier ? b.SupportX : b.X;
            switch (t.Kind)
            {
                case PlateTermKind.Inside: return x > _p.X0 - _p.Margin && x < _p.X1 + _p.Margin ? t.Share : 0;   // L2230
                case PlateTermKind.Overlap:                                                                       // L4889
                {
                    double k = (Math.Min(x + t.Half, _p.X1) - Math.Max(x - t.Half, _p.X0)) / (2 * t.Half);
                    return t.Share * (k < 0 ? 0 : k > 1 ? 1 : k);
                }
                case PlateTermKind.Ramp:                                                                          // L3024
                {
                    double k = (x - t.At) / t.Width;
                    return t.Share * (k < 0 ? 0 : k > 1 ? 1 : k);
                }
                case PlateTermKind.Near: return Math.Abs(x - t.At) < t.Half ? t.Share : 0;                        // L5383
                default: return 0;
            }
        }
    }
}
