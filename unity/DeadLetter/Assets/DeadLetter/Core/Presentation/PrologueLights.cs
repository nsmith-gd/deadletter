using System;
using DeadLetter.Core.Beings;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Cycles;
using DeadLetter.Core.Mechanisms.Drives;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl06;
using DeadLetter.Core.Streaming;

namespace DeadLetter.Core.Presentation
{
    /// <summary>What sets a proxy's level each frame (the prototype's per-frame <c>intensity</c> writes).</summary>
    public enum LightDriver
    {
        /// <summary>Its <see cref="LightDef.Intensity"/> (<c>userData.base</c>, L4087; or the constructor's).</summary>
        None,
        /// <summary>Not ported (the cord lamp: 0); the opening's spark light (0 in play).</summary>
        Off,
        /// <summary><c>5 · min(1.4, Σ relay lamps)</c> (L1567).</summary>
        Relay,
        /// <summary><c>24 · bulb</c>, the bulb steady in play (L1572).</summary>
        WorkBulb,
        /// <summary>The kick: <c>0.55</c> in play, at (x + 0.5, y + 1.0, 1.3) (L1573, L7587).</summary>
        Kick,
        /// <summary>The live cable: <c>2.5 · live</c> while it arcs; calm: a steady 0.4 instead of the flicker (L7939–L7941).</summary>
        Cable,
        /// <summary>The searchlight: 140, its target sweeping <c>t · 0.12</c> (L7943–L7945).</summary>
        Search,
        /// <summary><c>1.2 · doorOpen</c> (L7961).</summary>
        Door,
        /// <summary><c>9 · (1 − 0.7 · doorOpen) · (0.9 + 0.1 · sin 1.7t)</c> (L7962).</summary>
        Crank,
        /// <summary>The plate lamp <c>16 · lamp</c> and the room fill <c>3.2 · lamp</c>, lamp = region 2 or the passage (L2409–L2413).</summary>
        PlateLamp, RoomFill,
        /// <summary><c>0.6 · smooth(doorOpen · 1.5)</c> (L2408).</summary>
        Passage,
        /// <summary><c>0.1 + 3.6 · lit</c> (the first two), <c>0.1 + 1.6 · lit</c> (the third) (L2426).</summary>
        RackNear, RackFar,
        /// <summary>Idle: <c>1.6 · blink</c>; after: 1.4 rejected, else 0.4 (L2431–L2432).</summary>
        Scanner,
        /// <summary>DL-06's floor: <c>base · (lightRegion 3)</c>; the skylight breathes <c>0.85 + 0.15 · sin 0.3t</c> (L2846–L2847).</summary>
        SortingFloor, SortingSky,
        /// <summary>The Ration Hall's strip <c>14 · fl</c> and fill <c>2.2 · fl</c>, fl flickering unless calm (L4927–L4929); the candles (L4930).</summary>
        RationStrip, RationFill, Candles,
        /// <summary>DL-14a's sun: <c>base · (0.06 + 0.94 · sun)</c>, the night-light's sun track (L6274).</summary>
        AttSun,
        /// <summary>DL-14a's light through W1 / W2: <c>base · (1 − w)</c> (L6275–L6276).</summary>
        AttBlindW1, AttBlindW2,
        /// <summary>DL-14b's trolley beam: its base, riding 1.1 m ahead of the trolley (L6429).</summary>
        AttBeam,
        /// <summary>DL-14's jam lamp: <c>1.2 · (0.6 + 0.4 · sin 31t)</c> while the chain grinds against the pole, else 0 (L5465–L5466; its 0.1 s ease left out); calm: a steady 1.2 · 0.6 (FlashEffects' <c>dl14.clutchLight</c>).</summary>
        AttJam,
    }

    /// <summary>
    /// The prologue's light proxies for regions 1–3 (DL-01 to DL-06/07), seeded from index.html as §4.20 cites:
    /// <c>buildLights</c> L1460–L1478, DL-03/04's L2209–L2221, DL-06's L2608–L2617, the pass-6/10 lamps L4052–L4087 (the
    /// sorting hall, the bay, the voice players, the first secret room and its spill, the cot, the Ration Hall) and the
    /// atmosphere's L7872–L7885. Not seeded: the opening's spark light (its position is the GLB's <c>Sparks</c>; it is lit
    /// only in the opening), and regions 4+ (DL-08 on; U-15 moves every light to Blender's <c>LGT_</c> empties).
    /// </summary>
    public static class PrologueLights
    {
        public const double Off2 = 13, Off3 = 33, CrankX = 9.62, ScannerX = Off3 + 28.9, TubeX = 14.6, BayX = 44.5;
        private const double Deg = Math.PI / 180;

