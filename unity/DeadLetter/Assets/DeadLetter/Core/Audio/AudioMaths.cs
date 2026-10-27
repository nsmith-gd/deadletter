using System;
using System.Security.Cryptography;
using System.Text;
using DeadLetter.Core.Maths;

namespace DeadLetter.Core.Audio
{
    /// <summary>
    /// A seeded xorshift32 for the audio's random choices (takes, blip intervals, distant clanks). The prototype used
    /// <c>Math.random</c>; seeding keeps replays and tests deterministic (port_architecture §9 #11).
    /// </summary>
    public sealed class AudioRng
    {
        private uint _s;

        public AudioRng(uint seed) { _s = seed == 0 ? 0x9E3779B9u : seed; }

        public uint NextUInt()
        {
            uint x = _s;
            x ^= x << 13;
            x ^= x >> 17;
            x ^= x << 5;
            _s = x;
            return x;
        }

        /// <summary>Uniform in [0, 1).</summary>
        public double NextDouble() => (NextUInt() >> 8) * (1.0 / 16777216.0);

        /// <summary>Uniform integer in [0, n).</summary>
        public int Next(int n) => n <= 1 ? 0 : (int)(NextDouble() * n);
    }

    /// <summary>
    /// <c>AudioParam.setTargetAtTime</c> stepped exactly: after <paramref name="dt"/> seconds the value has covered
    /// 1 − e^(−dt/τ) of the distance to the target (63 % in τ), at any frame rate.
    /// </summary>
    public static class OnePole
    {
        public static double Step(double value, double target, double tau, double dt)
        {
            if (dt <= 0) return value;
            if (tau <= 0) return target;
            return target + (value - target) * Math.Exp(-dt / tau);
        }
    }

    /// <summary>
    /// One gain automation lane, like a WebAudio <c>AudioParam</c> with one live segment: hold, a linear ramp, or an
    /// exponential approach (<c>setTargetAtTime</c>). Every new segment starts from the value the lane has at its start
    /// time, which is <c>cancelAndHoldAtTime</c> semantics. (The prototype calls <c>cancelScheduledValues</c>, which in a
    /// browser can snap a half-finished linear fade back to its start value; that click is not ported.)
    /// </summary>
    public sealed class GainEnvelope
    {
        private enum Shape { Hold, Linear, Target }

        private Shape _shape;
        private double _t0, _v0, _t1, _v1, _tau;

        public GainEnvelope(double value = 0)
        {
            _shape = Shape.Hold;
            _v0 = _v1 = value;
        }

        /// <summary>The value the lane is heading for (the hold value, the ramp's end, or the target).</summary>
        public double Destination => _v1;

        public double ValueAt(double t)
        {
            switch (_shape)
            {
                case Shape.Linear:
                    if (t <= _t0) return _v0;
                    if (t >= _t1) return _v1;
                    return _v0 + (_v1 - _v0) * (t - _t0) / (_t1 - _t0);
                case Shape.Target:
                    if (t <= _t0) return _v0;
                    return _v1 + (_v0 - _v1) * Math.Exp(-(t - _t0) / _tau);
                default:
                    return _v0;
            }
        }

        /// <summary><c>setValueAtTime(v, t)</c> (held from then on).</summary>
        public void Set(double t, double value)
        {
            _shape = Shape.Hold;
            _t0 = t;
            _v0 = _v1 = value;
        }

        /// <summary><c>setValueAtTime(from, t); linearRampToValueAtTime(to, t + seconds)</c>.</summary>
        public void Ramp(double t, double from, double to, double seconds)
        {
            if (seconds <= 0) { Set(t, to); return; }
            _shape = Shape.Linear;
            _t0 = t; _v0 = from;
            _t1 = t + seconds; _v1 = to;
        }

        /// <summary><c>setTargetAtTime(target, t, tau)</c> from the value at <paramref name="t"/>.</summary>
        public void TargetAt(double t, double target, double tau)
        {
            double v = ValueAt(t);
            if (tau <= 0) { Set(t, target); return; }
            _shape = Shape.Target;
            _t0 = t; _v0 = v;
            _v1 = target; _tau = tau;
        }
    }

