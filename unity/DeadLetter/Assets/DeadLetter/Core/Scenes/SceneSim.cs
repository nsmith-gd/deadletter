using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using DeadLetter.Core.Simulation;

namespace DeadLetter.Core.Scenes
{
    /// <summary>
    /// One scene, simulated: D-17's motor on the scene's <see cref="LaneGeometry"/>, its <see cref="MechanismGraph"/>, the
    /// <see cref="InteractionResolver"/> over the mechanisms he can use, and the <see cref="CheckpointService"/>, stepped
    /// at a fixed 60 Hz in the prototype's order (port_architecture §3.1, <c>step</c> L8491–L8528):
    /// <list type="number">
    /// <item>#1 the game clock; a pending respawn (<c>respawnAt</c>, L8494).</item>
    /// <item>#4 the player: a running <see cref="SceneAct"/>, else the motor with this step's input, then the scene's
    /// position triggers (<see cref="SceneRules.AfterMotor"/>).</item>
    /// <item>#5–#7 the mechanisms (relays first: the scene definition's order), then
    /// <see cref="SceneRules.AfterGraph"/> (checkpoints and acts that follow a mechanism's transition).</item>
    /// </list>
    /// #2 (input) is the caller's <see cref="MotorInput"/>; #3 (the opening timeline), #8–#11 (presentation and audio)
    /// are not Core's; #9 ride sync has no rides in DL-01. Edge-triggered input is the caller's to clear (#12).
    /// <para>Time: <see cref="Step"/> always advances exactly 1/60 s (<see cref="StepSeconds"/>), the prototype's
    /// <c>__sim</c> step. <see cref="Advance"/> feeds variable frame time through <see cref="FixedTick"/>, whose 100 ns
    /// quantised step is used only to count steps (its 0.0166667 s would drift from the prototype's 1/60 by 2e-8 a step).</para>
    /// </summary>
    public sealed class SceneSim
    {
        /// <summary>The fixed step, exactly the prototype's <c>1 / 60</c> (L8473).</summary>
        public const double StepSeconds = 1.0 / 60.0;

        private static readonly MotorInput Crouching = new MotorInput { CrouchHeld = true };
        private readonly List<string> _cues = new List<string>(4);
        private SceneAct _act;
        private IInteractable _motorTarget, _endedTarget;
        private bool _pendingOpening;

        public SceneSim(SceneDef def, MotorConfig config = null, ISaveStore store = null)
        {
            Def = def ?? throw new ArgumentNullException(nameof(def));
            Config = config ?? def.Motor?.Invoke() ?? MotorConfig.Prototype();

            Graph = new MechanismGraph();
            for (int i = 0; i < def.Mechanisms.Length; i++)
            {
                var m = def.Mechanisms[i].Create() ?? throw new InvalidOperationException(def.Id + ": factory for " + def.Mechanisms[i].Id + " returned null.");
                if (!m.Id.Equals(def.Mechanisms[i].Id)) throw new InvalidOperationException(def.Id + ": " + def.Mechanisms[i].Id + " built " + m.Id + ".");
                Graph.Add(m);
            }
            Graph.Build();

            Lane = new LaneGeometry();
            Lane.AddRegion(def.Region, def.Lane?.Invoke() ?? throw new InvalidOperationException(def.Id + " has no lane table."));
            var contributors = def.LaneContributors?.Invoke(Graph);
            if (contributors != null) foreach (var c in contributors) Lane.AddContributor(def.Region, c);

            Resolver = new InteractionResolver(Config);
            for (int i = 0; i < Graph.Count; i++) if (Graph[i] is IInteractable it) Resolver.Register(it);
            var extra = def.Interactables?.Invoke(Graph);
            if (extra != null) foreach (var it in extra) Resolver.Register(it);

            Motor = new D17Motor(Config, Lane, Resolver);
            Checkpoints = new CheckpointService(Graph, def.CheckpointOrder, store ?? new NoStore(), 0, def.Id);
            Rules = def.Rules?.Invoke() ?? new SceneRules();
            Tick = new FixedTick(StepSeconds);
            Region = def.Region;
        }

        public SceneDef Def { get; }
        public MotorConfig Config { get; }
        public D17Motor Motor { get; }
        public LaneGeometry Lane { get; }
        public MechanismGraph Graph { get; }
        public InteractionResolver Resolver { get; }
        public CheckpointService Checkpoints { get; }
        public SceneRules Rules { get; }
        public FixedTick Tick { get; }