        /// <param name="touch">The prototype's <c>touch</c> (handheld tier): the relay casts no shadow (<c>castShadow = !touch</c>, L1466).</param>
        public static LightDef[] Build(bool touch = false) => new[]
        {
            // buildLights (L1460–L1478)
            new LightDef { Name = "hemi", Kind = LightKind.Hemisphere, Group = LightGroup.Always, Color = Rgb.Hex(0x26332f), Ground = Rgb.Hex(0x0b0b0a), Intensity = 0.45 },
            new LightDef { Name = "rim", Kind = LightKind.Directional, Group = LightGroup.Always, Color = Rgb.Hex(0x8db4c8), Intensity = 0.35, Position = new Vec3(5, 3, -8), Target = new Vec3(3, 0, 0) },
            Spot("relay", LightGroup.Relay, 0xbfffd0, 0, 7, 70, 0.8, 2, 2.0, 1.46, -0.8, 1.2, 0.2, 0.3, shadow: touch ? 0 : 512, driver: LightDriver.Relay),
            Spot("work", LightGroup.Work, 0xffe8cc, 0, 9, 58, 0.65, 2, 1.7, 2.05, -0.25, 1.9, 0, 0.1, shadow: 1024, driver: LightDriver.WorkBulb),
            new LightDef { Name = "kick", Kind = LightKind.Point, Group = LightGroup.Always, Color = Rgb.Hex(0xffe2c4), Distance = 2.6, Decay = 2, Kick = true, Driver = LightDriver.Kick },
            // the atmosphere's (L7872–L7885)
            Spot("search", LightGroup.Search, 0xcfe6ff, 0, 22, 9, 0.5, 1.2, 13.5, 6.5, -11, 10, 2.2, -6, driver: LightDriver.Search),
            Point("cord", LightGroup.Cord, 0xffd29a, 0, 3.2, 0.42, 1.95, -0.1, LightDriver.Off),
            Point("cable", LightGroup.Cable, 0xb8d4ff, 0, 3.5, 8.0, 1.3, -0.7, LightDriver.Cable),
            Point("door", LightGroup.Door, 0x9fe0c0, 0, 4, 10.4, 0.6, -1.2, LightDriver.Door),
            Spot("crank", LightGroup.Crank, 0xffd6a8, 0, 3.2, 26, 0.55, 1.6, CrankX + 0.1, 1.75, 0.35, CrankX, 0.45, -0.2, driver: LightDriver.Crank),
            Point("back", LightGroup.Back, 0x8fb6c4, 45, 16, 10.5, 3.4, -10.5, decay: 1.4),
            Spot("pool", LightGroup.Pool, 0xc9d8d2, 9, 6, 32, 0.7, 2, 5.6, 3.1, 0.9, 5.9, 0.2, 0),
            // DL-03/04 (L2209–L2221)
            Spot("plateLamp", LightGroup.Dl02, 0xffe2c0, 0, 7, 50, 0.6, 2, Off2 + 16.3, 2.08, 0.05, Off2 + 16.4, 0, 0, shadow: 512, driver: LightDriver.PlateLamp),
            Point("roomFill", LightGroup.Dl02, 0xc8d6cc, 0, 4.5, Off2 + 13.1, 1.4, 0.7, LightDriver.RoomFill),
            Point("passage", LightGroup.Dl02, 0x9fe0c0, 0, 3, 12.4, 0.8, -1.25, LightDriver.Passage),
            Point("rack0", LightGroup.Dl02, 0xd2e6ee, 0, 9, Off2 + 20.0, 2.4, -2.8, LightDriver.RackNear, 1.6),
            Point("rack1", LightGroup.Dl02, 0xd2e6ee, 0, 9, Off2 + 24.0, 2.4, -2.8, LightDriver.RackNear, 1.6),
            Point("rack2", LightGroup.Dl02, 0xd2e6ee, 0, 9, Off2 + 22.0, 1.5, -0.4, LightDriver.RackFar, 1.6),
            Point("scanner", LightGroup.Scanner, 0xff4a2a, 0, 3.5, ScannerX, 1.4, -0.3, LightDriver.Scanner),
            // DL-06's floor, pit and gallery (L2608–L2617)
            Point("floor0", LightGroup.Dl03, 0xffd8a8, 5, 6, Off3 + 31.6, 2.25, -0.2, LightDriver.SortingFloor),
            Point("floor1", LightGroup.Dl03, 0xffd8a8, 5, 6, Off3 + 34.6, 2.25, -0.2, LightDriver.SortingFloor),
            Point("pit0", LightGroup.Dl03, 0xffcf98, 14, 9, Off3 + 39.6, 2.5, -2.2, LightDriver.SortingFloor),
            Point("pit1", LightGroup.Dl03, 0xffcf98, 18, 10, Off3 + 43.8, 2.8, -3.6, LightDriver.SortingFloor),
            Point("pit2", LightGroup.Dl03, 0xffcf98, 12, 9, Off3 + 48.0, 2.3, -2.6, LightDriver.SortingFloor),
            Point("gallery0", LightGroup.Dl03, 0xdde8f0, 4, 6, Off3 + 40.5, 3.8, -0.2, LightDriver.SortingFloor),
            Point("gallery1", LightGroup.Dl03, 0xdde8f0, 4, 6, Off3 + 44.0, 3.8, -0.2, LightDriver.SortingFloor),
            Spot("pitSky", LightGroup.Dl03, 0xbfd0d8, 120, 22, 26, 0.8, 1.2, Off3 + 42.5, 11, -2, Off3 + 41.5, -2, -3, driver: LightDriver.SortingSky),
            // the pass-6/10 lamps (L4052–L4087)
            Point("sh0", LightGroup.SortingHall, 0xffd6a6, 4.0, 5.5, 20.6, 2.6, 0.3),
            Point("sh1", LightGroup.SortingHall, 0xffc890, 5.0, 4.0, 24.7, 2.7, 0.1),
            Point("sh2", LightGroup.SortingHall, 0xd9e6ff, 1.2, 3.0, TubeX, 1.6, -0.3),
            Point("sh3", LightGroup.SortingHall, 0xffc890, 1.2, 2.0, 24.2, 1.05, -0.25),
            Point("sh4", LightGroup.SortingHall, 0xb8c8d4, 1.8, 2.6, 17.6, 1.3, 0.35),
            Point("sh5", LightGroup.SortingHall, 0xd9e6ff, 1.0, 3.0, 19.78, 2.2, 0.5),
            Point("sh6", LightGroup.SortingHall, 0xb8c8d4, 0.9, 2.2, 16.7, 1.1, -0.9),
            Point("bay", LightGroup.Bay, 0xcfe4ff, 3.2, 4.5, BayX, 2.4, -0.2),
            Point("voice0", LightGroup.Voice0, 0xffcc8c, 1.2, 2.5, 16.6, 1.3, -0.4),
            Point("voice1", LightGroup.Voice1, 0xffcc8c, 1.2, 2.5, 68.0, 1.2, -0.2),
            Point("secret0", LightGroup.Secret0, 0xffcf8a, 2.2, 3.5, 67.42, 1.86, -3.15),
            Point("spill0", LightGroup.Spill0, 0xffcf8a, 1.3, 2.6, 66.9, 0.75, -0.95),
            Point("cot", LightGroup.Cot, 0xffc890, 1.1, 2.6, 4.75, 1.15, -2.2),
            Spot("rationStrip", LightGroup.Ration, 0xdcebd2, 14, 6.5, 31, 0.7, 2, Off2 + 41.75, 1.98, 0.1, Off2 + 41.75, 0, -0.25, driver: LightDriver.RationStrip),
            Point("rationFill", LightGroup.Ration, 0xdcebd2, 2.2, 4, Off2 + 41.4, 1.5, 0.3, LightDriver.RationFill),
            Point("candles", LightGroup.Ration, 0xffa050, 1.2, 2.2, Off2 + 36.65, 0.6, -0.95, LightDriver.Candles),
            Point("ventDay", LightGroup.Ration, 0x9fb8d8, 3, 6, Off2 + 37.8, 2.7, -2.6),
            Point("kitchen", LightGroup.Ration, 0xcfd6c8, 1.6, 3.5, Off2 + 45.2, 1.9, -0.4),
            Point("shrine", LightGroup.Ration, 0xb4c4d0, 1.2, 3.5, Off2 + 37.5, 1.6, -1.2),
        };

