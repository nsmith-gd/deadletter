using DeadLetter.Core.Maths;
using DeadLetter.Core.Presentation;
using UnityEngine;
using UnityEngine.Rendering;

namespace DeadLetter.Runtime.Lighting
{
    /// <summary>
    /// The fixed pool of real lights (port_architecture §4.20, §8.2; <c>buildLightPool</c>/<c>updateLightPool</c>,
    /// L8542–L8598). It owns the per-tier lights (<see cref="LightPoolBudget"/>: point, spot, shadowed spot, directional),
    /// made once in DL_Persistent, so URP's light count never changes; each frame it copies into them the proxies Core's
    /// <see cref="LightPool"/> assigned (colour, level, position, range, cone, shadow) and darkens the empty slots.
    /// <para><b>Hemisphere lights do not exist in URP.</b> The hemisphere slots become the ambient instead:
    /// <c>RenderSettings.ambientMode = Trilight</c> with Core's <see cref="LightPool.AmbientSky"/>, equator and ground
    /// colours (each hemisphere's colour × its level, summed).</para>
    /// <para>Proxies are three.js values (positions with z negated here, <see cref="Vec3.ToUnity"/>); three.js r169 lights
    /// are physical (candela, decay 2), which URP's linear intensities approximate: <see cref="intensityScale"/> is the
    /// director's to tune by eye. Decay and penumbra have no URP field: URP's falloff is inverse-square to the range, and the
    /// inner cone is <c>angle · (1 − penumbra)</c>.</para>
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class LightPoolView : MonoBehaviour
    {
        [Tooltip("three.js r169 (physical) → URP intensity, per kind.")]
        [SerializeField] private float pointScale = 1f, spotScale = 1f, directionalScale = 1f, ambientScale = 1f;
        [Tooltip("Shadow strength of the shadowed spot slots.")]
        [Range(0f, 1f)] [SerializeField] private float shadowStrength = 1f;

        private Light[] _point, _spot, _spotShadow, _dir;
        private LightPool _pool;

        public LightPool Pool => _pool;

        /// <summary>Makes the pool's real lights for <paramref name="pool"/>'s budget (once; a rebind reuses them).</summary>
        public void Bind(LightPool pool)
        {
            _pool = pool;
            if (pool == null || _point != null) return;
            LightPoolBudget b = pool.Budget;
            _point = Make("Point", b.Point, LightType.Point, false);
            _spot = Make("Spot", b.Spot, LightType.Spot, false);
            _spotShadow = Make("SpotShadow", b.SpotShadow, LightType.Spot, true);
            _dir = Make("Directional", b.Directional, LightType.Directional, false);
            RenderSettings.ambientMode = AmbientMode.Trilight;
        }

        /// <summary>Per frame after Core's <see cref="LightPool.Assign"/> (and the searchlight's target).</summary>
        public void Apply(Vec3 searchTarget)
        {
            if (_pool == null || _point == null) return;
            for (int s = 0; s < _point.Length; s++) Copy(_point[s], _pool.Point(s), pointScale, default);
            for (int s = 0; s < _spot.Length; s++) Copy(_spot[s], _pool.Spot(s), spotScale, searchTarget);
            for (int s = 0; s < _spotShadow.Length; s++) Copy(_spotShadow[s], _pool.SpotShadow(s), spotScale, searchTarget);
            for (int s = 0; s < _dir.Length; s++) Copy(_dir[s], _pool.Directional(s), directionalScale, default);
            RenderSettings.ambientSkyColor = ToColor(_pool.AmbientSky, ambientScale);
            RenderSettings.ambientEquatorColor = ToColor(_pool.AmbientEquator, ambientScale);
            RenderSettings.ambientGroundColor = ToColor(_pool.AmbientGround, ambientScale);
        }

        private void Copy(Light light, int proxy, float scale, Vec3 searchTarget)
        {
            if (proxy < 0)
            {
                light.intensity = 0f;
                if (light.enabled) light.enabled = false;                    // an empty shadow slot stops rendering its map (L8580)
                return;
            }
            if (!light.enabled) light.enabled = true;
            LightDef d = _pool[proxy];
            light.color = ToColor(d.Color, 1f);
            light.intensity = (float)_pool.Level(proxy) * scale;
            Vec3 p = _pool.Position(proxy).ToUnity();
            Transform t = light.transform;
            t.position = new Vector3((float)p.X, (float)p.Y, (float)p.Z);
            if (d.Kind == LightKind.Spot || d.Kind == LightKind.Directional)
            {
                Vec3 target = (d.Driver == LightDriver.Search ? searchTarget : d.Target).ToUnity();
                Vector3 dir = new Vector3((float)(target.X - p.X), (float)(target.Y - p.Y), (float)(target.Z - p.Z));
                if (dir.sqrMagnitude > 1e-8f) t.rotation = Quaternion.LookRotation(dir);
            }
            if (d.Kind != LightKind.Directional) light.range = d.Distance > 0 ? (float)d.Distance : 30f;
            if (d.Kind == LightKind.Spot)
            {
                float outer = (float)(d.Angle * 2 * Mathf.Rad2Deg);           // three.js angle is the half-angle
                light.spotAngle = outer;
                light.innerSpotAngle = outer * Mathf.Clamp01(1f - (float)d.Penumbra);
            }
            // No per-light map size: URP ignores Light.shadowCustomResolution, so the tier's shadow atlas settings apply.
        }

        private Light[] Make(string label, int n, LightType type, bool shadow)
        {
            var lights = new Light[n];
            for (int i = 0; i < n; i++)
            {
                var go = new GameObject("Pool " + label + " " + i);
                go.transform.SetParent(transform, false);
                Light l = go.AddComponent<Light>();
                l.type = type;
                l.intensity = 0f;
                l.shadows = shadow ? LightShadows.Soft : LightShadows.None;
                l.shadowStrength = shadowStrength;
                l.enabled = false;
                lights[i] = l;
            }
            return lights;
        }

        private static Color ToColor(Rgb c, float k) => new Color((float)c.R * k, (float)c.G * k, (float)c.B * k, 1f);
    }
}
