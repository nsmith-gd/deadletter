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
    /// <item>After the mechanisms: an escort that has caught him starts the motor's escorted act, then #9 ride sync
    /// (<see cref="MotorSync"/>; Core/Motor/README.md, "Integrating with a scene simulator").</item>
    /// </list>
    /// #2 (input) is the caller's <see cref="MotorInput"/>; #3 (the opening timeline), #8–#11 (presentation and audio)
    /// are not Core's. Edge-triggered input is the caller's to clear (#12).
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
        private IInteractable _endedTarget;
        private bool _pendingOpening;
        private readonly ISaveStore _store;
        /// <summary>The service holds a game (begun, continued, carried or new); until then Begin takes the slot's.</summary>
        private bool _hasGame;

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
            Sync = new MotorSync(Graph);
            _store = store ?? new NoStore();
            Checkpoints = new CheckpointService(Graph, def.CheckpointOrder, _store, 0, def.Id);
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
        /// <summary>The escort hook and #9 ride sync, after the mechanisms (#22).</summary>
        public MotorSync Sync { get; }

        /// <summary>The game clock, seconds (<c>game.clock</c>): +1/60 a step. Settable so a replay can start from a recorded clock.</summary>
        public double Clock { get; set; }
        /// <summary>Steps since <see cref="Begin"/> (or <see cref="NewGame"/>, <see cref="Continue"/>, <see cref="Handover"/>).</summary>
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
                return Motor.ActTarget is IMechanism m ? m.Id.Value : Motor.ActVerb.ToString();
            }
        }

        /// <summary>
        /// The act's phase: a scene act's own; a motor act's <see cref="ActPhase"/>, or, for a clip the station chained
        /// (#22, <see cref="D17Motor.ActPart"/> &gt; 0: the latch's Flinch), that clip's name.
        /// </summary>
        public string ActPhase => _act != null ? _act.Phase
            : !Motor.IsActing ? null
            : Motor.ActPart > 0 && Motor.ActPhase == global::DeadLetter.Core.Motor.ActPhase.Clip ? Motor.Clip
            : Motor.ActPhase.ToString();

        /// <summary>The thing the motor's current act is on (null outside an act): <see cref="D17Motor.ActTarget"/>.</summary>
        public IInteractable MotorActTarget => Motor.ActTarget;
        /// <summary>The target of a motor act that ended this step (else null).</summary>
        public IInteractable MotorActEndedOn => _endedTarget;

        /// <summary>D-17 as the mechanisms see him this step (<see cref="StepContext.Player"/>).</summary>
        public PlayerPose Pose => _act != null && _act.OwnsPose
            ? new PlayerPose(X, Y, Z, Motor.Crouched, Busy, Vx, Grounded, Motor.Hold != HoldKind.None)
            : _act != null ? new PlayerPose(Motor.X, Motor.Y, Motor.Z, Motor.Crouched, true, Motor.Vx, Motor.Grounded, Motor.Hold != HoldKind.None, Motor.IsHiding, Motor.IsEscorted)
            : PlayerPose.Of(Motor);

        // ---- Lifecycle -------------------------------------------------------------------------------------------------
        // The save is the CheckpointService's: NewGame is the only way to reset the slot; Continue reads it; Begin and
        // Handover keep the game the service holds (or the slot's, the first time), and write nothing themselves.

        /// <summary>
        /// A new game (Start over, <c>clearLetters</c> L4133; <c>startOpening</c> L8058): flags, seen moments and play time
        /// cleared, the slot written at the first checkpoint, and D-17 there. The only path that resets the slot. Only the
        /// scene that owns the first checkpoint (DL-01) starts one. <paramref name="fromOpening"/>: as <see cref="Begin"/>.
        /// </summary>
        public void NewGame(bool fromOpening = false)
        {
            string first = Def.CheckpointOrder[0];
            if (!Def.TryGetCheckpoint(first, out var cp)) throw new InvalidOperationException(Def.Id + " cannot start a new game: '" + first + "' is not its checkpoint.");
            Checkpoints.NewGame();
            _hasGame = true;
            Start(cp, fromOpening);
        }

        /// <summary>
        /// Continue from the slot (the title card's Continue; <see cref="CheckpointService.TryContinue"/>): its checkpoint,
        /// flags, seen moments, play time and options, the world rebuilt there (with the slot's snapshot when it was saved
        /// in this scene), and D-17 placed at the checkpoint (any of <see cref="PrologueCheckpoints"/>). False when the slot
        /// is empty or unreadable; nothing changes then. Throws when the slot's checkpoint has no place to put him.
        /// </summary>
        public bool Continue()
        {
            if (!_store.TryLoad(Checkpoints.Slot, out var m)) return false;
            if (!TryGetPlace(m.Checkpoint, out var cp)) throw new InvalidOperationException(Def.Id + " cannot continue at '" + m.Checkpoint + "'.");
            Checkpoints.Load(m);
            _hasGame = true;
            Start(cp, false);
            return true;
        }

        /// <summary>
        /// Builds the world at <paramref name="checkpoint"/>, one of this scene's (<c>startPlay</c> → <c>resetWorld</c>, L8083,
        /// L8015), and puts D-17 there. The game is kept: the flags, seen moments, play time and options the service holds,
        /// or, the first time, the slot's (so a scene begun over a save keeps its calm mode). Nothing is written.
        /// <paramref name="fromOpening"/>: play starts on the opening's last step (L8507), so the first <see cref="Step"/>
        /// is that step (the rules start the label beat there).
        /// </summary>
        public void Begin(string checkpoint, bool fromOpening = false)
        {
            if (!Def.TryGetCheckpoint(checkpoint, out var cp)) throw new ArgumentException(Def.Id + " has no checkpoint '" + checkpoint + "'.");
            KeepGame(null);
            Checkpoints.Restart(checkpoint);
            Start(cp, fromOpening);
        }

        /// <summary>
        /// He walks in from the previous scene (no cut, §2 of the scene docs): the world is built at
        /// <paramref name="checkpoint"/>, which may still be the previous scene's (DL-03 starts under DL-02's <c>room</c>),
        /// and he stands at rest at (<paramref name="x"/>, <paramref name="y"/>). <paramref name="carry"/>: the previous
        /// scene's service, whose game (flags, seen moments, play time, options) goes on here; it is flushed first. Without
        /// it the game is kept as <see cref="Begin"/> keeps it. Nothing is written. A moving D-17 is handed over by setting the
        /// motor's state after this (<see cref="D17Motor.SetState"/>).
        /// </summary>
        public void Handover(string checkpoint, double x, double y, int facing = 1, CheckpointService carry = null)
        {
            KeepGame(carry);
            Checkpoints.Restart(checkpoint);
            Steps = 0;
            Exited = false;
            _pendingOpening = false;
            _act = null;
            _endedTarget = null;
            RespawnAt = 0;
            SetRegion(Def.Region);
            Motor.Place(x, y, facing);
            Rules.OnBegin(this, checkpoint, false);
        }

        /// <summary>
        /// Respawn at the current checkpoint (<c>startPlay(game.checkpoint)</c> when <c>respawnAt</c> passes, L8494): any
        /// checkpoint of <see cref="PrologueCheckpoints"/>, including the previous scene's he walked in under.
        /// </summary>
        public void Respawn()
        {
            if (!TryGetPlace(Checkpoints.Current.Name, out var cp)) throw new InvalidOperationException(Def.Id + " cannot respawn at " + Checkpoints.Current.Name + ".");
            Checkpoints.Reload();
            Place(cp);
            Rules.OnBegin(this, cp.Name, false);
        }

        /// <summary>Where <paramref name="name"/> puts him: this scene's checkpoint, else the chapter's table.</summary>
        public bool TryGetPlace(string name, out CheckpointDef cp) => Def.TryGetCheckpoint(name, out cp) || PrologueCheckpoints.TryGet(name, out cp);

        private void KeepGame(CheckpointService carry)
        {
            if (carry != null && !ReferenceEquals(carry, Checkpoints))
            {
                carry.Flush();
                Checkpoints.Adopt(carry.ToModel());
            }
            else if (!_hasGame) Checkpoints.TryAdoptSlot();
            _hasGame = true;
        }

        private void Start(in CheckpointDef cp, bool fromOpening)
        {
            Steps = 0;
            Exited = false;
            _pendingOpening = fromOpening;
            Place(cp);
            Rules.OnBegin(this, cp.Name, fromOpening);
        }

        private void Place(in CheckpointDef cp)
        {
            _act = null;
            _endedTarget = null;
            RespawnAt = 0;
            SetRegion(cp.Region != 0 ? cp.Region : Def.Region);
            Motor.Place(cp.X, cp.Y, cp.Facing);
        }

        /// <summary>Starts a scene act (it replaces any running one). Its first <see cref="SceneAct.Step"/> is the next step's #4.</summary>
        public void StartAct(SceneAct act) => _act = act ?? throw new ArgumentNullException(nameof(act));

        /// <summary>
        /// Ends the running scene act now, from a rule after the mechanisms (the prototype clearing <c>game.act</c> in #6:
        /// DL-06's scanner ends the scan and the label check, L2799, L2812). The next step's #4 is the motor's again; an act
        /// that owned his pose leaves it to the rule to hand back (<see cref="D17Motor.Place"/>).
        /// </summary>
        public void EndAct() => _act = null;

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
            if (_act == null || !_act.OwnsPose) Sync.AfterMechanisms(Motor);                // escort start, #9 ride sync (L6399, L2959)
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
            var before = Motor.ActTarget;

            Motor.Step(input, dt);

            // The motor's stuck and death acts ask for the reload themselves (#22).
            if (Motor.RespawnDue(out double delay) && !(RespawnAt > 0)) RespawnAt = Clock + delay;
            if (wasActing && !Motor.IsActing) _endedTarget = before;
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
