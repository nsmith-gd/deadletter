using System;
using System.Collections.Generic;

namespace DeadLetter.Core.Art
{
    /// <summary>A linear RGB colour, as the prototype's tables give it (<c>lin()</c>, L492: three.js's linear working space).</summary>
    public readonly struct Rgb
    {
        public readonly double R, G, B;
        public Rgb(double r, double g, double b) { R = r; G = g; B = b; }
        public override string ToString() => "(" + R + ", " + G + ", " + B + ")";
    }

    /// <summary>
    /// A <c>WORN</c> entry (L393–L458): the base colour blended to dirt by grime and streak masks, then to chipped paint
    /// (with its own roughness), then to dust on up-facing surfaces. The masks are object-space value-noise fbm
    /// (<c>wornMaterial</c>, L493–L523; the Unity port is the <c>DeadLetter/Worn</c> shader).
    /// </summary>
    public sealed class WornSpec
    {
        public readonly Rgb Base, Dirt, Chip, Dust;
        public readonly double Rough, ChipRough, Metal, Grime, ChipScale, ChipAmt, DustAmt, Streak;

        /// <param name="dust">Null = the base colour (<c>s.dust || s.base</c>, L498).</param>
        /// <param name="dustAmt">0 when the entry has none (<c>s.dustAmt || 0</c>, L500).</param>
        /// <param name="streak">0.4 when the entry has none (<c>s.streak || 0.4</c>, L500).</param>
        public WornSpec(Rgb @base, Rgb dirt, Rgb chip, Rgb? dust, double rough, double chipRough, double metal, double grime,
            double chipScale, double chipAmt, double dustAmt, double streak)
        {
            Base = @base; Dirt = dirt; Chip = chip; Dust = dust ?? @base;
            Rough = rough; ChipRough = chipRough; Metal = metal; Grime = grime; ChipScale = chipScale; ChipAmt = chipAmt;
            DustAmt = dustAmt; Streak = streak;
        }
    }

    /// <summary>A <c>PLAIN</c> entry (L459–L467): flat colour, roughness, metalness.</summary>
    public sealed class PlainSpec
    {
        public readonly Rgb Color;
        public readonly double Roughness, Metalness;
        public PlainSpec(Rgb color, double roughness, double metalness) { Color = color; Roughness = roughness; Metalness = metalness; }
    }

    /// <summary>A <c>GLASSY</c> entry (L468): transparent, metalness 0.1, no depth write.</summary>
    public sealed class GlassySpec
    {
        public readonly Rgb Color;
        public readonly double Opacity, Roughness;
        public GlassySpec(Rgb color, double opacity, double roughness) { Color = color; Opacity = opacity; Roughness = roughness; }
    }

    /// <summary>An <c>EMIT</c> entry (L469–L490): black base, roughness 0.4, emissive colour × default intensity (the game drives most by name).</summary>
    public sealed class EmitSpec
    {
        public readonly Rgb Color;
        public readonly double Intensity;
        public EmitSpec(Rgb color, double intensity) { Color = color; Intensity = intensity; }
    }

    public enum MaterialKind
    {
        /// <summary>Not in the tables and no image: the exported material as it is (<c>else m = src</c>, L550).</summary>
        Source,
        Worn,
        Plain,
        Glassy,
        Emit,
        /// <summary>An image keeps its map, roughness 0.75; a decal (transparent source, <c>Chalk*</c>, <c>RingLetter*</c>) blends with alpha test 0.02 (L544–L548).</summary>
        Image,
        /// <summary><c>AtriumMist</c>: additive unlit, colour (0.32, 0.4, 0.48), opacity 0.22, double-sided (L538–L539).</summary>
        Additive,
    }

    /// <summary>What <c>materialFor</c> (L527–L554) makes of one Blender material.</summary>
    public sealed class MaterialSpec
    {
        public string Name;
        public MaterialKind Kind;
        public Rgb Color;
        public double Roughness = 1, Metalness;
        public bool Transparent;
        public double Opacity = 1;
        public bool DepthWrite = true;
        public double AlphaTest;
        public bool Decal;
        public Rgb Emissive;
        public double EmissiveIntensity;
        public WornSpec Worn;
    }