        private static LightDef Point(string name, LightGroup g, int color, double intensity, double distance, double x, double y, double z,
            LightDriver driver = LightDriver.None, double decay = 2)
            => new LightDef
            {
                Name = name, Kind = LightKind.Point, Group = g, Color = Rgb.Hex(color), Intensity = intensity, Distance = distance, Decay = decay,
                Position = new Vec3(x, y, z), Driver = driver,
            };

        private static LightDef Spot(string name, LightGroup g, int color, double intensity, double distance, double angleDeg, double penumbra,
            double decay, double x, double y, double z, double tx, double ty, double tz, int shadow = 0, LightDriver driver = LightDriver.None)
            => new LightDef
            {
                Name = name, Kind = LightKind.Spot, Group = g, Color = Rgb.Hex(color), Intensity = intensity, Distance = distance, Decay = decay,
                Angle = angleDeg * Deg, Penumbra = penumbra, Position = new Vec3(x, y, z), Target = new Vec3(tx, ty, tz),
                Shadow = shadow > 0, ShadowMap = shadow > 0 ? shadow : 512, Driver = driver,
            };
    }

    /// <summary>
    /// The prologue's lights each frame (port_architecture §4.20–§4.22): which proxies the light region and zone show
    /// (<see cref="LightRegionTracker"/>, <see cref="LightRegions.Visible"/>), each driven proxy's level from the sim (the
    /// relay's lamps, the door, the racks' rows, the scanner, the Ration Hall's strip), and the pool's assignment around the
    /// camera (<see cref="LightPool.Assign"/>). Calm mode (Settings, "Reduce flicker and flashes") takes the prototype's
    /// steady curves: the relay's soft pulse (the sequencer's own, L1543), the cable's steady glow (L7941), the racks'
    /// eased rows (L2418) and the strip's steady 1 (L4928). Allocation-free per frame.
    /// </summary>
    public sealed class PrologueLighting
    {
        /// <summary>The kick light rides at (x + 0.5, y + 1.0, 1.3) (L7587).</summary>
        public const double KickDx = 0.5, KickDy = 1.0, KickZ = 1.3, KickLevel = 0.55, WorkLevel = 24;

