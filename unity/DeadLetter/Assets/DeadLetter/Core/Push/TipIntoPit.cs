using System;
using DeadLetter.Core.Maths;

namespace DeadLetter.Core.Push
{
    /// <summary>
    /// Where a pushable that tips into a pit stops, falls and settles (port_architecture §4.11, §4.13j): the pit, the
    /// thing's half-length and height, how far its front wheels go over the lip, and the fall's timing. DL-01's cart
    /// and DL-11's duct (L4274, L4285, L4738–L4750, L4756–L4766, L4854–L4862).
    /// </summary>
    public sealed class TipParams
    {
        /// <summary>The pit: lane x0..x1, floor y.</summary>
        public double PitX0, PitX1, PitFloor;
        /// <summary>Half-length and height of the thing.</summary>
        public double Half, Height;
        /// <summary>It stops with its front wheels over the lip: travel ends at PitX0 − Half + LipOver (L4274, L4285).</summary>
        public double LipOver = 0.38;
        /// <summary>Where it settles: PitX0 + Half + SettleGap (cart 0.02, duct 0; L4757, L4855).</summary>
        public double SettleGap;
        /// <summary>Tip time and when it lands (<c>drop += dt / 0.9</c>; the cart lands at 0.8, the duct at 1; L4757, L4855).</summary>
        public double FallTime = 0.9, LandAt = 1, LandShake = 0.4;

        /// <summary>The end of its travel: at the lip (<c>max()</c>, L4274).</summary>
        public double LipX => PitX0 - Half + LipOver;
        public double SettleX => PitX0 + Half + SettleGap;

        /// <summary>DL-01's depot cart (0.55 high) into the drain trench 6.6–8.0 at −0.8, settling at 7.27 (L283, L3885, L4274, L4756–L4757).</summary>
        public static TipParams Dl01Cart() => new TipParams
        {
            PitX0 = 6.6, PitX1 = 8.0, PitFloor = -0.8, Half = 0.65, Height = 0.55,
            LipOver = 0.38, SettleGap = 0.02, LandAt = 0.8, LandShake = 0.4,
        };

        /// <summary>DL-11's duct (0.26 high) into the flood 149.1–150.6 at −0.25, settling at 149.85 (L3902–L3903, L4285, L4854–L4855).</summary>
        public static TipParams Dl11Duct() => new TipParams
        {
            PitX0 = 54 + 95.1, PitX1 = 54 + 96.6, PitFloor = -0.25, Half = 0.75, Height = 0.26,
            LipOver = 0.4, SettleGap = 0, LandAt = 1, LandShake = 0.3,
        };
    }

    /// <summary>
    /// The fall into the pit (<c>tipOver</c>, <c>tipInto</c>, L4739–L4750): over <see cref="TipParams.FallTime"/> the nose
    /// drops, it slides to where it settles and bounces once. A plain model, owned by a <see cref="Pushable"/> (or any
    /// mechanism that tips): <see cref="Begin"/> when it goes over, <see cref="Advance"/> each step until it settles.
    /// <para>Bridges/TippingBridge (DL-01's cart, DL-11's duct) predates Core/Push and computes the same curve itself;
    /// PushTests checks the two agree step for step.</para>
    /// </summary>
    public sealed class TipIntoPit
    {
        private readonly TipParams _p;

        public TipIntoPit(TipParams p) { _p = p ?? throw new ArgumentNullException(nameof(p)); }

        public TipParams Params => _p;
        /// <summary>Progress 0..1 (<c>s.drop</c>).</summary>
        public double Drop { get; private set; }
        /// <summary>Lane x while it falls, then <see cref="TipParams.SettleX"/>.</summary>
        public double X { get; private set; }
        /// <summary>The view's y offset and nose dip, radians (<c>tipInto</c>, L4743–L4750).</summary>
        public double ViewY { get; private set; }
        public double DipRad { get; private set; }
        public bool Landed { get; private set; }
        /// <summary>Where it went over the lip (<c>s.x0tip</c>).</summary>
        public double FromX { get; private set; }

        /// <summary>It goes over at <paramref name="x"/> (<c>tipOver</c>: <c>drop = 0, x0tip = x</c>, L4739).</summary>
        public void Begin(double x)
        {
            Drop = 0; FromX = X = x; ViewY = 0; DipRad = 0; Landed = false;
        }

        /// <summary>Settled in the pit (a checkpoint past it, or the end of the fall).</summary>
        public void Settle()
        {
            Drop = 1; X = _p.SettleX; ViewY = _p.PitFloor; DipRad = 0; Landed = true;
        }

        /// <summary>
        /// One step of the fall (<c>drop = min(1, drop + dt / FallTime)</c>, L4757, L4855). <paramref name="landedNow"/>:
        /// it hit the floor this step (thud and shake). Returns true on the step it settles.
        /// </summary>
        public bool Advance(double dt, out bool landedNow)
        {
            landedNow = false;
            Drop = Math.Min(1, Drop + dt / _p.FallTime);
            if (_p.LandAt < 1 && Drop >= _p.LandAt && !Landed) { Landed = true; landedNow = true; }
            if (Drop >= 1)
            {
                if (!Landed) landedNow = true;
                Settle();
                return true;
            }
            double t = Drop, k = Smooth.Step(Math.Min(1, t / 0.75));
            double dip = t < 0.5 ? -0.5 * Math.Sin(t / 0.5 * Math.PI / 2)
                : -0.5 * (1 - Smooth.Step((t - 0.5) / 0.35)) + (t > 0.85 ? 0.05 * Math.Sin((t - 0.85) / 0.15 * Math.PI) : 0);
            X = FromX + (_p.SettleX - FromX) * k;
            ViewY = _p.PitFloor * k * k - Math.Abs(Math.Sin(dip)) * _p.Half * 0.45 * (1 - k);
            DipRad = dip;
            return false;
        }

        /// <summary>Restores the model's fields (from a pushable's snapshot).</summary>
        public void Set(double drop, double x, double fromX, double viewY, double dipRad, bool landed)
        {
            Drop = drop; X = x; FromX = fromX; ViewY = viewY; DipRad = dipRad; Landed = landed;
        }
    }
}