    /// <summary>
    /// The prototype's material tables, keyed by Blender material name (port_architecture §4.3; index.html L393–L554),
    /// copied verbatim. For every name listed here the web build ignores the exported glTF material and builds its own;
    /// the Unity art pipeline (<c>ArtMaterials</c>) does the same, so the sets are not the export's white placeholders.
    /// </summary>
    public static class PrototypeMaterials
    {
        public static readonly IReadOnlyDictionary<string, WornSpec> Worn = new Dictionary<string, WornSpec>(StringComparer.Ordinal)
        {
            ["DarkMetal"] = new WornSpec(new Rgb(0.017, 0.016, 0.014), new Rgb(0.03, 0.024, 0.016), new Rgb(0.075, 0.068, 0.055), new Rgb(0.075, 0.072, 0.062), rough: 0.72, chipRough: 0.45, metal: 0.25, grime: 5, chipScale: 34, chipAmt: 0.78, dustAmt: 0.7, streak: 0.4),
            ["CreamPaint"] = new WornSpec(new Rgb(0.66, 0.58, 0.40), new Rgb(0.36, 0.30, 0.19), new Rgb(0.028, 0.025, 0.02), new Rgb(0.62, 0.57, 0.45), rough: 0.78, chipRough: 0.5, metal: 0, grime: 3, chipScale: 20, chipAmt: 0.63, dustAmt: 0.3, streak: 0.55),
            ["CreamLimb"] = new WornSpec(new Rgb(0.62, 0.55, 0.38), new Rgb(0.30, 0.25, 0.16), new Rgb(0.03, 0.027, 0.022), null, rough: 0.72, chipRough: 0.5, metal: 0, grime: 14, chipScale: 55, chipAmt: 0.66, dustAmt: 0, streak: 0.6),
            ["BareMetal"] = new WornSpec(new Rgb(0.42, 0.40, 0.35), new Rgb(0.2, 0.18, 0.14), new Rgb(0.05, 0.045, 0.04), null, rough: 0.5, chipRough: 0.6, metal: 0.6, grime: 10, chipScale: 40, chipAmt: 0.7, dustAmt: 0, streak: 0.4),
            ["RodMetal"] = new WornSpec(new Rgb(0.10, 0.092, 0.075), new Rgb(0.05, 0.042, 0.03), new Rgb(0.2, 0.18, 0.15), null, rough: 0.5, chipRough: 0.4, metal: 0.7, grime: 20, chipScale: 60, chipAmt: 0.75, dustAmt: 0, streak: 0.7),
            ["ParcelPaper"] = new WornSpec(new Rgb(0.36, 0.27, 0.17), new Rgb(0.2, 0.15, 0.09), new Rgb(0.45, 0.38, 0.28), null, rough: 0.85, chipRough: 0.8, metal: 0, grime: 30, chipScale: 80, chipAmt: 0.8, dustAmt: 0, streak: 0.4),
            ["Concrete"] = new WornSpec(new Rgb(0.075, 0.074, 0.07), new Rgb(0.035, 0.034, 0.03), new Rgb(0.12, 0.115, 0.105), new Rgb(0.11, 0.105, 0.095), rough: 0.92, chipRough: 0.9, metal: 0, grime: 1.3, chipScale: 9, chipAmt: 0.7, dustAmt: 0.5, streak: 0.5),
            ["WallPanel"] = new WornSpec(new Rgb(0.09, 0.095, 0.09), new Rgb(0.04, 0.04, 0.035), new Rgb(0.14, 0.13, 0.11), null, rough: 0.9, chipRough: 0.85, metal: 0, grime: 2, chipScale: 12, chipAmt: 0.74, dustAmt: 0, streak: 0.8),
            ["ShutterSteel"] = new WornSpec(new Rgb(0.14, 0.16, 0.15), new Rgb(0.09, 0.05, 0.025), new Rgb(0.16, 0.08, 0.035), new Rgb(0.12, 0.11, 0.1), rough: 0.7, chipRough: 0.6, metal: 0.4, grime: 3, chipScale: 16, chipAmt: 0.6, dustAmt: 0.5, streak: 0.8),
            ["DepotSteel"] = new WornSpec(new Rgb(0.05, 0.052, 0.05), new Rgb(0.05, 0.03, 0.018), new Rgb(0.16, 0.15, 0.13), new Rgb(0.09, 0.085, 0.075), rough: 0.6, chipRough: 0.4, metal: 0.6, grime: 6, chipScale: 40, chipAmt: 0.74, dustAmt: 0.6, streak: 0.4),
            ["DepotGreen"] = new WornSpec(new Rgb(0.06, 0.09, 0.07), new Rgb(0.04, 0.035, 0.025), new Rgb(0.12, 0.11, 0.1), null, rough: 0.65, chipRough: 0.5, metal: 0.2, grime: 8, chipScale: 40, chipAmt: 0.7, dustAmt: 0.5, streak: 0.4),
            ["LeverRed"] = new WornSpec(new Rgb(0.45, 0.05, 0.03), new Rgb(0.2, 0.04, 0.02), new Rgb(0.08, 0.07, 0.06), null, rough: 0.5, chipRough: 0.6, metal: 0.1, grime: 20, chipScale: 60, chipAmt: 0.7, dustAmt: 0, streak: 0.4),
            ["SafetyYellow"] = new WornSpec(new Rgb(0.55, 0.42, 0.06), new Rgb(0.2, 0.16, 0.05), new Rgb(0.07, 0.068, 0.062), null, rough: 0.8, chipRough: 0.9, metal: 0, grime: 4, chipScale: 10, chipAmt: 0.55, dustAmt: 0.6, streak: 0.4),
            ["CrateWood"] = new WornSpec(new Rgb(0.18, 0.12, 0.07), new Rgb(0.08, 0.055, 0.035), new Rgb(0.25, 0.19, 0.12), null, rough: 0.85, chipRough: 0.8, metal: 0, grime: 6, chipScale: 30, chipAmt: 0.75, dustAmt: 0, streak: 0.6),
            ["ParcelBrown"] = new WornSpec(new Rgb(0.3, 0.22, 0.13), new Rgb(0.15, 0.11, 0.07), new Rgb(0.4, 0.33, 0.24), new Rgb(0.2, 0.18, 0.15), rough: 0.9, chipRough: 0.85, metal: 0, grime: 10, chipScale: 40, chipAmt: 0.75, dustAmt: 0.7, streak: 0.4),
            ["CastIron"] = new WornSpec(new Rgb(0.035, 0.034, 0.032), new Rgb(0.05, 0.03, 0.018), new Rgb(0.13, 0.12, 0.1), new Rgb(0.08, 0.075, 0.065), rough: 0.75, chipRough: 0.45, metal: 0.5, grime: 9, chipScale: 50, chipAmt: 0.72, dustAmt: 0.5, streak: 0.4),
            ["LetterPaper"] = new WornSpec(new Rgb(0.55, 0.52, 0.45), new Rgb(0.3, 0.27, 0.2), new Rgb(0.62, 0.6, 0.55), new Rgb(0.5, 0.48, 0.42), rough: 0.9, chipRough: 0.9, metal: 0, grime: 18, chipScale: 40, chipAmt: 0.8, dustAmt: 0.5, streak: 0.4),
            ["PigeonWood"] = new WornSpec(new Rgb(0.12, 0.085, 0.055), new Rgb(0.06, 0.045, 0.03), new Rgb(0.2, 0.15, 0.1), new Rgb(0.1, 0.09, 0.08), rough: 0.85, chipRough: 0.8, metal: 0, grime: 6, chipScale: 30, chipAmt: 0.75, dustAmt: 0.6, streak: 0.4),
            ["PlateSteel"] = new WornSpec(new Rgb(0.11, 0.115, 0.11), new Rgb(0.06, 0.04, 0.025), new Rgb(0.2, 0.19, 0.17), new Rgb(0.1, 0.095, 0.085), rough: 0.55, chipRough: 0.4, metal: 0.7, grime: 5, chipScale: 30, chipAmt: 0.7, dustAmt: 0.4, streak: 0.4),
            ["ToteGreen"] = new WornSpec(new Rgb(0.08, 0.11, 0.09), new Rgb(0.05, 0.05, 0.04), new Rgb(0.16, 0.18, 0.15), new Rgb(0.1, 0.1, 0.09), rough: 0.7, chipRough: 0.6, metal: 0, grime: 12, chipScale: 40, chipAmt: 0.72, dustAmt: 0.5, streak: 0.4),
            ["BayEnamel"] = new WornSpec(new Rgb(0.36, 0.40, 0.41), new Rgb(0.29, 0.31, 0.31), new Rgb(0.2, 0.21, 0.2), new Rgb(0.33, 0.34, 0.33), rough: 0.38, chipRough: 0.6, metal: 0.1, grime: 2.5, chipScale: 60, chipAmt: 0.9, dustAmt: 0.1, streak: 0.15),
            ["DustyCream"] = new WornSpec(new Rgb(0.5, 0.46, 0.35), new Rgb(0.3, 0.26, 0.18), new Rgb(0.03, 0.027, 0.022), new Rgb(0.56, 0.54, 0.48), rough: 0.85, chipRough: 0.55, metal: 0, grime: 4, chipScale: 24, chipAmt: 0.64, dustAmt: 0.95, streak: 0.4),
            ["DustyDark"] = new WornSpec(new Rgb(0.03, 0.029, 0.026), new Rgb(0.05, 0.045, 0.035), new Rgb(0.09, 0.085, 0.075), new Rgb(0.15, 0.145, 0.13), rough: 0.82, chipRough: 0.5, metal: 0.2, grime: 5, chipScale: 34, chipAmt: 0.78, dustAmt: 1, streak: 0.4),
            ["FloodMud"] = new WornSpec(new Rgb(0.062, 0.05, 0.036), new Rgb(0.035, 0.028, 0.02), new Rgb(0.09, 0.076, 0.058), null, rough: 0.95, chipRough: 0.85, metal: 0, grime: 3, chipScale: 20, chipAmt: 0.6, dustAmt: 0, streak: 0.4),
            ["PawlSteel"] = new WornSpec(new Rgb(0.32, 0.31, 0.29), new Rgb(0.12, 0.1, 0.08), new Rgb(0.5, 0.48, 0.44), null, rough: 0.4, chipRough: 0.3, metal: 0.8, grime: 18, chipScale: 50, chipAmt: 0.7, dustAmt: 0, streak: 0.4),
            ["CaveRock"] = new WornSpec(new Rgb(0.05, 0.048, 0.045), new Rgb(0.028, 0.026, 0.024), new Rgb(0.085, 0.08, 0.072), null, rough: 0.95, chipRough: 0.9, metal: 0, grime: 1.5, chipScale: 8, chipAmt: 0.7, dustAmt: 0, streak: 0.7),
            ["HomePlaster"] = new WornSpec(new Rgb(0.34, 0.29, 0.21), new Rgb(0.17, 0.14, 0.10), new Rgb(0.24, 0.20, 0.15), null, rough: 0.9, chipRough: 0.85, metal: 0, grime: 3, chipScale: 18, chipAmt: 0.7, dustAmt: 0, streak: 0.6),
            ["BedroomPaint"] = new WornSpec(new Rgb(0.46, 0.38, 0.22), new Rgb(0.25, 0.20, 0.12), new Rgb(0.34, 0.29, 0.21), null, rough: 0.85, chipRough: 0.9, metal: 0, grime: 3, chipScale: 20, chipAmt: 0.74, dustAmt: 0, streak: 0.4),
            ["BedroomDado"] = new WornSpec(new Rgb(0.20, 0.30, 0.26), new Rgb(0.10, 0.13, 0.10), new Rgb(0.34, 0.29, 0.21), null, rough: 0.8, chipRough: 0.9, metal: 0, grime: 4, chipScale: 24, chipAmt: 0.7, dustAmt: 0, streak: 0.4),
            ["ChildPaint"] = new WornSpec(new Rgb(0.12, 0.24, 0.42), new Rgb(0.06, 0.09, 0.12), new Rgb(0.20, 0.14, 0.08), null, rough: 0.6, chipRough: 0.8, metal: 0, grime: 8, chipScale: 40, chipAmt: 0.7, dustAmt: 0, streak: 0.4),
            ["ToyFabric"] = new WornSpec(new Rgb(0.36, 0.33, 0.30), new Rgb(0.18, 0.15, 0.12), new Rgb(0.42, 0.40, 0.36), null, rough: 0.95, chipRough: 0.95, metal: 0, grime: 20, chipScale: 60, chipAmt: 0.8, dustAmt: 0, streak: 0.4),
            ["GiltFrame"] = new WornSpec(new Rgb(0.30, 0.21, 0.08), new Rgb(0.10, 0.07, 0.032), new Rgb(0.20, 0.09, 0.05), new Rgb(0.14, 0.12, 0.09), rough: 0.42, chipRough: 0.8, metal: 0.75, grime: 14, chipScale: 60, chipAmt: 0.74, dustAmt: 0.6, streak: 0.3),
            ["PupilWood"] = new WornSpec(new Rgb(0.36, 0.27, 0.17), new Rgb(0.17, 0.12, 0.08), new Rgb(0.46, 0.38, 0.27), new Rgb(0.3, 0.28, 0.24), rough: 0.7, chipRough: 0.6, metal: 0, grime: 12, chipScale: 40, chipAmt: 0.74, dustAmt: 0.5, streak: 0.4),
            ["LessonPlaster"] = new WornSpec(new Rgb(0.27, 0.25, 0.2), new Rgb(0.14, 0.12, 0.09), new Rgb(0.17, 0.15, 0.12), null, rough: 0.9, chipRough: 0.85, metal: 0, grime: 3, chipScale: 18, chipAmt: 0.7, dustAmt: 0, streak: 0.6),
            ["LessonDado"] = new WornSpec(new Rgb(0.13, 0.19, 0.15), new Rgb(0.07, 0.09, 0.07), new Rgb(0.25, 0.23, 0.19), null, rough: 0.75, chipRough: 0.9, metal: 0, grime: 4, chipScale: 24, chipAmt: 0.68, dustAmt: 0, streak: 0.5),
            ["LessonLeaf"] = new WornSpec(new Rgb(0.11, 0.17, 0.08), new Rgb(0.06, 0.08, 0.04), new Rgb(0.3, 0.24, 0.16), null, rough: 0.6, chipRough: 0.5, metal: 0, grime: 10, chipScale: 40, chipAmt: 0.72, dustAmt: 0, streak: 0.3),
            ["WorkPlaster"] = new WornSpec(new Rgb(0.33, 0.27, 0.18), new Rgb(0.17, 0.13, 0.08), new Rgb(0.23, 0.19, 0.14), new Rgb(0.26, 0.22, 0.16), rough: 0.9, chipRough: 0.85, metal: 0, grime: 3, chipScale: 18, chipAmt: 0.7, dustAmt: 0.4, streak: 0.5),
            ["PotClay"] = new WornSpec(new Rgb(0.34, 0.15, 0.075), new Rgb(0.16, 0.1, 0.06), new Rgb(0.42, 0.36, 0.28), new Rgb(0.36, 0.32, 0.26), rough: 0.9, chipRough: 0.95, metal: 0, grime: 10, chipScale: 40, chipAmt: 0.72, dustAmt: 0.5, streak: 0.3),
            ["DampSoil"] = new WornSpec(new Rgb(0.03, 0.022, 0.015), new Rgb(0.018, 0.013, 0.009), new Rgb(0.06, 0.045, 0.03), new Rgb(0.06, 0.05, 0.04), rough: 0.8, chipRough: 0.45, metal: 0, grime: 30, chipScale: 80, chipAmt: 0.7, dustAmt: 0.1, streak: 0.4),
            ["WinPlaster"] = new WornSpec(new Rgb(0.29, 0.27, 0.21), new Rgb(0.15, 0.13, 0.095), new Rgb(0.2, 0.185, 0.15), new Rgb(0.24, 0.22, 0.18), rough: 0.9, chipRough: 0.85, metal: 0, grime: 3, chipScale: 18, chipAmt: 0.7, dustAmt: 0.5, streak: 0.6),
            ["WinDado"] = new WornSpec(new Rgb(0.12, 0.16, 0.135), new Rgb(0.065, 0.075, 0.06), new Rgb(0.30, 0.27, 0.21), new Rgb(0.16, 0.17, 0.15), rough: 0.55, chipRough: 0.85, metal: 0, grime: 4, chipScale: 22, chipAmt: 0.68, dustAmt: 0.4, streak: 0.5),
            ["WinLino"] = new WornSpec(new Rgb(0.115, 0.085, 0.05), new Rgb(0.06, 0.045, 0.03), new Rgb(0.075, 0.07, 0.062), new Rgb(0.13, 0.12, 0.1), rough: 0.7, chipRough: 0.9, metal: 0, grime: 3, chipScale: 14, chipAmt: 0.66, dustAmt: 0.6, streak: 0.3),
            ["TannoyEnamel"] = new WornSpec(new Rgb(0.2, 0.24, 0.21), new Rgb(0.09, 0.1, 0.085), new Rgb(0.05, 0.048, 0.042), new Rgb(0.16, 0.16, 0.14), rough: 0.45, chipRough: 0.7, metal: 0.1, grime: 4, chipScale: 30, chipAmt: 0.68, dustAmt: 0.5, streak: 0.6),
            ["ChildCoat"] = new WornSpec(new Rgb(0.07, 0.11, 0.19), new Rgb(0.04, 0.05, 0.06), new Rgb(0.12, 0.15, 0.2), null, rough: 0.95, chipRough: 0.95, metal: 0, grime: 8, chipScale: 30, chipAmt: 0.75, dustAmt: 0.5, streak: 0.4),
            ["SorterCushion"] = new WornSpec(new Rgb(0.16, 0.045, 0.035), new Rgb(0.07, 0.03, 0.022), new Rgb(0.24, 0.17, 0.12), new Rgb(0.12, 0.1, 0.09), rough: 0.62, chipRough: 0.85, metal: 0, grime: 8, chipScale: 30, chipAmt: 0.72, dustAmt: 0.4, streak: 0.4),
            ["RingPlasterA"] = new WornSpec(new Rgb(0.20, 0.22, 0.22), new Rgb(0.10, 0.10, 0.09), new Rgb(0.13, 0.12, 0.10), null, rough: 0.9, chipRough: 0.85, metal: 0, grime: 3, chipScale: 18, chipAmt: 0.7, dustAmt: 0, streak: 0.6),
            ["RingPlasterB"] = new WornSpec(new Rgb(0.30, 0.20, 0.17), new Rgb(0.15, 0.10, 0.08), new Rgb(0.20, 0.16, 0.13), null, rough: 0.9, chipRough: 0.85, metal: 0, grime: 3, chipScale: 18, chipAmt: 0.7, dustAmt: 0, streak: 0.6),
            ["RoofSlate"] = new WornSpec(new Rgb(0.045, 0.05, 0.055), new Rgb(0.03, 0.03, 0.03), new Rgb(0.08, 0.08, 0.075), new Rgb(0.07, 0.07, 0.065), rough: 0.7, chipRough: 0.8, metal: 0, grime: 4, chipScale: 24, chipAmt: 0.72, dustAmt: 0.6, streak: 0.4),
            ["LivingPaint"] = new WornSpec(new Rgb(0.30, 0.27, 0.20), new Rgb(0.16, 0.13, 0.09), new Rgb(0.22, 0.19, 0.14), null, rough: 0.85, chipRough: 0.9, metal: 0, grime: 3, chipScale: 20, chipAmt: 0.74, dustAmt: 0, streak: 0.4),
            ["DrumOlive"] = new WornSpec(new Rgb(0.07, 0.08, 0.05), new Rgb(0.045, 0.038, 0.024), new Rgb(0.26, 0.25, 0.22), new Rgb(0.1, 0.095, 0.08), rough: 0.62, chipRough: 0.35, metal: 0.35, grime: 6, chipScale: 30, chipAmt: 0.68, dustAmt: 0.5, streak: 0.5),
            ["HandWorn"] = new WornSpec(new Rgb(0.46, 0.44, 0.39), new Rgb(0.2, 0.18, 0.15), new Rgb(0.62, 0.6, 0.55), null, rough: 0.35, chipRough: 0.3, metal: 0.3, grime: 22, chipScale: 60, chipAmt: 0.72, dustAmt: 0, streak: 0.2),
            ["CotCanvas"] = new WornSpec(new Rgb(0.16, 0.15, 0.10), new Rgb(0.08, 0.07, 0.045), new Rgb(0.2, 0.19, 0.15), null, rough: 0.95, chipRough: 0.95, metal: 0, grime: 6, chipScale: 30, chipAmt: 0.78, dustAmt: 0, streak: 0.3),
            ["CanteenGreen"] = new WornSpec(new Rgb(0.10, 0.13, 0.10), new Rgb(0.05, 0.055, 0.045), new Rgb(0.16, 0.15, 0.13), null, rough: 0.85, chipRough: 0.9, metal: 0, grime: 2, chipScale: 14, chipAmt: 0.7, dustAmt: 0, streak: 0.8),
            ["HandleBlack"] = new WornSpec(new Rgb(0.02, 0.02, 0.018), new Rgb(0.035, 0.03, 0.024), new Rgb(0.55, 0.53, 0.5), new Rgb(0.06, 0.058, 0.05), rough: 0.5, chipRough: 0.22, metal: 0.55, grime: 12, chipScale: 45, chipAmt: 0.58, dustAmt: 0.3, streak: 0.4),
            ["HandledSteel"] = new WornSpec(new Rgb(0.06, 0.065, 0.06), new Rgb(0.04, 0.035, 0.03), new Rgb(0.55, 0.53, 0.5), new Rgb(0.08, 0.075, 0.07), rough: 0.55, chipRough: 0.22, metal: 0.6, grime: 6, chipScale: 22, chipAmt: 0.52, dustAmt: 0.2, streak: 0.4),
            ["HandledBrass"] = new WornSpec(new Rgb(0.2, 0.14, 0.06), new Rgb(0.08, 0.06, 0.03), new Rgb(0.62, 0.46, 0.2), new Rgb(0.12, 0.1, 0.07), rough: 0.5, chipRough: 0.2, metal: 0.85, grime: 8, chipScale: 26, chipAmt: 0.5, dustAmt: 0.2, streak: 0.4),
            ["WornIron"] = new WornSpec(new Rgb(0.045, 0.043, 0.04), new Rgb(0.06, 0.035, 0.02), new Rgb(0.3, 0.29, 0.27), new Rgb(0.09, 0.085, 0.075), rough: 0.7, chipRough: 0.35, metal: 0.6, grime: 9, chipScale: 40, chipAmt: 0.6, dustAmt: 0.4, streak: 0.4),
            ["WornStrap"] = new WornSpec(new Rgb(0.2, 0.17, 0.11), new Rgb(0.1, 0.08, 0.05), new Rgb(0.32, 0.28, 0.2), new Rgb(0.2, 0.18, 0.14), rough: 0.95, chipRough: 0.9, metal: 0, grime: 14, chipScale: 50, chipAmt: 0.7, dustAmt: 0.3, streak: 0.4),
            ["LuggageLeather"] = new WornSpec(new Rgb(0.15, 0.08, 0.045), new Rgb(0.06, 0.035, 0.02), new Rgb(0.27, 0.18, 0.11), null, rough: 0.62, chipRough: 0.8, metal: 0, grime: 12, chipScale: 40, chipAmt: 0.74, dustAmt: 0.5, streak: 0.4),
            ["LuggageCanvas"] = new WornSpec(new Rgb(0.13, 0.135, 0.105), new Rgb(0.07, 0.065, 0.05), new Rgb(0.21, 0.2, 0.16), null, rough: 0.9, chipRough: 0.9, metal: 0, grime: 10, chipScale: 30, chipAmt: 0.72, dustAmt: 0.6, streak: 0.4),
            ["FloorPaint"] = new WornSpec(new Rgb(0.42, 0.39, 0.3), new Rgb(0.2, 0.18, 0.13), new Rgb(0.075, 0.074, 0.07), null, rough: 0.85, chipRough: 0.92, metal: 0, grime: 3, chipScale: 14, chipAmt: 0.58, dustAmt: 0.4, streak: 0.4),
            ["BoneDry"] = new WornSpec(new Rgb(0.25, 0.225, 0.175), new Rgb(0.11, 0.095, 0.07), new Rgb(0.33, 0.31, 0.26), null, rough: 0.88, chipRough: 0.9, metal: 0, grime: 10, chipScale: 40, chipAmt: 0.7, dustAmt: 0, streak: 0.4),
            ["CoatWool"] = new WornSpec(new Rgb(0.035, 0.034, 0.036), new Rgb(0.03, 0.026, 0.02), new Rgb(0.07, 0.066, 0.06), new Rgb(0.06, 0.058, 0.052), rough: 0.95, chipRough: 0.95, metal: 0, grime: 8, chipScale: 30, chipAmt: 0.75, dustAmt: 0.2, streak: 0.4),
            ["ToyPatch"] = new WornSpec(new Rgb(0.42, 0.30, 0.08), new Rgb(0.20, 0.14, 0.05), new Rgb(0.30, 0.32, 0.40), null, rough: 0.95, chipRough: 0.95, metal: 0, grime: 20, chipScale: 60, chipAmt: 0.8, dustAmt: 0, streak: 0.4),
        };

