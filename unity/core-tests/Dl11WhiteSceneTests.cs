using System.Collections.Generic;
using DeadLetter.Core.Beings;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Motor;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-11's first meeting with the White on the flooded lane (§4.15, §5 DL-11; L7234–L7273, L7096–L7198, L1921–L1929),
    /// with the real motor in the pipeline order: careful rule, motor #4, senses, graph (#8). Walking along the lane is
    /// quiet and safe; running is heard: the first find is a warning, after that it strikes.
    /// </summary>
    public class Dl11WhiteSceneTests
    {
        private const double Dt = Mech.Dt;
        private const string Id = "dl11.white";

        private sealed class Scene
        {
            public readonly MechanismGraph G = new MechanismGraph();
            public readonly BeingSenses Senses = new BeingSenses { Region = 5 };
            public readonly WhiteBrain White;
            public readonly D17Motor Motor;
            public readonly List<MechanismEvent> Log = new List<MechanismEvent>();
            public double MaxSpeedNearWater;
            public bool Dead;

            public Scene(double x)
            {
                White = G.Add(new WhiteBrain(Id, WhiteParams.Dl11(), Senses));
                G.Build();
                G.Reset(Checkpoint.Prototype("ringc"));
                Motor = Sim.Make(BoxWorld.Flat(100, 200), x, 0);
            }

            /// <summary>Respawn at the checkpoint (ringc, 135.25; L7998).</summary>
            public void Respawn(double x)
            {
                G.Reset(Checkpoint.Prototype("ringc"));
                Motor.Place(x, 0);
                Senses.Alive = true; Dead = false;
            }

            public void Step(MotorInput input)
            {
                Senses.BeginStep();
                Motor.Careful = White.WantsCareful(Motor.X);                 // wantsRun reads last step's water (L1925)
                if (!Dead) Motor.Step(input, Dt);
                Senses.ReadMotor(Motor);
                G.Step(Dt, Mech.Pose(Motor));
                Log.AddRange(Mech.Events(G));
                if (Motor.X > 145.95 - 1.4 && Motor.X < 150.6 + 1.4 && Motor.Grounded)
                    MaxSpeedNearWater = System.Math.Max(MaxSpeedNearWater, System.Math.Abs(Motor.Vx));
                if (Mech.Emitted(G, Id, WhiteEvent.Grab)) { Dead = true; Senses.Alive = false; }   // die('grabbed'): the death act
            }

            /// <summary>Holds right until he is past the lane (or dead). Returns the steps taken.</summary>
            public int CrossLane(MotorInput input, int max = 3000)
            {
                for (int i = 1; i <= max; i++)
                {
                    Step(input);
                    if (Dead || Motor.X > 154) return i;
                }
                return -1;
            }

            public int Count(WhiteEvent e) => Log.FindAll(x => x.Kind == MechanismEventKind.Event && x.Code == (int)e).Count;
            public int HeardHim() => Log.FindAll(x => x.Kind == MechanismEventKind.Event && x.Code == (int)WhiteEvent.Heard && x.Index == 1).Count;
            public bool EverIn(WhiteState s) => Log.Exists(x => x.Kind == MechanismEventKind.State && x.Code == (int)s);
        }

        private static MotorInput Walk => Sim.Move(1);                       // auto-run on: the careful rule walks him
        private static MotorInput Run => new MotorInput { Move = 1, RunModifierHeld = true };   // auto-run off + Shift

        [Fact]
        public void WalkingAlongTheLane_FromTheCheckpoint_IsQuiet_AndItNeverComesForHim()
        {
            var s = new Scene(135.25);                                         // ringc, past the barricade (L7998)
            s.White.Warned = true;                                             // even after a warning
            Assert.True(s.CrossLane(Walk) > 0);
            Assert.False(s.Dead);
            var shown = s.Log.Find(e => e.Kind == MechanismEventKind.Event && e.Code == (int)WhiteEvent.Shown);
            Assert.InRange(shown.Tick, 410, 430);                              // x > 145.3 after ~11 s of walking
            Assert.InRange(s.MaxSpeedNearWater, 0, 1.25);                      // never above (WALK+RUN)/2 near the water
            Assert.Equal(1, s.Count(WhiteEvent.Shown));                        // it shows itself far off (L7271)
            Assert.Equal(0, s.HeardHim());
            Assert.False(s.EverIn(WhiteState.Approach));
            Assert.Equal(0, s.Count(WhiteEvent.Warn) + s.Count(WhiteEvent.Grab));
        }

        [Fact]
        public void RunningAlongTheLane_TheFirstMeetingWarns_AndAfterThatItStrikes()
        {
            var s = new Scene(135.25);
            s.Motor.AutoRun = false;
            Assert.True(s.CrossLane(Run) > 0);
            Assert.False(s.Dead);                                              // the first find is only a warning (L7150)
            Assert.True(s.HeardHim() > 0);
            Assert.True(s.MaxSpeedNearWater > 1.25);
            Assert.Equal(1, s.Count(WhiteEvent.Warn));
            Assert.True(s.White.Warned);
            var warn = s.Log.Find(e => e.Kind == MechanismEventKind.Event && e.Code == (int)WhiteEvent.Warn);
            Assert.Equal(0, s.Count(WhiteEvent.Grab));

            // He comes back (respawned at ringc, or walked back): the warning persists, and this time it strikes.
            s.Respawn(135.25);
            Assert.True(s.White.Warned);
            int steps = s.CrossLane(Run);
            Assert.True(steps > 0);
            Assert.True(s.Dead);
            Assert.True(s.EverIn(WhiteState.Strike));
            Assert.Equal(1, s.Count(WhiteEvent.Grab));
            Assert.InRange(s.Motor.X, 145.7, 150.6);                           // taken from the bank
            for (int i = 0; i < 40; i++) s.Step(Run);
            Assert.Equal(1, s.Count(WhiteEvent.Drag));
            Assert.True(warn.Tick < s.Log.Find(e => e.Kind == MechanismEventKind.Event && e.Code == (int)WhiteEvent.Grab).Tick);
        }

        /// <summary>
        /// Prototype quirk, ported as is: the sighting puts its snout at 149.9 but the body clamp (L7183–L7186) uses the
        /// way it already faces. Facing −x (here it is still gliding toward its first target), the snout lands at 148.6,
        /// and a walker (0.9 m/s) from 145.3 comes within reach 1.35 after 2.17 s, inside the 2.2 s surface window: the
        /// first time it warns him, after a warning it takes him. Walking is only safe when it faces +x at the sighting.
        /// </summary>
        [Fact]
        public void TheSighting_FacingMinusX_ReachesEvenAWalker_PrototypeQuirk_L7154_L7183_L7271()
        {
            var s = new Scene(140.0);
            Assert.True(s.CrossLane(Walk) > 0);
            Assert.Equal(0, s.HeardHim());                                     // he was quiet all along
            var shown = s.Log.Find(e => e.Kind == MechanismEventKind.Event && e.Code == (int)WhiteEvent.Shown);
            Assert.Equal(1, s.Count(WhiteEvent.Warn));
            Assert.False(s.Dead);
            var warn = s.Log.Find(e => e.Kind == MechanismEventKind.Event && e.Code == (int)WhiteEvent.Warn);
            Assert.InRange((warn.Tick - shown.Tick) * Dt, 2.1, 2.2);

            s.Respawn(140.0);
            Assert.True(s.CrossLane(Walk) > 0);
            Assert.True(s.Dead);
            Assert.Equal(1, s.Count(WhiteEvent.Grab));
        }

        [Fact]
        public void TheScene_IsDeterministic()
        {
            var dumps = new List<string>[2];
            for (int r = 0; r < 2; r++)
            {
                var s = new Scene(140.0);
                s.Motor.AutoRun = false;
                var d = dumps[r] = new List<string>();
                for (int i = 0; i < 900; i++)
                {
                    s.Step(i % 400 < 250 ? Run : Sim.Move(-1));
                    d.Add(Sim.Snapshot(s.Motor) + "#" + Mech.Dump(s.G));
                }
            }
            Assert.Equal(dumps[0], dumps[1]);
        }
    }
}
