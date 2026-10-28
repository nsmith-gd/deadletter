using System;
using System.Collections.Generic;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl19;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-19: the only way up is the solution (§4; #46: the mid-air catch reaches about 1.09 m above takeoff). From every
    /// place he can stand below (the terrace landing, 361.0 to the half landing; the unpinned plate hops him off, the jack is
    /// a column), in every state of the jack, the pins and the half landing, standing, walking and running jumps in both
    /// directions, each in the real <see cref="ChapterSim"/>: none puts him on the upper flight or the upper terrace, none
    /// leaves him standing on an unpinned half landing, none puts him on the jack, and with the jack out of its bay none so
    /// much as touches the half landing (§10 "Blocked spot"). In the solved state the same search does find the way up.
    /// </summary>
    public class Dl19SkipSearchTests
    {
        private enum Mode { Stand, Walk, Run }

        private struct Outcome
        {
            public bool Up, EndsOnPlate, TouchedPlate, OnJack;
        }

        public static IEnumerable<object[]> States() => new[]
        {
            new object[] { "bay" }, new object[] { "bayOnStops" }, new object[] { "free" }, new object[] { "pocket" },
            new object[] { "pocketOnStops" }, new object[] { "pocketHeld" }, new object[] { "pocketLevel" }, new object[] { "pocketTop" },
            new object[] { "pocketForkEmpty" }, new object[] { "pocketPinnedDown" }, new object[] { "solved" },
        };

        [Theory]
        [MemberData(nameof(States))]
        public void NoSkip_StandingWalkingAndRunningJumps_BothWays_FromEveryPlaceBelow(string state)
        {
            var s = Dl19ChapterTests.Setup(state);
            var snap = Mech.Snapshot(s.Graph);
            var landing = Dl19ChapterTests.Landing(s);
            var jack = Dl19ChapterTests.Jack(s);
            bool solved = state == "solved", jackOut = jack.State != RatchetJackState.Parked;
            int attempts = 0, endsOnPlate = 0;
            for (int i = 0; i <= 52; i++)
            {
                double x0 = 361.0 + 0.05 * i;
                if (!Floor(s, x0)) continue;
                foreach (int dir in new[] { 1, -1 })
                    foreach (Mode mode in new[] { Mode.Stand, Mode.Walk, Mode.Run })
                    {
                        var o = Attempt(s, snap, x0, dir, mode);
                        attempts++;
                        string what = state + ": " + mode + " jump " + (dir > 0 ? "right" : "left") + " from " + x0.ToString("F2");
                        Assert.False(o.OnJack, what + " put him on the jack");
                        if (solved) { if (o.EndsOnPlate) endsOnPlate++; continue; }
                        Assert.False(o.Up, what + " reached the upper flight or terrace");
                        Assert.False(o.EndsOnPlate, what + " left him standing on the half landing");
                        if (jackOut) Assert.False(o.TouchedPlate, what + " got onto the half landing over the jack");
                    }
            }
            Assert.True(attempts >= 100, state + ": " + attempts + " attempts");
            if (solved) Assert.True(endsOnPlate > 0, "the search never found the solved way up");
            Assert.Equal(solved || state == "pocketPinnedDown", landing.Standable);                // pinned, but the jack still on the spot
        }

        /// <summary>He can stand at x on the terrace landing (1.2), clear of every face.</summary>
        private static bool Floor(ChapterSim s, double x)
        {
            var c = s.Config;
            return s.Lane.SupportAt(x) == Dl19Lane.FloorY && s.Lane.SurfaceAt(x - c.Half + 1e-6) <= Dl19Lane.FloorY + c.StepUp
                && s.Lane.SurfaceAt(x + c.Half - 1e-6) <= Dl19Lane.FloorY + c.StepUp;
        }

        private static Outcome Attempt(ChapterSim s, MemorySnapshot snap, double x0, int dir, Mode mode)
        {
            s.Graph.Restore(snap);
            s.EndAct();
            s.RespawnAt = 0;
            double start = x0;
            if (mode != Mode.Stand)
            {
                start = x0 - dir * 1.0;
                for (int k = 0; k < 100 && !Floor(s, start); k++) start += dir * 0.01;              // as far back as he can stand
            }
            s.Motor.Place(start, Dl19Lane.FloorY, dir);
            var o = new Outcome();
            var hold = new MotorInput { Move = mode == Mode.Stand ? 0 : dir, RunModifierHeld = mode == Mode.Walk };
            if (mode != Mode.Stand)
                for (int k = 0; k < 150 && (dir > 0 ? s.X < x0 : s.X > x0) && !(k > 5 && s.Vx == 0); k++) Watch(s, hold, ref o);
            var jump = hold;
            jump.JumpPressed = true;
            Watch(s, jump, ref o);
            for (int k = 0; k < 75; k++) Watch(s, hold, ref o);
            for (int k = 0; k < 120; k++) Watch(s, default, ref o);
            o.EndsOnPlate = OnPlate(s);
            return o;
        }

        private static void Watch(ChapterSim s, MotorInput input, ref Outcome o)
        {
            s.Step(input);
            if (s.Grounded && s.X >= Dl19Lane.FlightX0 && s.Y >= Dl19Lane.LevelY - 0.01) o.Up = true;
            if (s.Y > Dl19Lane.TerraceY + 0.2) o.OnJack = true;                                    // nothing below 2.5 but the jack's column
            if (OnPlate(s) || s.Graph.Log.Has(Dl19Scene.Landing, MechanismEventKind.Event, (int)HalfLandingEvent.Lurch)) o.TouchedPlate = true;
        }

        private static bool OnPlate(ChapterSim s)
        {
            double top = Dl19ChapterTests.Landing(s).TopAt(s.X);
            return s.Act == null && s.Grounded && !double.IsNaN(top) && Math.Abs(s.Y - top) <= 0.06;
        }
    }
}