        /// <summary>The game clock, seconds (<c>game.clock</c>): +1/60 a step. Settable so a replay can start from a recorded clock.</summary>
        public double Clock { get; set; }
        /// <summary>Steps since <see cref="Begin"/>.</summary>
        public long Steps { get; private set; }
        /// <summary>The prototype's <c>game.region</c>. The lane follows it while it has that region.</summary>
        public int Region { get; private set; }
        /// <summary>He has left the scene (e.g. DL-01's transit reached region 2); the next scene takes him on.</summary>
        public bool Exited { get; private set; }
        /// <summary>Clock time of a pending respawn (<c>game.respawnAt</c>), or 0.</summary>
        public double RespawnAt { get; set; }
        /// <summary>The scene act running now (null: the motor has him).</summary>
        public SceneAct Act => _act;
        /// <summary>Cue names raised this step (music, voices: "music:hall", "voice:dispatch_item"); cleared each step.</summary>
        public IReadOnlyList<string> Cues => _cues;

        // ---- D-17, as the scene sees him -----------------------------------------------------------------------------
        public double X => _act != null && _act.OwnsPose ? _act.X : Motor.X;
        public double Y => _act != null && _act.OwnsPose ? _act.Y : Motor.Y;
        /// <summary>Depth, Unity sign (+ into the set).</summary>
        public double Z => _act != null && _act.OwnsPose ? _act.Z : Motor.Z;
        public double Yaw => _act != null && _act.OwnsPose ? _act.Yaw : Motor.Yaw;
        public double Vx => _act != null && _act.OwnsPose ? 0 : Motor.Vx;
        public double Vy => _act != null && _act.OwnsPose ? 0 : Motor.Vy;
        public bool Grounded => _act != null && _act.OwnsPose ? _act.PoseGrounded : Motor.Grounded;
        public bool Busy => _act != null || Motor.IsActing;

        /// <summary>
        /// What he is doing, as (kind, phase): a scene act's own; a motor act's target mechanism ID (or "shove", or the
        /// verb) and its <see cref="ActPhase"/>; "mantle"; or (null, null) when he moves freely.
        /// </summary>
        public string ActKind
        {
            get
            {
                if (_act != null) return _act.Kind;
                if (Motor.IsMantling) return "mantle";
                if (!Motor.IsActing) return null;
                if (Motor.ActVerb == Verb.None) return "shove";
                return _motorTarget is IMechanism m ? m.Id.Value : Motor.ActVerb.ToString();
            }
        }

        public string ActPhase => _act != null ? _act.Phase : Motor.IsActing ? Motor.ActPhase.ToString() : null;

        /// <summary>The thing the motor's current act is on (null outside an act). U-11 does not expose it (#22); the scene records it when Use starts one.</summary>
        public IInteractable MotorActTarget => Motor.IsActing ? _motorTarget : null;
        /// <summary>The target of a motor act that ended this step (else null).</summary>
        public IInteractable MotorActEndedOn => _endedTarget;

        /// <summary>D-17 as the mechanisms see him this step (<see cref="StepContext.Player"/>).</summary>
        public PlayerPose Pose => new PlayerPose(X, Y, Z, Motor.Crouched, Busy, Vx, Grounded, Motor.Hold != HoldKind.None);

        // ---- Lifecycle -------------------------------------------------------------------------------------------------
        /// <summary>
        /// Builds the world at <paramref name="checkpoint"/> (<c>startPlay</c> → <c>resetWorld</c>, L8083, L8015) and puts
        /// D-17 there. <paramref name="fromOpening"/>: play starts on the opening's last step (L8507), so the first
        /// <see cref="Step"/> is that step (the rules start the label beat there).
        /// </summary>
        public void Begin(string checkpoint, bool fromOpening = false)
        {
            if (!Def.TryGetCheckpoint(checkpoint, out var cp)) throw new ArgumentException(Def.Id + " has no checkpoint '" + checkpoint + "'.");
            if (checkpoint == Def.CheckpointOrder[0]) Checkpoints.NewGame();
            else Checkpoints.Load(new SaveModel { Checkpoint = checkpoint, Scene = Def.Id });
            Steps = 0;
            Exited = false;
            _pendingOpening = fromOpening;
            Place(cp);
            Rules.OnBegin(this, checkpoint, fromOpening);
        }

        /// <summary>
        /// He walks in from the previous scene (no cut, §2 of the scene docs): the world is built at
        /// <paramref name="checkpoint"/>, which may still be the previous scene's (DL-03 starts under DL-02's <c>room</c>),
        /// and he stands at rest at (<paramref name="x"/>, <paramref name="y"/>). The hand-over of a moving D-17 is the
        /// runtime's (the motor cannot be given a velocity, #22). A respawn needs a checkpoint of this scene.
        /// </summary>
        public void Handover(string checkpoint, double x, double y, int facing = 1)
        {
            if (checkpoint == Def.CheckpointOrder[0]) Checkpoints.NewGame();
            else Checkpoints.Load(new SaveModel { Checkpoint = checkpoint, Scene = Def.Id });
            Steps = 0;
            Exited = false;
            _pendingOpening = false;
            _act = null;
            _motorTarget = _endedTarget = null;
            RespawnAt = 0;
            SetRegion(Def.Region);
            Motor.Place(x, y, facing);
            Rules.OnBegin(this, checkpoint, false);
        }

