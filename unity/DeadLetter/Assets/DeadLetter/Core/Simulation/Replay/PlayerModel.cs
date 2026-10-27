using System;

namespace DeadLetter.Core.Simulation.Replay
{
    /// <summary>
    /// The simulated player's random numbers: mulberry32, exactly as <c>tools/sim/bot.js</c> draws them (bot.js L9–L10),
    /// so a seed draws the same player (skill, curiosity) and the same hesitations as the prototype's runs. A test tool,
    /// never gameplay: game systems draw from <see cref="SimRng"/>.
    /// </summary>
    public struct Mulberry32
    {
        private uint _a;

        public Mulberry32(uint seed) { _a = seed; }

        /// <summary>The next value in [0, 1) (<c>R()</c>).</summary>
        public double Next()
        {
            unchecked
            {
                _a += 0x6D2B79F5u;
                uint t = _a;
                t = (t ^ (t >> 15)) * (t | 1u);
                t ^= t + (t ^ (t >> 7)) * (t | 61u);
                return (t ^ (t >> 14)) / 4294967296.0;
            }
        }
    }

    /// <summary>
    /// bot.js's player model (L14–L21): a player is a skill and a curiosity in [0, 1], drawn from the seed unless given.
    /// <see cref="Think"/>, <see cref="Look"/> and <see cref="React"/> are the seconds a person spends working out what
    /// to do, taking in a space and noticing they've stopped; <see cref="Mechanical"/> turns them off (0, 0, 0.12 s) and
    /// gives the shortest possible run. The think times are bot.js's calibrated guesses, not measurements.
    /// </summary>
    public sealed class PlayerModel
    {
        private Mulberry32 _r;

        public PlayerModel(uint seed, bool mechanical, double? skill = null, double? curious = null)
        {
            Seed = seed;
            Mechanical = mechanical;
            _r = new Mulberry32(seed);
            Skill = skill ?? Uniform(0, 1);                               // P = { skill: opts.skill ?? U(0, 1), ... }
            Curious = curious ?? Uniform(0, 1);
        }

        public uint Seed { get; }
        public bool Mechanical { get; }
        public double Skill { get; }
        public double Curious { get; }
        /// <summary>True when the player tries wrong things first (<c>mistakes = !opts.mechanical</c>).</summary>
        public bool Mistakes => !Mechanical;
        /// <summary>0.55 (quick) to 1.45 (slow), on thinking.</summary>
        public double Slow => 1.45 - 0.9 * Skill;

        public double Next() => _r.Next();
        public double Uniform(double lo, double hi) => lo + (hi - lo) * _r.Next();
        public bool Chance(double p) => _r.Next() < p;

        /// <summary>Box–Muller, as bot.js draws it (two values per call, in that order).</summary>
        public double Gauss()
        {
            double u = _r.Next(), v = _r.Next();
            return Math.Sqrt(-2 * Math.Log(1 - u)) * Math.Cos(2 * Math.PI * v);
        }

        public double LogNormal(double median, double sigma) => median * Math.Exp(sigma * Gauss());

        public double Think(double median) => Mechanical ? 0 : LogNormal(median * Slow, 0.7);
        public double Look(double median) => Mechanical ? 0 : LogNormal(median * (0.6 + 0.8 * Curious), 0.45);
        public double React() => Mechanical ? 0.12 : LogNormal(0.35 + 0.45 * Slow, 0.35);
    }
}
