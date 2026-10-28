using DeadLetter.Core.Camera;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace DeadLetter.Runtime.Camera
{
    /// <summary>
    /// The prototype's post (Core <see cref="PostLook"/>; index.html L338–L381, port_architecture §4.2) as the global
    /// <see cref="Volume"/>'s profile, built in Awake so it comes from the same constants on every machine (no profile asset
    /// to drift). <c>SettingsStore</c> holds the same Volume as its <c>postVolume</c> and applies brightness and calm-mode
    /// bloom on top, in Start. Also turns post-processing on for the camera and sets the page's clear and fog colours.
    /// <para>Interim until U-15's tiers: <b>Neutral</b> tone mapping stands in for AgX (URP has none; §4.2 wants a LUT
    /// exported from Blender, not ACES), and the vignette and grain are URP's, matched by eye to the page's final pass.</para>
    /// </summary>
    [DefaultExecutionOrder(-1000)]   // before SettingsStore reads the profile
    [RequireComponent(typeof(UnityEngine.Camera), typeof(Volume))]
    public sealed class LookVolume : MonoBehaviour
    {
        [SerializeField] private Volume volume;

        private VolumeProfile _profile;

        public Volume Volume => volume;

        private void Awake()
        {
            var cam = GetComponent<UnityEngine.Camera>();
            UniversalAdditionalCameraData data = cam.GetUniversalAdditionalCameraData();
            data.renderPostProcessing = true;
            data.antialiasing = AntialiasingMode.None;   // the page has no MSAA and no FXAA (L338–L341)
            cam.backgroundColor = Srgb(PostLook.BackgroundHex);
            RenderSettings.fogColor = Srgb(PostLook.FogHex);
            if (volume == null) volume = GetComponent<Volume>();

            _profile = ScriptableObject.CreateInstance<VolumeProfile>();
            _profile.name = "PrologueLook (runtime)";

            Tonemapping tone = _profile.Add<Tonemapping>(true);
            tone.mode.Override(TonemappingMode.Neutral);

            ColorAdjustments colour = _profile.Add<ColorAdjustments>(true);
            colour.postExposure.Override(Log2(PostLook.Exposure));

            Bloom bloom = _profile.Add<Bloom>(true);
            bloom.threshold.Override((float)PostLook.BloomThreshold);
            bloom.intensity.Override((float)PostLook.BloomStrength);
            bloom.scatter.Override((float)PostLook.BloomRadius);
            bloom.downscale.Override(BloomDownscaleMode.Half);

            Vignette vignette = _profile.Add<Vignette>(true);
            vignette.color.Override(Color.black);
            vignette.intensity.Override((float)PostLook.VignetteDarkening);
            vignette.smoothness.Override((float)(PostLook.VignetteOuter - PostLook.VignetteInner));
            vignette.rounded.Override(false);

            FilmGrain grain = _profile.Add<FilmGrain>(true);
            grain.type.Override(FilmGrainLookup.Thin1);
            grain.intensity.Override((float)(PostLook.GrainAmplitude * 10.0));
            grain.response.Override(0.8f);

            volume.isGlobal = true;
            volume.profile = _profile;
        }

        private void OnDestroy()
        {
            if (_profile != null) Destroy(_profile);
        }

        private static float Log2(double x) => (float)(System.Math.Log(x) / System.Math.Log(2.0));

        private static Color Srgb(int hex)
        {
            PostLook.Rgb(hex, out double r, out double g, out double b);
            return new Color((float)r, (float)g, (float)b, 1f);   // a Color is sRGB; Unity linearises it in a Linear project
        }
    }
}
