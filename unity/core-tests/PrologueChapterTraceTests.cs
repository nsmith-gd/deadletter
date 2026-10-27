using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.Json;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Hazards;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Bridges;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Docks;
using DeadLetter.Core.Mechanisms.Drives;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Mechanisms.Routes;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Push;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl02;
using DeadLetter.Core.Scenes.Dl03;
using DeadLetter.Core.Scenes.Dl06;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// The whole prologue as far as it is ported, DL-01 to DL-06, replayed through ONE <see cref="ChapterSim"/> over
    /// <see cref="ChapterDefs.Prologue"/>: the prototype's own run (the mechanical bot, seed 1,
    /// Traces/prologue_mech_seed1.jsonl.gz) from the first step of play at DL-01's <c>start</c> (#1768, the opening's last
    /// step) to the step the sorting floor becomes DL-07's (#14016), input for input, with no hand-over anywhere: one motor
    /// carries his speed, yaw and holds across every seam, one graph steps every scene's mechanisms all along, one
    /// checkpoint service holds the game.
    /// <para>The same signals and tolerance as the six scene replays (Dl01–Dl06TraceTests): 1e-6 on every continuous value,
    /// discrete ones on the same step; each step's act named by its own scene's mapping; each scene's mechanisms compared
    /// over the steps its replay compares them. Plus what only a chapter has: the scene that holds him
    /// (<see cref="ChapterSim.Current"/>) is the prototype's <c>sceneName</c> on every step, and
    /// <see cref="ChapterSim.SceneChanged"/> fires exactly on the steps it changes.</para>
    /// <para><b>The known motor differences</b> (#28), applied exactly as the scene replays apply them: <b>M5</b> (DL-03): Use
    /// lets go of the trolley with his speed zeroed, so the step it does (#5977) gives the motor back the speed it had;
    /// <b>M8</b> (DL-04): after letting go of the courier he steps back to the lane a step late, so z from #9534 to #9580 is
    /// the prototype's of the step before; the bay door's deliberate hold at the top (DL-04: compared to the prototype's
    /// law, as there); <b>M7, M9, M10</b> live in the scenes' rules and tuning, as in the scene replays. The scene
    /// replays' hand-over compensations (DL-05's yaw, DL-06's speed) are not needed: nothing is handed over.</para>
    /// </summary>
    public class PrologueChapterTraceTests
    {
        private const string TraceFile = Dl01TraceTests.TraceFile;
        private const double Tol = 1e-6, Dt = 1.0 / 60.0;

        internal sealed class Row
        {
            public TraceStep P;
            public double X, Y, Z, Vx, Yaw;
            public bool G, Exited;
            public string Act, Cp, Hold, Scene, Cues;
            public int Region;
            // DL-01
            public double Shutter, Lever, WeightY, Door1, Wheel, CartX, CartDrop, Relay;
            public bool Released, Lip;
            public string CartState;
            public int RelaySets;
            // DL-02
            public double Press, BoxX, BoxBase;
            public string BoxState, Letter;
            // DL-03
            public double TrolleyX, WeightX, WeightOff, Load, Needle, GateY, GateV;
            public string WeightState;
            // DL-04
            public double CourierX, Arm, BayDoor;
            public bool Want, PlateOn;
            public string CourierState;
            // DL-05
            public double DrumX, BodyX, W5, Needle5, Dip, Twitch, Hatch, Flag;
            public bool Served;
            public string DrumState, BodyState, Reading;
            // DL-06
            public string Scan, Route;
            public double ScanT, Stop, Points;
            public bool Belt;
            public int Riding;
            public string Carriers;
        }

        internal sealed class Replay
        {
            public readonly List<Row> Rows = new List<Row>();
            public ChapterSim Sim;
            public readonly List<(int step, string from, string to, ExitDir dir)> Changes = new List<(int, string, string, ExitDir)>();
            /// <summary>Steps where Use let go of the trolley and the motor was given back the speed it had (M5).</summary>
            public readonly List<int> ReleaseCompensated = new List<int>();
        }

        private static Replay _cached;
        private static readonly object Gate = new object();

        /// <summary>The window: the first step of play to the first step of DL-07.</summary>
        internal static (int from, int to) Window(Trace t)
            => (t.FirstIndex(p => p.Mode == "play"), t.FirstIndex(p => p.Scene != null && p.Scene.StartsWith("DL-07")));

        internal static Replay Run()
        {
            lock (Gate)
            {
                if (_cached != null) return _cached;
                var t = Trace.Load(TraceFile);
                var (from, to) = Window(t);
                var r = new Replay();
                var sim = new ChapterSim(ChapterDefs.Prologue());
                r.Sim = sim;
                int step = from - 1;
                sim.SceneChanged += (a, b, dir) => r.Changes.Add((step, a?.Id, b?.Id, dir));
                sim.Clock = t.Steps[from - 1].Clk;                                  // the quirk timers compare clock differences
                sim.Begin("start", fromOpening: true);
                r.Changes.Clear();                                                  // the placement at start

                var g = sim.Graph;
                var shutter = g.Get<Door>("dl01.shutter"); var latch = g.Get<Latch>("dl01.latch");
                var crank = g.Get<CrankActuator>("dl01.crank"); var cart = g.Get<TippingBridge>("dl01.cart");
                var relay = g.Get<PulseSequencer>("dl01.relay");
                var press = g.Get<PeriodicCrusher>("dl02.press"); var box = g.Get<CarriedItem>("dl02.box");
                var letter = g.Get<Dl02TubeLetter>("dl02.tubeLetter");
                var trolley = g.Get<Pushable>("dl03.trolley"); var weight = g.Get<Dl03Weight>("dl03.weight");
                var plate = g.Get<LoadPlate>("dl03.plate"); var gate = g.Get<FollowerActuator>("dl03.gate");
                var courier = g.Get<Pushable>("dl04.courier"); var cradle = g.Get<Cradle>("dl04.cradle");
                var bayPlate = g.Get<LoadPlate>("dl04.bayPlate"); var bayDoor = g.Get<PlateDoor>("dl04.bayDoor");
                var drum = g.Get<Pushable>("dl05.drum"); var body = g.Get<Pushable>("dl05.body");
                var scale = g.Get<WeighScale>("dl05.weighIn"); var hatch = g.Get<Door>("dl05.hatch"); var flag = g.Get<Door>("dl05.servedFlag");
                var scanner = g.Get<Dl06Scanner>("dl06.scanner"); var stopLever = g.Get<PointsLever>("dl06.stopLever");
                var points = g.Get<PointsLever>("dl06.points"); var line = g.Get<CarrierLine>("dl06.line");

                for (int k = from; k <= to; k++)
                {
                    step = t.Steps[k].I;
                    var given = t.Steps[k].Input;
                    var m = sim.Motor;
                    // M5, as Dl03TraceTests applies it: Use lets go of the trolley; the prototype keeps his push speed.
                    double vxBefore = m.Vx;
                    bool trolleyUse = given.UsePressed && m.Hold == HoldKind.Push && Base(m.Pushed) == trolley && sim.Act == null && !m.IsActing;
                    sim.Step(given);
                    if (trolleyUse && m.Hold == HoldKind.None)
                    {
                        SetMotorVx(m, vxBefore);
                        r.ReleaseCompensated.Add(step);
                    }

                    int sets = 0;
                    var log = g.Log;
                    for (int e = 0; e < log.Count; e++)
                        if (log[e].Id == "dl01.relay" && log[e].Kind == MechanismEventKind.Event && log[e].Code == (int)PulseEvent.LampLit && log[e].Index == 0) sets++;
                    var cues = new StringBuilder();
                    foreach (var c in sim.Cues) cues.Append(cues.Length > 0 ? "," : "").Append(c);
                    r.Rows.Add(new Row
                    {
                        P = t.Steps[k], X = sim.X, Y = sim.Y, Z = sim.Z, Vx = sim.Vx, Yaw = sim.Yaw, G = sim.Grounded, Exited = sim.Exited,
                        Act = ActOf(sim), Cp = sim.Checkpoints.Current.Name, Hold = HoldName(m), Scene = sim.Current?.Id, Region = sim.Region,
                        Cues = cues.ToString(),
                        Shutter = shutter.Position, Lever = latch.LeverDeg, WeightY = Door.ShutterCounterweightY(shutter.Elapsed),
                        Released = latch.State == LatchState.Released, Door1 = crank.Position, Wheel = crank.WheelDeg,
                        CartX = cart.X, CartDrop = cart.Drop, CartState = cart.State.ToString(), Lip = cart.State == TippingBridgeState.AtLip,
                        Relay = relay.Units, RelaySets = sets,
                        Press = press.Face, BoxX = box.X, BoxBase = box.BaseY, BoxState = box.State.ToString(), Letter = letter.State.ToString(),
                        TrolleyX = trolley.X, WeightState = WeightName(weight.State), WeightX = weight.FloorX, WeightOff = weight.Offset,
                        Load = plate.Load, Needle = plate.Needle, GateY = gate.Position, GateV = gate.Velocity,
                        CourierX = cradle.Position, CourierState = CourierName(cradle.State), Arm = cradle.ArmRad,
                        BayDoor = bayDoor.Open01, Want = bayDoor.Want, PlateOn = bayPlate.Engaged,
                        DrumX = drum.X, DrumState = StateName(drum, "set"), BodyX = body.X, BodyState = StateName(body, "plate"),
                        W5 = scale.Load, Reading = scale.Reading.ToString().ToLowerInvariant(), Needle5 = scale.Needle, Dip = scale.Dip,
                        Twitch = scale.TwitchOffset, Served = scale.Engaged, Hatch = hatch.Position, Flag = flag.Position,
                        Scan = scanner.Phase.ToString().ToLowerInvariant(), ScanT = scanner.T, Belt = stopLever.Engaged,
                        Route = points.Engaged ? "exit" : "chute", Stop = stopLever.LeverDeg, Points = points.LeverDeg,
                        Riding = line.Ride?.Seq ?? -1, Carriers = CarriersOf(line),
                    });
                }
                return _cached = r;
            }
        }

        // ---- The window -------------------------------------------------------------------------------------------------
        [Fact]
        public void Window_IsDl01sStart_ToDl07sFirstStep_AllSixScenes_NoHandOver()
        {
            var t = Trace.Load(TraceFile);
            var (from, to) = Window(t);
            Assert.Equal(1768, from);
            Assert.Equal(14016, to);
            var rows = Run().Rows;
            Assert.Equal(to - from + 1, rows.Count);
            for (int k = 1; k < rows.Count; k++) Assert.Equal(rows[k - 1].P.I + 1, rows[k].P.I);
            var scenes = new List<string>();
            foreach (var w in rows) { string s = w.P.Scene.Substring(0, 5); if (scenes.Count == 0 || scenes[scenes.Count - 1] != s) scenes.Add(s); }
            Assert.Equal(new[] { "DL-01", "DL-02", "DL-03", "DL-04", "DL-05", "DL-06", "DL-07" }, scenes);
        }

        // ---- (a) position -----------------------------------------------------------------------------------------------
        /// <summary>x, y, vx, yaw, grounded and the region at every step from the wake to the belt running to the exit.</summary>
        [Fact]
        public void X_Y_Vx_Yaw_Grounded_AndRegion_MatchEveryStep()
        {
            var bad = new List<string>();
            foreach (var w in Run().Rows)
            {
                Check(bad, w.P.I, "x", w.P.X, w.X);
                Check(bad, w.P.I, "y", w.P.Y, w.Y);
                Check(bad, w.P.I, "vx", w.P.Vx, w.Vx);
                Check(bad, w.P.I, "yaw", w.P.Yaw, w.Yaw);
                if (w.G != w.P.G) bad.Add($"#{w.P.I} grounded {w.P.G} vs {w.G}");
                if (w.Region != w.P.Region) bad.Add($"#{w.P.I} region {w.P.Region} vs {w.Region}");
            }
            Assert.True(bad.Count == 0, Report(bad));
        }

        /// <summary>z at every step but M8's (as Dl04TraceTests): from #9534 to #9580 it is the prototype's of the step before.</summary>
        [Fact]
        public void Z_MatchesEveryStep_ExceptM8_WhereItIsTheStepBefores()
        {
            var rows = Run().Rows;
            var bad = new List<string>();
            var lagged = new List<int>();
            for (int k = 0; k < rows.Count; k++)
            {
                var w = rows[k];
                if (Math.Abs(w.Z - -w.P.Z) <= Tol) continue;                                       // Unity z = −three z (§0.2)
                lagged.Add(w.P.I);
                Check(bad, w.P.I, "z (M8: the step before's)", -rows[k - 1].P.Z, w.Z);
            }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(47, lagged.Count);
            Assert.Equal(9534, lagged[0]);
            Assert.Equal(9580, lagged[lagged.Count - 1]);
        }

        /// <summary>M5 is compensated exactly where DL-03's replay compensates it, and nowhere else.</summary>
        [Fact]
        public void M5_IsCompensatedOnlyAtTheTrolleysRelease()
            => Assert.Equal(new[] { 5977 }, Run().ReleaseCompensated);

        // ---- (b) acts, holds, checkpoints ---------------------------------------------------------------------------------
        /// <summary>Every act and phase, named as its scene's replay names it, and what his hands hold.</summary>
        [Fact]
        public void Acts_And_Holds_MatchEveryStep()
        {
            var t = Trace.Load(TraceFile);
            var bad = new List<string>();
            var seen = new HashSet<string>();
            int room = t.FirstIndex(p => p.Cp == "room");
            foreach (var w in Run().Rows)
            {
                string want = ExpectedAct(t, w.P, room);
                if (want != null) seen.Add(want);
                if (want != w.Act) bad.Add($"#{w.P.I} {w.P.Scene.Substring(0, 5)} act {want ?? "-"} vs {w.Act ?? "-"}");
                if (w.P.Hold != w.Hold) bad.Add($"#{w.P.I} hold {w.P.Hold ?? "-"} vs {w.Hold ?? "-"}");
            }
            Assert.True(bad.Count == 0, Report(bad));
            foreach (var a in new[] { "quirk:CheckLabel", "dl01.latch:Flinch", "transit:3", "dl02.box:Clip", "dl03.weight:SetDownHigh", "quirk:Startle",
                         "realise:act", "bayTouch:act", "dl05.body:Hesitate", "quirk:Pat", "dl06.scanner:Check", "dl06.points:StepOut", "quirk:Proud" })
                Assert.Contains(a, seen);
        }

        /// <summary>Every checkpoint on the prototype's step: start to scanned, one service all along.</summary>
        [Fact]
        public void Checkpoints_FireOnThePrototypesSteps()
        {
            var rows = Run().Rows;
            var bad = new List<string>();
            var order = new List<string>();
            foreach (var w in rows)
            {
                if (w.P.Cp != w.Cp) bad.Add($"#{w.P.I} checkpoint {w.P.Cp} vs {w.Cp}");
                if (order.Count == 0 || order[order.Count - 1] != w.Cp) order.Add(w.Cp);
            }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(new[] { "start", "shutter", "hall", "door", "room", "weighroom", "solved", "bay", "ration", "hatch", "scanned" }, order);
        }

        // ---- (c) the scenes -------------------------------------------------------------------------------------------------
        /// <summary>
        /// The scene that holds him is the prototype's <c>sceneName</c> on every step (by region and x for DL-01 to DL-05, by
        /// what has happened for DL-06 → DL-07, which is past this chapter), and <see cref="ChapterSim.SceneChanged"/> fires
        /// once at each seam, on its step, going right.
        /// </summary>
        [Fact]
        public void CurrentScene_IsTheSceneName_EveryStep_AndSceneChangedFiresAtEachSeam()
        {
            var r = Run();
            var bad = new List<string>();
            var seams = new List<(int, string, string, ExitDir)>();
            string last = "DL-01";
            foreach (var w in r.Rows)
            {
                string proto = w.P.Scene.Substring(0, 5), core = w.Scene ?? "DL-07";          // past the chapter: DL-07's
                if (proto != core) bad.Add($"#{w.P.I} scene {proto} vs {core}");
                if (proto != last) { seams.Add((w.P.I, last, proto == "DL-07" ? null : proto, ExitDir.Right)); last = proto; }
            }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(seams, r.Changes);
            Assert.Equal(new[] { 3999, 5228, 6279, 9868, 12073, 14016 }, r.Changes.ConvertAll(c => c.step));
            Assert.True(r.Rows[r.Rows.Count - 1].Exited);
            for (int k = 0; k < r.Rows.Count - 1; k++) Assert.False(r.Rows[k].Exited);
        }

        /// <summary>The cues of the whole run, typed, on their steps (DL-04's two as its replay has them).</summary>
        [Fact]
        public void Cues_AreRaisedOnThePrototypesSteps()
        {
            var cues = new List<string>();
            foreach (var w in Run().Rows) if (w.Cues.Length > 0) cues.Add(w.P.I + ":" + w.Cues);
            Assert.Contains("1768:voice:dispatch_item", cues);
            Assert.Contains("6286:music:racks", cues);
            Assert.Contains("6347:moment:kin", cues);
            Assert.Contains(cues, c => c.EndsWith(":music:threshold", StringComparison.Ordinal));
            Assert.Contains(cues, c => c.EndsWith(":shot:scan", StringComparison.Ordinal));
        }

        // ---- (d) every scene's mechanisms, over the steps its replay compares them -------------------------------------------
        /// <summary>DL-01 (Dl01TraceTests): the shutter, the latch, the counterweight, the crank and its door, the cart, the relay, to <c>room</c>.</summary>
        [Fact]
        public void Dl01_Mechanisms_MatchEveryStep()
        {
            var bad = new List<string>();
            var rows = Run().Rows;
            int room = rows.FindIndex(w => w.P.Cp == "room"), relays = 0;
            for (int k = 0; k <= room; k++)
            {
                var w = rows[k]; var p = w.P;
                Check(bad, p.I, "shutterAngle", p.Sh, w.Shutter);
                Check(bad, p.I, "leverAngle", p.Lv, w.Lever);
                Check(bad, p.I, "weightY", p.Wy, w.WeightY);
                Check(bad, p.I, "doorOpen", p.Door, w.Door1);
                double d = Math.Abs(w.Wheel - p.Wh);
                if (Math.Min(d, Math.Abs(d - 60)) > Tol) bad.Add($"#{p.I} wheel {p.Wh} vs {w.Wheel}");   // modulo a stroke, as there
                Check(bad, p.I, "cart.x", p.Cx.Value, w.CartX);
                Check(bad, p.I, "cart.drop", p.Cd.Value, w.CartDrop);
                Check(bad, p.I, "frame (relay clock)", p.Fr, w.Relay);
                string cs = w.CartState == "AtLip" ? "free" : w.CartState.ToLowerInvariant();
                if (cs != p.Cs) bad.Add($"#{p.I} cart.state {p.Cs} vs {w.CartState}");
                if (w.Lip != p.Cl) bad.Add($"#{p.I} cart.lip {p.Cl} vs {w.Lip}");
                if (w.Released != p.Rel) bad.Add($"#{p.I} released {p.Rel} vs {w.Released}");
                bool protoSet = k == 0 ? p.Nr != 480 : p.Nr != rows[k - 1].P.Nr;
                if (protoSet != (w.RelaySets > 0)) bad.Add($"#{p.I} relay set {protoSet} vs {w.RelaySets}");
                relays += w.RelaySets;
            }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(7, relays);
        }

        /// <summary>DL-02 (Dl02TraceTests): the press's face, the box, the tube's letter, from <c>room</c> to the first step of DL-03.</summary>
        [Fact]
        public void Dl02_Mechanisms_MatchEveryStep()
        {
            var bad = new List<string>();
            var rows = Run().Rows;
            int room = rows.FindIndex(w => w.P.Cp == "room"), exit = rows.FindIndex(w => w.P.Scene.StartsWith("DL-03"));
            for (int k = room + 1; k <= exit; k++)
            {
                var w = rows[k]; var p = w.P;
                Check(bad, p.I, "press face", p.Pf.Value, w.Press);
                Check(bad, p.I, "box.x", p.Bx.Value, w.BoxX);
                Check(bad, p.I, "box.base", p.Bb.Value, w.BoxBase);
                string bs = w.BoxState == "Carried" ? "carried" : w.BoxState.ToLowerInvariant();
                if (bs != p.Bs) bad.Add($"#{p.I} box.state {p.Bs} vs {w.BoxState}");
                if (w.Letter.ToLowerInvariant() != p.Tl) bad.Add($"#{p.I} tube letter {p.Tl} vs {w.Letter}");
            }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.True(exit - room > 1000);
        }

        /// <summary>
        /// DL-03 (Dl03TraceTests): the trolley, the weight, the plate's load and needle, the gate, from his rest on DL-02's
        /// gantry (#5132) to the first step of DL-04, the four steps between the scene replay's two windows included.
        /// </summary>
        [Fact]
        public void Dl03_Mechanisms_MatchEveryStep()
        {
            var bad = new List<string>();
            var rows = Run().Rows;
            int from = rows.FindIndex(w => w.P.I == 5132), to = rows.FindIndex(w => w.P.Scene.StartsWith("DL-04"));
            for (int k = from; k <= to; k++)
            {
                var w = rows[k]; var p = w.P;
                Check(bad, p.I, "trolley.x", p.Tx, w.TrolleyX);
                Check(bad, p.I, "weight.x", p.Wx, w.WeightX);
                Check(bad, p.I, "weight.off", p.Wo, w.WeightOff);
                Check(bad, p.I, "load", p.Ld, w.Load);
                Check(bad, p.I, "needle", p.Nd, w.Needle);
                Check(bad, p.I, "gate.y", p.Gy, w.GateY);
                Check(bad, p.I, "gate.v", p.Gv, w.GateV);
                if (p.Ws != w.WeightState) bad.Add($"#{p.I} weight {p.Ws} vs {w.WeightState}");
            }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(6279, rows[to].P.I);
        }

        /// <summary>
        /// DL-04 (Dl04TraceTests): the courier, the cradle's arms and what the bay wants on every step DL-04 records them; the
        /// bay door against the prototype's law, with its deliberate hold at the top (never below the law, never more than
        /// a step above it).
        /// </summary>
        [Fact]
        public void Dl04_Mechanisms_MatchEveryStep()
        {
            var bad = new List<string>();
            int recorded = 0;
            double law = 0;
            foreach (var w in Run().Rows)
            {
                var p = w.P;
                if (p.Ks4 == null || p.I > 9868) continue;                                     // DL-04's fields, to the first step of DL-05
                recorded++;
                Check(bad, p.I, "courier.x", p.Kx4.Value, w.CourierX);
                Check(bad, p.I, "arms", p.Ka4.Value, w.Arm);
                if (p.Ks4 != w.CourierState) bad.Add($"#{p.I} courier {p.Ks4} vs {w.CourierState}");
                if ((p.Bw4.Value == 1) != w.Want) bad.Add($"#{p.I} want {p.Bw4} vs {w.Want}");
                if (w.CourierState != "seated" && w.PlateOn != w.Want) bad.Add($"#{p.I} plate {w.PlateOn} vs want {w.Want}");
                law = (w.Want ? 1 : 0) > law ? Math.Min(1, law + Dt / (w.CourierState == "seated" ? 2.2 : 1.1)) : Math.Max(0, law - Dt / 0.5);   // L4814
                Check(bad, p.I, "door (law)", p.Bd4.Value, law);
                double d = w.BayDoor - law;
                if (d < -1e-12 || d > Dt / 0.5 + 1e-12) bad.Add($"#{p.I} door {w.BayDoor:R} vs the law {law:R}");
            }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(9868 - 6279 + 1, recorded);
        }

        /// <summary>DL-05 (Dl05TraceTests): the drum, the body, the weigh-in, served, the hatch and the flag on every step DL-05 records them.</summary>
        [Fact]
        public void Dl05_Mechanisms_MatchEveryStep()
        {
            var bad = new List<string>();
            int compared = 0;
            foreach (var w in Run().Rows)
            {
                var p = w.P;
                if (p.D5x == null || p.I > 12073) continue;                                    // DL-05's fields, to the first step of DL-06
                compared++;
                Check(bad, p.I, "drum.x", p.D5x.Value, w.DrumX);
                Check(bad, p.I, "body.x", p.B5x.Value, w.BodyX);
                if (p.D5s != w.DrumState) bad.Add($"#{p.I} drum {p.D5s} vs {w.DrumState}");
                if (p.B5s != w.BodyState) bad.Add($"#{p.I} body {p.B5s} vs {w.BodyState}");
                Check(bad, p.I, "W", p.W5.Value, w.W5);
                if (p.W5r != w.Reading) bad.Add($"#{p.I} reading {p.W5r} vs {w.Reading}");
                Check(bad, p.I, "needle", p.N5.Value, w.Needle5);
                Check(bad, p.I, "dip", p.P5.Value, w.Dip);
                Check(bad, p.I, "twitch", p.T5.Value, w.Twitch);
                if (p.S5 != w.Served) bad.Add($"#{p.I} served {p.S5} vs {w.Served}");
                Check(bad, p.I, "hatch", p.H5.Value, w.Hatch);
                Check(bad, p.I, "flag", p.F5.Value, w.Flag);
            }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(12073 - 9868 + 1, compared);
        }

        /// <summary>DL-06 (Dl06TraceTests): the scanner, the belt, the route, both levers, what he rides and every carrier, on every step of DL-06.</summary>
        [Fact]
        public void Dl06_Mechanisms_MatchEveryStep()
        {
            var bad = new List<string>();
            int compared = 0, carriers = 0;
            foreach (var w in Run().Rows)
            {
                var p = w.P;
                if (p.Sp6 == null) continue;
                compared++;
                if (p.Sp6 != w.Scan) bad.Add($"#{p.I} scanner {p.Sp6} vs {w.Scan}");
                Check(bad, p.I, "scan.t", p.St6.Value, w.ScanT);
                if (p.Bl6 != w.Belt) bad.Add($"#{p.I} belt {p.Bl6} vs {w.Belt}");
                if (p.Rt6 != w.Route) bad.Add($"#{p.I} route {p.Rt6} vs {w.Route}");
                Check(bad, p.I, "stopLever", p.Sl6.Value, w.Stop);
                Check(bad, p.I, "pointsLever", p.Pl6.Value, w.Points);
                if ((int)(p.Rd6 ?? -1) != w.Riding) bad.Add($"#{p.I} riding {p.Rd6} vs {w.Riding}");
                CompareCarriers(bad, p.I, p.Cr6, w.Carriers, ref carriers);
            }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(14016 - 12073 + 1, compared);
            Assert.True(carriers > 1600, carriers.ToString());
        }

        // ---- Helpers --------------------------------------------------------------------------------------------------------
        /// <summary>
        /// The prototype's act as the scene replay that covers the step names it: DL-01's to <c>room</c> (the passage's
        /// last legs are in region 2, DL-02 by <c>sceneName</c>), then the step's own scene's (DL-07's first step as DL-06's).
        /// </summary>
        private static string ExpectedAct(Trace t, TraceStep p, int room)
        {
            if (p.I <= room) return Dl01TraceTests.ExpectedAct(p);
            switch (p.Scene.Substring(0, 5))
            {
                case "DL-01": return Dl01TraceTests.ExpectedAct(p);
                case "DL-02": return Dl02TraceTests.ExpectedAct(p);
                case "DL-03": return Dl03TraceTests.ExpectedAct(p);
                case "DL-04": return Dl04TraceTests.ExpectedAct(p);
                case "DL-05": return Dl05TraceTests.ExpectedAct(t, p);
                default: return Dl06TraceTests.ExpectedAct(t, p);
            }
        }

        private static string ActOf(ChapterSim sim)
        {
            string kind = SceneSim.KindOf(sim);
            return kind == null ? null : kind + ":" + (kind == "mantle" ? "" : SceneSim.PhaseOf(sim));
        }

        /// <summary>What his hands hold, as the trace records it (<c>game.hold</c>, with <c>pushKey</c> for a pushable).</summary>
        private static string HoldName(D17Motor m)
        {
            if (m.Hold == HoldKind.None) return null;
            if (m.Hold == HoldKind.Item) return m.Carried is Dl03Weight ? "weight" : "item";
            var b = Base(m.Pushed);
            string key = b.Id.Value.Substring(b.Id.Value.IndexOf('.') + 1);
            if (key == "trolley") return "trolley";                                                      // DL-03's: hold 'trolley'
            return "push:" + key + (m.Pushed is PushTwin ? "Alt" : "");
        }

        private static Mechanism Base(IPushable p) => p is PushTwin tw ? tw.Base : p as Mechanism;

        private static string WeightName(Dl03WeightState s) => s == Dl03WeightState.Floor ? "floor" : s == Dl03WeightState.Carried ? "carried" : "trolley";

        private static string CourierName(CradleState s)
            => s == CradleState.Free ? "free" : s == CradleState.Drawing ? "drawn" : s == CradleState.Closing ? "cradle" : "seated";

        private static string StateName(Pushable p, string docked)
            => p.State == PushableState.Docked ? docked : p.State == PushableState.Free ? "free" : p.State.ToString();

        private static readonly string[] CarrierStates = { "rise", "dock", "move", "unload", "tipload", "tip", "back", "sink" };

        /// <summary>The line's carriers in the recorder's shape (tools/sim/record_trace.mjs), as Dl06TraceTests writes them.</summary>
        private static string CarriersOf(CarrierLine line)
        {
            var sb = new StringBuilder("[");
            for (int i = 0; i < line.Count; i++)
            {
                var c = line.At(i);
                if (i > 0) sb.Append(',');
                sb.Append('[').Append(c.Seq).Append(",\"").Append(CarrierStates[(int)c.State]).Append("\",")
                  .Append(c.Route == CarrierRoute.None ? "null" : c.Route == CarrierRoute.Chute ? "\"chute\"" : "\"exit\"")
                  .Append(',').Append(R(c.Position)).Append(',').Append(R(c.Y)).Append(',').Append(R(c.S)).Append(',').Append(R(c.Wait))
                  .Append(',').Append(R(c.T)).Append(',').Append(c.Ridden ? 1 : 0).Append(',').Append(R(c.TipRad)).Append(",[");
                for (int k = 0; k < c.Parcels; k++)
                {
                    if (k > 0) sb.Append(',');
                    sb.Append('[').Append(R(c.ParcelSizeOf(k))).Append(',').Append(R(-c.ParcelZOf(k))).Append(',').Append(R(c.ParcelYawOf(k))).Append(']');
                }
                sb.Append("]]");
            }
            return sb.Append(']').ToString();
        }

        private static void CompareCarriers(List<string> bad, int i, string proto, string core, ref int seen)
        {
            using var a = JsonDocument.Parse(proto);
            using var b = JsonDocument.Parse(core);
            int n = a.RootElement.GetArrayLength();
            if (n != b.RootElement.GetArrayLength()) { bad.Add($"#{i} carriers {proto} vs {core}"); return; }
            for (int k = 0; k < n; k++)
            {
                seen++;
                var x = a.RootElement[k]; var y = b.RootElement[k];
                for (int f = 0; f < 11; f++)
                {
                    var u = x[f]; var v = y[f];
                    if (f == 10)
                    {
                        if (u.GetArrayLength() != v.GetArrayLength()) { bad.Add($"#{i} carrier {k} payload {u} vs {v}"); continue; }
                        for (int q = 0; q < u.GetArrayLength(); q++)
                            for (int e = 0; e < 3; e++) Check(bad, i, $"carrier {k} parcel {q}.{e}", u[q][e].GetDouble(), v[q][e].GetDouble());
                    }
                    else if (u.ValueKind == JsonValueKind.Number && f >= 3) Check(bad, i, $"carrier {k} field {f}", u.GetDouble(), v.GetDouble());
                    else if (u.ToString() != v.ToString()) bad.Add($"#{i} carrier {k} field {f} {u} vs {v}");
                }
            }
        }

        private static string R(double v) => v.ToString("R", System.Globalization.CultureInfo.InvariantCulture);

        /// <summary>M5's compensation: the motor keeps no setter for its speed (U-11), so the test sets it as the prototype keeps it.</summary>
        private static void SetMotorVx(D17Motor m, double vx) => typeof(D17Motor).GetProperty(nameof(D17Motor.Vx)).SetValue(m, vx);

        private static void Check(List<string> bad, int i, string what, double proto, double core)
        {
            if (!(Math.Abs(core - proto) <= Tol)) bad.Add($"#{i} {what} {proto:R} vs {core:R}");
        }

        private static string Report(List<string> bad)
        {
            var sb = new StringBuilder().Append(bad.Count).Append(" mismatches");
            for (int i = 0; i < bad.Count && i < 16; i++) sb.Append("\n  ").Append(bad[i]);
            return sb.ToString();
        }

        /// <summary>Writes the replay side by side as TSV when PROLOGUE_TRACE_DUMP names a file.</summary>
        [Fact]
        public void Dump()
        {
            var path = Environment.GetEnvironmentVariable("PROLOGUE_TRACE_DUMP");
            if (string.IsNullOrEmpty(path)) return;
            var t = Trace.Load(TraceFile);
            var sb = new StringBuilder("i\tsc\tcsc\tpx\tcx\tpy\tcy\tpz\tcz\tpvx\tcvx\tpyaw\tcyaw\tpg\tcg\tpact\tcact\tph\tch\tpcp\tccp\tcues\tin\n");
            foreach (var w in Run().Rows)
            {
                var p = w.P;
                sb.Append(p.I).Append('\t').Append(p.Scene.Substring(0, 5)).Append('\t').Append(w.Scene)
                  .Append('\t').Append(p.X).Append('\t').Append(R(w.X)).Append('\t').Append(p.Y).Append('\t').Append(R(w.Y))
                  .Append('\t').Append(-p.Z).Append('\t').Append(R(w.Z)).Append('\t').Append(p.Vx).Append('\t').Append(R(w.Vx))
                  .Append('\t').Append(p.Yaw).Append('\t').Append(R(w.Yaw)).Append('\t').Append(p.G ? 1 : 0).Append('\t').Append(w.G ? 1 : 0)
                  .Append('\t').Append(ExpectedAct(t, p, t.FirstIndex(q => q.Cp == "room"))).Append('\t').Append(w.Act).Append('\t').Append(p.Hold).Append('\t').Append(w.Hold)
                  .Append('\t').Append(p.Cp).Append('\t').Append(w.Cp).Append('\t').Append(w.Cues)
                  .Append('\t').Append(p.L ? "L" : "").Append(p.R ? "R" : "").Append(p.JP ? "J" : "").Append(p.UP ? "U" : "").Append(p.SH ? "S" : "").Append('\n');
            }
            File.WriteAllText(path, sb.ToString());
        }
    }
}
