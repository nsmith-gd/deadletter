using System;

namespace DeadLetter.Core.Art
{
    /// <summary>The two texture targets of port_architecture §8.2 (Switch handheld and docked share one set of assets).</summary>
    public enum ArtPlatform
    {
        /// <summary>Steam / Itch: BC7, max 2048² (murals 4096²), ≤ 600 MB resident.</summary>
        PC,
        /// <summary>Switch: ASTC 6×6, max 1024² (UI 2048²), ≤ 160 MB resident.</summary>
        Switch,
    }

    /// <summary>What a texture is for, which sets its size cap.</summary>
    public enum TextureUse
    {
        /// <summary>Set dressing, signs, atlases.</summary>
        Default,
        /// <summary>A wide painted backdrop (chapter 1's 4096×1024 mural): 4096 on PC, the default cap on Switch.</summary>
        Mural,
        /// <summary>Interface art: 2048 on both.</summary>
        UI,
    }

    /// <summary>
    /// The texture budget of port_architecture §8.2, as numbers the Editor importer applies per platform (the sources in
    /// <c>art/</c> are never shrunk) and the tests check exported regions against. Estimates use 1 byte per pixel for
    /// BC7 and 16 bytes per 6×6 block for ASTC 6×6, plus a full mip chain.
    /// </summary>
    public static class TextureBudget
    {
        public const int PcMax = 2048, PcMuralMax = 4096, SwitchMax = 1024, UiMax = 2048;
        public const long PcResidentBytes = 600L * 1024 * 1024;
        public const long SwitchResidentBytes = 160L * 1024 * 1024;

        /// <summary>Unity's maxTextureSize for a texture of this use on this platform.</summary>
        public static int MaxSize(ArtPlatform platform, TextureUse use)
        {
            if (use == TextureUse.UI) return UiMax;
            if (platform == ArtPlatform.PC) return use == TextureUse.Mural ? PcMuralMax : PcMax;
            return SwitchMax;
        }

        /// <summary>A texture wider or taller than the PC default cap is a mural; everything else is default (UI is never inferred).</summary>
        public static TextureUse Classify(int width, int height) => Math.Max(width, height) > PcMax ? TextureUse.Mural : TextureUse.Default;

        /// <summary>
        /// The imported size: halved (both sides, at least 1) until the larger side fits <paramref name="maxSize"/>, as Unity's
        /// max size does for power-of-two sources. Non-power-of-two sources are kept at their size (the importer sets NPOT
        /// scale to None) and scaled by the same rule, a close upper bound.
        /// </summary>
        public static void Fit(int width, int height, int maxSize, out int w, out int h)
        {
            if (width <= 0 || height <= 0 || maxSize <= 0) throw new ArgumentOutOfRangeException(nameof(width));
            w = width; h = height;
            while (Math.Max(w, h) > maxSize)
            {
                w = Math.Max(1, w / 2);
                h = Math.Max(1, h / 2);
            }
        }

        /// <summary>GPU bytes of one compressed level.</summary>
        public static long LevelBytes(int w, int h, ArtPlatform platform)
        {
            if (platform == ArtPlatform.PC) return 16L * ((w + 3) / 4) * ((h + 3) / 4);    // BC7: 16 bytes per 4×4
            return 16L * ((w + 5) / 6) * ((h + 5) / 6);                                     // ASTC 6×6: 16 bytes per 6×6
        }

        /// <summary>Resident bytes of a texture after the platform's cap and compression, with mips.</summary>
        public static long EstimateBytes(int width, int height, ArtPlatform platform, TextureUse use, bool mips = true)
        {
            Fit(width, height, MaxSize(platform, use), out int w, out int h);
            long total = 0;
            while (true)
            {
                total += LevelBytes(w, h, platform);
                if (!mips || (w == 1 && h == 1)) break;
                w = Math.Max(1, w / 2);
                h = Math.Max(1, h / 2);
            }
            return total;
        }

        /// <summary>The resident budget for one streaming window (§8.2).</summary>
        public static long ResidentBudget(ArtPlatform platform) => platform == ArtPlatform.PC ? PcResidentBytes : SwitchResidentBytes;
    }
}
