using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Push;

namespace DeadLetter.Core.Scenes.Dl03
{
    /// <summary>
    /// DL-03 The Weight of the Job (port_architecture §5; docs/scenes/DL-03_the_weight_of_the_job.md): the plate opens the
    /// gate only while something heavy enough stands on it; the weight carried onto the trolley and the trolley pushed
    /// onto the plate hold it open without him. Region 2 from the sill (<c>SH.x1</c> 25.0) to the gate (30.6), where DL-04
    /// begins (<c>sceneName</c>, L8139). Lines are index.html at 7b3c123 (<c>buildDL02/updateDL02</c>: module names lag).
    /// </summary>
    public static class Dl03Scene
    {
        public const string Id = "DL-03";

        /// <summary><c>SH.x1</c> (L3887): DL-02 ends, DL-03 begins (L8139).</summary>
        public const double X0 = 25.0;
        /// <summary><c>GATE_X</c> (L323): DL-04 begins at x ≥ GATE_X (L8139).</summary>
        public const double GateX = Dl03Lane.GateX, GateOpenH = 1.2;
        /// <summary>The <c>weighroom</c> checkpoint once he is on the floor past OFF2 + 12.6 (L4946).</summary>
        public const double WeighroomX = 13 + 12.6;
        /// <summary><c>TROLLEY_HALF</c>, <c>WEIGHT_R</c>, <c>GRIP_FWD</c> (L320–L321); <c>EXIT2_X</c> = OFF2 + 25.6 (L329).</summary>
        public const double TrolleyHalf = 0.28, WeightR = 0.1, GripFwd = 0.29, Exit2X = 13 + 25.6;
        /// <summary>Set-down on the deck: within TROLLEY_HALF + 0.02 of its centre, clamped to ±0.17 (L2264, L2269).</summary>
        public const double DeckReach = TrolleyHalf + 0.02, DeckClamp = 0.17;

        /// <summary>The scene definition.</summary>
        public static SceneDef Def() => new SceneDef
        {
            Id = Id,
            Title = "The Weight of the Job",
            X0 = X0, X1 = GateX,
            Region = Dl03Lane.Region,
            Checkpoints = PrologueCheckpoints.Of(Id),                                     // weighroom, solved (L7981–L7982); he walks in under DL-02's room
            // Step order = the prototype's: updatePlayer moves the trolley and the weight (#4), then updateDL02 weighs the
            // plate and moves the gate (#6, L2364–L2392).
            Mechanisms = new[]
            {
                new MechanismDef("dl03.trolley", () => new Pushable("dl03.trolley", PushableParams.Dl03Trolley())),
                new MechanismDef("dl03.weight", () => new Dl03Weight("dl03.weight")),
                new MechanismDef("dl03.plate", () => new LoadPlate("dl03.plate", LoadPlateParams.Dl03Plate())),
                new MechanismDef("dl03.gate", () => new FollowerActuator("dl03.gate", FollowerParams.Dl03Gate())),
            },
            Interactables = g => new IInteractable[] { new PushTwin(g.Get<Pushable>("dl03.trolley")) },   // grabR, L2256
            Lane = Dl03Lane.Table,
            LaneContributors = Dl03Lane.Contributors,
            Rules = () => new Dl03Rules(),
        };
    }

    /// <summary>
    /// DL-03's bespoke rules: <c>standFree</c> for the weight's and the trolley's stand points (L2239–L2242); the set-down
    /// in front of him, onto the deck or clear floor, or refused (<c>beginSetDown</c>, L2261–L2271); the solved checkpoint
    /// once the plate holds without him (L2394–L2397); the reveal on passing the gate (L2399–L2402); the gate's slam
    /// startling him (L2387, <c>playQuirk</c> L3841); the <c>weighroom</c> checkpoint (L4946); and the way on into DL-04
    /// (<c>sceneName</c>, L8139).
    /// </summary>
    public sealed class Dl03Rules : SceneRules
    {
        private Pushable _trolley;
        private Dl03Weight _weight;
        private LoadPlate _plate;
        private FollowerActuator _gate;
        private bool _revealed, _revealPending;

