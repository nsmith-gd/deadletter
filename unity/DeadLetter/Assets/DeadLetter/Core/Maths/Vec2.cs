using System;

namespace DeadLetter.Core.Maths
{
    /// <summary>
    /// A point or vector in the play plane (x along the lane, y up), in metres, double precision.
    /// Core keeps the prototype's double maths (JavaScript numbers); Runtime converts to float at the edge.
    /// Blittable, immutable, no allocations: IL2CPP/AOT safe.
    /// </summary>
    public readonly struct Vec2 : IEquatable<Vec2>
    {
        public readonly double X;
        public readonly double Y;

        public Vec2(double x, double y) { X = x; Y = y; }

        public static readonly Vec2 Zero = new Vec2(0, 0);

        public static Vec2 operator +(Vec2 a, Vec2 b) => new Vec2(a.X + b.X, a.Y + b.Y);
        public static Vec2 operator -(Vec2 a, Vec2 b) => new Vec2(a.X - b.X, a.Y - b.Y);
        public static Vec2 operator *(Vec2 a, double k) => new Vec2(a.X * k, a.Y * k);

        public bool Equals(Vec2 other) => X.Equals(other.X) && Y.Equals(other.Y);
        public override bool Equals(object obj) => obj is Vec2 v && Equals(v);
        public override int GetHashCode() => (X.GetHashCode() * 397) ^ Y.GetHashCode();
        public override string ToString() => "(" + X.ToString("R") + ", " + Y.ToString("R") + ")";
    }
}
