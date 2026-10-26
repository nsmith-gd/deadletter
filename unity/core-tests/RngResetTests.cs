using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Routes;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>A reload replays exactly: mechanisms with a seeded RNG reseed on Reset, so the same checkpoint gives the
    /// same crates and sounds however long the player played before dying.</summary>
    public class RngResetTests
    {
        private static readonly PlayerPose OnDeckAway = new PlayerPose(89.5, 1.6);

        /// <summary>The mechanisms' state; the graph's tick keeps counting across a reload by design.</summary>
        private static string State(MechanismGraph g) =>
            System.Text.RegularExpressions.Regex.Replace(Mech.Dump(g), @"graph/tick=\d+\n", "");

        [Fact]
        public void ReturnsBelt_ResetReplaysTheSameCrates()
        {
            var g = Mech.Graph("cage", new TestSource("dl08.pawl") { Engaged = true }, new ReturnsBelt("dl08.belt", ReturnsBeltParams.Dl08Belt()));
            Mech.Run(g, 1200, OnDeckAway);
            string first = State(g);

            g.Reset(Mech.Cp("cage"));
            Mech.Run(g, 1200, OnDeckAway);
            Assert.Equal(first, State(g));
        }

        [Fact]
        public void ReturnsBelt_ResetAfterALongerRunStillReplaysTheSameCrates()
        {
            var fresh = Mech.Graph("cage", new TestSource("dl08.pawl") { Engaged = true }, new ReturnsBelt("dl08.belt", ReturnsBeltParams.Dl08Belt()));
            Mech.Run(fresh, 1200, OnDeckAway);

            var played = Mech.Graph("cage", new TestSource("dl08.pawl") { Engaged = true }, new ReturnsBelt("dl08.belt", ReturnsBeltParams.Dl08Belt()));
            Mech.Run(played, 3333, OnDeckAway);
            played.Reset(Mech.Cp("cage"));
            Mech.Run(played, 1200, OnDeckAway);

            Assert.Equal(State(fresh), State(played));
        }
    }
}