        /// <summary>The racks have been revealed (<c>game.revealed</c>); the cue waits until he passes the gate (pass 5).</summary>
        public bool Revealed => _revealed;
        public bool RevealPending => _revealPending;

        public override void OnBegin(SceneSim sim, string checkpoint, bool fromOpening)
        {
            _trolley = sim.Graph.Get<Pushable>("dl03.trolley");
            _weight = sim.Graph.Get<Dl03Weight>("dl03.weight");
            _plate = sim.Graph.Get<LoadPlate>("dl03.plate");
            _gate = sim.Graph.Get<FollowerActuator>("dl03.gate");
            Func<double, bool> free = x => StandFree(sim, x);
            _trolley.CanStandAt = free;
            _weight.CanStandAt = free;
            _revealed = sim.Checkpoints.Current.Past("solved");                                     // game.revealed = !!c.solved, L8027
            _revealPending = false;
        }

        /// <summary>
        /// <c>standFree</c> (L2239–L2242): inside the room (ROOM_LEFT up to his right limit) and nothing under the stand
        /// point's feet (support &lt; 0.05). The limit is the one where he stands now (<c>rightLimit()</c> reads game.x).
        /// </summary>
        public static bool StandFree(SceneSim sim, double x)
        {
            sim.Lane.Limits(sim.Motor.X, sim.Motor.Y, out _, out double right);
            if (x < Dl03Lane.RoomLeft || x > right) return false;
            return sim.Lane.SupportAt(x) < 0.05;
        }

        /// <summary>
        /// Use while carrying the weight (<c>nearUse2</c> → <c>'setdown'</c>, L2246; <c>beginSetDown</c>, L2261–L2271): in front
        /// of him GRIP_FWD on, onto the deck if the trolley is there, else onto clear floor away from the trolley and the
        /// gate; neither: he refuses (<c>Sound.worried</c>). The motor never refuses a lane set-down and has no deck, so the
        /// rules take the Use (U-11 gap, #22).
        /// </summary>
        public override void BeforeMotor(SceneSim sim, ref MotorInput input)
        {
            var m = sim.Motor;
            if (!input.UsePressed || m.IsActing || m.IsMantling || !m.Grounded || m.Hold != HoldKind.Item || m.Carried != _weight) return;
            double tx = m.X + m.Facing * Dl03Scene.GripFwd, d = Math.Abs(tx - _trolley.X);
            bool onDeck = d <= Dl03Scene.DeckReach;
            bool floorOk = !onDeck && d > Dl03Scene.TrolleyHalf + Dl03Scene.WeightR + 0.01 && tx > Dl03Lane.RoomX0 + 0.15
                && Math.Abs(tx - Dl03Scene.GateX) > 0.2 && tx < Dl03Scene.Exit2X;
            if (!onDeck && !floorOk)
            {
                // Refused: no act; he stops dead and the step ends there (game.vx = 0, L1821; return, L1962).
                input = MotorInput.None;
                m.Stop();
                sim.Cue("sound:worried");
                return;
            }
            double target = onDeck ? _trolley.X + Smooth.Clamp(tx - _trolley.X, -Dl03Scene.DeckClamp, Dl03Scene.DeckClamp) : tx;
            sim.StartAct(new Dl03SetDownAct(_weight, _trolley, onDeck, target, m.X, m.Y, m.Yaw, m.Facing, sim.Config.YawRate));
        }

