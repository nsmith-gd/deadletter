using System;
using DeadLetter.Core.Maths;

namespace DeadLetter.Core.Presentation
{
    /// <summary>
    /// Chapter 2's light proxies (region 7, DL-18 and DL-19, <see cref="LightGroup.SomeoneHome"/>; issue #57). No
    /// prototype: placeholder pools from the scene docs' light notes (DL-18 §3, §11 "Light pools"; DL-19 §11, chapter2_plan
    /// §4 "Light and sound", §8 rule 6), in chapter 2's lane coordinates (the host applies the world origin, #54). Built as
    /// <see cref="AttendanceLights"/> is: <c>P</c> a point light, <c>S</c> a spot with penumbra 0.6 and decay 2, its shadow
    /// off on the handheld tier. Driven: the relay boxes' green pilot lamps on the new cable's 7 s cycle
    /// (<see cref="PilotLevel"/>, in step with their click in <see cref="SomeoneHomeSounds"/>; FlashEffects'
    /// <c>ch2.relayPilots</c>), and the jack's pool, which rides over the jack (<see cref="JackY"/>, <see cref="JackZ"/>).
    /// Shown with region 7 only (<see cref="LightRegions.Visible"/>).
    /// </summary>
    public static class SomeoneHomeLights
    {
        private const LightGroup G = LightGroup.SomeoneHome;

        /// <summary>The new cable's relay boxes click and blink their pilot lamps every 7 s (chapter2_plan §4 "The new cable"; DL-18 §3, §8; DL-19 §8).</summary>
        public const double RelayPeriod = 7;
        /// <summary>
        /// The relay boxes: DL-18's on the gallery (§3: 349.4, 2.2), and one on the cable over DL-19's upper terrace (its x is
        /// not in the doc: a placeholder at 370.4, under the ceiling).
        /// </summary>
        public static readonly double[] RelayX = { 349.4, 370.4 };
        public static readonly double[] RelayY = { 2.2, 4.2 };
        /// <summary>The pilot's blink: up over <see cref="BlinkSeconds"/> from its rest level and back, once per period.</summary>
        public const double BlinkSeconds = 0.3, PilotRest = 0.55, PilotCalm = 0.7;
        /// <summary>The jack's pool rides this high above the jack, a little in front of it (DL-19 §11: "placeholder pools on the bracket and the jack").</summary>
        public const double JackY = 2.4, JackZ = 0.2;

        /// <summary>
        /// A pilot lamp's level, 0–1 of its base, at clock <paramref name="t"/>: resting at 0.55, a 0.3 s sine bump to 1 as
        /// the relay clicks (every 7 s). Calm: a steady 0.7 (no blink).
        /// </summary>
        public static double PilotLevel(double t, bool calm)
        {
            if (calm) return PilotCalm;
            double phase = t - Math.Floor(t / RelayPeriod) * RelayPeriod;
            double bump = phase < BlinkSeconds ? Math.Sin(Math.PI * phase / BlinkSeconds) : 0;
            return PilotRest + (1 - PilotRest) * bump;
        }

        public static LightDef[] Build(bool touch = false)
        {
            int n = 0;
            LightDef P(int color, double i, double d, double x, double y, double z, LightDriver driver = LightDriver.None) => new LightDef
            {
                Name = "home" + n++, Kind = LightKind.Point, Group = G, Color = Rgb.Hex(color), Intensity = i, Distance = d, Decay = 2,
                Position = new Vec3(x, y, z), Driver = driver,
            };
            LightDef S(int color, double i, double d, double ax, double ay, double az, double tx, double ty, double tz, double angle, bool shadow = false) => new LightDef
            {
                Name = "home" + n++, Kind = LightKind.Spot, Group = G, Color = Rgb.Hex(color), Intensity = i, Distance = d, Decay = 2,
                Angle = angle, Penumbra = 0.6, Position = new Vec3(ax, ay, az), Target = new Vec3(tx, ty, tz),
                Shadow = shadow && !touch, ShadowMap = 512,
            };
            return new[]
            {
                // DL-18: the gallery's two maintained lamps (§3: 348.0, 350.4 at 2.3; "amber pools", chapter2_plan §4).
                P(0xffc890, 1.6, 4.5, 348.0, 2.2, -0.3), P(0xffc890, 1.6, 4.5, 350.4, 2.2, -0.3),
                // The relay box's green pilot lamp (§3: 349.4, 2.2).
                P(0x7dff9a, 0.5, 1.5, RelayX[0], RelayY[0], -0.9, LightDriver.HomeRelayPilot),
                // The lit window across the shaft (§11 LitWindow: far background, high; lit always).
                P(0xffd08a, 2.0, 5, 350.0, 4.0, -12.0),
                // The box room is dark but for a pool on the foot rail and the strap (§11); the sky panel is read by the strap's spill.
                S(0xffd8a8, 4, 3.5, 353.8, 2.2, 0.8, 353.8, 0.55, -0.3, 0.45), S(0xffd8a8, 3.5, 3.5, 353.45, 2.2, 0.9, 353.45, 0.75, -0.4, 0.4, true),
                // The terrace landing: the shaft's cool air (a dim fill).
                P(0x8fa6c8, 0.5, 5, 358.0, 2.8, 0.4),
                // DL-19: bracket, pin and pocket share one pool (chapter2_plan §8 rule 6), shadowed; the jack has its own, riding over it.
                S(0xffd8a8, 5, 4, 363.65, 3.0, 1.0, 363.65, 1.5, -0.4, 0.5, true),
                P(0xffd8a8, 1.4, 2.4, 362.85, 1.2 + JackY, JackZ, LightDriver.HomeJack),
                // The upper terrace: the relay's pilot on the cable, and the shaft's air.
                P(0x7dff9a, 0.5, 1.5, RelayX[1], RelayY[1], -0.9, LightDriver.HomeRelayPilot),
                P(0x8fa6c8, 0.6, 6, 373.0, 4.0, 0.4),
            };
        }
    }
}