        private readonly ChapterSim _sim;
        private readonly ChapterPresenter _presenter;
        private readonly ChapterSounds _sounds;
        private readonly LightPool _pool;
        private readonly LightRegionTracker _regions = new LightRegionTracker();
        private readonly PulseSequencer _relay;
        private readonly CrankActuator _crank;
        private readonly Dl06Scanner _scanner;
        // Chapter 1's driven lights (null elsewhere).
        private readonly CycleClock _nightLight;
        private readonly PairedBlindDrive _blinds14, _blinds14a;
        private readonly EscortTrolley _trolley;

        public PrologueLighting(ChapterSim sim, ChapterPresenter presenter, ChapterSounds sounds, LightPoolBudget budget = null, LightDef[] defs = null)
        {
            _sim = sim ?? throw new ArgumentNullException(nameof(sim));
            _presenter = presenter ?? new ChapterPresenter(sim);
            _sounds = sounds;
            _pool = new LightPool(defs ?? PrologueLights.Build(budget != null && budget.Touch), budget);
            sim.Graph.TryGet("dl01.relay", out _relay);
            sim.Graph.TryGet("dl01.crank", out _crank);
            sim.Graph.TryGet("dl06.scanner", out _scanner);
            sim.Graph.TryGet("dl14a.nightLight", out _nightLight);
            sim.Graph.TryGet("dl14.blinds", out _blinds14);
            sim.Graph.TryGet("dl14a.blinds", out _blinds14a);
            sim.Graph.TryGet("dl14b.trolley", out _trolley);
        }

        public LightPool Pool => _pool;
        public LightRegionTracker Regions => _regions;
        /// <summary>The searchlight's target now (three.js axes; it sweeps, L7944).</summary>
        public Vec3 SearchTarget { get; private set; }

        /// <summary>He was placed (begin, continue, respawn): the lists as <c>resetWorld</c> sets them (L8055).</summary>
        public void Place()
        {
            _regions.Place(_sim.Region, _sim.Checkpoints.Current.Past(Dl06Scene.ScannedCheckpoint) || _sim.Checkpoints.Current.Name == Dl06Scene.ScannedCheckpoint, _sim.X);
        }

        /// <summary>One frame, with the camera at lane x <paramref name="cameraX"/>.</summary>
        public void Update(double cameraX, bool calm)
        {
            var sim = _sim;
            double t = sim.Clock, x = sim.X;
            bool scanning = _scanner != null && _scanner.Phase != Dl06ScanPhase.Idle;
            _regions.Update(sim.Region, x, cameraX, _presenter.TransitLeg, scanning);
            int r = _regions.Region;
            LightZone zone = _regions.Zone;
            for (int i = 0; i < _pool.Count; i++)
            {
                LightDef d = _pool[i];
                _pool.SetVisible(i, LightRegions.Visible(d.Group, r, zone, false));
                _pool.SetLevel(i, Level(d, i, t, calm, r));
            }
            for (int i = 0; i < _pool.Count; i++)
            {
                if (_pool[i].Kick) _pool.SetPosition(i, new Vec3(x + KickDx, sim.Y + KickDy, KickZ));
                else if (_pool[i].Driver == LightDriver.AttBeam && _trolley != null)
                    _pool.SetPosition(i, new Vec3(_trolley.X + (_trolley.Dir > 0 ? 1 : -1) * AttendanceLights.BeamAhead, AttendanceLights.BeamY, AttendanceLights.BeamZ));
            }
            double a = t * 0.12;
            SearchTarget = new Vec3(10 + Math.Sin(a) * 5, 2.2 + Math.Sin(a * 1.7) * 1.2, -6);
            _pool.Assign(cameraX);
        }