        /// <summary>Respawn at the current checkpoint (<c>startPlay(game.checkpoint)</c> when <c>respawnAt</c> passes, L8494).</summary>
        public void Respawn()
        {
            Checkpoints.Reload();
            if (!Def.TryGetCheckpoint(Checkpoints.Current.Name, out var cp)) throw new InvalidOperationException(Def.Id + " cannot respawn at " + Checkpoints.Current.Name + ".");
            Place(cp);
            Rules.OnBegin(this, cp.Name, false);
        }

        private void Place(in CheckpointDef cp)
        {
            _act = null;
            _motorTarget = _endedTarget = null;
            RespawnAt = 0;
            SetRegion(cp.Region != 0 ? cp.Region : Def.Region);
            Motor.Place(cp.X, cp.Y, 1);
        }

        /// <summary>Starts a scene act (it replaces any running one). Its first <see cref="SceneAct.Step"/> is the next step's #4.</summary>
        public void StartAct(SceneAct act) => _act = act ?? throw new ArgumentNullException(nameof(act));

        /// <summary>Switches <c>game.region</c> (and the lane, while it has a table for it).</summary>
        public void SetRegion(int region)
        {
            Region = region;
            if (Lane.HasRegion(region)) Lane.Region = region;
        }

        /// <summary>He has left the scene: the motor stops here and the next scene's simulation takes over.</summary>
        public void Exit() => Exited = true;

        /// <summary>Raise a cue for presentation (music, voice) this step.</summary>
        public void Cue(string name) => _cues.Add(name);

        /// <summary>Variable frame time in: steps at 60 Hz with <paramref name="input"/> (read once per step). Returns the steps taken.</summary>
        public int Advance(double frameSeconds, Func<MotorInput> input)
        {
            int n = Tick.Advance(frameSeconds);
            for (int i = 0; i < n; i++) Step(input());
            return n;
        }

        // ---- The step (§3.1) -----------------------------------------------------------------------------------------
        public void Step(in MotorInput input)
        {
            const double dt = StepSeconds;
            _cues.Clear();
            _endedTarget = null;
            Clock += dt;                                                                    // #1, L8493
            Steps++;
            if (RespawnAt > 0 && Clock >= RespawnAt) { RespawnAt = 0; Respawn(); }          // L8494

            if (_pendingOpening) { _pendingOpening = false; Rules.OnOpeningEnd(this); }

            if (!Exited || _act != null) StepPlayer(input, dt);                             // #4 (after the exit, only the act that carries him out)
            Graph.Step(dt, Pose);                                                           // #5–#7
            Rules.AfterGraph(this);
        }

        private void StepPlayer(MotorInput input, double dt)
        {
            if (_act == null) Rules.BeforeMotor(this, ref input);
            if (_act != null)
            {
                var act = _act;
                bool keep = act.Step(this, input, dt);
                if (!act.OwnsPose) Motor.Step(act.Crouch && keep ? Crouching : MotorInput.None, dt);   // he stands; yaw and clip run on
                if (!keep && _act == act) _act = act.Next;
                return;
            }

            bool wasFree = !Motor.IsActing && !Motor.IsMantling && Motor.Hold == HoldKind.None;
            bool wasActing = Motor.IsActing;
            var before = _motorTarget;
            Candidate use = default;
            bool willUse = input.UsePressed && !Motor.IsActing && !Motor.IsMantling && Motor.PreviewUse(out use);

            Motor.Step(input, dt);

            if (Motor.IsActing && !wasActing) _motorTarget = willUse ? use.Target : null;
            // U-11 gap (#22): a station he uses on the lane (StandZ 0) still spends one step in StepIn before its clip
            // (D17Motor.StepAct: Arrived → StepIn; next step → EnterClip). The prototype starts the clip on the step he
            // arrives or finishes turning (updateAct L1846–L1850, L1879). Run that empty step now, so the clip frames and
            // everything keyed to them (the latch's release, the crank's strokes) fall on the prototype's steps. Once
            // the motor enters the clip directly this never triggers.
            if (Motor.IsActing && Motor.ActPhase == global::DeadLetter.Core.Motor.ActPhase.StepIn && _motorTarget is IStation st
                && Math.Abs(st.StandZ - Motor.Z) < Config.ArriveZ)
                Motor.Step(MotorInput.None, dt);
            if (wasActing && !Motor.IsActing) { _endedTarget = before; _motorTarget = null; }
            bool freeStep = wasFree && !Motor.IsActing && !Motor.IsMantling && Motor.Hold == HoldKind.None;
            Rules.AfterMotor(this, freeStep);
        }

        /// <summary>No saving (tests, replays): checkpoints still advance and reload from memory.</summary>
        private sealed class NoStore : ISaveStore
        {
            public bool TryLoad(int slot, out SaveModel model) { model = null; return false; }
            public void Save(int slot, SaveModel model) { }
            public void Delete(int slot) { }
        }
    }
}
