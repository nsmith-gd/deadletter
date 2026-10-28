using System;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Platform;

namespace DeadLetter.Core.Presentation
{
    /// <summary>A light's type. Hemisphere lights have no URP equivalent: the pool blends them into the ambient (<see cref="LightPool.Ambient"/>).</summary>
    public enum LightKind { Point, Spot, Directional, Hemisphere }

    /// <summary>A colour, components 0–1, as three.js's hex colours are authored (sRGB, which Unity's light and ambient colours also take).</summary>
    public readonly struct Rgb
    {
        public readonly double R, G, B;
        public Rgb(double r, double g, double b) { R = r; G = g; B = b; }
        public static Rgb Hex(int hex) => new Rgb(((hex >> 16) & 0xff) / 255.0, ((hex >> 8) & 0xff) / 255.0, (hex & 0xff) / 255.0);
        public static Rgb operator *(Rgb a, double k) => new Rgb(a.R * k, a.G * k, a.B * k);
        public static Rgb operator +(Rgb a, Rgb b) => new Rgb(a.R + b.R, a.G + b.G, a.B + b.B);
        public static readonly Rgb Black = new Rgb(0, 0, 0);
        public override string ToString() => "(" + R.ToString("0.###") + ", " + G.ToString("0.###") + ", " + B.ToString("0.###") + ")";
    }

    /// <summary>
    /// One light proxy (port_architecture §4.20: every light the scenes build is a proxy; the pool copies the best into real
    /// lights). Values are three.js's as authored (position and target in three.js axes: Unity z = −z, <see cref="Vec3.ToUnity"/>;
    /// intensity in three.js units, which the runtime scales). U-15 moves these to Blender's <c>LGT_</c> empties; until then
    /// the seed is <see cref="PrologueLights"/>.
    /// </summary>
    public sealed class LightDef
    {
        public string Name;
        public LightKind Kind;
        /// <summary>Which region list switches it (<see cref="LightRegions.Visible"/>).</summary>
        public LightGroup Group;
        public Rgb Color;
        /// <summary>Hemisphere: the ground colour.</summary>
        public Rgb Ground;
        /// <summary>The level it has when nothing drives it (<c>userData.base</c>, or the constructor's).</summary>
        public double Intensity;
        /// <summary>Range, metres (0 = unbounded); the decay exponent.</summary>
        public double Distance, Decay = 2;
        /// <summary>Spot: cone half-angle (radians) and penumbra (0–1).</summary>
        public double Angle, Penumbra;
        public bool Shadow;
        public int ShadowMap = 512;
        public Vec3 Position, Target;
        /// <summary>The character's kick light: always first in the pool (score + 1e6, L8572).</summary>
        public bool Kick;
        /// <summary>A glint lamp: next after the kick (+1e5, L8572).</summary>
        public bool Boost;
        /// <summary>What sets its level each frame (<see cref="LightDriver.None"/>: <see cref="Intensity"/>).</summary>
        public LightDriver Driver;

        public override string ToString() => Name + " " + Kind + " " + Group;
    }

    /// <summary>The pool's real lights per kind (§8.2; the prototype's <c>LIGHT_POOL</c>, L8542).</summary>
    public sealed class LightPoolBudget
    {
        public int Point, Spot, SpotShadow, Directional, Hemisphere;
        /// <summary>The prototype's <c>touch</c>: lamps that cast shadows only off touch devices (the relay, L1466) don't on this tier.</summary>
        public bool Touch;

        /// <summary><c>LIGHT_POOL</c> = point 10, spot 4, spotShadow 2, dir 2, hemi 2 (L8542); the PC tier (§8.2).</summary>
        public static LightPoolBudget Prototype => new LightPoolBudget { Point = 10, Spot = 4, SpotShadow = 2, Directional = 2, Hemisphere = 2 };
        /// <summary>§8.2 Switch handheld: 6 point, 3 spot, 1 shadowed spot, 1 directional; hemisphere → ambient.</summary>
        public static LightPoolBudget SwitchHandheld => new LightPoolBudget { Point = 6, Spot = 3, SpotShadow = 1, Directional = 1, Hemisphere = 2, Touch = true };
        /// <summary>§8.2 Switch docked: 8 point, 4 spot, 2 shadowed spots, 1 directional.</summary>
        public static LightPoolBudget SwitchDocked => new LightPoolBudget { Point = 8, Spot = 4, SpotShadow = 2, Directional = 1, Hemisphere = 2 };

