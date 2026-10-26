using System;

namespace DeadLetter.Core.Audio
{
    /// <summary>
    /// <c>Sound</c>'s continuous layers (index.html L576–L740) plus <see cref="WhiteHiss"/>, the White's own warning hiss
    /// (port_architecture §9 #16: in the web build it shares <see cref="Hiss"/> with the DL-01 steam, which overwrites it
    /// every frame, so the warning is never heard; Unity gives it its own source).
    /// </summary>
    public enum SfxLoop { Hum, Buzz, Hiss, Roll, Tubes, Belt, Drum, Air, Drag, WhiteHiss }

    /// <summary>
    /// The continuous layers' levels. Each glides to the level its caller sets with the prototype's
    /// <c>setTargetAtTime</c> τ; the loops are rendered at level 1 (scale included), so volume = level.
    /// </summary>
    public sealed class SfxLoopMixer
    {
        /// <summary>The bank key of each layer's loop file (docs/unity/audio_inventory.md, continuous layers).</summary>
        public static readonly string[] Keys =
            { "loop_hum", "loop_buzz", "loop_hiss", "loop_roll", "loop_tubes", "loop_belt", "loop_drum", "loop_air", "loop_drag", "loop_hiss" };

        /// <summary>τ per layer: hum 0.4 (L604), buzz 0.01 (L605), hiss 0.2 (L636), roll 0.06 (L659), tubes 0.3 (L668),
        /// belt 0.25 (L691), drum 0.08 (L704), air 0.8 (L726), drag 0.06 (L739); the White's hiss as the hiss.</summary>
        public static readonly double[] Tau = { 0.4, 0.01, 0.2, 0.06, 0.3, 0.25, 0.08, 0.8, 0.06, 0.2 };

        /// <summary>The White's warning: <c>Sound.hiss(1)</c>, then <c>hiss(0)</c> 0.9 s later (L7152).</summary>
        public const double WhiteWarningSeconds = 0.9;

        public const int Count = 10;

        private readonly double[] _target = new double[Count];
        private readonly double[] _value = new double[Count];
        private double _whiteUntil = double.NegativeInfinity;

        /// <summary>The level the game asks for (<c>Sound.hum(level)</c> etc.).</summary>
        public void Set(SfxLoop loop, double level)
        {
            _target[(int)loop] = Math.Max(0, level);
        }

        public double Target(SfxLoop loop) => _target[(int)loop];

        /// <summary>The volume to put on the layer's looping AudioSource.</summary>
        public double Volume(SfxLoop loop) => _value[(int)loop];

        /// <summary>The White rears and hisses (L7152), on its own layer.</summary>
        public void WhiteWarning(double now)
        {
            _whiteUntil = now + WhiteWarningSeconds;
            _target[(int)SfxLoop.WhiteHiss] = 1;
        }

        /// <summary>Glides every layer by <paramref name="dt"/>.</summary>
        public void Step(double now, double dt)
        {
            if (now >= _whiteUntil) _target[(int)SfxLoop.WhiteHiss] = 0;
            for (int i = 0; i < Count; i++) _value[i] = OnePole.Step(_value[i], _target[i], Tau[i], dt);
        }
    }

    public enum DistantSound { None, Distant, Groan }

    /// <summary>The atmosphere's sound rules from <c>updateAtmosphere</c> (index.html L7808–L7966).</summary>
    public sealed class AtmosphereRules
    {
        /// <summary><c>atmos.nextClank</c> starts at 8 s (L7811).</summary>
        public const double FirstClank = 8;
        public const double ClankMin = 6, ClankSpread = 8, DistantChance = 0.6;

        private readonly AudioRng _rng;

        public AtmosphereRules(uint seed) { _rng = new AudioRng(seed); }

        public double NextClank { get; private set; } = FirstClank;

        /// <summary>
        /// Distant machinery (L7964): past <see cref="NextClank"/>, in play and not under a moment's shot, a distant thud
        /// (60 %) or a groan, then the next in 6–14 s. While voices are held it waits, and fires as soon as they are not.
        /// </summary>
        public DistantSound Update(double t, bool inPlay, bool voicesHeld)
        {
            if (!(t > NextClank) || !inPlay || voicesHeld) return DistantSound.None;
            NextClank = t + ClankMin + _rng.NextDouble() * ClankSpread;
            return _rng.NextDouble() < DistantChance ? DistantSound.Distant : DistantSound.Groan;
        }

        /// <summary>
        /// The DL-01 steam's hiss level (L7965): max(0, 1 − |8.7 − x| / 2.5) in play × <c>atmos.hissLevel</c> (1 while a
        /// wisp puffs, else 0.35, L7936).
        /// </summary>
        public static double SteamHiss(double x, bool inPlay, double hissLevel = 1)
        {
            if (!inPlay) return 0;
            return Math.Max(0, 1 - Math.Abs(8.7 - x) / 2.5) * hissLevel;
        }

        /// <summary><c>hissLevel</c>: 1 while a steam wisp puffs, else 0.35 (L7936).</summary>
        public static double HissLevel(bool puffing) => puffing ? 1 : 0.35;
    }
}
