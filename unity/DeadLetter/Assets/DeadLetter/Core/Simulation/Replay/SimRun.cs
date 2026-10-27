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
        /// <summary>Thirty minutes of game time: past the slowest first playthrough of a chapter (seed 216 needs ~11 for DL-01–06).</summary>
        public const int DefaultMaxSteps = 60 * 1800;

        public static SimResult Play(ISimTarget target, ScriptedPlayer player, int maxSteps = DefaultMaxSteps)
        {
            var wall = Stopwatch.StartNew();
            player.Begin(target);
            var cues = target as ICueSource;
            for (int i = 0; i < maxSteps && !player.Done; i++)
            {
                var input = player.Tick();
                if (player.Done) break;
                target.Step(input);
                if (cues != null && cues.Cues.Count > 0)
                {
                    double t = target.Clock - (player.Out.TryGetMark("play", out var play) ? play : target.Clock);
                    foreach (var c in cues.Cues)
                        player.Out.Cues.Add(t.ToString("0.00", System.Globalization.CultureInfo.InvariantCulture) + " " + c);
                }
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
    }
}
