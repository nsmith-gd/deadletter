using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Loose;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Scenes;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// U-11b (#22): the generic carryable and pushable (§4.10–§4.11), played with the real motor through DL-03 The Weight of
    /// the Job: lift the weight, set it on the trolley's deck, push the trolley onto the plate; the plate weighs them
    /// (IPlateBody) and the gate holds at 0.864 without him (L2229–L2403).
    /// </summary>
    public class LooseTests
    {
        private const double Dt = Mech.Dt, PlateMid = (13 + 15.8 + 13 + 16.55) / 2;

        private sealed class Dl03
        {
            public readonly MechanismGraph G = new MechanismGraph();
            public readonly Pushable Trolley;
            public readonly Carryable Weight;
            public readonly LoadPlate Plate;
            public readonly FollowerActuator Gate;
            public readonly LaneGeometry Lane;
            public readonly InteractionResolver R = new InteractionResolver();
            public readonly D17Motor M;

            public Dl03(string cp, double x, CarryableParams weight = null, double trolleyX = double.NaN)
            {
                var tp = PushableParams.Dl03Trolley();
                if (!double.IsNaN(trolleyX)) tp.StartX = trolleyX;
                Trolley = G.Add(new Pushable("dl03.trolley", tp));                                // the deck steps before what rides it
                Weight = G.Add(new Carryable("dl03.weight", weight ?? CarryableParams.Dl03Weight()));
                Plate = G.Add(new LoadPlate("dl03.plate", LoadPlateParams.Dl03Plate()));
                Gate = G.Add(new FollowerActuator("dl03.gate", FollowerParams.Dl03Gate()));
                G.Build();
                G.Reset(Checkpoint.Prototype(cp));
                R.Register(Weight); R.Register(Trolley); R.Register(Trolley.Twin); R.Register(Trolley.DeckTarget);
                Lane = new LaneGeometry(13 + 12.32, 13 + 17.6 - 0.06 - 0.17).Solid(20, 40, 0)
                    .Add(new CarryableLane(Weight)).Add(new PushableLane(Trolley));
                M = new D17Motor(MotorConfig.Prototype(), Lane, R);
                M.Place(x, 0);
            }

            public void Step(MotorInput i) { M.Step(i, Dt); G.Step(Dt, PlayerPose.Of(M)); }

            public int Until(Func<D17Motor, MotorInput> input, Func<bool> done, int max = 2000)
            {
                for (int k = 1; k <= max; k++) { Step(input(M)); if (done()) return k; }
                return -1;
            }

            /// <summary>Walk (not run) toward x and stop there.</summary>
            public void WalkTo(double x)
            {
                Until(m => new MotorInput { Move = Math.Sign(x - m.X), RunModifierHeld = true }, () => Math.Abs(M.X - x) < 0.03, 1500);
                Until(m => MotorInput.None, () => Math.Abs(M.Vx) < 1e-3, 120);
            }

            public void Use(Verb expect, object target)
            {
                Assert.True(M.PreviewUse(out var c), "nothing answers at " + M.X);
                Assert.Equal(expect, c.Verb);
                Assert.Same(target, c.Target);
                Step(Sim.Use());
                Until(m => MotorInput.None, () => !M.IsActing, 600);
            }
        }

        [Fact]
        public void Dl03_LiftTheWeight_SetItOnTheDeck_PushTheTrolleyOntoThePlate_TheGateHolds_L2396_L2403()
        {
            var s = new Dl03("weighroom", 13 + 12.0);
            Assert.Equal(CarryableState.Rest, s.Weight.State);
            Assert.Equal(0.22, s.Lane.SurfaceAt(s.Weight.X, 0), 12);             // solid on the floor (L1726)
            Assert.Equal(0.16, s.Lane.SurfaceAt(s.Trolley.X, 0), 12);            // the trolley to its deck (L1725)

            s.Use(Verb.Lift, s.Weight);                                          // Lift f22 attach, f39 carrying
            Assert.Equal(HoldKind.Item, s.M.Hold);
            Assert.Equal(CarryableState.Carried, s.Weight.State);
            Assert.Equal(BodySupport.Carried, s.Weight.Support);
            Assert.Equal(0, s.Lane.SurfaceAt(13 + 12.62, 0));                     // gone from the floor

            // Up to the trolley: the deck answers when the spot GRIP_FWD ahead is over it (L2266–L2267).
            s.Until(m => new MotorInput { Move = 1 }, () => s.M.Vx == 0 && s.M.X > 13 + 13.5, 1500);
            Assert.InRange(s.M.X, s.Trolley.X - 0.28 - 0.17 - 0.01, s.Trolley.X - 0.28 - 0.17 + 0.01);   // against its deck
            s.Use(Verb.Place, s.Trolley.DeckTarget);
            Assert.Equal(CarryableState.OnDeck, s.Weight.State);
            Assert.Same(s.Trolley, s.Weight.Deck);
            Assert.Equal(BodySupport.Carrier, s.Weight.Support);
            Assert.InRange(s.Weight.X - s.Trolley.X, -0.17, 0.17);               // clamped to ±0.17 (L2272)
            Assert.Equal(0.16, s.Weight.BaseY, 12);
            Assert.Equal(0.16 + 0.22, s.Lane.SurfaceAt(s.Weight.X, 0), 12);
            Assert.True(s.Trolley.Loaded);
            Assert.Equal(0.42, s.Trolley.Speed);                                 // PUSH_LOADED (L2335)

            // Grab it from behind and push it onto the plate.
            s.WalkTo(s.Trolley.X - 0.62);
            s.Use(Verb.Grab, s.Trolley);
            Assert.Equal(HoldKind.Push, s.M.Hold);
            s.Step(Sim.Move(1));
            Assert.Equal(3 * Dt, s.M.Vx, 12);                                    // acc 3 (L2332)
            s.Until(m => Sim.Move(1), () => s.Trolley.X >= PlateMid, 2000);
            Assert.Equal(PushableState.Held, s.Trolley.State);
            Assert.Equal(BodySupport.Pushed, s.Trolley.Support);
            s.Step(Sim.Use());                                                   // let go
            Assert.Equal(HoldKind.None, s.M.Hold);
            s.Step(Sim.Move(0));
            Assert.Equal(PushableState.Free, s.Trolley.State);
            Assert.Equal(s.Trolley.X + (s.Weight.X - s.Trolley.X), s.Weight.X, 12);   // the weight rode with it
            Assert.False(s.Plate.PlayerOn);
            int solved = s.Until(m => MotorInput.None, () => s.Plate.SolvedWith(s.Gate.Position, 1.2), 600);
            Assert.True(solved > 0, "the plate with the trolley and the weight, without him, opens the gate");
            Assert.Equal(0.3 + 0.42, s.Plate.Load, 12);
        }

        [Fact]
        public void Dl03_TheTrolleyStopsAgainstTheWeightOnTheFloor_FromEitherEnd_L2342_L2346()
        {
            var s = new Dl03("weighroom", 13 + 13.6, new CarryableParams { X = 13 + 15.2, Radius = 0.1, Height = 0.22, Decks = new MechanismId[] { "dl03.trolley" } });
            Assert.Equal(13 + 15.2 - 0.39, s.Trolley.Max, 12);
            s.Use(Verb.Grab, s.Trolley);
            s.Until(m => Sim.Move(1), () => s.M.Vx == 0 && s.Trolley.X > 13 + 14.6, 1500);
            Assert.Equal(13 + 15.2 - 0.39, s.Trolley.X, 9);                       // TROLLEY_HALF + WEIGHT_R + 0.01
            Assert.Equal(HoldKind.Push, s.M.Hold);                                // the old holds stop there in his hands (L2338)
            Assert.Equal(-1, s.Trolley.Twin.Side);
            Assert.Equal(s.Trolley.X, s.Trolley.Twin.X);
        }

        [Fact]
        public void Dl03_HeCarriesTheWeightOntoThePlate_ItWeighsWithHim_L2236()
        {
            var s = new Dl03("weighroom", 13 + 12.0, trolleyX: 13 + 16.95);      // the trolley parked past the plate
            s.Use(Verb.Lift, s.Weight);
            Assert.True(s.Until(m => new MotorInput { Move = 1 }, () => s.Plate.PlayerOn, 2000) > 0);
            s.Step(Sim.Move(0));
            Assert.Equal(1.0 + 0.42, s.Plate.Load, 12);                          // LOAD.d17 + carried weight (L2236)
            Assert.Equal(1.0, Math.Min(1, s.Plate.Load));
        }

        [Theory]
        [InlineData("weighroom", 13 + 14.55, CarryableState.Rest)]
        [InlineData("solved", PlateMid, CarryableState.OnDeck)]
        public void Dl03_ResetFromCheckpoint_TheTrolleyAndTheWeightAreWhereTheyWere_L8025_L8026(string cp, double trolleyX, CarryableState w)
        {
            var s = new Dl03(cp, 26.0);
            Assert.Equal(trolleyX, s.Trolley.X, 12);
            Assert.Equal(w, s.Weight.State);
            if (w == CarryableState.OnDeck) Assert.Equal(PlateMid - 0.12, s.Weight.X, 12);
            else Assert.Equal(13 + 12.62, s.Weight.X, 12);
            Mech.Run(s.G, 1, PlayerPose.Of(s.M));
            Assert.Equal(cp == "solved" ? 0.72 : 0, s.Plate.Load, 12);
        }

        [Fact]
        public void Loose_RestoredWithTheWeightOnTheDeck_ContinuesBitIdentically()
        {
            var a = new Dl03("weighroom", 13 + 12.0);
            a.Use(Verb.Lift, a.Weight);
            a.Until(m => new MotorInput { Move = 1 }, () => a.M.Vx == 0 && a.M.X > 13 + 13.5, 1500);
            a.Use(Verb.Place, a.Trolley.DeckTarget);
            var b = new Dl03("weighroom", 26.0);
            b.G.Restore(Mech.Snapshot(a.G));
            Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            Assert.Equal(CarryableState.OnDeck, b.Weight.State);
            Assert.Equal(a.Weight.X, b.Weight.X, 12);
            for (int k = 0; k < 120; k++)
            {
                a.Step(Sim.Move(-1));
                b.G.Step(Dt, PlayerPose.Of(a.M));
                Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            }
        }

        [Fact]
        public void Dl08Trolley_HeavyAndSlow_RunsOnToTheRailOnceTheEngageableHolds_L2332_L2341()
        {
            var pawl = new TestSource("dl08.pawl");
            var t = new Pushable("dl08.trolley", PushableParams.Dl08Trolley());
            Mech.Graph("goods", pawl, t);
            Assert.Equal(1.3, t.Accel);
            Assert.Equal(0.34, t.Speed);
            Assert.Equal(33 + 51.9 - 0.04 - 0.36, t.Max, 12);
            pawl.Engaged = true;
            Assert.Equal(33 + 55.6 - 0.36 - 0.02, t.Max, 12);
            var lane = new PushableLane(t);
            Assert.Equal(1.6 + 0.44, lane.Surface(t.X + 0.31, 1.6, 1.6), 12);    // solid to its ballast, inset 0.04 (L1731)
            Assert.Equal(1.6, lane.Surface(t.X + 0.33, 1.6, 1.6), 12);
        }
    }
}
