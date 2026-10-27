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
    internal sealed class TraceStep
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
                default: throw new InvalidDataException("Unknown trace field '" + k + "'.");
            }
        }

        private static bool B(JsonElement v) => v.ValueKind == JsonValueKind.Number ? v.GetInt32() != 0 : v.ValueKind == JsonValueKind.True;
        private static string S(JsonElement v) => v.ValueKind == JsonValueKind.String ? v.GetString() : null;
        private static double? N(JsonElement v) => v.ValueKind == JsonValueKind.Number ? v.GetDouble() : (double?)null;

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
        public static SceneSim Run(Trace t, SceneDef def, string checkpoint, bool fromOpening, int from, int to,
            Action<TraceStep, SceneSim> onStep, Func<int, SceneSim, MotorInput> input = null)
        {
            var sim = new SceneSim(def);
            sim.Clock = t.Steps[from - 1].Clk;
            sim.Begin(checkpoint, fromOpening);
            for (int k = from; k <= to; k++)
            {
                sim.Step(input != null ? input(k, sim) : t.Steps[k].Input);
                onStep(t.Steps[k], sim);
            }
            return sim;
        }
    }
}
