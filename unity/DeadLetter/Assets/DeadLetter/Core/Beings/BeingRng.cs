namespace DeadLetter.Core.Beings
{
    /// <summary>
    /// A seeded xorshift64 generator owned by one being and snapshotted with it: it replaces the prototype's
    /// <c>Math.random()</c> in the White's patrol targets (L7136) and the trolley's squeaks (L6377, L6387)
    /// (port_architecture §9 #11). Stand-in for <c>Core/Simulation/SimRng</c> (§2), which does not exist yet: when it
    /// lands, swap this for it and keep the seeds. Each being reseeds on Reset, so reloading a checkpoint replays exactly.
    /// </summary>
    public sealed class BeingRng
    {
        private const ulong Fallback = 0x9E3779B97F4A7C15UL;
        private ulong _s;

        public BeingRng(ulong seed) { Seed(seed); }

        /// <summary>Restart the sequence (0 is not a valid xorshift state and is replaced by a fixed constant).</summary>
        public void Seed(ulong seed) => _s = seed == 0 ? Fallback : seed;

        /// <summary>The raw state, for snapshots.</summary>
        public long State
        {
            get => (long)_s;
            set => Seed((ulong)value);
        }

        /// <summary>Uniform in [0, 1), 53 bits.</summary>
        public double NextDouble()
        {
            ulong x = _s;
            x ^= x << 13;
            x ^= x >> 7;
            x ^= x << 17;
            _s = x;
            return (x >> 11) * (1.0 / 9007199254740992.0);
        }
    }
}
