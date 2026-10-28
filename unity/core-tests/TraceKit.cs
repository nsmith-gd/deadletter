using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Text.Json;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Scenes;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// One 60 Hz step of a golden trace recorded from the prototype by <c>tools/sim/record_trace.mjs</c> (format in
    /// tools/sim/README.md): the input the game consumed that step and the state after it. Lines are deltas; the loader
    /// carries unchanged fields forward. Three.js z is kept as recorded (− into the set).
    /// </summary>
    internal sealed partial class TraceStep
    {
        public int I;
        // Input (index.html L1215): left/right keys, axis, edges and holds, the walk modifier.
        public bool L, R, JP, JH, UP, UH, SH;
        public double AX;
        // D-17 after the step.
        public double Clk, X, Y, Z, Vx, Vy, Yaw;
        public int F, Tr, Region;
        public bool G, C, Mt;
        public string Mode, Act, Hold, Cp, Clip, Scene;
        public double Fr;
        // DL-01: game.released, shutterAngle, leverAngle, weightY, doorOpen, wheelAngle, the cart, nextRelay.
        public bool Rel;
        public double Sh, Lv, Wy, Door, Wh;
        public double? Cx, Cd;
        public string Cs;
        public bool Cl;
        public double Nr;
        // DL-02 (only while in DL-02, else carried forward): the press's face, the box (x, base, state), the tube's letter,
        // deaths so far and a pending respawn (game.respawnAt, 0 = none).
        public double? Pf, Bx, Bb;
        public string Bs, Tl;
        public int Dn;
        public double Ra;
        // DL-03: the trolley's x, the weight's state, x (game.weight.x) and deck offset, game.load, the needle, the gate's y and fall speed.
        public double Tx, Wx, Wo, Ld, Nd, Gy, Gv;
        public string Ws;
        // DL-04 (only while in DL-04, else carried forward; null before): the fallen courier's x and state, the cradle's
        // arms (rotation.x), the bay door (0..1) and what the bay wants (him on the plate, or the courier seated).
        public double? Kx4, Ka4, Bd4, Bw4;
        public string Ks4;
        // DL-05 (only while in DL-05 and on the step he leaves it; null before): the drum and the body (x, state), the
        // weigh-in's W, reading, needle and plate dip, the hatch's twitch lift, the hatch's height, the flag, served.
        public double? D5x, B5x, W5, N5, P5, T5, H5, F5;
        public string D5s, B5s, W5r;
        public bool? S5;
        // DL-06 (only while in DL-06 and on the step he leaves it; null before): the scanner's phase and clock, the belt
        // running, the route, the stop and points levers' angles, the carrier he rides (its id) and the carriers (raw JSON:
        // [id, state, route, x, y, s, wait, t, ridden, tip, [[size, z, yaw], ...]] each, tools/sim/record_trace.mjs).
        public string Sp6, Rt6, Cr6;
        public double? St6, Sl6, Pl6, Rd6;
        public bool? Bl6;

        public TraceStep Clone() => (TraceStep)MemberwiseClone();

        /// <summary>The input as Core takes it: <c>move = input.axis || (right − left)</c> (L1932); Shift is the walk modifier.</summary>
        public MotorInput Input => new MotorInput
        {
            Move = AX != 0 ? AX : (R ? 1 : 0) - (L ? 1 : 0),
            MoveIsAnalog = AX != 0,
            JumpPressed = JP, JumpHeld = JH, UsePressed = UP, UseHeld = UH, RunModifierHeld = SH,
        };

        public override string ToString() => $"#{I} x={X:R} y={Y:R} z={Z:R} vx={Vx:R} vy={Vy:R} g={G} act={Act} hold={Hold} cp={Cp} clip={Clip}";
    }

    internal sealed class Trace
    {
        public JsonElement Header;
        public readonly List<TraceStep> Steps = new List<TraceStep>();
        public string EndError;
        public long CompressedBytes;

        private static readonly Dictionary<string, Trace> Cache = new Dictionary<string, Trace>();

        /// <summary>Loads (once per run) a trace from <c>unity/core-tests/Traces/</c>.</summary>
        public static Trace Load(string name)
        {
            lock (Cache)
            {
                if (Cache.TryGetValue(name, out var t)) return t;
                t = Read(Path.Combine(Dir(), name));
                Cache[name] = t;
                return t;
            }
        }

        public static string Dir()
        {
            for (var d = new DirectoryInfo(AppContext.BaseDirectory); d != null; d = d.Parent)
            {
                var p = Path.Combine(d.FullName, "Traces");
                if (Directory.Exists(p) && File.Exists(Path.Combine(d.FullName, "DeadLetter.Core.Tests.csproj"))) return p;
            }
            throw new DirectoryNotFoundException("unity/core-tests/Traces not found above " + AppContext.BaseDirectory);
        }

        private static Trace Read(string path)
        {
            var t = new Trace { CompressedBytes = new FileInfo(path).Length };
            using var gz = new GZipStream(File.OpenRead(path), CompressionMode.Decompress);
            using var rd = new StreamReader(gz);
            string line = rd.ReadLine();
            using (var h = JsonDocument.Parse(line)) t.Header = h.RootElement.Clone();
            var cur = new TraceStep();
            while ((line = rd.ReadLine()) != null)
            {
                using var doc = JsonDocument.Parse(line);
                var e = doc.RootElement;
                if (e.TryGetProperty("end", out _))
                {
                    if (e.TryGetProperty("error", out var err) && err.ValueKind == JsonValueKind.String) t.EndError = err.GetString();
                    break;
                }
                cur = cur.Clone();
                foreach (var p in e.EnumerateObject()) Apply(cur, p.Name, p.Value);
                t.Steps.Add(cur);
            }
            return t;
        }

        private static void Apply(TraceStep s, string k, JsonElement v)
        {
            switch (k)
            {
                case "i": s.I = v.GetInt32(); break;
                case "L": s.L = B(v); break;
                case "R": s.R = B(v); break;
                case "JP": s.JP = B(v); break;
                case "JH": s.JH = B(v); break;
                case "UP": s.UP = B(v); break;
                case "UH": s.UH = B(v); break;
                case "SH": s.SH = B(v); break;
                case "AX": s.AX = v.GetDouble(); break;
                case "clk": s.Clk = v.GetDouble(); break;
                case "x": s.X = v.GetDouble(); break;
                case "y": s.Y = v.GetDouble(); break;
                case "z": s.Z = v.GetDouble(); break;
                case "vx": s.Vx = v.GetDouble(); break;
                case "vy": s.Vy = v.GetDouble(); break;
                case "yaw": s.Yaw = v.GetDouble(); break;
                case "f": s.F = v.GetInt32(); break;
                case "g": s.G = B(v); break;
                case "c": s.C = B(v); break;
                case "m": s.Mode = S(v); break;
                case "a": s.Act = S(v); break;
                case "h": s.Hold = S(v); break;
                case "mt": s.Mt = B(v); break;
                case "tr": s.Tr = v.GetInt32(); break;
                case "r": s.Region = v.GetInt32(); break;
                case "cp": s.Cp = S(v); break;
                case "fr": s.Fr = v.GetDouble(); break;
                case "clip": s.Clip = S(v); break;
                case "sc": s.Scene = S(v); break;
                case "rel": s.Rel = B(v); break;
                case "sh": s.Sh = v.GetDouble(); break;
                case "lv": s.Lv = v.GetDouble(); break;
                case "wy": s.Wy = v.GetDouble(); break;
                case "door": s.Door = v.GetDouble(); break;
                case "wh": s.Wh = v.GetDouble(); break;
                case "cx": s.Cx = N(v); break;
                case "cs": s.Cs = S(v); break;
                case "cd": s.Cd = N(v); break;
                case "cl": s.Cl = v.ValueKind == JsonValueKind.Number && v.GetInt32() != 0; break;
                case "nr": s.Nr = v.GetDouble(); break;
                case "pf": s.Pf = N(v); break;
                case "bx": s.Bx = N(v); break;
                case "bb": s.Bb = N(v); break;
                case "bs": s.Bs = S(v); break;
                case "tl": s.Tl = S(v); break;
                case "dn": s.Dn = v.GetInt32(); break;
                case "ra": s.Ra = v.GetDouble(); break;
                case "tx": s.Tx = v.GetDouble(); break;
                case "ws": s.Ws = S(v); break;
                case "wx": s.Wx = v.GetDouble(); break;
                case "wo": s.Wo = v.GetDouble(); break;
                case "ld": s.Ld = v.GetDouble(); break;
                case "nd": s.Nd = v.GetDouble(); break;
                case "gy": s.Gy = v.GetDouble(); break;
                case "gv": s.Gv = v.GetDouble(); break;
                case "kx4": s.Kx4 = N(v); break;
                case "ks4": s.Ks4 = S(v); break;
                case "ka4": s.Ka4 = N(v); break;
                case "bd4": s.Bd4 = N(v); break;
                case "bw4": s.Bw4 = N(v); break;
                case "d5x": s.D5x = N(v); break;
                case "d5s": s.D5s = S(v); break;
                case "b5x": s.B5x = N(v); break;
                case "b5s": s.B5s = S(v); break;
                case "w5": s.W5 = N(v); break;
                case "w5r": s.W5r = S(v); break;
                case "n5": s.N5 = N(v); break;
                case "p5": s.P5 = N(v); break;
                case "t5": s.T5 = N(v); break;
                case "h5": s.H5 = N(v); break;
                case "f5": s.F5 = N(v); break;
                case "s5": s.S5 = B(v); break;
                case "sp6": s.Sp6 = S(v); break;
                case "st6": s.St6 = N(v); break;
                case "bl6": s.Bl6 = B(v); break;
                case "rt6": s.Rt6 = S(v); break;
                case "sl6": s.Sl6 = N(v); break;
                case "pl6": s.Pl6 = N(v); break;
                case "rd6": s.Rd6 = N(v); break;
                case "cr6": s.Cr6 = S(v); break;
                default: if (!s.ApplyChapter1(k, v)) throw new InvalidDataException("Unknown trace field '" + k + "'."); break;
            }
        }

        internal static bool B(JsonElement v) => v.ValueKind == JsonValueKind.Number ? v.GetInt32() != 0 : v.ValueKind == JsonValueKind.True;
        internal static string S(JsonElement v) => v.ValueKind == JsonValueKind.String ? v.GetString() : null;
        internal static double? N(JsonElement v) => v.ValueKind == JsonValueKind.Number ? v.GetDouble() : (double?)null;

        /// <summary>Index of the first step in <paramref name="mode"/> (e.g. the first step of play).</summary>
        public int FirstIndex(Func<TraceStep, bool> pred)
        {
            for (int i = 0; i < Steps.Count; i++) if (pred(Steps[i])) return i;
            return -1;
        }
    }

    /// <summary>
    /// Replays a window of a trace through a scene's <see cref="SceneSim"/>: the scene begins at a checkpoint with the
    /// game clock of the step before the window (the quirk timers compare clock differences, so it must be the same
    /// double), then each record's input is stepped and <c>onStep</c> compares. A later scene's parity test is this
    /// call with its own definition, checkpoint, window and comparisons (see Dl01TraceTests).
    /// </summary>
    internal static class TraceReplay
    {
        /// <param name="from">Index of the window's first step (the first step of play, or the step after a checkpoint).</param>
        /// <param name="to">Index of its last step, inclusive.</param>
        /// <param name="input">Optional: the input to give Core at step k (a documented compensation); default the record's own.</param>
        /// <param name="handover">
        /// Optional: start from the record of the step before the window instead of a checkpoint's spot, for a scene he
        /// walks into (<see cref="SceneSim.Handover"/> at <paramref name="checkpoint"/>), in that step's state: x, y, z, vx,
        /// vy, yaw, facing, grounded and crouched (<see cref="D17Motor.SetState"/>), so a D-17 still turning or running in
        /// is handed over as he is.
        /// </param>
        public static SceneSim Run(Trace t, SceneDef def, string checkpoint, bool fromOpening, int from, int to,
            Action<TraceStep, SceneSim> onStep, Func<int, SceneSim, MotorInput> input = null, bool handover = false)
        {
            var sim = new SceneSim(def);
            sim.Clock = t.Steps[from - 1].Clk;
            var before = t.Steps[from - 1];
            if (handover)
            {
                sim.Handover(checkpoint, before.X, before.Y, before.F);
                sim.Motor.SetState(StateOf(t, from - 1, sim.Config));
            }
            else sim.Begin(checkpoint, fromOpening);
            for (int k = from; k <= to; k++)
            {
                sim.Step(input != null ? input(k, sim) : t.Steps[k].Input);
                onStep(t.Steps[k], sim);
            }
            return sim;
        }

        /// <summary>
        /// The motor state record <paramref name="i"/> shows (Unity z = −three z, §0.2; the motor's vy is the prototype's
        /// less the parity offset) and its clip (at its start: the records do not carry the clip's time; the step sets its
        /// speed before the mixer advances). In the air, PeakY is the prototype's <c>game.peakY</c>: the highest y since
        /// he last stood (the take-off record's and every airborne one's, L2030, L2034, L2036), not this record's y.
        /// </summary>
        public static MotorSnapshot StateOf(Trace t, int i, MotorConfig c)
        {
            var p = t.Steps[i];
            return new MotorSnapshot
            {
                X = p.X, Y = p.Y, Z = -p.Z, Vx = p.Vx, Vy = p.G ? 0 : p.Vy - c.ParityVelocityOffset,
                Facing = p.F, Yaw = p.Yaw, Grounded = p.G, Crouched = p.C, PeakY = PeakYOf(t, i),
                Clip = p.Clip, ClipTime = 0, ClipTimeScale = 1,
            };
        }

        /// <summary><c>game.peakY</c> at record <paramref name="i"/>: his y on the ground, else the top of the fall so far.</summary>
        public static double PeakYOf(Trace t, int i)
        {
            double peak = t.Steps[i].Y;
            for (int j = i; j >= 0; j--)
            {
                var s = t.Steps[j];
                peak = Math.Max(peak, s.Y);
                if (s.G) break;                                         // the take-off (or walk-off) record: peakY = y there
            }
            return peak;
        }
    }
}
