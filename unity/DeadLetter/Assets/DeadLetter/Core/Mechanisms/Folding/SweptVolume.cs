using System;

namespace DeadLetter.Core.Mechanisms.Folding
{
    /// <summary>
    /// A box of a leaf, in lane x and in the leaf's own frame: U along the leaf from the hinge, V across it (V+ is the
    /// side that faces up when the leaf is down).
    /// </summary>
    public readonly struct LeafBox
    {
        public readonly double X0, X1, U0, U1, V0, V1;

        public LeafBox(double x0, double x1, double u0, double u1, double v0, double v1)
        {
            X0 = x0; X1 = x1; U0 = u0; U1 = u1; V0 = v0; V1 = v1;
        }
    }

    /// <summary>
    /// An oriented box of a swept volume: a lane-x extent times a rectangle in the cross-section plane (D = depth from the
    /// frame's back wall toward the lane, Y = height). Leaves on one frame share the plane, so their hinge axes are parallel.
    /// </summary>
    public readonly struct SweptBox
    {
        public readonly double X0, X1;
        /// <summary>Centre (D, Y), unit axis (Ux, Uy) along its first half-extent Hu; the second axis is (−Uy, Ux), half-extent Hv.</summary>
        public readonly double Cd, Cy, Ux, Uy, Hu, Hv;

        public SweptBox(double x0, double x1, double cd, double cy, double ux, double uy, double hu, double hv)
        {
            X0 = x0; X1 = x1; Cd = cd; Cy = cy; Ux = ux; Uy = uy; Hu = hu; Hv = hv;
        }

        /// <summary>An axis-aligned box (D-17's body).</summary>
        public static SweptBox Aligned(double x0, double x1, double d0, double d1, double y0, double y1)
            => new SweptBox(x0, x1, (d0 + d1) / 2, (y0 + y1) / 2, 1, 0, (d1 - d0) / 2, (y1 - y0) / 2);

        /// <summary>True if the boxes overlap by more than <paramref name="margin"/> (touching is not overlapping). Separating axes.</summary>
        public static bool Overlap(in SweptBox a, in SweptBox b, double margin)
        {
            if (!(a.X0 < b.X1 - margin && b.X0 < a.X1 - margin)) return false;
            double dx = b.Cd - a.Cd, dy = b.Cy - a.Cy;
            return !Separated(a, b, a.Ux, a.Uy, dx, dy, margin) && !Separated(a, b, -a.Uy, a.Ux, dx, dy, margin)
                && !Separated(a, b, b.Ux, b.Uy, dx, dy, margin) && !Separated(a, b, -b.Uy, b.Ux, dx, dy, margin);
        }

        private static bool Separated(in SweptBox a, in SweptBox b, double nx, double ny, double dx, double dy, double margin)
        {
            double ra = a.Hu * Math.Abs(a.Ux * nx + a.Uy * ny) + a.Hv * Math.Abs(-a.Uy * nx + a.Ux * ny);
            double rb = b.Hu * Math.Abs(b.Ux * nx + b.Uy * ny) + b.Hv * Math.Abs(-b.Uy * nx + b.Ux * ny);
            return Math.Abs(dx * nx + dy * ny) >= ra + rb - margin;
        }
    }

    /// <summary>
    /// Something that occupies space a folding leaf sweeps through (another leaf; later a shelf or a bed section). The
    /// boxes describe its current pose.
    /// </summary>
    public interface ISweptVolume
    {
        int VolumeCount { get; }
        SweptBox Volume(int i);
    }
}
