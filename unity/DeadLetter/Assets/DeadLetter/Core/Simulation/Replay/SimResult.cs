using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace DeadLetter.Core.Simulation.Replay
{
    /// <summary>
    /// One playthrough's result, shaped like bot.js's <c>out</c> plus the fields sim.mjs adds (sim.mjs L30, L37), so
    /// <c>tools/sim/summarise.py</c> reads Core runs and prototype runs alike. summarise.py needs <c>seed</c>,
    /// <c>player</c>, <c>error</c> and <c>marks</c> (with <c>opening</c>, <c>play</c>, <c>end</c> and the scene names
    /// <c>DL-xx</c>); <c>deaths</c> and <c>found</c> are optional. <see cref="Engine"/> is new: "core" for these runs.
    /// </summary>
    public sealed class SimResult
    {
        private readonly List<KeyValuePair<string, double>> _marks = new List<KeyValuePair<string, double>>();

        public uint Seed;
        public double Skill, Curious;
        public readonly List<string> Events = new List<string>();
        /// <summary>Presentation cues the run raised, "&lt;seconds from play&gt; &lt;cue&gt;" (Core runs only; summarise.py ignores them).</summary>
        public readonly List<string> Cues = new List<string>();
        public bool Done;
        public string Error;
        public int Deaths, Found;
        public double X, Clock;
        public string Mode, Act, Hold;
        /// <summary>Wall-clock seconds the run took.</summary>
        public double Wall;
        public string Engine = "core";

        /// <summary>The marks in the order they were set (a JSON object keeps that order, as bot.js's does).</summary>
        public IReadOnlyList<KeyValuePair<string, double>> Marks => _marks;

        /// <summary>Sets a mark the first time only (<c>mark</c>, bot.js L23), rounded to 0.01 s as <c>toFixed(2)</c>.</summary>
        public void Mark(string key, double clock)
        {
            if (HasMark(key)) return;
            _marks.Add(new KeyValuePair<string, double>(key, Math.Round(clock, 2, MidpointRounding.AwayFromZero)));
        }

        public bool HasMark(string key) => TryGetMark(key, out _);

        public bool TryGetMark(string key, out double value)
        {
            foreach (var kv in _marks)
                if (kv.Key == key) { value = kv.Value; return true; }
            value = double.NaN;
            return false;
        }

        /// <summary>The mark, or NaN.</summary>
        public double MarkOr(string key) => TryGetMark(key, out var v) ? v : double.NaN;

        /// <summary>One JSON line (no trailing newline).</summary>
        public string ToJson()
        {
            var sb = new StringBuilder(512);
            sb.Append("{\"seed\":").Append(Seed.ToString(CultureInfo.InvariantCulture));
            sb.Append(",\"player\":{\"skill\":").Append(Num(Math.Round(Skill, 2))).Append(",\"curious\":").Append(Num(Math.Round(Curious, 2))).Append('}');
            sb.Append(",\"marks\":{");
            for (int i = 0; i < _marks.Count; i++)
            {
                if (i > 0) sb.Append(',');
                Str(sb, _marks[i].Key); sb.Append(':').Append(Num(_marks[i].Value));
            }
            sb.Append("},\"events\":[");
            for (int i = 0; i < Events.Count; i++)
            {
                if (i > 0) sb.Append(',');
                Str(sb, Events[i]);
            }
            sb.Append("],\"cues\":[");
            for (int i = 0; i < Cues.Count; i++)
            {
                if (i > 0) sb.Append(',');
                Str(sb, Cues[i]);
            }
            sb.Append("],\"done\":").Append(Done ? "true" : "false");
            sb.Append(",\"error\":"); Str(sb, Error);
            sb.Append(",\"deaths\":").Append(Deaths.ToString(CultureInfo.InvariantCulture));
            sb.Append(",\"found\":").Append(Found.ToString(CultureInfo.InvariantCulture));
            sb.Append(",\"x\":").Append(Num(X));
            sb.Append(",\"clock\":").Append(Num(Clock));
            sb.Append(",\"mode\":"); Str(sb, Mode);
            sb.Append(",\"act\":"); Str(sb, Act);
            sb.Append(",\"hold\":"); Str(sb, Hold);
            sb.Append(",\"wall\":").Append(Num(Math.Round(Wall, 2)));
            sb.Append(",\"pageErrors\":[]");
            sb.Append(",\"engine\":"); Str(sb, Engine);
            sb.Append('}');
            return sb.ToString();
        }

        /// <summary>A JSON number; NaN and infinities (not JSON) become null.</summary>
        private static string Num(double v) =>
            double.IsNaN(v) || double.IsInfinity(v) ? "null" : v.ToString("R", CultureInfo.InvariantCulture);

        private static void Str(StringBuilder sb, string s)
        {
            if (s == null) { sb.Append("null"); return; }
            sb.Append('"');
            foreach (char c in s)
            {
                switch (c)
                {
                    case '"': sb.Append("\\\""); break;
                    case '\\': sb.Append("\\\\"); break;
                    case '\n': sb.Append("\\n"); break;
                    case '\r': sb.Append("\\r"); break;
                    case '\t': sb.Append("\\t"); break;
                    default:
                        if (c < 0x20) sb.Append("\\u").Append(((int)c).ToString("x4", CultureInfo.InvariantCulture));
                        else sb.Append(c);
                        break;
                }
            }
            sb.Append('"');
        }
    }
}