        public static LightPoolBudget For(PlatformKind kind, bool docked = true)
            => kind == PlatformKind.Switch ? (docked ? SwitchDocked : SwitchHandheld) : Prototype;
    }

    /// <summary>
    /// The fixed light pool (<c>updateLightPool</c>, L8562–L8598): each frame the lit proxies nearest the camera are copied
    /// into a fixed number of real lights per kind, so the light count (and URP's shader variants) never change. A proxy is
    /// lit when its region list shows it and its level is above 0 (<c>lightOn</c>). Score =
    /// <c>(kick ? 1e6 : boost ? 1e5 : 0) + intensity · (distance or 10) / (1 + gap² + 0.05 · dx²)</c>, gap = how far it is
    /// beyond its reach (distance or 30) from the camera's x; a proxy over 9 m beyond its reach is skipped. Shadowed spots
    /// beyond the shadow slots compete as plain spots. Directional and hemisphere lights score by intensity.
    /// <para>URP has no hemisphere light: the hemisphere slots' sky and ground colours (× intensity) are summed into
    /// <see cref="Ambient"/>, which the runtime sets as <c>RenderSettings</c>' trilight ambient.</para>
    /// Assignment allocates nothing; ties keep the proxies' order, as the prototype's stable sort does.
    /// </summary>
    public sealed class LightPool
    {
        public const double KickScore = 1e6, BoostScore = 1e5, SkipBeyond = 9, DefaultReach = 30, DefaultDistance = 10, DxWeight = 0.05;

        private readonly LightDef[] _defs;
        private readonly LightPoolBudget _budget;
        private readonly double[] _level;
        private readonly bool[] _visible;
        private readonly Vec3[] _position;
        private readonly double[] _score;
        private readonly int[] _point, _spot, _spotShadow, _dir, _hemi;
        private readonly double[] _sPoint, _sSpot, _sSpotShadow, _sDir, _sHemi;

        public LightPool(LightDef[] defs, LightPoolBudget budget = null)
        {
            _defs = defs ?? throw new ArgumentNullException(nameof(defs));
            _budget = budget ?? LightPoolBudget.Prototype;
            int n = defs.Length;
            _level = new double[n];
            _visible = new bool[n];
            _position = new Vec3[n];
            _score = new double[n];
            for (int i = 0; i < n; i++) { _level[i] = defs[i].Intensity; _position[i] = defs[i].Position; _visible[i] = true; }
            _point = Slots(_budget.Point, out _sPoint);
            _spot = Slots(_budget.Spot, out _sSpot);
            _spotShadow = Slots(_budget.SpotShadow, out _sSpotShadow);
            _dir = Slots(_budget.Directional, out _sDir);
            _hemi = Slots(_budget.Hemisphere, out _sHemi);
        }

        private static int[] Slots(int n, out double[] scores)
        {
            var s = new int[Math.Max(0, n)];
            for (int i = 0; i < s.Length; i++) s[i] = -1;
            scores = new double[s.Length];
            return s;
        }

        public int Count => _defs.Length;
        public LightDef this[int i] => _defs[i];
        public LightPoolBudget Budget => _budget;

        /// <summary>Proxy <paramref name="i"/>'s level this frame (its driver's, or the def's).</summary>
        public double Level(int i) => _level[i];
        public void SetLevel(int i, double level) => _level[i] = level;
        /// <summary>Its region list shows it (<c>l.visible</c>).</summary>
        public bool Visible(int i) => _visible[i];
        public void SetVisible(int i, bool on) => _visible[i] = on;
        /// <summary>Its position (three.js axes): the def's, or where a moving light is (the kick follows him).</summary>
        public Vec3 Position(int i) => _position[i];
        public void SetPosition(int i, Vec3 p) => _position[i] = p;
        /// <summary><c>lightOn</c>: shown and above 0.</summary>
        public bool On(int i) => _visible[i] && _level[i] > 0;

