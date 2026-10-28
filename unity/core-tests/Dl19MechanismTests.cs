using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-19 A Repair That Held, mechanism level: the half landing, the ratchet jack and the bracket's pins
    /// (docs/scenes/DL-19_a_repair_that_held.md §3, §4, §10, §11). The motor is scripted here: pushes as its detent hold
    /// does (<c>D17Motor.StepPush</c>), the crank held with Use, the pins' tug. No prototype exists.
    /// </summary>
    public class Dl19MechanismTests
    {
        private const double Dt = Mech.Dt;
        internal static readonly string[] Ch2 = Checkpoint.GameOrder;

        private sealed class Rig
        {
            public readonly RatchetJack Jack = new RatchetJack("dl19.jack", RatchetJackParams.Dl19Jack());
            public readonly BracketPins Pins = new BracketPins("dl19.pins", BracketPinsParams.Dl19Pins());
            public readonly HalfLanding Landing = new HalfLanding("dl19.landing", HalfLandingParams.Dl19HalfLanding());
            public readonly MechanismGraph G = new MechanismGraph();
            /// <summary>Every event and state change since the rig was built (the graph's log holds one step).</summary>
            public readonly List<MechanismEvent> Log = new List<MechanismEvent>();
            /// <summary>Steps since the rig was built.</summary>
            public int Steps;
            /// <summary>Called after every step (assertions that must hold throughout).</summary>
            public Action<Rig> Check;

            /// <summary>D-17 on the terrace landing, by the jack and the bracket (not on the platform).</summary>
            public static readonly PlayerPose Here = Mech.Pose(363.1, 1.2);

            public Rig(string cp = "half_landing")
            {
                G.Add(Jack);
                G.Add(Pins);
                G.Add(Landing);
                G.Build();
                G.Reset(new Checkpoint(Ch2, cp));
            }

            public void Step(PlayerPose? pose = null)
            {
                G.Step(Dt, pose ?? Here);
                Steps++;
                for (int i = 0; i < G.Log.Count; i++) Log.Add(G.Log[i]);
                Check?.Invoke(this);
            }

            public void Idle(int steps, PlayerPose? pose = null) { for (int i = 0; i < steps; i++) Step(pose); }

            /// <summary>
            /// Holds the jack and walks it toward <paramref name="dir"/> as the motor's push does (detents: he lets go at the
            /// bay or the pocket once it has moved 0.02), for at most <paramref name="max"/> steps. Returns the steps, or −1 if
            /// it never reached a detent.
            /// </summary>
            public int Push(int dir, int max = 600)
            {
                var c = Jack.Chassis;
                double from = c.X, v = 0;
                for (int k = 1; k <= max; k++)
                {
                    double hi = c.Max;
                    v = Smooth.MoveTowards(v, dir * c.Speed, c.Accel * Dt);
                    double tx = Smooth.Clamp(c.X + v * Dt, c.Min, hi);
                    c.MoveTo(tx, (tx - c.X) / Dt);
                    Step();
                    if (Math.Abs(c.X - from) > 0.02 && (Math.Abs(c.X - hi) < 0.005 || Math.Abs(c.X - c.Min) < 0.005))
                    {
                        c.OnReleased(false);
                        Step();
                        return k;
                    }
                }
                c.OnReleased(false);
                Step();
                return -1;
            }

            private double _crankPrev;
            private int _crankK;

            /// <summary>Holds Use at the crank (stick back to wind down) until <paramref name="until"/> or <paramref name="max"/> steps, then lets go.</summary>
            public int Crank(bool down, Func<bool> until, int max = 1200)
            {
                StartCrank();
                for (int k = 1; k <= max; k++)
                {
                    CrankStep(down);
                    if (until != null && until()) { StopCrank(); return k; }
                }
                StopCrank();
                return -1;
            }

            public void StartCrank() { _crankPrev = 0; _crankK = 0; }

            public void CopyCrankClock(Rig from) { _crankPrev = from._crankPrev; _crankK = from._crankK; }

            public void CrankStep(bool down)
            {
                _crankK++;
                double f = _crankK * Mech.FramesPerStep;
                var s = Jack.OnActFrame(new ActFrame(_crankPrev, f, _crankK * Dt, new MotorInput { UseHeld = true, Move = down ? -1 : 0 }, ClipNames.Crank));
                Assert.False(s.IsDone);
                _crankPrev = f;
                Step();
            }

            public void StopCrank()
            {
                _crankK++;
                double f = _crankK * Mech.FramesPerStep;
                var s = Jack.OnActFrame(new ActFrame(_crankPrev, f, _crankK * Dt, new MotorInput { UseHeld = false }, ClipNames.Crank));
                Assert.True(s.IsDone);                                           // letting go of Use ends the act
                Step();
            }

            /// <summary>One Use of the bracket (the tug clip to its end). Returns the steps.</summary>
            public int UsePins(Action<int> onStep = null)
            {
                Assert.True(Pins.Offer(InteractionQuery.At(363.25, 1.2), out _));
                double prev = 0;
                for (int k = 1; k <= 400; k++)
                {
                    double f = k * Mech.FramesPerStep;
                    var s = Pins.OnActFrame(new ActFrame(prev, f, k * Dt, default, ClipNames.Tug));
                    Step();
                    onStep?.Invoke(k);
                    prev = f;
                    if (s.IsDone) return k;
                }
                throw new InvalidOperationException("The tug never ended.");
            }

            public int Count<T>(MechanismId id, T evt) where T : struct, Enum
            {
                int n = 0, code = Convert.ToInt32(evt);
                foreach (var e in Log) if (e.Id == id && e.Kind == MechanismEventKind.Event && e.Code == code) n++;
                return n;
            }

            /// <summary>From whatever state it is in: jack into the pocket, level, swap the pins, wind down, draw the jack back.</summary>
            public void Solve()
            {
                if (Jack.State != RatchetJackState.InPocket) Assert.True(Push(+1) > 0);
                Assert.Equal(RatchetJackState.InPocket, Jack.State);
                if (Pins.State != BracketPinsState.SpareSeated)
                {
                    if (!Landing.MarksMeet)
                        Assert.True(Crank(Landing.Position > Landing.Params.LevelY, () => Landing.MarksMeet) > 0);
                    for (int i = 0; i < 4 && Pins.State != BracketPinsState.SpareSeated; i++) UsePins();
                }
                Assert.Equal(BracketPinsState.SpareSeated, Pins.State);
                if (Jack.Extension > 0) Assert.True(Crank(true, () => Jack.Extension <= 0) > 0);
                Assert.True(Push(-1) > 0);
                Assert.Equal(RatchetJackState.Parked, Jack.State);
                Assert.Equal(HalfLandingState.Pinned, Landing.State);
                Assert.Equal(1.75, Landing.Position, 12);
            }
        }

        /// <summary>Every pin is in exactly one of the fork, the cup, the clip or his hands, and never two in the fork.</summary>
        private static void AssertPinsPlaced(BracketPins p)
        {
            Assert.Contains(p.BentPin, new[] { PinPlace.Fork, PinPlace.Cup });
            Assert.Contains(p.SparePin, new[] { PinPlace.Clip, PinPlace.Hands, PinPlace.Fork });
            Assert.False(p.BentPin == PinPlace.Fork && p.SparePin == PinPlace.Fork);
            if (p.BentHalfOut) Assert.Equal(PinPlace.Fork, p.BentPin);
        }

        // ---- Geometry and the start ---------------------------------------------------------------------------------------

        [Fact]
        public void Params_JackTopOfTravel_HoldsTheLeftEndAt1_85_AndItsSaddleStartsUnderTheCupOnTheStops()
        {
            var lp = HalfLandingParams.Dl19HalfLanding();
            var jp = RatchetJackParams.Dl19Jack();
            Assert.Equal(1.85, lp.LeftTopForSaddle(jp.SaddleLowY + jp.Travel), 12);
            Assert.True(jp.SaddleLowY < lp.CupY(lp.StopsY));                     // it rolls in under a platform on its stops
            Assert.Equal(1.75, lp.TopAt(1.55, 366.2), 12);                       // hinged at its right end
            Assert.Equal(1.55, lp.TopAt(1.55, 363.6), 12);
            Assert.Equal(363.35, jp.PocketX - jp.Half, 12);                      // the pocket 363.35–364.05
            Assert.Equal(364.05, jp.PocketX + jp.Half, 12);
        }

        [Fact]
        public void Start_DroopingOnTheBentPin_Creaking_JackInItsBay_SpareInItsClip()
        {
            var r = new Rig();
            r.Idle(1);
            Assert.Equal(HalfLandingState.Drooping, r.Landing.State);
            Assert.Equal(1.55, r.Landing.Position, 12);
            Assert.Equal(1.55, r.Landing.TopAt(363.6), 12);
            Assert.True(double.IsNaN(r.Landing.TopAt(366.3)));
            Assert.False(r.Landing.Standable);
            Assert.Equal(RatchetJackState.Parked, r.Jack.State);
            Assert.Equal(362.85, r.Jack.X, 12);
            Assert.Equal(0, r.Jack.Extension);
            Assert.Equal(BracketPinsState.BentSeated, r.Pins.State);
            Assert.Equal(PinPlace.Fork, r.Pins.BentPin);
            Assert.Equal(PinPlace.Clip, r.Pins.SparePin);
            Assert.Equal(PinSound.Creak, r.Pins.Sound);
            Assert.False(r.Jack.Offer(InteractionQuery.At(362.98, 1.2), out _)); // the crank works only in the pocket
            r.Idle(300);
            Assert.Equal(1.55, r.Landing.Position, 12);                          // it hangs there
        }

        // ---- The solution ----------------------------------------------------------------------------------------------------

        [Fact]
        public void Solution_JackIn_CrankToLevel_PullTheBentPin_SeatTheSpare_WindDown_PinnedAt1_75()
        {
            var r = new Rig();
            r.Check = x => AssertPinsPlaced(x.Pins);

            // 1. Push the jack into its pocket: its wheels drop into the seats with a clunk.
            Assert.True(r.Push(+1) > 0);
            Assert.Equal(RatchetJackState.InPocket, r.Jack.State);
            Assert.Equal(363.7, r.Jack.X, 12);
            Assert.Equal(363.9, r.Jack.SaddleX, 12);
            Assert.Equal(1, r.Count("dl19.jack", RatchetJackEvent.Clunk));
            Assert.True(r.Jack.Offer(InteractionQuery.At(362.98, 1.2), out var pose));
            Assert.Equal(+1, pose.Face);

            // 2. Crank: the saddle meets the cup, lifts it off the pin, levels it; the creak stops and the rattle starts.
            int meet = -1, rattle = -1;
            int n = r.Crank(false, () =>
            {
                if (meet < 0 && r.Landing.MarksMeet) meet = r.Steps;
                if (rattle < 0 && r.Pins.Sound == PinSound.Rattle) rattle = r.Steps;
                return rattle > 0;
            });
            Assert.True(n > 0);
            Assert.InRange((rattle - meet) * Dt, 0, 0.2);                        // §10 "The tell": within 0.2 s
            Assert.Equal(HalfLandingState.Level, r.Landing.State);
            Assert.Equal(1.0, r.Landing.Load);
            Assert.True(n * Dt < 8);
            Assert.True(r.Count("dl19.jack", RatchetJackEvent.Click) >= 10);     // a click per 0.02 m
            r.Idle(120);
            Assert.True(r.Landing.MarksMeet);                                    // the ratchet holds where he let go

            // 3. Pull the bent pin into the cup, take the spare, seat it.
            r.UsePins();
            Assert.Equal(BracketPinsState.ForkEmpty, r.Pins.State);
            Assert.Equal(PinPlace.Cup, r.Pins.BentPin);
            Assert.Equal(1, r.Count("dl19.pins", BracketPinsEvent.Clink));
            Assert.Equal(PinSound.Quiet, r.Pins.Sound);
            r.UsePins();
            Assert.Equal(PinPlace.Hands, r.Pins.SparePin);
            r.UsePins();
            Assert.Equal(PinPlace.Fork, r.Pins.SparePin);
            Assert.Equal(1, r.Count("dl19.pins", BracketPinsEvent.Seated));
            Assert.Equal(1.75, r.Landing.Position, 12);                          // seated low in the band, it draws the lug home
            Assert.False(r.Pins.Offer(InteractionQuery.At(363.25, 1.2), out _)); // nothing more to do at the bracket

            // 4. Wind down: it settles onto the new pin, no creak, no bang; the jack rolls back to its bay.
            Assert.True(r.Crank(true, () => r.Jack.Extension <= 0) > 0);
            Assert.Equal(HalfLandingState.Pinned, r.Landing.State);
            Assert.Equal(1.75, r.Landing.Position, 12);
            Assert.Equal(0, r.Landing.Load);
            Assert.True(r.Landing.Standable);
            Assert.Equal(0, r.Count("dl19.landing", HalfLandingEvent.Drop));
            Assert.Equal(PinSound.Quiet, r.Pins.Sound);
            Assert.True(r.Push(-1) > 0);
            Assert.Equal(RatchetJackState.Parked, r.Jack.State);
            r.Idle(300);
            Assert.Equal(1.75, r.Landing.Position, 12);

            // Standing on it now: no lurch.
            var on = Mech.Pose(364.5, 1.75);
            r.Idle(30, on);
            Assert.Equal(0, r.Count("dl19.landing", HalfLandingEvent.Lurch));
        }

        // ---- Wrong paths ---------------------------------------------------------------------------------------------------

        [Fact]
        public void WrongPath_BentPinPulledWhileLoaded_DropsOntoTheStops_PinBites_Within2s_AndTheSolutionStaysPossible()
        {
            var r = new Rig();
            r.Check = x => { AssertPinsPlaced(x.Pins); Assert.True(x.Landing.Position >= 1.45 - 1e-12); };
            int start = r.Steps, draw = -1, stops = -1;
            r.UsePins(k =>
            {
                if (draw < 0 && r.Pins.State == BracketPinsState.BentHalfOut) draw = r.Steps;
                if (stops < 0 && r.Landing.State == HalfLandingState.OnStops) stops = r.Steps;
            });
            Assert.True(stops > 0);
            Assert.InRange((stops - start) * Dt, 0, 2.0);                         // §4: under 2 s
            Assert.InRange((stops - draw) * Dt, 0, 0.5);                          // §10: onto the stops within 0.5 s
            Assert.Equal(1.45, r.Landing.Position, 12);
            Assert.Equal(1, r.Count("dl19.pins", BracketPinsEvent.Draw));
            Assert.Equal(1, r.Count("dl19.landing", HalfLandingEvent.Drop));      // a bang
            Assert.True(r.Log.Exists(e => e.Id == "dl19.landing" && e.Code == (int)HalfLandingEvent.Drop && e.Kind == MechanismEventKind.Event
                                          && e.Index == 0 && e.Value >= 1.0));
            Assert.Equal(PinPlace.Fork, r.Pins.BentPin);                          // left half out
            Assert.True(r.Pins.BentHalfOut);
            Assert.Equal(PinSound.Quiet, r.Pins.Sound);                           // on the stops: the pin bites, nothing creaks

            r.UsePins();                                                         // another Use only strains
            Assert.Equal(1, r.Count("dl19.pins", BracketPinsEvent.Strain));
            Assert.Equal(BracketPinsState.BentHalfOut, r.Pins.State);
            Assert.Equal(HalfLandingState.OnStops, r.Landing.State);

            // Recovery: re-jack to level in under 8 s (§10), then the same swap.
            Assert.True(r.Push(+1) > 0);
            int lift = r.Crank(false, () => r.Landing.MarksMeet);
            Assert.InRange(lift * Dt, 0, 8);
            Assert.Equal(PinSound.Rattle, r.Pins.Sound);
            r.Solve();
        }

        [Fact]
        public void WrongPath_StandingOnItUnpinned_Lurches_DroopingAndOnTheStops()
        {
            var r = new Rig();
            var onIt = Mech.Pose(363.9, r.Landing.TopAt(363.9));
            r.Idle(5, onIt);
            Assert.Equal(1, r.Count("dl19.landing", HalfLandingEvent.Lurch));   // once per stepping on
            var e = r.Log.Find(x => x.Id == "dl19.landing" && x.Kind == MechanismEventKind.Event && x.Code == (int)HalfLandingEvent.Lurch);
            Assert.Equal(0, e.Index);
            Assert.Equal(0.03, e.Value, 12);                                     // it lurches 3 cm
            Assert.Equal(1.55, r.Landing.Position, 12);                          // and springs back: nothing changes
            r.Idle(5);                                                           // the hop back

            r.UsePins();
            Assert.Equal(HalfLandingState.OnStops, r.Landing.State);
            r.Idle(3, Mech.Pose(363.9, r.Landing.TopAt(363.9)));
            Assert.Equal(2, r.Count("dl19.landing", HalfLandingEvent.Lurch));
            e = r.Log.FindLast(x => x.Id == "dl19.landing" && x.Kind == MechanismEventKind.Event && x.Code == (int)HalfLandingEvent.Lurch);
            Assert.Equal(1, e.Index);                                            // it rocks and clangs
            r.Idle(3, Mech.Pose(363.9, r.Landing.TopAt(363.9), grounded: false));
            r.Idle(3, Mech.Pose(363.9, 1.0));                                    // nowhere near its top
            Assert.Equal(2, r.Count("dl19.landing", HalfLandingEvent.Lurch));
        }

        [Fact]
        public void SeatingTheSpare_NotLevel_Chatters_AndHeKeepsIt()
        {
            var r = new Rig();
            r.Check = x => AssertPinsPlaced(x.Pins);
            Assert.True(r.Push(+1) > 0);
            r.Crank(false, () => r.Landing.MarksMeet);
            r.UsePins();                                                         // bent pin out, into the cup
            Assert.Equal(BracketPinsState.ForkEmpty, r.Pins.State);
            r.Crank(true, () => r.Jack.Extension <= 0);                          // lowering with no pin: back onto the stops
            Assert.Equal(HalfLandingState.OnStops, r.Landing.State);
            Assert.Equal(0, r.Count("dl19.landing", HalfLandingEvent.Drop));     // it settles, no bang
            r.UsePins();
            Assert.Equal(BracketPinsState.SpareCarried, r.Pins.State);
            Assert.Equal(1, r.Count("dl19.pins", BracketPinsEvent.Taken));
            r.UsePins();
            Assert.Equal(1, r.Count("dl19.pins", BracketPinsEvent.Chatter));
            Assert.Equal(PinPlace.Hands, r.Pins.SparePin);                       // he keeps it
            Assert.Equal(HalfLandingState.OnStops, r.Landing.State);
            r.Crank(false, () => r.Landing.Position > 1.75 + 0.02);              // too high: still chatters
            Assert.False(r.Landing.MarksMeet);
            r.UsePins();
            Assert.Equal(2, r.Count("dl19.pins", BracketPinsEvent.Chatter));
            Assert.Equal(PinPlace.Hands, r.Pins.SparePin);
            r.Solve();
        }

        [Fact]
        public void WindingToTheTop_BindsAt1_85_TheCreakReturns()
        {
            var r = new Rig();
            Assert.True(r.Push(+1) > 0);
            r.Crank(false, null, max: 6 * 60);
            Assert.Equal(r.Jack.Params.Travel, r.Jack.Extension, 12);
            Assert.Equal(1.85, r.Landing.Position, 9);
            Assert.Equal(HalfLandingState.Held, r.Landing.State);
            Assert.Equal(1, r.Count("dl19.jack", RatchetJackEvent.Bind));        // once per hold
            Assert.Equal(PinSound.Creak, r.Pins.Sound);                          // the pin binds again
            r.UsePins();                                                         // loaded: it bites part-way; the jack holds the platform
            Assert.Equal(BracketPinsState.BentHalfOut, r.Pins.State);
            Assert.Equal(1.85, r.Landing.Position, 9);
            r.Solve();
        }

        [Fact]
        public void WithTheSpareSeated_WindingUpBindsAgainstThePin_TheLandingStaysInItsBand()
        {
            var r = new Rig();
            Assert.True(r.Push(+1) > 0);
            r.Crank(false, () => r.Landing.Position >= 1.745);                   // level, low in the band
            r.UsePins(); r.UsePins(); r.UsePins();
            Assert.Equal(BracketPinsState.SpareSeated, r.Pins.State);
            r.Crank(false, null, max: 120);
            Assert.InRange(r.Landing.Position, 1.75, 1.77 + 1e-9);
            Assert.True(r.Count("dl19.jack", RatchetJackEvent.Bind) >= 1);
            Assert.Equal(HalfLandingState.Level, r.Landing.State);
            Assert.True(r.Crank(true, () => r.Jack.Extension <= 0) > 0);
            Assert.Equal(HalfLandingState.Pinned, r.Landing.State);
            Assert.Equal(1.75, r.Landing.Position, 12);
        }

        [Fact]
        public void LoadedJack_CannotBePushed_HeHeaves_ItRollsOnceWoundDown()
        {
            var r = new Rig();
            Assert.True(r.Push(+1) > 0);
            r.Crank(false, () => r.Landing.State == HalfLandingState.Held);
            Assert.True(r.Jack.Loaded);
            Assert.Equal(r.Jack.X, r.Jack.Chassis.Min);
            Assert.Equal(r.Jack.X, r.Jack.Chassis.Max);
            Assert.Equal(-1, r.Push(-1, max: 120));                              // he heaves and it stays
            Assert.Equal(363.7, r.Jack.X, 12);
            Assert.Equal(RatchetJackState.InPocket, r.Jack.State);
            Assert.Equal(1, r.Count("dl19.jack", RatchetJackEvent.Heave));
            r.Crank(true, () => r.Jack.Extension <= 0);
            Assert.Equal(HalfLandingState.Drooping, r.Landing.State);            // back onto the bent pin, gently
            Assert.Equal(0, r.Count("dl19.landing", HalfLandingEvent.Drop));
            Assert.False(r.Jack.Loaded);
            Assert.True(r.Push(-1) > 0);
            Assert.Equal(RatchetJackState.Parked, r.Jack.State);
            Assert.Equal(362.85, r.Jack.X, 12);
        }

        // ---- No pin is ever lost --------------------------------------------------------------------------------------------

        [Theory]
        [InlineData(1)]
        [InlineData(7)]
        [InlineData(42)]
        [InlineData(2026)]
        public void RandomPlay_EveryPinIsAlwaysInOnePlace_NothingWorseThanTheStops_AndItCanStillBeSolved(int seed)
        {
            var r = new Rig();
            r.Check = x =>
            {
                AssertPinsPlaced(x.Pins);
                Assert.InRange(x.Landing.Position, 1.45 - 1e-12, 1.85 + 1e-9);
                Assert.InRange(x.Jack.X, 362.85 - 1e-12, 363.7 + 1e-12);
                Assert.InRange(x.Jack.Extension, 0, x.Jack.Params.Travel);
            };
            var rng = new Random(seed);
            for (int i = 0; i < 60; i++)
            {
                switch (rng.Next(6))
                {
                    case 0: r.Push(+1, max: 1 + rng.Next(240)); break;
                    case 1: r.Push(-1, max: 1 + rng.Next(240)); break;
                    case 2: if (r.Jack.State == RatchetJackState.InPocket) r.Crank(false, null, max: 1 + rng.Next(240)); break;
                    case 3: if (r.Jack.State == RatchetJackState.InPocket) r.Crank(true, null, max: 1 + rng.Next(240)); break;
                    case 4: if (r.Pins.State != BracketPinsState.SpareSeated) r.UsePins(); break;
                    default: r.Idle(1 + rng.Next(60), rng.Next(4) == 0 ? Mech.Pose(364.0, r.Landing.TopAt(364.0)) : Rig.Here); break;
                }
            }
            r.Solve();
        }

        // ---- Reset and persistence -----------------------------------------------------------------------------------------

        [Theory]
        [InlineData("ring_a", false)]
        [InlineData("terrace", false)]
        [InlineData("half_landing", false)]
        [InlineData("repaired", true)]
        public void Reset_FromEachCheckpoint(string cp, bool solved)
        {
            var r = new Rig();
            Assert.True(r.Push(+1) > 0);                                         // dirty everything first
            r.Crank(false, () => r.Landing.MarksMeet);
            r.UsePins(); r.UsePins();
            Assert.Equal(PinPlace.Hands, r.Pins.SparePin);

            r.G.Reset(new Checkpoint(Ch2, cp));
            r.Idle(1);
            Assert.Equal(RatchetJackState.Parked, r.Jack.State);                 // the jack in its bay, fully down
            Assert.Equal(362.85, r.Jack.X, 12);
            Assert.Equal(0, r.Jack.Extension);
            if (solved)
            {
                Assert.Equal(HalfLandingState.Pinned, r.Landing.State);
                Assert.Equal(1.75, r.Landing.Position, 12);
                Assert.Equal(PinPlace.Fork, r.Pins.SparePin);
                Assert.Equal(PinPlace.Cup, r.Pins.BentPin);
                Assert.True(r.Landing.Standable);
            }
            else
            {
                Assert.Equal(HalfLandingState.Drooping, r.Landing.State);
                Assert.Equal(1.55, r.Landing.Position, 12);
                Assert.Equal(PinPlace.Clip, r.Pins.SparePin);                    // a carried spare returns to its clip
                Assert.Equal(PinPlace.Fork, r.Pins.BentPin);
                Assert.False(r.Pins.BentHalfOut);
            }
        }

        [Fact]
        public void CheckpointSnapshot_CarriesTheJackAndEveryPin_ThroughAReload()
        {
            var r = new Rig("terrace");
            var cps = new CheckpointService(r.G, Ch2, new MemorySaveStore());
            cps.Restart("terrace");
            r.UsePins();                                                         // the wrong path: half out, on the stops
            Assert.True(r.Push(+1) > 0);
            r.Crank(false, () => r.Landing.State == HalfLandingState.Held && r.Landing.Position > 1.6);
            Assert.True(cps.Reach("half_landing"));
            string atReach = SaveKit.Dump(r.G);
            r.Crank(false, () => r.Landing.MarksMeet);
            r.UsePins();
            Assert.Equal(BracketPinsState.ForkEmpty, r.Pins.State);

            cps.Reload();
            Assert.Equal(atReach, SaveKit.Dump(r.G));
            Assert.Equal(RatchetJackState.InPocket, r.Jack.State);
            Assert.Equal(BracketPinsState.BentHalfOut, r.Pins.State);
            Assert.Equal(HalfLandingState.Held, r.Landing.State);
            r.Solve();
        }

        [Fact]
        public void RestoredMidCrank_ContinuesBitIdentically()
        {
            var a = new Rig();
            Assert.True(a.Push(+1) > 0);
            a.StartCrank();
            for (int k = 0; k < 100; k++) a.CrankStep(false);                   // mid-lift: the saddle carries it
            Assert.Equal(HalfLandingState.Held, a.Landing.State);

            var b = new Rig();
            b.G.Restore(Mech.Snapshot(a.G));
            b.CopyCrankClock(a);                                                 // the motor's clip clock carries on
            Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            for (int k = 0; k < 200; k++)
            {
                bool down = k >= 150;                                            // up to the top, binding, then back down
                a.CrankStep(down);
                b.CrankStep(down);
                Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            }
            a.StopCrank();
            b.StopCrank();
            Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
        }
    }
}