        private double Level(LightDef d, int i, double t, bool calm, int lightRegion)
        {
            double door = _crank != null ? _crank.Position : 0;
            switch (d.Driver)
            {
                case LightDriver.Off: return 0;
                case LightDriver.Relay:
                {
                    double relay = 0;
                    if (_relay != null) for (int k = 0; k < _relay.LampCount; k++) relay += _relay.Value(k);
                    return 5.0 * Math.Min(1.4, relay);
                }
                case LightDriver.WorkBulb: return WorkLevel;
                case LightDriver.Kick: return KickLevel;
                case LightDriver.Cable:
                {
                    bool arcing = _sounds != null && t < _sounds.SparkUntil;
                    if (!arcing) return 0;
                    return calm ? 0.4 : 2.5 * (Math.Sin(t * 90) > 0 ? 1 : 0.3);
                }
                case LightDriver.Search: return 140;
                case LightDriver.Door: return 1.2 * door;
                case LightDriver.Crank: return 9 * (1 - 0.7 * door) * (0.9 + 0.1 * Math.Sin(t * 1.7));
                case LightDriver.PlateLamp: return 16 * PlateLamp();
                case LightDriver.RoomFill: return 3.2 * PlateLamp();
                case LightDriver.Passage: return 0.6 * Smooth.Step(door * 1.5);
                case LightDriver.RackNear: return 0.1 + 3.6 * RacksLit(t, calm);
                case LightDriver.RackFar: return 0.1 + 1.6 * RacksLit(t, calm);
                case LightDriver.Scanner:
                    if (_scanner == null) return 0;
                    if (_scanner.Phase == Dl06ScanPhase.Idle) return 1.6 * (0.5 + 0.5 * Math.Sin(t * 2.2));
                    return _scanner.Rejected ? 1.4 : 0.4;
                case LightDriver.SortingFloor: return d.Intensity * (lightRegion == 3 ? 1 : 0);
                case LightDriver.SortingSky: return d.Intensity * (lightRegion == 3 ? 1 : 0) * (0.85 + 0.15 * Math.Sin(t * 0.3));
                case LightDriver.RationStrip: return 14 * RationFlicker(t, calm);
                case LightDriver.RationFill: return 2.2 * RationFlicker(t, calm);
                case LightDriver.Candles: return 1.2 * (0.88 + 0.12 * Math.Sin(t * 7.3) * Math.Sin(t * 3.1));
                case LightDriver.AttSun: return d.Intensity * (0.06 + 0.94 * (_nightLight != null && _nightLight.TrackCount > 0 ? _nightLight.Value(0) : 1));
                case LightDriver.AttBlindW1: return d.Intensity * (1 - (_blinds14a != null ? _blinds14a.A : 0));
                case LightDriver.AttBlindW2: return d.Intensity * (1 - (_blinds14a != null ? _blinds14a.B : 0));
                case LightDriver.AttBeam: return d.Intensity;
                case LightDriver.AttJam: return _blinds14 != null && _blinds14.Slipping ? 1.2 * (calm ? 0.6 : 0.6 + 0.4 * Math.Sin(t * 31)) : 0;
                default: return d.Intensity;
            }
        }

        /// <summary>The plate lamp's switch: region 2, or he is in the passage (<c>r2</c>, L2405).</summary>
        private double PlateLamp() => _sim.Region == 2 || _presenter.TransitLeg >= 0 ? 1 : 0;

        private double RacksLit(double t, bool calm)
        {
            if (_sounds != null) return _sounds.RacksLit;
            return 0;
        }

        /// <summary>The Ration Hall's strip (L4927): a stutter when sin(0.7t) &gt; 0.93, else a faint shimmer; calm: steady 1.</summary>
        public static double RationFlicker(double t, bool calm)
        {
            if (calm) return 1;
            return Math.Sin(t * 0.7) > 0.93 ? 0.25 + 0.75 * (Math.Sin(t * 61) > 0 ? 1 : 0) : 0.92 + 0.08 * Math.Sin(t * 9.1);
        }
    }
}
