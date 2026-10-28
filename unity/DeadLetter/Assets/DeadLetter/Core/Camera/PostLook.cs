namespace DeadLetter.Core.Camera
{
    /// <summary>
    /// The prototype's renderer and post constants (index.html L338–L381; port_architecture §4.2), for the URP Volume the
    /// runtime builds (<c>LookVolume</c>). Colours are the page's sRGB hex values.
    /// </summary>
    public static class PostLook
    {
        /// <summary>Tone-mapping exposure (L344–L345); the options' brightness (0.8–1.8) multiplies it (L8307–L8313).</summary>
        public const double Exposure = 1.4;

        /// <summary>Clear colour <c>0x030404</c> (L350).</summary>
        public const int BackgroundHex = 0x030404;
        /// <summary>FogExp2 colour <c>0x040505</c> (L351); the density is the framing's, per frame (L7797).</summary>
        public const int FogHex = 0x040505;

        /// <summary>UnrealBloomPass strength 0.55 (calm 0.35), radius 0.5, threshold 0.92, at half resolution (L357, L8290, L377).</summary>
        public const double BloomStrength = 0.55, BloomStrengthCalm = 0.35, BloomRadius = 0.5, BloomThreshold = 0.92;

        /// <summary>The final pass's vignette: <c>mix(0.55, 1, smoothstep(0.85, 0.2, r))</c> (L360–L369): 45 % darker at the rim.</summary>
        public const double VignetteDarkening = 0.45, VignetteInner = 0.2, VignetteOuter = 0.85;

        /// <summary>The final pass's grain: noise of ±0.0175 added to the colour (<c>* 0.035</c>, L360–L369).</summary>
        public const double GrainAmplitude = 0.0175;

        /// <summary>The page's exposure × the player's brightness (1.0 = the authored look).</summary>
        public static double ExposureFor(double brightness) => Exposure * (brightness > 0 ? brightness : 1.0);

        /// <summary><c>0xRRGGBB</c> → sRGB components in [0, 1].</summary>
        public static void Rgb(int hex, out double r, out double g, out double b)
        {
            r = ((hex >> 16) & 0xff) / 255.0;
            g = ((hex >> 8) & 0xff) / 255.0;
            b = (hex & 0xff) / 255.0;
        }
    }
}
