using DeadLetter.Core.Save;
using DeadLetter.Core.Simulation;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>Core's one RNG: each sequence reproduces the generator it replaced (BeingRng, RouteRng) bit for bit.</summary>
    public class SimRngTests
    {
        /// <summary>The retired <c>Beings/BeingRng</c>, verbatim.</summary>
        private static double OldBeing(ref ulong s)
        {
            ulong x = s;
            x ^= x << 13;
            x ^= x >> 7;
            x ^= x << 17;
            s = x;
            return (x >> 11) * (1.0 / 9007199254740992.0);
        }

        /// <summary>The retired <c>Routes/RouteRng</c>, verbatim.</summary>
        private static double OldRoute(ref long seed)
        {
            const long M = 2147483647;
            seed = ((seed * 16807 + 11) % M + M) % M;
            return seed / (double)M;
        }

        [Theory]
        [InlineData(0x5EED_0FF1CE_D17UL)]     // WhiteParams.Seed
        [InlineData(0x7201_14B0UL)]           // EscortTrolleyParams.Seed
        [InlineData(1UL)]
        public void Xorshift_MatchesBeingRng(ulong seed)
        {
            var r = SimRng.Xorshift(seed);
            ulong s = seed;
            for (int i = 0; i < 1000; i++) Assert.Equal(OldBeing(ref s), r.NextDouble());
        }

        [Fact]
        public void Xorshift_SeedZero_UsesTheFixedFallback()
        {
            var r = SimRng.Xorshift(0);
            ulong s = 0x9E3779B97F4A7C15UL;
            for (int i = 0; i < 100; i++) Assert.Equal(OldBeing(ref s), r.NextDouble());
        }

        [Theory]
        [InlineData(1L)]                      // ReturnsBeltParams.Seed
        [InlineData(7L * 3 + 130)]            // a carrier payload seed: count · 7 + floor(clock · 13)
        [InlineData(0L)]
        public void Lcg_MatchesRouteRng(long seed)
        {
            var r = SimRng.Lcg(seed);
            long s = seed;
            for (int i = 0; i < 1000; i++) Assert.Equal(OldRoute(ref s), r.NextDouble());
        }

        [Theory]
        [InlineData(SimRngKind.Xorshift64)]
        [InlineData(SimRngKind.Lcg)]
        public void Snapshot_RoundTrip_ContinuesTheSequence(SimRngKind kind)
        {
            var a = kind == SimRngKind.Lcg ? SimRng.Lcg(42) : SimRng.Xorshift(42);
            for (int i = 0; i < 17; i++) a.NextDouble();
            var snap = new MemorySnapshot();
            a.Write(snap, "rng");
            var b = kind == SimRngKind.Lcg ? SimRng.Lcg(9) : SimRng.Xorshift(9);
            b.Read(snap, "rng");
            for (int i = 0; i < 100; i++) Assert.Equal(a.NextDouble(), b.NextDouble());
        }

        [Fact]
        public void Reseed_ReplaysFromTheStart()
        {
            var r = SimRng.Xorshift(123);
            double first = r.NextDouble();
            r.NextDouble();
            r.Reseed(123);
            Assert.Equal(first, r.NextDouble());
            Assert.Equal(SimRngKind.Xorshift64, r.Kind);
        }
    }
}
