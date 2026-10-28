using System;
using System.Collections.Generic;

namespace DeadLetter.Core.Art
{
    /// <summary>What kind of prototype material a name maps to (<c>materialFor</c>, index.html L526–L556).</summary>
    public enum PrototypeSurface
    {
        /// <summary><c>WORN</c>: painted/worn metal, wood, plaster (the grime/chip/dust shader is U-15's; this is its base).</summary>
        Worn,
        /// <summary><c>PLAIN</c>: a flat MeshStandardMaterial.</summary>
        Plain,
        /// <summary><c>GLASSY</c>: transparent (opacity), metalness 0.1, no depth write.</summary>
        Glassy,
        /// <summary><c>EMIT</c>: black base, emissive colour × intensity (0 = driven at runtime: lamps that pulse/turn on).</summary>
        Emissive,
    }

    /// <summary>One entry of the prototype's material tables. Colours are linear RGB (three.js <c>setRGB</c> in its linear working space).</summary>
    public readonly struct PrototypeMaterial
    {
        public readonly string Name;
        public readonly PrototypeSurface Surface;
        public readonly double R, G, B;
        public readonly double Roughness, Metalness;
        /// <summary>Glassy: opacity. Emissive: emissive intensity. Otherwise 1.</summary>
        public readonly double Amount;

        public PrototypeMaterial(string name, PrototypeSurface surface, double r, double g, double b, double roughness, double metalness, double amount)
        {
            Name = name; Surface = surface; R = r; G = g; B = b; Roughness = roughness; Metalness = metalness; Amount = amount;
        }
    }

    /// <summary>
    /// The prototype's look by Blender material name: <c>WORN</c> (L393–L458), <c>PLAIN</c> (L459–L467), <c>GLASSY</c> (L468) and
    /// <c>EMIT</c> (L469–L490) in <c>game/undelivered/index.html</c>, applied by <c>materialFor</c> (L526–L556) ahead of the
    /// glTF's own factors. The Blender export carries almost none of this (most factors are white and D-17's GLB has only
    /// three decal textures), so without it the sets render white and D-17 grey. Generated from index.html (base colour,
    /// roughness, metalness, opacity, emission); the worn shader's grime, chips and dust stay U-15's (port_architecture §4.3).
    /// <para><see cref="Lookup"/> strips Blender's <c>.001</c> suffixes as <c>materialFor</c> does (D-17's are <c>.003</c>).</para>
    /// </summary>
    public static class PrototypeMaterials
    {
        private static PrototypeMaterial W(string n, double r, double g, double b, double rough, double metal) => new PrototypeMaterial(n, PrototypeSurface.Worn, r, g, b, rough, metal, 1);
        private static PrototypeMaterial P(string n, double r, double g, double b, double rough, double metal) => new PrototypeMaterial(n, PrototypeSurface.Plain, r, g, b, rough, metal, 1);
        private static PrototypeMaterial G(string n, double r, double g, double b, double opacity, double rough) => new PrototypeMaterial(n, PrototypeSurface.Glassy, r, g, b, rough, 0.1, opacity);
        private static PrototypeMaterial E(string n, double r, double g, double b, double intensity) => new PrototypeMaterial(n, PrototypeSurface.Emissive, r, g, b, 0.4, 0, intensity);

