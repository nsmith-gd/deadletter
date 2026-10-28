using System;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Scenes.Dl19
{
    /// <summary>
    /// DL-19 A Repair That Held (docs/scenes/DL-19_a_repair_that_held.md; chapter2_plan §4): the half landing droops on a
    /// bent pin. Push the jack into its pocket, crank it level, swap the bent pin for the spare, wind the jack down, draw
    /// it back, and climb onto the half landing and up to the upper terrace. Region 7 from 361.0 (DL-18's end) to the lower
    /// flat's front door at 377.0 (DL-20). No prototype: values cite the doc's sections.
    /// <para>Mechanisms, in step order: the jack (<see cref="RatchetJackParams.Dl19Jack"/>; its push face
    /// <see cref="RatchetJack.Chassis"/> is registered beside it), the pins (<see cref="BracketPinsParams.Dl19Pins"/>) and
    /// the half landing (<see cref="HalfLandingParams.Dl19HalfLanding"/>). The lane is <see cref="Dl19Lane"/>; the rest is
    /// <see cref="Dl19Rules"/>.</para>
    /// </summary>
    public static class Dl19Scene
    {
        public const string Id = "DL-19";

        public const double X0 = Dl19Lane.X0, X1 = Dl19Lane.X1;
        /// <summary>Checkpoints (§9, §11): <c>half_landing</c> on the terrace landing before the jack bay, <c>repaired</c> on the upper terrace.</summary>
        public const double HalfLandingX = 362.0, RepairedX = 371.0;

        public static readonly MechanismId Jack = "dl19.jack", Pins = "dl19.pins", Landing = "dl19.landing";

        /// <summary>The scene definition.</summary>
        public static SceneDef Def() => new SceneDef
        {
            Id = Id,
            Title = "A Repair That Held",
            X0 = X0, X1 = X1,
            Region = Dl19Lane.Region,                                                    // its checkpoints: half_landing, repaired (§9)
            // The jack first (it reads the platform's last load), then the pins, then the platform, which reads both.
            Mechanisms = new[]
            {
                new MechanismDef(Jack, () => new RatchetJack(Jack, RatchetJackParams.Dl19Jack())),
                new MechanismDef(Pins, () => new BracketPins(Pins, BracketPinsParams.Dl19Pins())),
                new MechanismDef(Landing, () => new HalfLanding(Landing, HalfLandingParams.Dl19HalfLanding())),
            },
            Interactables = g => new IInteractable[] { g.Get<RatchetJack>(Jack).Chassis },
            Lane = Dl19Lane.Table,
            LaneContributors = Dl19Lane.Contributors,
            Rules = () => new Dl19Rules(),
        };
    }

    /// <summary>
    /// DL-19's rules:
    /// <list type="bullet">
    /// <item>The checkpoints by position (§9): <c>half_landing</c> on the terrace landing from 362.0, <c>repaired</c> on the
    /// upper terrace (2.3) from 371.0. At <c>half_landing</c> "the jack's position and every pin persist": whenever they come
    /// to rest in a new place with his hands free (and the spare not in them), the checkpoint's snapshot is taken again
    /// (<see cref="Save.CheckpointService.Recapture"/>), so a respawn or a continue finds them there.</item>
    /// <item>Step on (§2, §4, §10): on the half landing's <see cref="HalfLandingEvent.Lurch"/> he teeters, hops back off its
    /// left end and settles (<see cref="Dl19LurchAct"/>); the lane makes the plate's top ground in every state.</item>
    /// <item>Pin first (§2 "Replace me"): the drop onto the stops startles him once he is free (within 1.5 s).</item>
    /// <item>The spare seats (§7, §8): cue <c>held</c>, and the <c>witness</c> insert once.</item>
    /// <item>Curiosities (§6): the drip tube ticks once a minute; the pot (Use, from the pinned half landing's left end): a
    /// close look, 3 s.</item>
    /// </list>
    /// </summary>
    public sealed class Dl19Rules : SceneRules
    {
        /// <summary>The pot (§3: 363.5, pot at 2.0), looked at from the pinned half landing's left end (1.75).</summary>
        public static readonly Station Pot = new Station(standX: 363.75, reach: 0.15, face: 0, floorY: Dl19Lane.LevelY);
        public const double PotFromY = Dl19Lane.LevelY - 0.05;
        /// <summary>The drip tube ticks once a minute (§6, §8); the look lasts 3 s (§6); a drop startles him if he is free within this.</summary>
        public const double DripSeconds = 60, LookSeconds = 3, StartleWithin = 1.5;
        /// <summary>The witness insert plays once (§7).</summary>
        public const string SeenWitness = "witness";

        public static readonly ActId PotKind = ActId.Of("dl19.pot"), Look = ActId.Of("Look");
        public static readonly CueId Drip = CueId.Of("dl19.drip"), PotLook = CueId.Of("dl19.pot.look"), Held = CueId.Of("held"),
            Witness = CueId.Of("witness"), Lurch = CueId.Of("dl19.lurch"), Rock = CueId.Of("dl19.rock"), Bang = CueId.Of("dl19.bang"),
            Settle = CueId.Of("dl19.settle");

        private static readonly BeatAct.Beat[] PotBeats = { new BeatAct.Beat(Look, LookSeconds, PotLook, 0) };

        private RatchetJack _jack;
        private BracketPins _pins;
        private HalfLanding _landing;
        private bool _halfLanding, _repaired;
        private double _nextDrip, _startleUntil = double.NaN;
        private int _witness;
        private (RatchetJackState, double, double, BracketPinsState, HalfLandingState) _kept;

        public RatchetJack Jack => _jack;
        public BracketPins Pins => _pins;
        public HalfLanding Landing => _landing;

        public override void OnBegin(ChapterSim sim, string checkpoint, bool fromOpening)
        {
            _jack = sim.Graph.Get<RatchetJack>(Dl19Scene.Jack);
            _pins = sim.Graph.Get<BracketPins>(Dl19Scene.Pins);
            _landing = sim.Graph.Get<HalfLanding>(Dl19Scene.Landing);
            var cp = sim.Checkpoints.Current;
            _halfLanding = cp.Past("half_landing");
            _repaired = cp.Past("repaired");
            _nextDrip = sim.Clock + DripSeconds;
            _startleUntil = double.NaN;
            _witness = sim.Checkpoints.Seen.Resolve(SeenWitness);
            _kept = Progress();
        }

        /// <summary>Use at the pot, when no mechanism answers.</summary>
        public override void BeforeMotor(ChapterSim sim, ref MotorInput input)
        {
            if (!input.UsePressed || sim.Region != Dl19Lane.Region) return;
            var m = sim.Motor;
            if (m.IsActing || m.IsMantling || m.Hold != HoldKind.None || !m.Grounded || m.PreviewUse(out _)) return;
            var q = m.Query();
            if (!Pot.Answers(q) || q.Y < PotFromY || !_landing.Standable) return;
            input.UsePressed = false;
            m.Stop();
            sim.StartAct(new BeatAct(PotKind, PotBeats));
        }

        public override void AfterGraph(ChapterSim sim)
        {
            var log = sim.Graph.Log;

            // Step on: teeter, hop back, settle (§10 "Wrong path, step on").
            for (int i = 0; i < log.Count; i++)
            {
                var e = log[i];
                if (e.Id != Dl19Scene.Landing || e.Kind != MechanismEventKind.Event) continue;
                if (e.Code == (int)HalfLandingEvent.Lurch && !(sim.Act is Dl19LurchAct))
                {
                    sim.Cue(e.Index == 1 ? Rock : Lurch);
                    double back = _jack.State == RatchetJackState.Parked ? Dl19LurchAct.BackX : Math.Min(Dl19LurchAct.BackX, _jack.X0 - 0.18);
                    sim.StartAct(new Dl19LurchAct(sim.X, sim.Y, sim.Yaw, back, Dl19Lane.FloorY));
                }
                else if (e.Code == (int)HalfLandingEvent.Drop)
                {
                    sim.Cue(Bang);
                    if (e.Index == 0 && Math.Abs(sim.X - _landing.Params.LeftX) < 1.5) _startleUntil = sim.Clock + StartleWithin;   // onto the stops
                }
            }
            if (!double.IsNaN(_startleUntil))
            {
                if (sim.Clock > _startleUntil) _startleUntil = double.NaN;
                else if (SceneQuirk.CanStart(sim)) { _startleUntil = double.NaN; SceneQuirk.Start(sim, ClipNames.Startle, cancel: true); }
            }
            if (log.Has(Dl19Scene.Pins, MechanismEventKind.Event, (int)BracketPinsEvent.Seated))
            {
                sim.Cue(Held);
                if (!sim.Checkpoints.Seen.Get(_witness)) { sim.Cue(Witness); sim.Checkpoints.MarkSeen(SeenWitness); }
            }
            if (sim.Clock >= _nextDrip) { _nextDrip += DripSeconds; sim.Cue(Drip); }

            if (sim.Region != Dl19Lane.Region) return;
            double x = sim.X;
            if (!_halfLanding && x >= Dl19Scene.HalfLandingX && sim.Grounded && Math.Abs(sim.Y - Dl19Lane.FloorY) < 1e-6)
            {
                _halfLanding = true;
                sim.Checkpoints.Reach("half_landing");
                _kept = Progress();
            }
            if (!_repaired && x >= Dl19Scene.RepairedX && sim.Grounded && sim.Y >= Dl19Lane.TerraceY - 1e-9)
            {
                _repaired = _halfLanding = true;
                sim.Checkpoints.Reach("repaired");
            }
            // The jack and the pins persist at half_landing (§9): taken again whenever they rest somewhere new. Not while he
            // holds the spare: "on a respawn a carried spare returns to its clip" (§3), as it was when last taken.
            if (_halfLanding && !_repaired && !sim.Busy && !_jack.Held && _landing.State != HalfLandingState.Falling
                && _pins.State != BracketPinsState.SpareCarried)
            {
                var now = Progress();
                if (!now.Equals(_kept) && sim.Checkpoints.Current.Name == "half_landing")
                {
                    _kept = now;
                    sim.Checkpoints.Recapture();
                }
            }
        }

        private (RatchetJackState, double, double, BracketPinsState, HalfLandingState) Progress()
            => (_jack.State, _jack.X, _jack.Extension, _pins.State, _landing.State);
    }

    /// <summary>
    /// He stepped onto the half landing unpinned (§2 "Step on it", §3 states, §10): <c>Teeter</c> where he stands, a hop
    /// back off its left end onto the terrace landing, then <c>Settle</c> (a 0.3 s knee dip and a servo whine: cue
    /// <c>dl19.settle</c>). It owns his pose, and hands him back to the motor at rest where it put him, facing the landing,
    /// so nothing of it carries into his next jump (§10: "Settle never changes jump distance"). The hop starts 0.6 s in,
    /// within §10's 1.5 s.
    /// </summary>
    public sealed class Dl19LurchAct : SceneAct
    {
        public const double TeeterSeconds = 0.6, HopSeconds = 0.45, SettleSeconds = 0.3, HopHeight = 0.12;
        /// <summary>Where the hop puts him: the mantle spot, his front 5 cm short of the plate's left end (§3: 363.35–363.6).</summary>
        public const double BackX = 363.38;

        public static readonly ActId LandingKind = ActId.Of(Dl19Scene.Landing), Teeter = ActIds.Clip("Teeter"),
            Hop = ActIds.Clip(ClipNames.Hop), SettlePhase = ActId.Of("Settle");

        private readonly double _x0, _y0, _x1, _y1;
        private bool _settled;

        public Dl19LurchAct(double x, double y, double yaw, double backX, double backY) : base(LandingKind, Teeter)
        {
            X = _x0 = x; Y = _y0 = y; Yaw = yaw;
            _x1 = backX; _y1 = backY;
        }

        public override bool OwnsPose => true;
        public override bool PoseGrounded => Phase != Hop;

        public override bool Step(ChapterSim sim, in MotorInput input, double dt)
        {
            T += dt;
            if (T < TeeterSeconds) return true;
            if (T < TeeterSeconds + HopSeconds)
            {
                Phase = Hop;
                double u = (T - TeeterSeconds) / HopSeconds;
                X = _x0 + (_x1 - _x0) * u;
                Y = _y0 + (_y1 - _y0) * u + 4 * HopHeight * u * (1 - u);
                return true;
            }
            X = _x1; Y = _y1;
            if (!_settled) { _settled = true; Phase = SettlePhase; sim.Cue(Dl19Rules.Settle); }
            if (T < TeeterSeconds + HopSeconds + SettleSeconds) return true;
            sim.Motor.Place(_x1, _y1, +1);
            return false;
        }
    }
}