        public static readonly IReadOnlyDictionary<string, PlainSpec> Plain = new Dictionary<string, PlainSpec>(StringComparer.Ordinal)
        {
            ["Att17FlowWater"] = new PlainSpec(new Rgb(0.46, 0.56, 0.58), roughness: 0.08, metalness: 0),
            ["NewCable"] = new PlainSpec(new Rgb(0.016, 0.016, 0.018), roughness: 0.28, metalness: 0),
            ["NewSteel"] = new PlainSpec(new Rgb(0.26, 0.27, 0.28), roughness: 0.4, metalness: 0.8),
            ["TeaEnamel"] = new PlainSpec(new Rgb(0.58, 0.55, 0.47), roughness: 0.35, metalness: 0),
            ["EyeDark"] = new PlainSpec(new Rgb(0.003, 0.003, 0.003), roughness: 0.3, metalness: 0),
            ["Shaft"] = new PlainSpec(new Rgb(0.004, 0.004, 0.004), roughness: 0.9, metalness: 0),
            ["Cable"] = new PlainSpec(new Rgb(0.014, 0.013, 0.012), roughness: 0.55, metalness: 0),
            ["Rubber"] = new PlainSpec(new Rgb(0.012, 0.012, 0.011), roughness: 0.7, metalness: 0),
            ["Water"] = new PlainSpec(new Rgb(0.01, 0.012, 0.012), roughness: 0.04, metalness: 0.3),
            ["Copper"] = new PlainSpec(new Rgb(0.55, 0.3, 0.18), roughness: 0.35, metalness: 1),
            ["ReflectTag"] = new PlainSpec(new Rgb(0.8, 0.78, 0.7), roughness: 0.15, metalness: 0.6),
            ["BeltRubber"] = new PlainSpec(new Rgb(0.02, 0.02, 0.019), roughness: 0.8, metalness: 0),
            ["AtriumPlaster"] = new PlainSpec(new Rgb(0.2, 0.185, 0.15), roughness: 0.9, metalness: 0),
            ["AtriumDark"] = new PlainSpec(new Rgb(0.006, 0.006, 0.006), roughness: 0.8, metalness: 0),
            ["AtriumStone"] = new PlainSpec(new Rgb(0.058, 0.052, 0.045), roughness: 0.95, metalness: 0),
            ["AtriumCut"] = new PlainSpec(new Rgb(0.085, 0.078, 0.066), roughness: 0.95, metalness: 0),
            ["AtriumSheet"] = new PlainSpec(new Rgb(0.075, 0.082, 0.08), roughness: 0.6, metalness: 0.4),
            ["AtriumRust"] = new PlainSpec(new Rgb(0.11, 0.048, 0.025), roughness: 0.85, metalness: 0),
            ["AtriumMasonry"] = new PlainSpec(new Rgb(0.15, 0.135, 0.115), roughness: 0.85, metalness: 0),
            ["SectionCap"] = new PlainSpec(new Rgb(0.012, 0.011, 0.01), roughness: 0.95, metalness: 0),
            ["FloodScum"] = new PlainSpec(new Rgb(0.09, 0.095, 0.075), roughness: 0.9, metalness: 0),
            ["DirtyGlass"] = new PlainSpec(new Rgb(0.03, 0.035, 0.035), roughness: 0.25, metalness: 0.2),
            ["AtriumCloth"] = new PlainSpec(new Rgb(0.2, 0.13, 0.065), roughness: 0.9, metalness: 0),
            ["AtriumWood"] = new PlainSpec(new Rgb(0.085, 0.06, 0.04), roughness: 0.88, metalness: 0),
            ["Barricade"] = new PlainSpec(new Rgb(0.4, 0.06, 0.04), roughness: 0.7, metalness: 0),
            ["AtriumVine"] = new PlainSpec(new Rgb(0.055, 0.068, 0.036), roughness: 0.9, metalness: 0),
            ["AtriumMoss"] = new PlainSpec(new Rgb(0.085, 0.1, 0.05), roughness: 0.95, metalness: 0),
            ["AtriumWet"] = new PlainSpec(new Rgb(0.014, 0.016, 0.015), roughness: 0.35, metalness: 0),
            ["CandleWax"] = new PlainSpec(new Rgb(0.55, 0.5, 0.4), roughness: 0.6, metalness: 0),
            ["GaugeNeedle"] = new PlainSpec(new Rgb(0.02, 0.018, 0.016), roughness: 0.4, metalness: 0.3),
            ["BrassPolished"] = new PlainSpec(new Rgb(0.8, 0.62, 0.32), roughness: 0.22, metalness: 1),
            ["Brass"] = new PlainSpec(new Rgb(0.45, 0.32, 0.12), roughness: 0.45, metalness: 0.8),
            ["DeadBulb"] = new PlainSpec(new Rgb(0.16, 0.16, 0.15), roughness: 0.25, metalness: 0),
        };