        public override void AfterGraph(SceneSim sim)
        {
            // updateDL02 (#6), in its order. The gate's slam startles him (L2387): playQuirk's own conditions (L3842), and
            // it stops him (game.vx = 0, L3843).
            if (sim.Graph.Log.Has("dl03.gate", MechanismEventKind.Event, (int)FollowerEvent.Startle) && sim.Act == null && !sim.Exited)
            {
                var m = sim.Motor;
                if (!m.IsActing && !m.IsMantling && m.Hold == HoldKind.None && m.Grounded)
                {
                    m.Stop();                                                                     // game.vx = 0
                    sim.StartAct(new QuirkAct("Startle", QuirkAct.ClipSeconds("Startle"), cancel: true, startClock: sim.Clock));
                }
            }
            // Solved once the plate holds without him and the gate has wound up to that (L2394–L2397).
            if (!_revealed && _plate.SolvedWith(_gate.Position, Dl03Scene.GateOpenH))
            {
                _revealed = true; _revealPending = true;
                sim.Checkpoints.Reach("solved");
            }
            // The reveal plays the moment he is through the gate, however it was opened (L2399–L2402).
            if ((_revealPending || !_revealed) && sim.Region == Dl03Lane.Region && sim.X > Dl03Scene.GateX + 0.2)
            {
                _revealed = true; _revealPending = false;
                sim.Checkpoints.Reach("solved");
                sim.Cue("music:racks");
            }
            // updateCh1 (#7): the weighroom checkpoint (L4946).
            if (sim.Region == Dl03Lane.Region && sim.X > Dl03Scene.WeighroomX && sim.Y < 0.05) sim.Checkpoints.Reach("weighroom");
            // sceneName (L8139): past the gate is DL-04.
            if (!sim.Exited && sim.X >= Dl03Scene.GateX) sim.Exit();
        }
    }

    /// <summary>
    /// Setting the weight down (<c>beginSetDown</c>/<c>updateAct2</c>, L2261–L2287): SetDownHigh onto the deck or SetDown
    /// onto the floor, played where he stands. f14 it leaves his hands, onto the deck at its offset from the trolley's
    /// centre or onto the floor at the spot; f21 a pat; f35 his hands are free. He does not move meanwhile (vx = 0, L1821);
    /// his yaw settles on his facing (<c>updateCharacter</c>). It owns his pose: the motor's carry would let him drift.
    /// At the end the motor is put back at rest with empty hands (<see cref="D17Motor.Place"/>: U-11 has no other way to
    /// end a carry, #22).
    /// </summary>
    public sealed class Dl03SetDownAct : SceneAct
    {
        /// <summary>SetDown events (L2283, L2285, L2286).</summary>
        public const double ReleaseFrame = 14, PatFrame = 21, DoneFrame = 35;

        private readonly Dl03Weight _weight;
        private readonly Pushable _trolley;
        private readonly double _targetX, _yawRate;
        private readonly int _facing;
        private bool _fresh = true, _released, _patted;

        public Dl03SetDownAct(Dl03Weight weight, Pushable trolley, bool onDeck, double targetX, double x, double y, double yaw, int facing, double yawRate)
            : base(weight.Id.Value, onDeck ? ClipNames.SetDownHigh : ClipNames.SetDown)
        {
            _weight = weight; _trolley = trolley; OnDeck = onDeck; _targetX = targetX; _facing = facing; _yawRate = yawRate;
            X = x; Y = y; Z = 0; Yaw = yaw;
        }

        public bool OnDeck { get; }
        public override bool OwnsPose => true;

        public override bool Step(SceneSim sim, in MotorInput input, double dt)
        {
            bool keep = true;
            if (_fresh) _fresh = false;                                     // the clip starts this step (time 0)
            else
            {
                T += dt;                                                    // the mixer advances before updatePlayer reads it
                double f = T * 24;                                          // actions[clip].time * FPS
                if (f >= ReleaseFrame && !_released)                        // L2283–L2286
                {
                    _released = true;
                    if (OnDeck) _weight.OnSetDownOnTrolley(_targetX - _trolley.X);
                    else _weight.OnSetDown(_targetX, 0);
                    sim.Cue(OnDeck ? "sound:setDownHigh" : "sound:setDown");
                }
                if (f >= PatFrame && !_patted) { _patted = true; sim.Cue("sound:knock"); }
                if (f >= DoneFrame) keep = false;                           // L2287
            }
            Yaw = Smooth.MoveTowards(Yaw, _facing * Math.PI / 2, _yawRate * dt);
            if (!keep) sim.Motor.Place(X, Y, _facing);                     // hold = null, Idle
            return keep;
        }
    }
}
