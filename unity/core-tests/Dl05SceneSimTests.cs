using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Push;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl05;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-05 as Core runs it (<see cref="Dl05Scene.Def"/> in a <see cref="SceneSim"/>): the checkpoints' worlds, the
    /// hatch in the lane, the drum's two stops and the body's <c>avail</c> (Core/Push's <see cref="PushableParams.StopAt"/>
    /// and <see cref="PushableParams.MinRoom"/>), the nearest grip winning whatever his facing, and the whole weigh-in
    /// played through. L3447–L3454, L4104–L4107, L4165–L4178, L4251–L4295, L4463–L4466, L4684–L4731, L4878–L4947.
    /// </summary>
    public class Dl05SceneSimTests
    {
        private static readonly MotorInput Use = new MotorInput { UsePressed = true, UseHeld = true };
        private static readonly MotorInput Right = new MotorInput { Move = 1 };
        private static readonly MotorInput Left = new MotorInput { Move = -1 };

        private static SceneSim Begin(string cp)
        {
            var s = new SceneSim(Dl05Scene.Def());
            s.Begin(cp);
            return s;
        }

        private static int Until(SceneSim s, MotorInput input, Func<SceneSim, bool> done, int max = 5000)
        {
            for (int i = 1; i <= max; i++) { s.Step(input); if (done(s)) return i; }
            throw new Xunit.Sdk.XunitException("never: x=" + s.X + " act=" + s.ActKind + ":" + s.ActPhase + " hold=" + s.Motor.Hold);
        }

        private static Pushable Drum(SceneSim s) => s.Graph.Get<Pushable>("dl05.drum");
        private static Pushable Body(SceneSim s) => s.Graph.Get<Pushable>("dl05.body");
        private static WeighScale Scale(SceneSim s) => s.Graph.Get<WeighScale>("dl05.weighIn");
        private static Door Hatch(SceneSim s) => s.Graph.Get<Door>("dl05.hatch");
        private static Door Flag(SceneSim s) => s.Graph.Get<Door>("dl05.servedFlag");

        private static bool UseWouldGrab(SceneSim s, IInteractable target)
            => s.Act == null && s.Motor.PreviewUse(out var c) && c.Verb == Verb.Grab && ReferenceEquals(c.Target, target);

        // ---- The checkpoints' worlds ----------------------------------------------------------------------------------
        [Fact]
        public void Ration_TheDrumAndTheBodyAtTheirStarts_TheHatchShut_L4104_L4107()
        {
            var s = Begin("ration");
            Assert.Equal(48.6, s.X, 12);
            Assert.Equal(53.45, Drum(s).X, 12);
            Assert.Equal(PushableState.Free, Drum(s).State);
            Assert.Equal(52.3, Body(s).X, 12);
            Assert.Equal(PushableState.Free, Body(s).State);
            Assert.Equal(WeighState.Weighing, Scale(s).State);
            Assert.Equal(WeighReading.Empty, Scale(s).Reading);
            Assert.Equal(0, Scale(s).Needle);
            Assert.Equal(0, Hatch(s).Position);
            Assert.Equal(0, Flag(s).Position);
        }

        [Fact]
        public void Hatch_TheDrumAtTheWall_TheBodyOnThePlate_Served_L4104_L4107()
        {
            var s = Begin("hatch");
            Assert.Equal(57.05, s.X, 12);
            Assert.Equal(56.02, Drum(s).X, 12);
            Assert.Equal(PushableState.Docked, Drum(s).State);
            Assert.Equal(54.8, Body(s).X, 12);
            Assert.Equal(PushableState.Docked, Body(s).State);
            Assert.True(Scale(s).Engaged);
            Assert.Equal(WeighReading.Person, Scale(s).Reading);
            Assert.Equal(-140, Scale(s).Needle);
            Assert.Equal(0.64, Hatch(s).Position, 12);
            Assert.Equal(1, Flag(s).Position, 12);
            s.Step(default);
            Assert.True(Scale(s).Engaged);                                         // served is latched: the drum and body stay put
            Assert.Equal(1.0, Scale(s).Load, 12);
        }

        // ---- The hatch in the lane --------------------------------------------------------------------------------------
        /// <summary>Shut, it is a wall from either side (HALF + 0.01 from the wall's foot, L4176–L4178) and a 0.01 ceiling over the crawl (L4165).</summary>
        [Fact]
        public void HatchShut_IsAWall_AndTheCrawlIsClosed_L4165_L4176()
        {
            var s = Begin("ration");
            s.Lane.Limits(55.0, 0, out _, out double right);
            Assert.Equal(56.30 - 0.17 - 0.01, right, 12);
            s.Lane.Limits(57.0, 0, out double left, out _);
            Assert.Equal(56.50 + 0.17 + 0.01, left, 12);
            Assert.Equal(0.01, s.Lane.CeilingAt(56.4), 12);
            Assert.Equal(5.5, s.Lane.CeilingAt(56.05), 12);                         // the crawl is (56.1, 56.7), open ends
            Assert.Equal(5.5, s.Lane.CeilingAt(56.1), 12);
            Assert.Equal(2.4, s.Lane.CeilingAt(60.0), 12);                          // the scanner corridor, L1629
        }

        /// <summary>At its serving height (0.64) there is no wall; the crawl's ceiling is the hatch's edge (L4165, L4176).</summary>
        [Fact]
        public void HatchServed_IsTheCrawlsCeiling_AndNoWall()
        {
            var s = Begin("hatch");
            s.Lane.Limits(55.0, 0, out _, out double right);
            Assert.Equal(Dl05Lane.Region3X + 1, right, 12);
            Assert.Equal(0.64, s.Lane.CeilingAt(56.4), 12);
            var lane = new HatchLane(new FixedHeight(0.62 - 1e-9));                // within 0.02 of 0.64 the wall stands
            double l = 0, r = 100;
            lane.Limits(55.0, 0, ref l, ref r);
            Assert.Equal(56.12, r, 12);
        }

        private sealed class FixedHeight : IPositionSource
        {
            public FixedHeight(double h) { Position = h; }
            public double Position { get; }
        }

        // ---- Core/Push: the drum's two stops, the body's avail ----------------------------------------------------------
        /// <summary>The drum's travel ends on the plate while it stands more than 0.01 short of it, then at the wall (L4277).</summary>
        [Theory]
        [InlineData(53.45, 54.8)]
        [InlineData(54.789, 54.8)]
        [InlineData(54.79, 56.02)]
        [InlineData(54.8, 56.02)]
        public void Drum_StopsOnThePlate_ThenAtTheWall_L4277(double x, double max)
        {
            var drum = new Pushable("dl05.drum", Dl05Scene.DrumParams());
            var body = new Pushable("dl05.body", Dl05Scene.BodyParams());
            var g = Mech.Graph("ration", drum, body);
            drum.MoveTo(x, 0); drum.OnReleased(false); Mech.Run(g, 1);
            Assert.Equal(max, drum.Max, 12);
            Assert.Equal(53.45, drum.Min, 12);
            Assert.False(drum.HasDetents);                                          // he keeps hold at the first stop
        }

        /// <summary>The body stops 1.075 short of the drum ahead of it, and is offered only with more than 0.05 to go (L4280–L4281).</summary>
        [Fact]
        public void Body_StopsShortOfTheDrum_AndIsOfferedOnlyWithRoomToMove_L4280_L4281()
        {
            var drum = new Pushable("dl05.drum", Dl05Scene.DrumParams());
            var body = new Pushable("dl05.body", Dl05Scene.BodyParams());
            var g = Mech.Graph("ration", drum, body);
            var q = new InteractionQuery(53.35, 0, 0, -1, true, false, HoldKind.None, null, null);
            Assert.Equal(53.45 - 0.225 - 0.83 - 0.02, body.Max, 12);               // 52.375
            Assert.True(body.IsAvailable(q));                                       // 0.075 to go
            body.MoveTo(52.33, 0); body.OnReleased(false); Mech.Run(g, 1);
            Assert.False(body.IsAvailable(q));                                      // 0.045
            Assert.False(new PushTwin(body, 0.06).IsAvailable(q));                  // the twin shares avail
            drum.MoveTo(56.02, 0); drum.OnTravelEnd(); Mech.Run(g, 1);
            Assert.Equal(PushableState.Docked, drum.State);
            Assert.Equal(54.8, body.Max, 12);                                       // RH5.bodyPlate
            Assert.True(body.IsAvailable(q));
        }

        // ---- The nearest grip wins (M7) -----------------------------------------------------------------------------------
        /// <summary>
        /// #10227 of the trace: facing left at 53.049, the body's grip (53.35) is 0.30 ahead, the drum's (52.9) 0.15 behind.
        /// The prototype takes the nearest (L4251–L4255); the scene makes sure Core does too.
        /// </summary>
        [Fact]
        public void Use_TakesTheNearestGrip_WhicheverWayHeFaces_L4254()
        {
            var s = new SceneSim(Dl05Scene.Def());
            s.Handover("ration", 53.049394, 0, -1);
            Assert.True(UseWouldGrab(s, Drum(s)));
            s.Handover("ration", 53.2, 0, 1);                                       // body 0.15 behind, drum 0.30 ahead
            Assert.True(UseWouldGrab(s, Body(s)));
        }

        /// <summary>
        /// M7 (U-11, #22): the resolver ranks targets in front of him before those behind for pushables too; the prototype's
        /// push branch has no facing preference (<c>d &lt; best.d</c>, L4254). The scene works round it (<see cref="WeighIn05"/>).
        /// </summary>
        [Fact(Skip = "U-11 issue M7 (#22, still in #25): InteractionResolver ranks in-front targets first for pushables; the prototype's push branch "
            + "takes the nearest grip whatever his facing (nearUse L4251-L4255). Facing left at 53.049 it offers the body (0.30 ahead), not the drum (0.15 behind).")]
        public void Resolver_TakesTheNearestGrip_WhicheverWayHeFaces_L4254()
        {
            var drum = new Pushable("dl05.drum", Dl05Scene.DrumParams());
            var body = new Pushable("dl05.body", Dl05Scene.BodyParams());
            Mech.Graph("ration", drum, body);
            var r = new InteractionResolver();
            r.Register(drum); r.Register(body);
            Assert.True(r.Resolve(new InteractionQuery(53.049394, 0, 0, -1, true, false, HoldKind.None, null, null), out var c));
            Assert.Same(drum, c.Target);
        }

        // ---- The weigh-in, played through ---------------------------------------------------------------------------------
        /// <summary>
        /// From <c>ration</c>: past the drawing (the label check, L4941), push the drum over the plate (it does not stop there:
        /// L4277, L4724) to the wall, where it is set; drag the body (the first grab hesitates 1.6 s, L4466) onto the plate,
        /// where it lies; PERSON held a second serves (L4899), the hatch winds up to 0.64 at 0.22 m/s and the flag drops; 1.6 s
        /// after he let go he pats it (L4731); he crawls under into the kitchen (<c>hatch</c>, L4936) and on into region 3.
        /// </summary>
        [Fact]
        public void TheWeighIn_PlayedThrough()
        {
            var s = Begin("ration");
            Until(s, Right, x => x.ActKind == "quirk");
            Assert.Equal("CheckLabel", s.ActPhase);
            Assert.True(s.X > Dl05Scene.LabelX0);

            // The drum: one push from its start to the wall.
            Until(s, Right, x => UseWouldGrab(x, Drum(x)));
            s.Step(Use);
            Until(s, default, x => x.Motor.Hold == HoldKind.Push);
            int lets = 0;
            bool overSeen = false;
            Until(s, Right, x =>
            {
                overSeen |= Scale(x).Reading == WeighReading.Over;
                if (x.Motor.Hold == HoldKind.None) lets++;
                return x.Motor.Hold == HoldKind.None;
            });
            Assert.Equal(1, lets);
            Assert.True(overSeen);
            Assert.Equal(PushableState.Docked, Drum(s).State);
            Assert.True(Math.Abs(Drum(s).X - 56.02) < 0.005);
            Assert.False(Drum(s).IsAvailable(s.Motor.Query()));

            // The body: back to its rope, the first grab hesitates.
            Until(s, Left, x => UseWouldGrab(x, Body(x)));
            s.Step(Use);
            Until(s, default, x => x.ActKind == "dl05.body" && x.ActPhase == "Hesitate");
            int still = Until(s, default, x => x.ActPhase != "Hesitate");
            Assert.Equal(97, still);                                               // a.t > 1.6: the 97th step after he arrives
            Until(s, default, x => x.Motor.Hold == HoldKind.Push);
            Until(s, Right, x => x.Motor.Hold == HoldKind.None);
            Assert.Equal(PushableState.Docked, Body(s).State);
            Assert.True(Math.Abs(Body(s).X - 54.8) < 0.005);
            Assert.True(Scale(s).Engaged);
            Assert.Equal(WeighReading.Person, Scale(s).Reading);
            Assert.False(double.IsNaN(((WeighIn05)s.Rules).PatAt));

            // The pat, 96 steps after he let go; the hatch winds up; the flag is down.
            int pat = Until(s, default, x => x.ActKind == "quirk");
            Assert.Equal("Pat", s.ActPhase);
            Assert.Equal(96, pat);
            Until(s, default, x => Hatch(x).Engaged);
            Assert.Equal(0.64, Hatch(s).Position, 12);
            Assert.Equal(1, Flag(s).Position, 12);

            // Under the hatch, crouched, into the kitchen; on into region 3.
            bool crouched = false;
            Until(s, Right, x => { crouched |= x.Motor.Crouched && x.X > 56.1 && x.X < 56.7; return x.Checkpoints.Current.Name == "hatch"; });
            Assert.True(crouched);
            Until(s, Right, x => x.Exited);
            Assert.Equal(3, s.Region);
            Assert.True(s.X > Dl05Lane.Region3X);
        }

        /// <summary>He alone reads UNDER; the drum on the plate reads OVER; neither serves (L4891–L4899).</summary>
        [Fact]
        public void HeAlone_ReadsUnder_AndNothingIsServed()
        {
            var s = new SceneSim(Dl05Scene.Def());
            s.Handover("ration", 54.6, 0, 1);
            for (int i = 0; i < 180; i++) s.Step(default);
            Assert.Equal(WeighReading.Under, Scale(s).Reading);
            Assert.Equal(0.2, Scale(s).Load, 12);
            Assert.False(Scale(s).Engaged);
            Assert.Equal(0, Hatch(s).Position);
        }
    }
}