        public static readonly IReadOnlyDictionary<string, GlassySpec> Glassy = new Dictionary<string, GlassySpec>(StringComparer.Ordinal)
        {
            ["Window"] = new GlassySpec(new Rgb(0.8, 0.82, 0.8), opacity: 0.16, roughness: 0.06),
            ["Canister"] = new GlassySpec(new Rgb(0.45, 0.48, 0.45), opacity: 0.5, roughness: 0.35),
        };

        public static readonly IReadOnlyDictionary<string, EmitSpec> Emit = new Dictionary<string, EmitSpec>(StringComparer.Ordinal)
        {
            ["Att14bTrolleyLamp"] = new EmitSpec(new Rgb(1, 0.8, 0.5), intensity: 4),
            ["Att14bBeam"] = new EmitSpec(new Rgb(1, 0.85, 0.6), intensity: 1),
            ["Att16aCarLamp"] = new EmitSpec(new Rgb(1, 0.8, 0.52), intensity: 4),
            ["Att15HideLamp"] = new EmitSpec(new Rgb(1, 0.7, 0.4), intensity: 5),
            ["Att16PitGlow"] = new EmitSpec(new Rgb(1, 0.42, 0.14), intensity: 2.2),
            ["Att17GrowLamp"] = new EmitSpec(new Rgb(0.78, 0.84, 1), intensity: 3),
            ["Att17Bulb"] = new EmitSpec(new Rgb(1, 0.78, 0.5), intensity: 5),
            ["Att17StairLamp"] = new EmitSpec(new Rgb(1, 0.8, 0.55), intensity: 6),
            ["AttBulbGlow"] = new EmitSpec(new Rgb(1, 0.82, 0.58), intensity: 4),
            ["AttLessonLamp"] = new EmitSpec(new Rgb(1, 0.78, 0.42), intensity: 0),
            ["AttShoot"] = new EmitSpec(new Rgb(0.78, 0.92, 0.62), intensity: 0.35),
            ["AttGlobeLamp"] = new EmitSpec(new Rgb(1, 0.86, 0.62), intensity: 3),
            ["AttCupboardLamp"] = new EmitSpec(new Rgb(1, 0.72, 0.42), intensity: 6),
            ["EndWindowGlow"] = new EmitSpec(new Rgb(1, 0.64, 0.32), intensity: 9),
            ["EndCurtainGlow"] = new EmitSpec(new Rgb(1, 0.42, 0.16), intensity: 3.2),
            ["EndPilotLamp"] = new EmitSpec(new Rgb(1, 0.6, 0.18), intensity: 6),
            ["SecretLampGlow"] = new EmitSpec(new Rgb(1, 0.78, 0.5), intensity: 6),
            ["DenLanternGlow"] = new EmitSpec(new Rgb(1, 0.55, 0.22), intensity: 2.5),
            ["Glow"] = new EmitSpec(new Rgb(1, 0.36, 0.08), intensity: 7),
            ["GlowDim"] = new EmitSpec(new Rgb(0.85, 0.3, 0.08), intensity: 0.9),
            ["ParcelLamp"] = new EmitSpec(new Rgb(1, 0.55, 0.2), intensity: 6),
            ["LampA"] = new EmitSpec(new Rgb(0.85, 0.3, 0.08), intensity: 0.9),
            ["LampB"] = new EmitSpec(new Rgb(0.85, 0.3, 0.08), intensity: 0.9),
            ["LampC"] = new EmitSpec(new Rgb(0.85, 0.3, 0.08), intensity: 0.9),
            ["EyeGlint"] = new EmitSpec(new Rgb(1, 0.84, 0.62), intensity: 2.5),
            ["WorkBulb"] = new EmitSpec(new Rgb(1, 0.92, 0.8), intensity: 0),
            ["CradleStatus"] = new EmitSpec(new Rgb(0.35, 1, 0.45), intensity: 0),
            ["Spark"] = new EmitSpec(new Rgb(0.7, 0.85, 1), intensity: 0),
            ["FarGlow"] = new EmitSpec(new Rgb(0.45, 0.55, 0.6), intensity: 0.09),
            ["RelayA"] = new EmitSpec(new Rgb(0.75, 1, 0.82), intensity: 0),
            ["RelayB"] = new EmitSpec(new Rgb(0.75, 1, 0.82), intensity: 0),
            ["RelayC"] = new EmitSpec(new Rgb(0.75, 1, 0.82), intensity: 0),
            ["CordBulb"] = new EmitSpec(new Rgb(1, 0.85, 0.6), intensity: 0),
            ["DoorGlow"] = new EmitSpec(new Rgb(0.6, 0.85, 0.72), intensity: 0),
            ["PassageGlow"] = new EmitSpec(new Rgb(0.6, 0.85, 0.72), intensity: 0),
            ["PlateBulb"] = new EmitSpec(new Rgb(1, 0.9, 0.75), intensity: 0),
            ["ScanLamp0"] = new EmitSpec(new Rgb(1, 0.25, 0.12), intensity: 0),
            ["ScanLamp1"] = new EmitSpec(new Rgb(1, 0.25, 0.12), intensity: 0),
            ["ScanLamp2"] = new EmitSpec(new Rgb(1, 0.25, 0.12), intensity: 0),
            ["ScanBar"] = new EmitSpec(new Rgb(1, 0.2, 0.1), intensity: 0),
            ["GuideArrow"] = new EmitSpec(new Rgb(1, 0.3, 0.12), intensity: 0),
            ["DockLamp"] = new EmitSpec(new Rgb(1, 0.7, 0.3), intensity: 0),
            ["Interlock"] = new EmitSpec(new Rgb(1, 0.2, 0.1), intensity: 0),
            ["PitBulb"] = new EmitSpec(new Rgb(1, 0.86, 0.66), intensity: 0),
            ["GalleryBulb"] = new EmitSpec(new Rgb(0.9, 0.95, 1), intensity: 0),
            ["CarrierLamp"] = new EmitSpec(new Rgb(1, 0.6, 0.2), intensity: 0),
            ["RowLight0"] = new EmitSpec(new Rgb(0.8, 0.92, 0.95), intensity: 0),
            ["RowLight1"] = new EmitSpec(new Rgb(0.8, 0.92, 0.95), intensity: 0),
            ["RowLight2"] = new EmitSpec(new Rgb(0.8, 0.92, 0.95), intensity: 0),
            ["RowLight3"] = new EmitSpec(new Rgb(0.8, 0.92, 0.95), intensity: 0),
            ["RowLight4"] = new EmitSpec(new Rgb(0.8, 0.92, 0.95), intensity: 0),
            ["RowLight5"] = new EmitSpec(new Rgb(0.8, 0.92, 0.95), intensity: 0),
            ["HallBulb4"] = new EmitSpec(new Rgb(1, 0.88, 0.7), intensity: 0),
            ["AtLanding"] = new EmitSpec(new Rgb(1, 0.62, 0.18), intensity: 0),
            ["PawlLamp"] = new EmitSpec(new Rgb(1, 0.55, 0.16), intensity: 0),
            ["BeaconLamp"] = new EmitSpec(new Rgb(1, 0.55, 0.12), intensity: 0),
            ["TunnelBulb"] = new EmitSpec(new Rgb(0.95, 0.9, 0.78), intensity: 0),
            ["RampLamp0"] = new EmitSpec(new Rgb(0.55, 1, 0.65), intensity: 0),
            ["RampLamp1"] = new EmitSpec(new Rgb(0.55, 1, 0.65), intensity: 0),
            ["RampLamp2"] = new EmitSpec(new Rgb(0.55, 1, 0.65), intensity: 0),
            ["RampLamp3"] = new EmitSpec(new Rgb(0.55, 1, 0.65), intensity: 0),
            ["RampLamp4"] = new EmitSpec(new Rgb(0.55, 1, 0.65), intensity: 0),
            ["RampLamp5"] = new EmitSpec(new Rgb(0.55, 1, 0.65), intensity: 0),
            ["WindowSun"] = new EmitSpec(new Rgb(1, 0.72, 0.38), intensity: 0),
            ["HomeLampBulb"] = new EmitSpec(new Rgb(1, 0.76, 0.46), intensity: 0),
            ["LaneBulb"] = new EmitSpec(new Rgb(0.78, 0.88, 1), intensity: 0),
            ["TermLamp0"] = new EmitSpec(new Rgb(0.75, 1, 0.82), intensity: 0),
            ["TermLamp1"] = new EmitSpec(new Rgb(0.75, 1, 0.82), intensity: 0),
            ["TermLamp2"] = new EmitSpec(new Rgb(0.75, 1, 0.82), intensity: 0),
            ["AtriumWindowGlow"] = new EmitSpec(new Rgb(1, 0.55, 0.24), intensity: 1.2),
            ["AtriumHazeLights"] = new EmitSpec(new Rgb(0.6, 0.72, 0.9), intensity: 0.6),
            ["HallBulbGlow"] = new EmitSpec(new Rgb(1, 0.82, 0.55), intensity: 0),
            ["C108BellLamp"] = new EmitSpec(new Rgb(1, 0.55, 0.16), intensity: 3),
            ["PressLamp"] = new EmitSpec(new Rgb(1, 0.16, 0.08), intensity: 0),
            ["C108Lamp"] = new EmitSpec(new Rgb(1, 0.7, 0.42), intensity: 1.2),
            ["BayLight"] = new EmitSpec(new Rgb(0.72, 0.88, 1), intensity: 2),
            ["BayLamp0"] = new EmitSpec(new Rgb(0.72, 0.92, 1), intensity: 0),
            ["BayLamp1"] = new EmitSpec(new Rgb(0.72, 0.92, 1), intensity: 0),
            ["BayLamp2"] = new EmitSpec(new Rgb(0.72, 0.92, 1), intensity: 0),
            ["FallenLamp"] = new EmitSpec(new Rgb(0.85, 0.3, 0.08), intensity: 0),
            ["SeatedLamp"] = new EmitSpec(new Rgb(0.85, 0.3, 0.08), intensity: 0),
            ["SortLampBulb"] = new EmitSpec(new Rgb(1, 0.85, 0.6), intensity: 6),
            ["TubeLamp"] = new EmitSpec(new Rgb(0.8, 0.9, 1), intensity: 2.5),
            ["GantryLamp"] = new EmitSpec(new Rgb(1, 0.78, 0.5), intensity: 8),
            ["SlotLamp9"] = new EmitSpec(new Rgb(1, 0.62, 0.22), intensity: 0),
            ["SlotLamp2"] = new EmitSpec(new Rgb(1, 0.62, 0.22), intensity: 0),
            ["SlotLamp6"] = new EmitSpec(new Rgb(1, 0.62, 0.22), intensity: 0),
            ["LandingAmber"] = new EmitSpec(new Rgb(1, 0.62, 0.18), intensity: 0),
            ["StopStripe"] = new EmitSpec(new Rgb(1, 0.55, 0.15), intensity: 0),
            ["CageBulb"] = new EmitSpec(new Rgb(1, 0.86, 0.62), intensity: 0),
            ["TrayLamp"] = new EmitSpec(new Rgb(1, 0.78, 0.45), intensity: 4),
            ["LiftUpLampGlow"] = new EmitSpec(new Rgb(1, 0.58, 0.18), intensity: 0),
            ["ServiceUpLampGlow"] = new EmitSpec(new Rgb(1, 0.58, 0.18), intensity: 0),
            ["LobbyBulb"] = new EmitSpec(new Rgb(1, 0.84, 0.6), intensity: 0),
            ["CarLamp"] = new EmitSpec(new Rgb(1, 0.9, 0.75), intensity: 0),
            ["DispatchLineLamp"] = new EmitSpec(new Rgb(1, 0.62, 0.26), intensity: 4),
            ["CarPlateLamp0"] = new EmitSpec(new Rgb(0.72, 0.92, 1), intensity: 0),
            ["CarPlateLamp1"] = new EmitSpec(new Rgb(0.72, 0.92, 1), intensity: 0),
            ["CarPlateLamp2"] = new EmitSpec(new Rgb(0.72, 0.92, 1), intensity: 0),
            ["CrankLamp"] = new EmitSpec(new Rgb(1, 0.86, 0.64), intensity: 0),
            ["ShaftSky"] = new EmitSpec(new Rgb(0.62, 0.74, 0.9), intensity: 0.6),
            ["RationLamp"] = new EmitSpec(new Rgb(0.86, 0.95, 0.84), intensity: 3),
            ["RationCandle"] = new EmitSpec(new Rgb(1, 0.62, 0.25), intensity: 4),
            ["RingLamp"] = new EmitSpec(new Rgb(1, 0.78, 0.5), intensity: 0),
            ["RingLampRed"] = new EmitSpec(new Rgb(1, 0.18, 0.1), intensity: 0),
            ["HomeLight"] = new EmitSpec(new Rgb(1, 0.72, 0.4), intensity: 0),
            ["SkyPanel"] = new EmitSpec(new Rgb(0.7, 0.8, 0.9), intensity: 0),
        };