        /// <summary>The proxy in each real light, or −1 for a dark slot.</summary>
        public int PointSlots => _point.Length;
        public int Point(int slot) => _point[slot];
        public int SpotSlots => _spot.Length;
        public int Spot(int slot) => _spot[slot];
        public int SpotShadowSlots => _spotShadow.Length;
        public int SpotShadow(int slot) => _spotShadow[slot];
        public int DirectionalSlots => _dir.Length;
        public int Directional(int slot) => _dir[slot];
        public int HemisphereSlots => _hemi.Length;
        public int Hemisphere(int slot) => _hemi[slot];

        /// <summary>The ambient the hemisphere slots make: sky (up), equator (their mean) and ground colours, intensity included.</summary>
        public Rgb AmbientSky { get; private set; }
        public Rgb AmbientEquator { get; private set; }
        public Rgb AmbientGround { get; private set; }

        /// <summary>How many lit proxies wanted a slot of each kind this frame (a budget check; the overflow goes dark).</summary>
        public int Wanted { get; private set; }

        /// <summary>The proxy's score with the camera at lane x <paramref name="cameraX"/>; NaN when it is off or too far.</summary>
        public double Score(int i, double cameraX)
        {
            if (!On(i)) return double.NaN;
            var d = _defs[i];
            if (d.Kind == LightKind.Hemisphere || d.Kind == LightKind.Directional) return _level[i];
            double x = _position[i].X;
            double reach = d.Distance > 0 ? d.Distance : DefaultReach, gap = Math.Max(0, Math.Abs(x - cameraX) - reach);
            if (gap > SkipBeyond) return double.NaN;
            double dx = x - cameraX;
            return (d.Kick ? KickScore : d.Boost ? BoostScore : 0) + _level[i] * (d.Distance > 0 ? d.Distance : DefaultDistance) / (1 + gap * gap + DxWeight * dx * dx);
        }

        /// <summary><c>updateLightPool</c> with the camera at lane x <paramref name="cameraX"/>.</summary>
        public void Assign(double cameraX)
        {
            Clear(_point, _sPoint); Clear(_spot, _sSpot); Clear(_spotShadow, _sSpotShadow); Clear(_dir, _sDir); Clear(_hemi, _sHemi);
            int wanted = 0;
            for (int i = 0; i < _defs.Length; i++)
            {
                double s = Score(i, cameraX);
                _score[i] = s;
                if (double.IsNaN(s)) continue;
                wanted++;
                switch (_defs[i].Kind)
                {
                    case LightKind.Hemisphere: Insert(_hemi, _sHemi, i, s); break;
                    case LightKind.Directional: Insert(_dir, _sDir, i, s); break;
                    case LightKind.Point: Insert(_point, _sPoint, i, s); break;
                    case LightKind.Spot: if (_defs[i].Shadow) Insert(_spotShadow, _sSpotShadow, i, s); break;
                }
            }
            // Spots, with the shadowed spots that found no shadow slot (L8577–L8578), in proxy order as the prototype's push does.
            for (int i = 0; i < _defs.Length; i++)
            {
                if (_defs[i].Kind != LightKind.Spot || double.IsNaN(_score[i])) continue;
                if (_defs[i].Shadow && Array.IndexOf(_spotShadow, i) >= 0) continue;
                Insert(_spot, _sSpot, i, _score[i]);
            }
            Wanted = wanted;
            Rgb sky = Rgb.Black, ground = Rgb.Black;
            for (int k = 0; k < _hemi.Length; k++)
            {
                int i = _hemi[k];
                if (i < 0) continue;
                sky += _defs[i].Color * _level[i];
                ground += _defs[i].Ground * _level[i];
            }
            AmbientSky = sky;
            AmbientGround = ground;
            AmbientEquator = (sky + ground) * 0.5;
        }

        private static void Clear(int[] slots, double[] scores)
        {
            for (int i = 0; i < slots.Length; i++) { slots[i] = -1; scores[i] = double.NegativeInfinity; }
        }

        /// <summary>Into the top list, highest first; an equal score goes after the ones already there (a stable sort).</summary>
        private static void Insert(int[] slots, double[] scores, int index, double score)
        {
            int n = slots.Length;
            if (n == 0 || !(score > scores[n - 1]) && slots[n - 1] >= 0) return;
            int at = n - 1;
            while (at > 0 && (slots[at - 1] < 0 || score > scores[at - 1])) at--;
            for (int j = n - 1; j > at; j--) { slots[j] = slots[j - 1]; scores[j] = scores[j - 1]; }
            slots[at] = index;
            scores[at] = score;
        }
    }
}
