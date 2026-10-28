using DeadLetter.Core.Maths;

namespace DeadLetter.Core.Presentation
{
    /// <summary>
    /// Chapter 1's light proxies (region 6, <see cref="LightGroup.Attendance"/>), seeded from <c>buildAtt</c>'s
    /// <c>refs.attLights</c> (index.html L5174–L5221): <c>P(color, i, d, x, y, z)</c> is a point light, <c>S(color, i, d, at, to,
    /// angle, shadow)</c> a spot with penumbra 0.6 and decay 2, its shadow 512² and off on the handheld tier
    /// (<c>!touchDevice</c>). As written, not as commented: DL-12's strip-and-gate spot is inside a comment (L5180) and the
    /// grow lamp is built at 0 (rev 0.3). Driven: the DL-14a sun (<c>base · (0.06 + 0.94 · sun)</c>), the light through each
    /// blind (<c>base · (1 − w)</c>, L6274–L6276), the escort trolley's beam riding ahead of it (L6429) and DL-14's jam lamp
    /// (L5466). Shown with region 6 only (<see cref="LightRegions.Visible"/>).
    /// </summary>
    public static class AttendanceLights
    {
        private const LightGroup G = LightGroup.Attendance;
        /// <summary>The beam rides 1.1 m ahead of the trolley, at 0.95 m, z −0.2 (L6429).</summary>
        public const double BeamAhead = 1.1, BeamY = 0.95, BeamZ = -0.2;