    /// <summary>
    /// Pan by the source's on-screen x (the reviewer's decision on #20: the web build pans nothing; Unity pans gently,
    /// ±<see cref="DefaultEdgePan"/> at the frame edges, linear between, clamped off-screen). One tunable value.
    /// </summary>
    public static class PanLaw
    {
        public const double DefaultEdgePan = 0.4;

        /// <param name="viewportX">0 = left frame edge, 1 = right (Unity viewport space).</param>
        /// <param name="edgePan">Pan at the frame edges, 0..1.</param>
        public static double FromViewportX(double viewportX, double edgePan = DefaultEdgePan)
        {
            if (double.IsNaN(viewportX) || double.IsInfinity(viewportX)) return 0;
            double e = Smooth.Clamp(Math.Abs(edgePan), 0, 1);
            return Smooth.Clamp((viewportX - 0.5) * 2.0 * e, -e, e);
        }
    }

    /// <summary>
    /// The buses of index.html as mixer gains (docs/unity/audio_inventory.md, Conventions → Gain): <c>Sound</c> → master
    /// 0.8 (L570); <c>Ambience</c> → bus 0.9 (L1150) → master; <c>Voice</c> → bus 1 → master; <c>Music</c> → bus → limiter
    /// (L823–L824) → master. In Unity: <c>Master</c> carries the 0.8 and each child group its own bus gain.
    /// </summary>
    public static class AudioMix
    {
        public const string MasterGroup = "Master", MusicGroup = "Music", SfxGroup = "SFX", VoiceGroup = "Voice", AmbienceGroup = "Ambience";

        public const double Master = 0.8;        // L570
        public const double SfxBus = 1.0;
        public const double AmbienceBus = 0.9;   // L1150
        public const double VoiceBus = 1.0;
        public const double MusicBus = 1.0;

        /// <summary>The music limiter, L823–L824 (WebAudio DynamicsCompressor).</summary>
        public const double LimiterThresholdDb = -24, LimiterKneeDb = 12, LimiterRatio = 4, LimiterAttack = 0.25, LimiterRelease = 1.2;

        /// <summary>The options' sound toggle glides the master with τ 0.05 s (L603).</summary>
        public const double EnableTau = 0.05;

        /// <summary>Linear gain → decibels for a mixer fader (−80 dB floor, Unity's minimum).</summary>
        public static double ToDb(double gain) => gain <= 1e-4 ? -80.0 : Math.Max(-80.0, 20.0 * Math.Log10(gain));
    }

    /// <summary>
    /// Stable asset GUIDs for files the importer copies into <c>Assets/Audio/</c> (they are gitignored, so Unity would
    /// otherwise give each machine its own GUID and every reference would break on re-import). GUID = MD5 of the
    /// project-relative path (forward slashes, as given), as 32 lower-case hex digits.
    /// </summary>
    public static class StableGuid
    {
        public static string ForPath(string projectRelativePath)
        {
            if (projectRelativePath == null) throw new ArgumentNullException(nameof(projectRelativePath));
            string p = projectRelativePath.Replace('\\', '/');
            using (MD5 md5 = MD5.Create())
            {
                byte[] h = md5.ComputeHash(Encoding.UTF8.GetBytes(p));
                var sb = new StringBuilder(32);
                for (int i = 0; i < h.Length; i++) sb.Append(h[i].ToString("x2"));
                return sb.ToString();
            }
        }

        /// <summary>The minimal .meta Unity accepts for a file: it keeps the GUID and fills in the importer on import.</summary>
        public static string FileMeta(string projectRelativePath) =>
            "fileFormatVersion: 2\nguid: " + ForPath(projectRelativePath) + "\n";

        /// <summary>A folder's .meta.</summary>
        public static string FolderMeta(string projectRelativePath) =>
            "fileFormatVersion: 2\nguid: " + ForPath(projectRelativePath) + "\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n" +
            "  userData: \n  assetBundleName: \n  assetBundleVariant: \n";

        /// <summary>The GUID line of an existing .meta, or null.</summary>
        public static string ReadGuid(string metaText)
        {
            if (metaText == null) return null;
            foreach (string raw in metaText.Split('\n'))
            {
                string line = raw.Trim();
                if (line.StartsWith("guid:", StringComparison.Ordinal)) return line.Substring(5).Trim();
            }
            return null;
        }
    }
}
