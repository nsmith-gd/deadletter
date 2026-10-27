using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Simulation.Replay
{
    /// <summary>
    /// A run's per-step input, run-length encoded (U-18: "recorded-input" replays). Replaying it into the same scene
    /// from the same checkpoint reproduces the run bit for bit, because Core steps at a fixed 60 Hz and every system
    /// draws from seeded generators (§2, §3.1). The same file drives the Core replay tests and, in Unity, the PlayMode
    /// replays (Runtime feeds each step's input to the step instead of the Input System).
    /// <para>Text format, one run per line after a header:
    /// <c>dlrec 1 &lt;scene&gt; &lt;checkpoint&gt; &lt;steps&gt;</c>, then <c>&lt;count&gt; &lt;move&gt; [flags]</c> where move is
    /// the lane axis ("R" round-trip) and flags are J (jump pressed), j (jump held), U (use pressed), u (use held),
    /// R (run modifier), C (crouch), A (analog move). Lines starting with # are comments.</para>
    /// </summary>
    public sealed class InputRecording
    {
        public const string Magic = "dlrec";
        public const int Version = 1;

        private readonly List<MotorInput> _runInput = new List<MotorInput>();
        private readonly List<int> _runCount = new List<int>();

        public InputRecording(string scene, string checkpoint)
        {
            Scene = scene ?? "";
            Checkpoint = checkpoint ?? "start";
        }

        public string Scene { get; }
        public string Checkpoint { get; }
        /// <summary>Number of steps recorded.</summary>
        public int Steps { get; private set; }
        /// <summary>Number of runs (lines) after encoding.</summary>
        public int Runs => _runCount.Count;

        public void Add(in MotorInput input)
        {
            int n = _runCount.Count;
            if (n > 0 && Same(_runInput[n - 1], input)) _runCount[n - 1]++;
            else { _runInput.Add(input); _runCount.Add(1); }
            Steps++;
        }

        /// <summary>Every step's input, in order.</summary>
        public IEnumerable<MotorInput> Inputs()
        {
            for (int i = 0; i < _runCount.Count; i++)
                for (int k = 0; k < _runCount[i]; k++) yield return _runInput[i];
        }

        private static bool Same(in MotorInput a, in MotorInput b) =>
            a.Move.Equals(b.Move) && a.MoveIsAnalog == b.MoveIsAnalog && a.JumpPressed == b.JumpPressed && a.JumpHeld == b.JumpHeld
            && a.UsePressed == b.UsePressed && a.UseHeld == b.UseHeld && a.RunModifierHeld == b.RunModifierHeld && a.CrouchHeld == b.CrouchHeld;

        public string ToText()
        {
            var sb = new StringBuilder(16 + _runCount.Count * 12);
            sb.Append(Magic).Append(' ').Append(Version.ToString(CultureInfo.InvariantCulture)).Append(' ')
              .Append(Token(Scene)).Append(' ').Append(Token(Checkpoint)).Append(' ').Append(Steps.ToString(CultureInfo.InvariantCulture)).Append('\n');
            for (int i = 0; i < _runCount.Count; i++)
            {
                var m = _runInput[i];
                sb.Append(_runCount[i].ToString(CultureInfo.InvariantCulture)).Append(' ').Append(m.Move.ToString("R", CultureInfo.InvariantCulture));
                string f = (m.JumpPressed ? "J" : "") + (m.JumpHeld ? "j" : "") + (m.UsePressed ? "U" : "") + (m.UseHeld ? "u" : "")
                    + (m.RunModifierHeld ? "R" : "") + (m.CrouchHeld ? "C" : "") + (m.MoveIsAnalog ? "A" : "");
                if (f.Length > 0) sb.Append(' ').Append(f);
                sb.Append('\n');
            }
            return sb.ToString();
        }

        private static string Token(string s) => string.IsNullOrEmpty(s) ? "-" : s.Replace(' ', '_');

        /// <summary>Parses <see cref="ToText"/>'s format; throws <see cref="FormatException"/> on anything else.</summary>
        public static InputRecording Parse(string text)
        {
            if (text == null) throw new ArgumentNullException(nameof(text));
            var lines = text.Split('\n');
            InputRecording rec = null;
            int declared = -1;
            for (int li = 0; li < lines.Length; li++)
            {
                string line = lines[li].Trim();
                if (line.Length == 0 || line[0] == '#') continue;
                var t = line.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                if (rec == null)
                {
                    if (t.Length != 5 || t[0] != Magic) throw new FormatException("not a dlrec header: " + line);
                    if (int.Parse(t[1], CultureInfo.InvariantCulture) != Version) throw new FormatException("unsupported dlrec version " + t[1]);
                    rec = new InputRecording(t[2] == "-" ? "" : t[2], t[3] == "-" ? "" : t[3]);
                    declared = int.Parse(t[4], CultureInfo.InvariantCulture);
                    continue;
                }
                if (t.Length < 2 || t.Length > 3) throw new FormatException("line " + (li + 1) + ": " + line);
                int count = int.Parse(t[0], CultureInfo.InvariantCulture);
                if (count <= 0) throw new FormatException("line " + (li + 1) + ": count must be positive");
                var m = new MotorInput { Move = double.Parse(t[1], NumberStyles.Float, CultureInfo.InvariantCulture) };
                if (t.Length == 3)
                    foreach (char c in t[2])
                    {
                        switch (c)
                        {
                            case 'J': m.JumpPressed = true; break;
                            case 'j': m.JumpHeld = true; break;
                            case 'U': m.UsePressed = true; break;
                            case 'u': m.UseHeld = true; break;
                            case 'R': m.RunModifierHeld = true; break;
                            case 'C': m.CrouchHeld = true; break;
                            case 'A': m.MoveIsAnalog = true; break;
                            default: throw new FormatException("line " + (li + 1) + ": unknown flag '" + c + "'");
                        }
                    }
                for (int k = 0; k < count; k++) rec.Add(m);
            }
            if (rec == null) throw new FormatException("empty recording");
            if (rec.Steps != declared) throw new FormatException("header says " + declared + " steps, body has " + rec.Steps);
            return rec;
        }
    }
}
