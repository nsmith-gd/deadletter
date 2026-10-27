using System;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Plates
{
    public enum LoadPlateState { Empty, Loaded }

    public enum LoadPlateEvent
    {
        /// <summary>The load rose through <see cref="LoadPlateParams.PressAt"/> (<c>Sound.plate</c>, DL-03 L2373).</summary>
        Press,
    }

    public sealed class LoadPlateParams
    {
        public PlateSensorParams Sensor = new PlateSensorParams();
        /// <summary>Emit <see cref="LoadPlateEvent.Press"/> when the load rises through this (L2373).</summary>
        public double PressAt = 0.05;
        /// <summary><see cref="LoadPlate.Engaged"/> (and state Loaded) while the load is at least this.</summary>
        public double EngageAt = 0.05;
        /// <summary>DL-03: the plate passes when it holds this much without him (<c>PASS_LOAD</c>, L324).</summary>
        public double PassLoad = double.PositiveInfinity;
        /// <summary>Needle = min(NeedleMax, load · NeedleGain), eased at NeedleRate /s (<c>needle += (want − needle)·min(1, dt·rate)</c>); 0 = no needle.</summary>
        public double NeedleRate, NeedleGain = 1, NeedleMax = 1;
        /// <summary>A second, slower dial on the same reading (DL-10's balance gauge, L4645); 0 = none.</summary>
        public double GaugeRate;
        /// <summary><see cref="LoadPlate.EngagedFor"/> after a reset that finds it loaded (DL-10 <c>loadedAt: −100</c>, L4101).</summary>
        public double ResetEngagedFor = 100;

        /// <summary>DL-01 curio: the needle swings −95° while he stands within 0.22 of x 1.45, at dt·3 (L3885, L4767–L4769).</summary>
        public static LoadPlateParams Dl01Scale() => new LoadPlateParams
        {
            Sensor = new PlateSensorParams { PlayerX0 = 1.45 - 0.22, PlayerX1 = 1.45 + 0.22, PlayerMaxY = 0.1, PlayerShare = 1 },   // SCALE1_X
            NeedleRate = 3,
        };

        /// <summary>
        /// DL-03: D-17 1.0, trolley 0.3, weight 0.42 (on the floor, on the trolley or carried) on the plate 28.8–29.55
        /// (± 0.02); needle at dt·5 (L323–L324, L2229–L2238, L2372–L2374). He counts below y 0.25, or standing below 0.45
        /// (<c>game.y &lt; 0.45 &amp;&amp; (game.grounded || game.y &lt; 0.25)</c>, L2232): on the weight on the trolley (y 0.38).
        /// </summary>
        public static LoadPlateParams Dl03Plate() => new LoadPlateParams
        {
            Sensor = new PlateSensorParams
            {
                X0 = 13 + 15.8, X1 = 13 + 16.55, Margin = 0.02,                      // PLATE, L323; onPlate L2230
                PlayerX0 = 13 + 15.8 - 0.02, PlayerX1 = 13 + 16.55 + 0.02, PlayerMaxY = 0.25, PlayerShare = 1.0,   // LOAD.d17
                PlayerGroundedMaxY = 0.45,                                                                        // L2232
                Terms = new[] { PlateTerm.Inside("dl03.trolley", 0.3), PlateTerm.Inside("dl03.weight", 0.42) },  // LOAD, L324
            },
            PassLoad = 0.68, NeedleRate = 5,                                         // PASS_LOAD L324; L2374
        };

        /// <summary>DL-04: D-17 on the bay plate 44.0–45.0 below y 0.1 (RK.plate, L3890, L4786).</summary>
        public static LoadPlateParams Dl04BayPlate() => new LoadPlateParams
        {
            Sensor = new PlateSensorParams { PlayerX0 = 44.0, PlayerX1 = 45.0, PlayerMaxY = 0.1, PlayerShare = 1 },
        };

        /// <summary>
        /// DL-08: the goods pan 83.5–84.9: 1.05 × the share of the trolley rolled onto it + 0.5 for him (within 0.04,
        /// below DECK + 0.6) (L3007–L3012, L3021–L3030). The platform (Lifts) subtracts 0.5 when he stands on it.
        /// </summary>
        public static LoadPlateParams Dl08Pan() => new LoadPlateParams
        {
            Sensor = new PlateSensorParams
            {
                X0 = 33 + 50.5, X1 = 33 + 51.9,                                      // PAN
                PlayerX0 = 33 + 50.5 - 0.04, PlayerX1 = 33 + 51.9 + 0.04, PlayerMaxY = 1.6 + 0.6, PlayerShare = 0.5,   // DECK 1.6, LOAD4.d17
                Terms = new[] { PlateTerm.Ramp("dl08.trolley", 33 + 50.5 - 0.36 + 0.1, 2 * 0.36 - 0.2, 1.05) },        // T4_HALF 0.36, LOAD4.trolley
            },
        };

        /// <summary>DL-09: the counterweight tray: one per plate in it; the balance gauge reads plates / 2 at dt·3 (L5016, L5054–L5055).</summary>
        public static LoadPlateParams Dl09Tray() => new LoadPlateParams
        {
            Sensor = new PlateSensorParams { Terms = new[] { PlateTerm.Placed("dl09.plate0", 1), PlateTerm.Placed("dl09.plate1", 1) } },
            NeedleRate = 3, NeedleGain = 0.5, EngageAt = 2,                         // the cage holds only with both (L5025)
        };

        /// <summary>DL-10: the car's floor plate feels the suitcase set into the car; needle at dt·2.5, gauge at dt·1.5 (L4560, L4641, L4645).</summary>
        public static LoadPlateParams Dl10CarPlate() => new LoadPlateParams
        {
            Sensor = new PlateSensorParams { Terms = new[] { PlateTerm.Placed("dl10.case", 1) } },
            NeedleRate = 2.5, GaugeRate = 1.5,
        };

        /// <summary>DL-16a: the dumbwaiter's load, tin1 1 + tin2 1 in the car, judged against <c>need: 0</c> (L5904, L5935–L5938, L6171–L6174).</summary>
        public static LoadPlateParams Dl16aCarLoad() => new LoadPlateParams
        {
            Sensor = new PlateSensorParams { Terms = new[] { PlateTerm.Placed("dl16a.tin1", 1), PlateTerm.Placed("dl16a.tin2", 1) } },
        };

        /// <summary>DL-16a <c>ATT3.need</c> (L5904; §9 #6: the redesign set it to 0).</summary>
        public const double Dl16aNeed = 0;
    }

    /// <summary>
    /// A plate or scale that sums the weighted shares of what is on it (§4.13a): D-17 inside an interval, bodies by
    /// <see cref="PlateTerm"/>. One class for the DL-01 curio scale, the DL-03 plate, the DL-04 bay plate, the DL-08
    /// pan, the DL-09 tray, the DL-10 car plate and the DL-16a car load. Signals: <see cref="Load"/> (load shares;
    /// read by <c>FollowerActuator</c>, lifts), <see cref="Engaged"/> = load ≥ EngageAt (read by doors), and
    /// <see cref="Position"/> = the needle (0..NeedleMax).
    /// </summary>
    public sealed class LoadPlate : Mechanism, ILoad, IEngageable, IPositionSource
    {
        private readonly LoadPlateParams _p;
        private readonly PlateSensor _sensor;
        private double _engagedFor = -1;

        public LoadPlate(MechanismId id, LoadPlateParams p) : base(id)
        {
            _p = p ?? throw new ArgumentNullException(nameof(p));
            _sensor = new PlateSensor(p.Sensor);
        }

        public LoadPlateState State => (LoadPlateState)StateCode;
        /// <summary>Load shares on it this step.</summary>
        public double Load { get; private set; }
        /// <summary>Load shares without D-17 (and what he carries): DL-03's <c>plateLoad(false)</c>.</summary>
        public double LoadWithoutPlayer { get; private set; }
        public bool PlayerOn { get; private set; }
        public bool Engaged => State == LoadPlateState.Loaded;
        /// <summary>Seconds it has been loaded (0 on the step it was), −1 while empty: DL-10's sill lamps (L4647).</summary>
        public double EngagedFor => _engagedFor;
        /// <summary>The dial, 0..NeedleMax (DL-01 × −95°, DL-03 gate needle, DL-09 × 48°, DL-10 × −2.6 rad).</summary>
        public double Needle { get; private set; }
        /// <summary>The second dial (DL-10's balance gauge × 48°).</summary>
        public double Gauge { get; private set; }
        public double Position => Needle;
        /// <summary>DL-03: holds the pass load without him (L2396).</summary>
        public bool Passing => LoadWithoutPlayer >= _p.PassLoad;

        /// <summary>DL-03's solved test: passing, and the gate has wound up to that height (L2396).</summary>
        public bool SolvedWith(double gateY, double openHeight) => Passing && gateY >= _p.PassLoad * openHeight - 0.01;

        /// <summary>DL-16a's bell: +1 over the need (buzz), −1 under (it shoots up), 0 equal (it rises) (L6171–L6174).</summary>
        public int Judge(double need) => Load > need ? 1 : Load < need ? -1 : 0;

        /// <summary>DL-10's sill lamp <paramref name="i"/> (0..2) is lit 0.25 + 0.3·i s after loading (L4647).</summary>
        public bool SillLampLit(int i) => _engagedFor > 0.25 + 0.3 * i;

        public override void Link(MechanismLinker link) => _sensor.Link(link);

        /// <summary>Derived from its bodies (already reset), without him: <c>game.load = weight + trolley</c>, needle = load (L8027–L8028).</summary>
        public override void Reset(in Checkpoint cp)
        {
            PlayerOn = false;
            Load = LoadWithoutPlayer = _sensor.Load(false);
            Needle = Gauge = NeedleTarget();
            bool on = Load >= _p.EngageAt;
            _engagedFor = on ? _p.ResetEngagedFor : -1;
            Init((int)(on ? LoadPlateState.Loaded : LoadPlateState.Empty));
        }

        public override void Step(in StepContext ctx)
        {
            bool on = _sensor.PlayerOn(ctx.Player);
            double before = Load;
            PlayerOn = on;
            Load = _sensor.Load(on);
            LoadWithoutPlayer = on ? _sensor.Load(false) : Load;
            if (before < _p.PressAt && Load >= _p.PressAt) Emit(ctx, (int)LoadPlateEvent.Press);   // L2373

            double want = NeedleTarget();
            if (_p.NeedleRate > 0) Needle += (want - Needle) * (1 - Smooth.DecayFactor(_p.NeedleRate, ctx.Dt));   // L2374 (§9 #10)
            else Needle = want;
            if (_p.GaugeRate > 0) Gauge += (want - Gauge) * (1 - Smooth.DecayFactor(_p.GaugeRate, ctx.Dt));       // L4645
            else Gauge = want;

            bool engaged = Load >= _p.EngageAt;
            _engagedFor = engaged ? (_engagedFor < 0 ? 0 : _engagedFor + ctx.Dt) : -1;
            Enter(ctx, (int)(engaged ? LoadPlateState.Loaded : LoadPlateState.Empty));
        }

        private double NeedleTarget() => Math.Min(_p.NeedleMax, Load * _p.NeedleGain);

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("load", Load);
            w.WriteDouble("loadOff", LoadWithoutPlayer);
            w.WriteBool("on", PlayerOn);
            w.WriteDouble("needle", Needle);
            w.WriteDouble("gauge", Gauge);
            w.WriteDouble("for", _engagedFor);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            Load = r.ReadDouble("load");
            LoadWithoutPlayer = r.ReadDouble("loadOff");
            PlayerOn = r.ReadBool("on");
            Needle = r.ReadDouble("needle");
            Gauge = r.ReadDouble("gauge");
            _engagedFor = r.ReadDouble("for");
        }
    }
}