        public static LightDef[] Build(bool touch = false)
        {
            int n = 0;
            LightDef P(int color, double i, double d, double x, double y, double z, LightDriver driver = LightDriver.None) => new LightDef
            {
                Name = "att" + n++, Kind = LightKind.Point, Group = G, Color = Rgb.Hex(color), Intensity = i, Distance = d, Decay = 2,
                Position = new Vec3(x, y, z), Driver = driver,
            };
            LightDef S(int color, double i, double d, double ax, double ay, double az, double tx, double ty, double tz, double angle, bool shadow = false) => new LightDef
            {
                Name = "att" + n++, Kind = LightKind.Spot, Group = G, Color = Rgb.Hex(color), Intensity = i, Distance = d, Decay = 2,
                Angle = angle, Penumbra = 0.6, Position = new Vec3(ax, ay, az), Target = new Vec3(tx, ty, tz),
                Shadow = shadow && !touch, ShadowMap = 512,
            };
            return new[]
            {
                // DL-12: the bench's globe, the coat on the bin, down the well behind the arrival door, the corridor's globe, the caretaker's lamp and its spill.
                P(0xffd199, 2.0, 5, 205.4, 2.5, -0.1), S(0xffd8a8, 7, 4, 202.6, 2.4, 0.6, 202.6, 0.55, -0.59, 0.5),
                P(0x99b8e6, 0.6, 3, 200.75, 1.6, -2.9), P(0xffd8b0, 1.6, 5, 212.4, 2.5, -0.1), P(0xffb873, 1.8, 3, 213.0, 1.2, -3.0), P(0xffb873, 0.5, 1.6, 212.0, 0.9, -1.5),
                // DL-13: the front seat, the apparatus (shadowed), the steps (shadowed), the case, the shoot, the doors, the desks.
                S(0xffd8a8, 7, 4.5, 219.6, 2.6, 0.8, 219.6, 0.4, 0, 0.6), S(0xffe2c0, 14, 8, 222.6, 3.4, 1.6, 222.6, 1.0, -0.6, 0.7, true),
                S(0xffe6c8, 16, 8, 226.0, 4.1, 0.6, 226.0, 1.0, -0.3, 0.65, true), P(0xffe0c0, 2.2, 3.2, 226.2, 1.6, 0.9),
                P(0xffd090, 0.9, 1.5, 225.0, 3.42, -1.25), P(0xffe0c0, 1.0, 2.5, 228.6, 3.75, -0.9), P(0xffd8b0, 0.9, 3.5, 216.6, 2.4, -0.2),
                P(0xffe0c0, 1.4, 4, 231.2, 3.9, 0.2), P(0xb8c8dc, 0.9, 3.5, 218.3, 3.3, -2.0),
                // DL-14: the globes, the hatch, the stair's top, the cupboard's lamp, and pools on the desk and the crank.
                P(0xffdcaa, 1.6, 5, 234.6, 3.1, 0), P(0xffdcaa, 1.6, 5, 240.75, 3.1, 0), P(0xbcd0e8, 0.8, 3, 239.7, 2.9, 0.3), P(0xffdcaa, 0.8, 3.5, 233.4, 3.4, 0.4),
                P(0xffb870, 2.0, 3.5, 232.62, 0.98, -2.78), S(0xffd8a8, 6, 7, 237.4, 3.7, 1.4, 237.4, 0.8, -0.6, 0.75), S(0xffe0b8, 4, 5, 242.4, 2.4, 1.6, 242.4, 0.5, -0.32, 0.5),
                // DL-15: the sick bay pendant, the duct mouth, the lift's sign and lamps, the front row, Mara's place, the attendance board,
                // the blackboard and figure A, the door end, the dim alcove of empty desks, the hiding place's lamp and its slit.
                P(0xffd8b0, 1.8, 4.5, 280.2, 2.95, -0.45), P(0xbcd0e8, 0.5, 2.0, 278.95, 2.0, -1.3), S(0xffe0b8, 5, 5, 282.0, 3.2, 1.2, 282.0, 2.1, -0.8, 0.45),
                S(0xffd8a8, 7, 6, 284.6, 3.0, 0.6, 284.6, 0.35, -0.9, 0.75, true), S(0xffe0b8, 5, 5, 286.0, 2.9, 0.9, 286.0, 0.45, -0.7, 0.4, true),
                S(0xffe2c0, 4.5, 5, 288.1, 3.2, 1.0, 288.1, 2.1, -1.38, 0.4), S(0xffe6c8, 8, 7, 290.3, 3.3, 1.4, 290.3, 1.4, -1.38, 0.6, true),
                P(0xffd8b0, 1.0, 3.5, 292.9, 2.6, 0.0), P(0xb8c8dc, 0.35, 4, 284.8, 2.6, -2.6), P(0xffb870, 1.8, 2.4, 280.62, 0.25, -0.95), P(0xffb873, 0.5, 1.4, 279.8, 0.15, -0.25),
                // DL-16: the two lit globes, the lever, the rack (shadowed), the counterweight, the boiler's glow down the well, a wash on the mural.
                P(0xffdcaa, 1.6, 5, 295.0, 2.45, 0), P(0xffdcaa, 1.6, 5, 300.05, 2.45, 0), S(0xffe0b8, 4, 4, 296.0, 2.4, 1.4, 296.0, 0.4, -0.35, 0.5),
                S(0xffd8a8, 7, 6, 305.3, 2.9, 1.6, 305.6, 1.2, -1.0, 0.7, true), S(0xffd8a8, 4, 5, 308.5, 2.7, 1.6, 308.5, 0.8, 0, 0.6),
                P(0xff7a30, 1.2, 2.5, 298.5, -1.1, -0.3), P(0xe8dcc8, 0.6, 6, 299.0, 2.4, 2.0),
                // DL-17: the pendant's pool, the bench lamp, the drawer, the grow lamp (off, rev 0.3), the stair door, the way in.
                S(0xffc27a, 5, 4, 329.95, 2.15, -0.8, 329.95, 0.0, -0.8, 1.0), S(0xffcc8c, 3, 2.5, 329.04, 1.34, -0.9, 329.5, 0.9, -0.7, 0.8),
                S(0xffd69e, 4, 4, 330.2, 1.8, 1.6, 330.2, 0.3, -0.45, 0.35), S(0xbdd1ff, 0, 3, 334.5, 1.57, -1.05, 334.5, 0.9, -1.05, 0.9),
                P(0xffc890, 0.6, 3, 339.25, 2.2, -0.95), P(0xffd8a8, 0.8, 4, 325.2, 2.6, -0.2),
                // Rev 0.3: the stair up to ring A, warm from above; the RESIDENTIAL ACCESS sign over the door.
                P(0xffc890, 3.2, 5.5, 341.8, 2.7, -0.15), P(0xffd8a8, 1.2, 3.5, 343.3, 3.5, -0.84), P(0xffc890, 1.0, 2.5, 340.5, 0.8, -0.1),
                P(0xffd8a8, 0.9, 2.0, 339.2, 2.2, 0.35),
                // Rev 0.3: the children's refuge behind the hatch.
                P(0xffb070, 1.4, 2.2, 239.6, 2.5, -1.9),
                // Pass 8: A's wheel and the pole through it, in their own low pool.
                S(0xffd8a8, 3.5, 4, 235.3, 2.6, 1.2, 234.95, 0.7, -0.62, 0.42),
                // The expansion (L5210–L5219). DL-14a: the night-light's sun, the light through W1 and W2, a dim fill.
                P(0xffe2b0, 2.6, 6, 253.9, 2.3, -0.9, LightDriver.AttSun), P(0xbcd4ff, 2.4, 5, 256.2, 2.5, -0.5, LightDriver.AttBlindW1),
                P(0xffc890, 2.0, 5, 260.1, 2.5, -0.7, LightDriver.AttBlindW2),
                // DL-14b: the trolley's beam (it follows the trolley).
                P(0xffd9a0, 1.6, 2.8, 266.0, BeamY, BeamZ, LightDriver.AttBeam),
                P(0x8fa6c8, 0.5, 6, 255.5, 3.0, 0.8), P(0x8fa6c8, 0.35, 4, 249.5, 2.4, 0.4),
                // DL-14b's globes, the stair; DL-16a: the servery, the car, the passage; DL-17: the rig.
                P(0xffdcaa, 1.3, 5, 266.8, 2.5, 0), P(0xffdcaa, 1.3, 5, 272.8, 2.5, 0), P(0xffd8a8, 1.4, 4, 276.8, 2.9, 0.2), P(0xb8c8dc, 0.5, 2.5, 269.9, 1.4, -0.7),
                P(0xffd8a8, 1.8, 5, 311.4, 3.0, 0.1), P(0xffe0b8, 1.4, 2.2, 313.0, 1.0, -0.2), P(0xffdcaa, 1.4, 5, 317.0, 3.4, 0.3), P(0xffdcaa, 1.0, 4, 322.6, 2.4, 0.2),
                P(0xffe0c0, 1.6, 3.5, 338.0, 1.9, 0.6),
                // DL-14's jam lamp at A's wheel: it flares with the grinding (L5221, L5466).
                P(0xff9a3c, 0, 1.8, 235.0, 0.75, -0.35, LightDriver.AttJam),
            };
        }
    }
}
