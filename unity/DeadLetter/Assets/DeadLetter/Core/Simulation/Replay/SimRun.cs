using System.Diagnostics;

namespace DeadLetter.Core.Simulation.Replay
{
    /// <summary>
    /// Plays a <see cref="ScriptedPlayer"/> through an <see cref="ISimTarget"/> at 60 Hz, as sim.mjs drives bot.js
    /// (sim.mjs L20–L37): one <see cref="ScriptedPlayer.Tick"/> then one step, until the script ends or the step budget
    /// runs out (sim.mjs's wall timeout).
    /// </summary>
    public static class SimRun
    {
        /// <summary>Ten minutes of game time: longer than any one scene's slowest first playthrough.</summary>
        public const int DefaultMaxSteps = 60 * 600;

        /// <param name="record">If given, every step's input is appended to it.</param>
        public static SimResult Play(ISimTarget target, ScriptedPlayer player, int maxSteps = DefaultMaxSteps, InputRecording record = null)
        {
            var wall = Stopwatch.StartNew();
            player.Begin(target);
            for (int i = 0; i < maxSteps && !player.Done; i++)
            {
                var input = player.Tick();
                if (player.Done) break;
                record?.Add(input);
                target.Step(input);
            }
            var o = player.Out;
            if (!o.Done) o.Error = "wall timeout at x=" + target.X.ToString("R", System.Globalization.CultureInfo.InvariantCulture);
            o.X = target.X;
            o.Clock = target.Clock;
            o.Mode = target.Playing ? "play" : "opening";
            o.Act = target.Act;
            o.Hold = target.Hold == Interaction.HoldKind.None ? null : target.Hold.ToString().ToLowerInvariant();
            o.Wall = wall.Elapsed.TotalSeconds;
            return o;
        }

        /// <summary>Feeds a recording into <paramref name="target"/>, one input per step; <paramref name="afterStep"/> sees each step.</summary>
        public static void Replay(ISimTarget target, InputRecording recording, System.Action<int> afterStep = null)
        {
            int i = 0;
            foreach (var input in recording.Inputs())
            {
                target.Step(input);
                afterStep?.Invoke(i++);
            }
        }
    }
}