        public static readonly PrototypeMaterial[] All =
        {
            W("DarkMetal", 0.017, 0.016, 0.014, 0.72, 0.25),
            W("CreamPaint", 0.66, 0.58, 0.4, 0.78, 0.0),
            W("CreamLimb", 0.62, 0.55, 0.38, 0.72, 0.0),
            W("BareMetal", 0.42, 0.4, 0.35, 0.5, 0.6),
            W("RodMetal", 0.1, 0.092, 0.075, 0.5, 0.7),
            W("ParcelPaper", 0.36, 0.27, 0.17, 0.85, 0.0),
            W("Concrete", 0.075, 0.074, 0.07, 0.92, 0.0),
            W("WallPanel", 0.09, 0.095, 0.09, 0.9, 0.0),
            W("ShutterSteel", 0.14, 0.16, 0.15, 0.7, 0.4),
            W("DepotSteel", 0.05, 0.052, 0.05, 0.6, 0.6),
            W("DepotGreen", 0.06, 0.09, 0.07, 0.65, 0.2),
            W("LeverRed", 0.45, 0.05, 0.03, 0.5, 0.1),
            W("SafetyYellow", 0.55, 0.42, 0.06, 0.8, 0.0),
            W("CrateWood", 0.18, 0.12, 0.07, 0.85, 0.0),
            W("ParcelBrown", 0.3, 0.22, 0.13, 0.9, 0.0),
            W("CastIron", 0.035, 0.034, 0.032, 0.75, 0.5),
            W("LetterPaper", 0.55, 0.52, 0.45, 0.9, 0.0),
            W("PigeonWood", 0.12, 0.085, 0.055, 0.85, 0.0),
            W("PlateSteel", 0.11, 0.115, 0.11, 0.55, 0.7),
            W("ToteGreen", 0.08, 0.11, 0.09, 0.7, 0.0),
            W("BayEnamel", 0.36, 0.4, 0.41, 0.38, 0.1),
            W("DustyCream", 0.5, 0.46, 0.35, 0.85, 0.0),
            W("DustyDark", 0.03, 0.029, 0.026, 0.82, 0.2),
            W("FloodMud", 0.062, 0.05, 0.036, 0.95, 0.0),
            W("PawlSteel", 0.32, 0.31, 0.29, 0.4, 0.8),
            W("CaveRock", 0.05, 0.048, 0.045, 0.95, 0.0),
            W("HomePlaster", 0.34, 0.29, 0.21, 0.9, 0.0),
            W("BedroomPaint", 0.46, 0.38, 0.22, 0.85, 0.0),
            W("BedroomDado", 0.2, 0.3, 0.26, 0.8, 0.0),
            W("ChildPaint", 0.12, 0.24, 0.42, 0.6, 0.0),
            W("ToyFabric", 0.36, 0.33, 0.3, 0.95, 0.0),
            W("GiltFrame", 0.3, 0.21, 0.08, 0.42, 0.75),
            W("PupilWood", 0.36, 0.27, 0.17, 0.7, 0.0),
            W("LessonPlaster", 0.27, 0.25, 0.2, 0.9, 0.0),
            W("LessonDado", 0.13, 0.19, 0.15, 0.75, 0.0),
            W("LessonLeaf", 0.11, 0.17, 0.08, 0.6, 0.0),
            W("WorkPlaster", 0.33, 0.27, 0.18, 0.9, 0.0),
            W("PotClay", 0.34, 0.15, 0.075, 0.9, 0.0),
            W("DampSoil", 0.03, 0.022, 0.015, 0.8, 0.0),
            W("WinPlaster", 0.29, 0.27, 0.21, 0.9, 0.0),
            W("WinDado", 0.12, 0.16, 0.135, 0.55, 0.0),
            W("WinLino", 0.115, 0.085, 0.05, 0.7, 0.0),
            W("TannoyEnamel", 0.2, 0.24, 0.21, 0.45, 0.1),
            W("ChildCoat", 0.07, 0.11, 0.19, 0.95, 0.0),
            W("SorterCushion", 0.16, 0.045, 0.035, 0.62, 0.0),
            W("RingPlasterA", 0.2, 0.22, 0.22, 0.9, 0.0),
            W("RingPlasterB", 0.3, 0.2, 0.17, 0.9, 0.0),
            W("RoofSlate", 0.045, 0.05, 0.055, 0.7, 0.0),
            W("LivingPaint", 0.3, 0.27, 0.2, 0.85, 0.0),
            W("DrumOlive", 0.07, 0.08, 0.05, 0.62, 0.35),
            W("HandWorn", 0.46, 0.44, 0.39, 0.35, 0.3),
            W("CotCanvas", 0.16, 0.15, 0.1, 0.95, 0.0),
            W("CanteenGreen", 0.1, 0.13, 0.1, 0.85, 0.0),
            W("HandleBlack", 0.02, 0.02, 0.018, 0.5, 0.55),
            W("HandledSteel", 0.06, 0.065, 0.06, 0.55, 0.6),
            W("HandledBrass", 0.2, 0.14, 0.06, 0.5, 0.85),
            W("WornIron", 0.045, 0.043, 0.04, 0.7, 0.6),
            W("WornStrap", 0.2, 0.17, 0.11, 0.95, 0.0),
            W("LuggageLeather", 0.15, 0.08, 0.045, 0.62, 0.0),
            W("LuggageCanvas", 0.13, 0.135, 0.105, 0.9, 0.0),
            W("FloorPaint", 0.42, 0.39, 0.3, 0.85, 0.0),
            W("BoneDry", 0.25, 0.225, 0.175, 0.88, 0.0),
            W("CoatWool", 0.035, 0.034, 0.036, 0.95, 0.0),
            W("ToyPatch", 0.42, 0.3, 0.08, 0.95, 0.0),

            P("Att17FlowWater", 0.46, 0.56, 0.58, 0.08, 0.0),
            P("NewCable", 0.016, 0.016, 0.018, 0.28, 0.0),
            P("NewSteel", 0.26, 0.27, 0.28, 0.4, 0.8),
            P("TeaEnamel", 0.58, 0.55, 0.47, 0.35, 0.0),
            P("EyeDark", 0.003, 0.003, 0.003, 0.3, 0.0),
            P("Shaft", 0.004, 0.004, 0.004, 0.9, 0.0),
            P("Cable", 0.014, 0.013, 0.012, 0.55, 0.0),
            P("Rubber", 0.012, 0.012, 0.011, 0.7, 0.0),
            P("Water", 0.01, 0.012, 0.012, 0.04, 0.3),
            P("Copper", 0.55, 0.3, 0.18, 0.35, 1.0),
            P("ReflectTag", 0.8, 0.78, 0.7, 0.15, 0.6),
            P("BeltRubber", 0.02, 0.02, 0.019, 0.8, 0.0),
            P("AtriumPlaster", 0.2, 0.185, 0.15, 0.9, 0.0),
            P("AtriumDark", 0.006, 0.006, 0.006, 0.8, 0.0),
            P("AtriumStone", 0.058, 0.052, 0.045, 0.95, 0.0),
            P("AtriumCut", 0.085, 0.078, 0.066, 0.95, 0.0),
            P("AtriumSheet", 0.075, 0.082, 0.08, 0.6, 0.4),
            P("AtriumRust", 0.11, 0.048, 0.025, 0.85, 0.0),
            P("AtriumMasonry", 0.15, 0.135, 0.115, 0.85, 0.0),
            P("SectionCap", 0.012, 0.011, 0.01, 0.95, 0.0),
            P("FloodScum", 0.09, 0.095, 0.075, 0.9, 0.0),
            P("DirtyGlass", 0.03, 0.035, 0.035, 0.25, 0.2),
            P("AtriumCloth", 0.2, 0.13, 0.065, 0.9, 0.0),
            P("AtriumWood", 0.085, 0.06, 0.04, 0.88, 0.0),
            P("Barricade", 0.4, 0.06, 0.04, 0.7, 0.0),
            P("AtriumVine", 0.055, 0.068, 0.036, 0.9, 0.0),
            P("AtriumMoss", 0.085, 0.1, 0.05, 0.95, 0.0),
            P("AtriumWet", 0.014, 0.016, 0.015, 0.35, 0.0),
            P("CandleWax", 0.55, 0.5, 0.4, 0.6, 0.0),
            P("GaugeNeedle", 0.02, 0.018, 0.016, 0.4, 0.3),
            P("BrassPolished", 0.8, 0.62, 0.32, 0.22, 1.0),
            P("Brass", 0.45, 0.32, 0.12, 0.45, 0.8),
            P("DeadBulb", 0.16, 0.16, 0.15, 0.25, 0.0),

            G("Window", 0.8, 0.82, 0.8, 0.16, 0.06),
            G("Canister", 0.45, 0.48, 0.45, 0.5, 0.35),

            E("Att14bTrolleyLamp", 1.0, 0.8, 0.5, 4.0),
            E("Att14bBeam", 1.0, 0.85, 0.6, 1.0),
            E("Att16aCarLamp", 1.0, 0.8, 0.52, 4.0),
            E("Att15HideLamp", 1.0, 0.7, 0.4, 5.0),
            E("Att16PitGlow", 1.0, 0.42, 0.14, 2.2),
            E("Att17GrowLamp", 0.78, 0.84, 1.0, 3.0),
            E("Att17Bulb", 1.0, 0.78, 0.5, 5.0),
            E("Att17StairLamp", 1.0, 0.8, 0.55, 6.0),
            E("AttBulbGlow", 1.0, 0.82, 0.58, 4.0),
            E("AttLessonLamp", 1.0, 0.78, 0.42, 0.0),
            E("AttShoot", 0.78, 0.92, 0.62, 0.35),
            E("AttGlobeLamp", 1.0, 0.86, 0.62, 3.0),
            E("AttCupboardLamp", 1.0, 0.72, 0.42, 6.0),
            E("EndWindowGlow", 1.0, 0.64, 0.32, 9.0),
            E("EndCurtainGlow", 1.0, 0.42, 0.16, 3.2),
            E("EndPilotLamp", 1.0, 0.6, 0.18, 6.0),
            E("SecretLampGlow", 1.0, 0.78, 0.5, 6.0),
            E("DenLanternGlow", 1.0, 0.55, 0.22, 2.5),
            E("Glow", 1.0, 0.36, 0.08, 7.0),
            E("GlowDim", 0.85, 0.3, 0.08, 0.9),
            E("ParcelLamp", 1.0, 0.55, 0.2, 6.0),
            E("LampA", 0.85, 0.3, 0.08, 0.9),
            E("LampB", 0.85, 0.3, 0.08, 0.9),
            E("LampC", 0.85, 0.3, 0.08, 0.9),
            E("EyeGlint", 1.0, 0.84, 0.62, 2.5),
            E("WorkBulb", 1.0, 0.92, 0.8, 0.0),
            E("CradleStatus", 0.35, 1.0, 0.45, 0.0),
            E("Spark", 0.7, 0.85, 1.0, 0.0),
            E("FarGlow", 0.45, 0.55, 0.6, 0.09),
            E("RelayA", 0.75, 1.0, 0.82, 0.0),
            E("RelayB", 0.75, 1.0, 0.82, 0.0),
            E("RelayC", 0.75, 1.0, 0.82, 0.0),
            E("CordBulb", 1.0, 0.85, 0.6, 0.0),
            E("DoorGlow", 0.6, 0.85, 0.72, 0.0),
            E("PassageGlow", 0.6, 0.85, 0.72, 0.0),
            E("PlateBulb", 1.0, 0.9, 0.75, 0.0),
            E("ScanLamp0", 1.0, 0.25, 0.12, 0.0),
            E("ScanLamp1", 1.0, 0.25, 0.12, 0.0),
            E("ScanLamp2", 1.0, 0.25, 0.12, 0.0),
            E("ScanBar", 1.0, 0.2, 0.1, 0.0),
            E("GuideArrow", 1.0, 0.3, 0.12, 0.0),
            E("DockLamp", 1.0, 0.7, 0.3, 0.0),
            E("Interlock", 1.0, 0.2, 0.1, 0.0),
            E("PitBulb", 1.0, 0.86, 0.66, 0.0),
            E("GalleryBulb", 0.9, 0.95, 1.0, 0.0),
            E("CarrierLamp", 1.0, 0.6, 0.2, 0.0),
            E("RowLight0", 0.8, 0.92, 0.95, 0.0),
            E("RowLight1", 0.8, 0.92, 0.95, 0.0),
            E("RowLight2", 0.8, 0.92, 0.95, 0.0),
            E("RowLight3", 0.8, 0.92, 0.95, 0.0),
            E("RowLight4", 0.8, 0.92, 0.95, 0.0),
            E("RowLight5", 0.8, 0.92, 0.95, 0.0),
            E("HallBulb4", 1.0, 0.88, 0.7, 0.0),
            E("AtLanding", 1.0, 0.62, 0.18, 0.0),
            E("PawlLamp", 1.0, 0.55, 0.16, 0.0),
            E("BeaconLamp", 1.0, 0.55, 0.12, 0.0),
            E("TunnelBulb", 0.95, 0.9, 0.78, 0.0),
            E("RampLamp0", 0.55, 1.0, 0.65, 0.0),
            E("RampLamp1", 0.55, 1.0, 0.65, 0.0),
            E("RampLamp2", 0.55, 1.0, 0.65, 0.0),
            E("RampLamp3", 0.55, 1.0, 0.65, 0.0),
            E("RampLamp4", 0.55, 1.0, 0.65, 0.0),
            E("RampLamp5", 0.55, 1.0, 0.65, 0.0),
            E("WindowSun", 1.0, 0.72, 0.38, 0.0),
            E("HomeLampBulb", 1.0, 0.76, 0.46, 0.0),
            E("LaneBulb", 0.78, 0.88, 1.0, 0.0),
            E("TermLamp0", 0.75, 1.0, 0.82, 0.0),
            E("TermLamp1", 0.75, 1.0, 0.82, 0.0),
            E("TermLamp2", 0.75, 1.0, 0.82, 0.0),
            E("AtriumWindowGlow", 1.0, 0.55, 0.24, 1.2),
            E("AtriumHazeLights", 0.6, 0.72, 0.9, 0.6),
            E("HallBulbGlow", 1.0, 0.82, 0.55, 0.0),
            E("C108BellLamp", 1.0, 0.55, 0.16, 3.0),
            E("PressLamp", 1.0, 0.16, 0.08, 0.0),
            E("C108Lamp", 1.0, 0.7, 0.42, 1.2),
            E("BayLight", 0.72, 0.88, 1.0, 2.0),
            E("BayLamp0", 0.72, 0.92, 1.0, 0.0),
            E("BayLamp1", 0.72, 0.92, 1.0, 0.0),
            E("BayLamp2", 0.72, 0.92, 1.0, 0.0),
            E("FallenLamp", 0.85, 0.3, 0.08, 0.0),
            E("SeatedLamp", 0.85, 0.3, 0.08, 0.0),
            E("SortLampBulb", 1.0, 0.85, 0.6, 6.0),
            E("TubeLamp", 0.8, 0.9, 1.0, 2.5),
            E("GantryLamp", 1.0, 0.78, 0.5, 8.0),
            E("SlotLamp9", 1.0, 0.62, 0.22, 0.0),
            E("SlotLamp2", 1.0, 0.62, 0.22, 0.0),
            E("SlotLamp6", 1.0, 0.62, 0.22, 0.0),
            E("LandingAmber", 1.0, 0.62, 0.18, 0.0),
            E("StopStripe", 1.0, 0.55, 0.15, 0.0),
            E("CageBulb", 1.0, 0.86, 0.62, 0.0),
            E("TrayLamp", 1.0, 0.78, 0.45, 4.0),
            E("LiftUpLampGlow", 1.0, 0.58, 0.18, 0.0),
            E("ServiceUpLampGlow", 1.0, 0.58, 0.18, 0.0),
            E("LobbyBulb", 1.0, 0.84, 0.6, 0.0),
            E("CarLamp", 1.0, 0.9, 0.75, 0.0),
            E("DispatchLineLamp", 1.0, 0.62, 0.26, 4.0),
            E("CarPlateLamp0", 0.72, 0.92, 1.0, 0.0),
            E("CarPlateLamp1", 0.72, 0.92, 1.0, 0.0),
            E("CarPlateLamp2", 0.72, 0.92, 1.0, 0.0),
            E("CrankLamp", 1.0, 0.86, 0.64, 0.0),
            E("ShaftSky", 0.62, 0.74, 0.9, 0.6),
            E("RationLamp", 0.86, 0.95, 0.84, 3.0),
            E("RationCandle", 1.0, 0.62, 0.25, 4.0),
            E("RingLamp", 1.0, 0.78, 0.5, 0.0),
            E("RingLampRed", 1.0, 0.18, 0.1, 0.0),
            E("HomeLight", 1.0, 0.72, 0.4, 0.0),
            E("SkyPanel", 0.7, 0.8, 0.9, 0.0),
        };

        private static readonly Dictionary<string, PrototypeMaterial> ByName = Index();

        private static Dictionary<string, PrototypeMaterial> Index()
        {
            var d = new Dictionary<string, PrototypeMaterial>(StringComparer.Ordinal);
            // materialFor tests WORN, then PLAIN, GLASSY, EMIT: the first table that has a name wins.
            foreach (PrototypeMaterial m in All) if (!d.ContainsKey(m.Name)) d.Add(m.Name, m);
            return d;
        }

        /// <summary><paramref name="materialName"/> without Blender's numeric suffix (<c>CreamLimb.003</c> → <c>CreamLimb</c>).</summary>
        public static string BaseName(string materialName)
        {
            if (string.IsNullOrEmpty(materialName)) return materialName;
            int dot = materialName.LastIndexOf('.');
            if (dot <= 0 || dot == materialName.Length - 1) return materialName;
            for (int i = dot + 1; i < materialName.Length; i++) if (materialName[i] < '0' || materialName[i] > '9') return materialName;
            return materialName.Substring(0, dot);
        }

        public static bool Lookup(string materialName, out PrototypeMaterial m) => ByName.TryGetValue(BaseName(materialName) ?? "", out m);
    }
}