        /// <summary>"Name.001" → "Name" (a second copy of a material comes back numbered, L528).</summary>
        public static string BaseName(string name)
        {
            if (string.IsNullOrEmpty(name)) return name;
            int dot = name.LastIndexOf('.');
            if (dot <= 0 || dot == name.Length - 1) return name;
            for (int i = dot + 1; i < name.Length; i++) if (name[i] < '0' || name[i] > '9') return name;
            return name.Substring(0, dot);
        }

        /// <summary>
        /// <c>materialFor</c> (L527–L554) for one exported material: the tables in the prototype's order (WORN, PLAIN,
        /// GLASSY, AtriumMist, EMIT), then an image keeps its map, else the source.
        /// </summary>
        /// <param name="name">The Blender material name (a <c>.NNN</c> suffix is stripped).</param>
        /// <param name="hasImage">The exported material has a base colour map.</param>
        /// <param name="sourceTransparent">The exported material blends (glTF alphaMode BLEND).</param>
        public static MaterialSpec For(string name, bool hasImage = false, bool sourceTransparent = false)
        {
            string n = BaseName(name) ?? "";
            var s = new MaterialSpec { Name = n };
            if (Worn.TryGetValue(n, out WornSpec w))
            {
                s.Kind = MaterialKind.Worn; s.Worn = w; s.Color = w.Base; s.Roughness = w.Rough; s.Metalness = w.Metal;
            }
            else if (Plain.TryGetValue(n, out PlainSpec p))
            {
                s.Kind = MaterialKind.Plain; s.Color = p.Color; s.Roughness = p.Roughness; s.Metalness = p.Metalness;
                if (n == "Water")   // L535: a little see-through, and rougher so lamps don't blind off it
                {
                    s.Color = new Rgb(0.03, 0.05, 0.052); s.Roughness = 0.24; s.Metalness = 0.04;
                    s.Transparent = true; s.Opacity = 0.66; s.DepthWrite = false;
                }
            }
            else if (Glassy.TryGetValue(n, out GlassySpec g))
            {
                s.Kind = MaterialKind.Glassy; s.Color = g.Color; s.Roughness = g.Roughness; s.Metalness = 0.1;
                s.Transparent = true; s.Opacity = g.Opacity; s.DepthWrite = false;
            }
            else if (n == "AtriumMist")
            {
                s.Kind = MaterialKind.Additive; s.Color = new Rgb(0.32, 0.4, 0.48); s.Transparent = true; s.Opacity = 0.22; s.DepthWrite = false;
            }
            else if (Emit.TryGetValue(n, out EmitSpec e))
            {
                s.Kind = MaterialKind.Emit; s.Color = new Rgb(0, 0, 0); s.Roughness = 0.4;
                s.Emissive = e.Color; s.EmissiveIntensity = e.Intensity;
            }
            else if (hasImage)
            {
                bool decal = sourceTransparent || n.StartsWith("Chalk", StringComparison.Ordinal) || n.StartsWith("RingLetter", StringComparison.Ordinal);
                s.Kind = MaterialKind.Image; s.Color = new Rgb(1, 1, 1); s.Roughness = 0.75;
                s.Decal = decal; s.Transparent = decal; s.DepthWrite = !decal; s.AlphaTest = decal ? 0.02 : 0;
            }
            else s.Kind = MaterialKind.Source;
            return s;
        }
    }
}
