using DeadLetter.Core.Save;

namespace DeadLetter.Core.Simulation
{
    /// <summary>The two sequences <see cref="SimRng"/> can produce.</summary>
    public enum SimRngKind : byte
    {
        /// <summary>xorshift64 (13, 7, 17), 53-bit doubles. The default: every <c>Math.random()</c> the port replaces.</summary>
        Xorshift64,
        /// <summary>
        /// The prototype's own seeded LCG (L2666–L2667: <c>seed = (seed · 16807 + 11) mod 2147483647</c>; value =
        /// seed / 2147483647): the carrier payloads (seeded as the prototype seeds them, so they match it) and the DL-08
        /// returns-belt crates (L3130, L3139), which were ported with it.
        /// </summary>
        Lcg,
    }

    /// <summary>
    /// Core's one random generator (port_architecture §2, §9 #11): a seeded value type owned by the system that draws
    /// from it, reseeded on Reset so a checkpoint reload replays exactly, and snapshotted with its owner
    /// (<see cref="Write"/>/<see cref="Read"/>, one long). No allocation, no global state; never <c>System.Random</c>.
    /// <para>Two sequences, chosen at construction and fixed by the owner's params (not snapshotted):
    /// <see cref="Xorshift"/> (what <c>BeingRng</c> was) and <see cref="Lcg"/> (what <c>RouteRng</c> was). Each
    /// reproduces its predecessor bit for bit from the same seed.</para>
    /// <para>It is a mutable struct: hold it in a non-readonly field and never copy it to draw.</para>
    /// </summary>
    public struct SimRng
    {
        private const ulong XorshiftFallback = 0x9E3779B97F4A7C15UL;
        private const long LcgM = 2147483647;

        private long _s;
        private SimRngKind _kind;

        /// <summary>A xorshift64 generator. Seed 0 is not a valid xorshift state and is replaced by a fixed constant.</summary>
        public static SimRng Xorshift(ulong seed)
        {
            var r = new SimRng { _kind = SimRngKind.Xorshift64 };
            r.Reseed((long)seed);
            return r;
        }

        /// <summary>The prototype's LCG (see <see cref="SimRngKind.Lcg"/>).</summary>
        public static SimRng Lcg(long seed)
        {
            var r = new SimRng { _kind = SimRngKind.Lcg };
            r.Reseed(seed);
            return r;
        }

        public SimRngKind Kind => _kind;

        /// <summary>The raw state, for snapshots and tests. Setting it is <see cref="Reseed"/>.</summary>
        public long State
        {
            get => _s;
            set => Reseed(value);
        }

        /// <summary>Restart the sequence from <paramref name="seed"/> (xorshift: 0 becomes a fixed constant).</summary>
        public void Reseed(long seed)
        {
            _s = _kind == SimRngKind.Xorshift64 && seed == 0 ? unchecked((long)XorshiftFallback) : seed;
        }

        /// <summary>Uniform in [0, 1).</summary>
        public double NextDouble()
        {
            if (_kind == SimRngKind.Lcg)
            {
                _s = ((_s * 16807 + 11) % LcgM + LcgM) % LcgM;
                return _s / (double)LcgM;
            }
            ulong x = unchecked((ulong)_s);
            x ^= x << 13;
            x ^= x >> 7;
            x ^= x << 17;
            _s = unchecked((long)x);
            return (x >> 11) * (1.0 / 9007199254740992.0);
        }

        /// <summary>The prototype's per-step chance idiom, <c>Math.random() &lt; p</c> (e.g. <c>p = dt · 1.5</c>).</summary>
        public bool Chance(double p) => NextDouble() < p;

        public void Write(ISnapshotWriter w, string key) => w.WriteLong(key, _s);

        public void Read(ISnapshotReader r, string key) => Reseed(r.ReadLong(key));
    }
}
