using System;

namespace DeadLetter.Core.Maths
{
    /// <summary>
    /// A point or vector in metres, double precision, in the <b>prototype's (three.js) axes</b>: x along the lane, y up,
    /// z toward the camera (the lane is z = 0, the set is at −z). Core camera maths keeps these axes so every constant reads
    /// exactly as in <c>index.html</c>; <see cref="ToUnity"/> applies port_architecture §0.2 (<c>Unity = (x, y, −z)</c>) at
    /// the edge. Blittable, immutable, no allocations: IL2CPP/AOT safe.
    /// </summary>
    public readonly struct Vec3 : IEquatable<Vec3>
    {
        public readonly double X;
        public readonly double Y;
        public readonly double Z;

        public Vec3(double x, double y, double z) { X = x; Y = y; Z = z; }

        public static readonly Vec3 Zero = new Vec3(0, 0, 0);

        public static Vec3 operator +(Vec3 a, Vec3 b) => new Vec3(a.X + b.X, a.Y + b.Y, a.Z + b.Z);
        public static Vec3 operator -(Vec3 a, Vec3 b) => new Vec3(a.X - b.X, a.Y - b.Y, a.Z - b.Z);
        public static Vec3 operator *(Vec3 a, double k) => new Vec3(a.X * k, a.Y * k, a.Z * k);

        /// <summary>three.js <c>a.lerp(b, k)</c> (unclamped).</summary>
        public static Vec3 Lerp(Vec3 a, Vec3 b, double k) =>
            new Vec3(a.X + (b.X - a.X) * k, a.Y + (b.Y - a.Y) * k, a.Z + (b.Z - a.Z) * k);

        public double Length => Math.Sqrt(X * X + Y * Y + Z * Z);

        /// <summary>The same point in Unity's axes: <c>(x, y, −z)</c>, port_architecture §0.2.</summary>
        public Vec3 ToUnity() => new Vec3(X, Y, -Z);

        public bool Equals(Vec3 other) => X.Equals(other.X) && Y.Equals(other.Y) && Z.Equals(other.Z);
        public override bool Equals(object obj) => obj is Vec3 v && Equals(v);
        public override int GetHashCode() => ((X.GetHashCode() * 397) ^ Y.GetHashCode()) * 397 ^ Z.GetHashCode();
        public override string ToString() => "(" + X.ToString("R") + ", " + Y.ToString("R") + ", " + Z.ToString("R") + ")";
    }
}
