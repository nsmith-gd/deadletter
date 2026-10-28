using System;
using System.Collections.Generic;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Hazards;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using DeadLetter.Core.Simulation;
using DeathKind = DeadLetter.Core.Hazards.DeathKind;

namespace DeadLetter.Core.Scenes
{
    /// <summary>Which way he crossed a seam (<see cref="ChapterSim.SceneChanged"/>); <see cref="None"/>: he was placed there.</summary>
    public enum ExitDir { None, Left, Right }

    /// <summary>
    /// One chapter, simulated as one world (port_architecture §7, "Core state is global"): D-17's motor on the chapter's
    /// <see cref="LaneGeometry"/> (every scene's tables and contributors, a region per prototype region), one
    /// <see cref="MechanismGraph"/> holding every scene's mechanisms, the <see cref="InteractionResolver"/> over all of
    /// them, and one <see cref="CheckpointService"/>. Nothing freezes when he leaves a scene, a respawn or continue at any
    /// checkpoint rebuilds the whole world there, and no state is handed from scene to scene.
    /// <para>The step, at a fixed 60 Hz in the prototype's order (§3.1, <c>step</c> L8491–L8528):
    /// <list type="number">
    /// <item>#1 the game clock; a pending respawn (<c>respawnAt</c>, L8494).</item>
    /// <item>#4 the player: a running <see cref="SceneAct"/>, else the rules' <see cref="SceneRules.BeforeMotor"/>, the
    /// motor with this step's input, and <see cref="SceneRules.AfterMotor"/>.</item>
    /// <item>#5–#7 every mechanism (the update order below), then <see cref="SceneRules.AfterGraph"/>.</item>
    /// <item>After the mechanisms: an escort that has caught him starts the motor's escorted act, then #9 ride sync
    /// (<see cref="MotorSync"/>; Core/Motor/README.md, "Integrating with a scene simulator").</item>
    /// <item>The seam: the scene that holds him now (<see cref="Current"/>) is committed, and
    /// <see cref="SceneChanged"/> fires if it changed.</item>
    /// </list>
    /// The step hooks run for the scene that held him when the step began, plus every <see cref="SceneRules.Always"/>
    /// rule, in lane order. #2 (input) is the caller's; #3 (the opening timeline), #8–#11 (presentation and audio) are
    /// not Core's. Edge-triggered input is the caller's to clear (#12).</para>
    /// <para><b>Mechanism update order:</b> each scene's own step order (its definition's), scenes in lane order. The
    /// prototype updates by system instead (the relay, <c>updateMechanisms</c>, <c>updateDL02</c>, <c>updateDL03</c> …
    /// <c>updateCh1</c>, <c>updateHazards</c>, L8511–L8518), which interleaves scenes; the two orders step every mechanism
    /// on the same pose and agree because no mechanism reads another scene's (a cross-scene link would have to be added
    /// after its source, which <see cref="MechanismGraph.Build"/> checks). The whole-prologue replay holds to 1e-6 with it.</para>
    /// <para>Time: <see cref="Step"/> always advances exactly 1/60 s (<see cref="StepSeconds"/>), the prototype's
    /// <c>__sim</c> step. <see cref="Advance"/> feeds variable frame time through <see cref="FixedTick"/>, whose 100 ns
    /// quantised step is used only to count steps. A step allocates nothing.</para>
    /// </summary>
    public sealed class ChapterSim
    {
        /// <summary>The fixed step, exactly the prototype's <c>1 / 60</c> (L8473).</summary>
        public const double StepSeconds = 1.0 / 60.0;

        private static readonly MotorInput Crouching = new MotorInput { CrouchHeld = true };

        private readonly SceneDef[] _scenes;
        private readonly SceneRules[] _rules;
        private readonly IMechanism[][] _mechanisms;
        private readonly Dictionary<Type, object> _shared = new Dictionary<Type, object>();
        private readonly List<Cue> _cues = new List<Cue>(8);
        private readonly ISaveStore _store;
        private SceneAct _act;
        private IInteractable _endedTarget;
        private int _current = -1;
        private bool _pendingOpening, _placed;
        /// <summary>The service holds a game (begun, continued or new); until then Begin takes the slot's.</summary>
        private bool _hasGame;

        /// <param name="config">The chapter's motor tuning (null = the prototype's). The motor keeps this instance.</param>
        /// <param name="store">Where the slot is saved (null = nowhere: checkpoints still advance and reload from memory).</param>
        public ChapterSim(ChapterDef def, MotorConfig config = null, ISaveStore store = null)
        {
            Def = def ?? throw new ArgumentNullException(nameof(def));
            int n = def.Scenes.Count;
            _scenes = new SceneDef[n];
            for (int i = 0; i < n; i++) _scenes[i] = def.Scenes[i];

            Graph = new MechanismGraph();
            _mechanisms = new IMechanism[n][];
            for (int i = 0; i < n; i++)
            {
                var s = _scenes[i];
                _mechanisms[i] = new IMechanism[s.Mechanisms.Length];
                for (int j = 0; j < s.Mechanisms.Length; j++)
                {
                    var md = s.Mechanisms[j];
                    var m = md.Create() ?? throw new InvalidOperationException(s.Id + ": factory for " + md.Id + " returned null.");
                    if (!m.Id.Equals(md.Id)) throw new InvalidOperationException(s.Id + ": " + md.Id + " built " + m.Id + ".");
                    _mechanisms[i][j] = Graph.Add(m);
                }
            }
            Graph.Build();
            Lane = BuildLane();

            Config = config ?? MotorConfig.Prototype();

            Resolver = new InteractionResolver(Config);
            for (int i = 0; i < n; i++)
            {
                foreach (var m in _mechanisms[i]) if (m is IInteractable it) Resolver.Register(it);
                var extra = _scenes[i].Interactables?.Invoke(Graph);
                if (extra != null) foreach (var it in extra) Resolver.Register(it);
            }

            Motor = new D17Motor(Config, Lane, Resolver);
            Sync = new MotorSync(Graph);
            _store = store ?? new NoStore();
            Checkpoints = new CheckpointService(Graph, def.Checkpoints.Order, _store, 0, def.Id);
            _rules = new SceneRules[n];
            for (int i = 0; i < n; i++) _rules[i] = _scenes[i].Rules?.Invoke() ?? new SceneRules();
            Tick = new FixedTick(StepSeconds);
            Region = _scenes[0].Region;
        }

        public ChapterDef Def { get; }
        /// <summary>The motor's tuning, the chapter's in every scene (a station's own step-in speed is the station's, <see cref="StationPose.StepInSpeed"/>).</summary>
        public MotorConfig Config { get; }
        public D17Motor Motor { get; }
        /// <summary>Every scene's lane: per region, the scenes' tables joined (<see cref="LaneTable.Join"/>) and all their contributors.</summary>
        public LaneGeometry Lane { get; }
        /// <summary>Every scene's mechanisms, stepped every step in the chapter's update order.</summary>
        public MechanismGraph Graph { get; }
        public InteractionResolver Resolver { get; }
        public CheckpointService Checkpoints { get; }
        public FixedTick Tick { get; }
        /// <summary>The escort hook and #9 ride sync, after the mechanisms (#22).</summary>
        public MotorSync Sync { get; }

        /// <summary>The game clock, seconds (<c>game.clock</c>): +1/60 a step. Settable so a replay can start from a recorded clock.</summary>
        public double Clock { get; set; }
        /// <summary>Steps since the last begin, new game or continue.</summary>
        public long Steps { get; private set; }
        /// <summary>The prototype's <c>game.region</c>: the lane follows it.</summary>
        public int Region { get; private set; }
        /// <summary>Clock time of a pending respawn (<c>game.respawnAt</c>), or 0.</summary>
        public double RespawnAt { get; set; }
        /// <summary>Deaths so far in this simulation (<c>game.deaths</c>, L7437).</summary>
        public int Deaths { get; private set; }
        /// <summary>The scene act running now (null: the motor has him).</summary>
        public SceneAct Act => _act;
        /// <summary>The cues raised this step (music, voices, shots, moments, shakes); cleared at each step's start.</summary>
        public IReadOnlyList<Cue> Cues => _cues;

        // ---- Where he is ----------------------------------------------------------------------------------------------
        /// <summary>
        /// The scene that holds him (<c>sceneName</c>, L8135–L8144), as of the last step's end: the scene of his region whose
        /// [X0, X1) holds his x (the region's first scene also everything left of it, its last everything right of it), then
        /// on past any that <see cref="SceneRules.HasLeft"/>. Null before he is placed and once he is past the chapter's last
        /// scene (<see cref="Exited"/>).
        /// </summary>
        public SceneDef Current => _current >= 0 ? _scenes[_current] : null;
        /// <summary>He is past the chapter's last scene: the motor stops here, and the next chapter takes him on.</summary>
        public bool Exited => _placed && _current < 0;

        /// <summary>
        /// The seam's commit point: fires at the end of the step in which another scene took him (from, to, which way), or
        /// when he is placed in another scene (<see cref="ExitDir.None"/>). To is null when he leaves the chapter.
        /// </summary>
        public event Action<SceneDef, SceneDef, ExitDir> SceneChanged;

        /// <summary>The scene that owns <paramref name="checkpoint"/>, if it is in this chapter (else null).</summary>
        public SceneDef SceneOf(string checkpoint)
        {
            string id = Def.Checkpoints.SceneOf(checkpoint);
            return id == null ? null : Def.Scene(id);
        }

        /// <summary>
        /// <paramref name="checkpoint"/> is placed in this chapter's table and owned by one of its scenes, so <see cref="Begin"/>,
        /// <see cref="Continue"/> and <see cref="Respawn"/> can put him there (a placed row whose scene the chapter lacks cannot).
        /// </summary>
        public bool CanContinueAt(string checkpoint) => CanContinueAt(checkpoint, out _);

        private bool CanContinueAt(string checkpoint, out CheckpointDef cp)
            => Def.Checkpoints.TryGet(checkpoint, out cp) && SceneOf(checkpoint) != null;

        /// <summary>The scene next to <see cref="Current"/> in lane order on the <paramref name="dir"/> side (null: none, or not placed).</summary>
        public SceneDef Next(ExitDir dir)
        {
            if (_current < 0) return null;
            int i = dir == ExitDir.Right ? _current + 1 : dir == ExitDir.Left ? _current - 1 : -1;
            return i >= 0 && i < _scenes.Length ? _scenes[i] : null;
        }

        /// <summary>
        /// Metres from him to <see cref="Current"/>'s edge on the <paramref name="dir"/> side, for streaming the next scene in
        /// (0 when the scene there shares this one's stretch, as DL-07 shares DL-06's floor; +∞ when not placed). A region
        /// seam is at its X too: DL-01 ends where the passage comes out, DL-05 at the corridor.
        /// </summary>
        public double DistanceToSeam(ExitDir dir)
        {
            if (_current < 0 || dir == ExitDir.None) return double.PositiveInfinity;
            var s = _scenes[_current];
            var next = Next(dir);
            if (next != null && next.Region == s.Region && next.X0 == s.X0 && next.X1 == s.X1) return 0;
            return dir == ExitDir.Right ? Math.Max(0, s.X1 - X) : Math.Max(0, X - s.X0);
        }

        /// <summary>The mechanisms <paramref name="scene"/> defines, in its step order: what a scene's view binds to (read-only).</summary>
        public IReadOnlyList<IMechanism> MechanismsOf(SceneDef scene) => _mechanisms[IndexOf(scene)];

        /// <summary>The rules <paramref name="scene"/> runs with.</summary>
        public SceneRules RulesOf(SceneDef scene) => _rules[IndexOf(scene)];

        /// <summary>
        /// The chapter's one <typeparamref name="T"/>: state that more than one scene's rules read or write (the prototype's
        /// <c>game.*</c> fields; DL-03's solve and DL-04's reveal share <c>game.revealed</c>). Made on first use; take it in
        /// <see cref="SceneRules.OnBegin"/> (not per step: this looks it up).
        /// </summary>
        public T Shared<T>() where T : class, new()
        {
            if (!_shared.TryGetValue(typeof(T), out var o)) _shared.Add(typeof(T), o = new T());
            return (T)o;
        }

        // ---- D-17, as the scenes see him -----------------------------------------------------------------------------
        public double X => _act != null && _act.OwnsPose ? _act.X : Motor.X;
        public double Y => _act != null && _act.OwnsPose ? _act.Y : Motor.Y;
        /// <summary>Depth, Unity sign (+ into the set).</summary>
        public double Z => _act != null && _act.OwnsPose ? _act.Z : Motor.Z;
        public double Yaw => _act != null && _act.OwnsPose ? _act.Yaw : Motor.Yaw;
        public double Vx => _act != null && _act.OwnsPose ? 0 : Motor.Vx;
        public double Vy => _act != null && _act.OwnsPose ? 0 : Motor.Vy;
        public bool Grounded => _act != null && _act.OwnsPose ? _act.PoseGrounded : Motor.Grounded;
        /// <summary>In a scene act or a motor act.</summary>
        public bool Busy => _act != null || Motor.IsActing;
        /// <summary>The motor act's phase: <c>None</c> outside one and while a scene act holds him (then see <see cref="SceneActKind"/>, <see cref="SceneActPhase"/>).</summary>
        public ActPhase ActPhase => _act == null && Motor.IsActing ? Motor.ActPhase : ActPhase.None;
        /// <summary>
        /// The scene act's kind (<see cref="SceneAct.Kind"/>; <see cref="ActId.None"/> while the motor has him): what a view
        /// matches, by an integer compare, alongside <see cref="ActPhase"/> (<c>dl06.scanner</c> is <see cref="Dl06.Dl06ScanAct.Scanner"/>).
        /// </summary>
        public ActId SceneActKind => _act != null ? _act.Kind : ActId.None;
        /// <summary>The scene act's phase (<see cref="SceneAct.Phase"/>: <c>Check</c>, a clip, a leg); <see cref="ActId.None"/> outside one.</summary>
        public ActId SceneActPhase => _act != null ? _act.Phase : ActId.None;
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
        // The save is the CheckpointService's: NewGame is the only way to reset the slot; Continue reads it; Begin keeps the
        // game the service holds (or the slot's, the first time) and writes nothing.

        /// <summary>
        /// A new game (Start over, <c>clearLetters</c> L4133; <c>startOpening</c> L8058): flags, seen moments and play time
        /// cleared, the slot written at the first checkpoint, and D-17 there. The only path that resets the slot; only the
        /// chapter whose scene owns the first checkpoint starts one. <paramref name="fromOpening"/>: as <see cref="Begin"/>.
        /// </summary>
        public void NewGame(bool fromOpening = false)
        {
            string first = Def.Checkpoints.Order[0];
            if (!CanContinueAt(first, out var cp))
                throw new InvalidOperationException(Def.Id + " cannot start a new game: '" + first + "' is not one of its scenes'.");
            Checkpoints.NewGame();
            _hasGame = true;
            Start(cp, fromOpening);
        }

        /// <summary>
        /// Continue from the slot (the title card's Continue): its checkpoint, flags, seen moments, play time and options,
        /// the world rebuilt there with the slot's snapshot (any scene's: the chapter is one graph), and D-17 placed at the
        /// checkpoint. False when the slot is empty or unreadable, or when its checkpoint is not one of this chapter's
        /// scenes' (<see cref="SceneOf"/> null: another chapter's, or a scene not ported yet, such as the prologue table's
        /// DL-07 to DL-11 rows): nothing changes then, here or in the slot, and the runtime continues in the chapter that
        /// owns it (<see cref="CanContinueAt"/>).
        /// </summary>
        public bool Continue()
        {
            if (!_store.TryLoad(Checkpoints.Slot, out var m) || m.OptionsOnly) return false;   // options only: nothing to continue (#24)
            if (!CanContinueAt(m.Checkpoint, out var cp)) return false;
            Checkpoints.Load(m);
            _hasGame = true;
            Start(cp, false);
            return true;
        }

        /// <summary>
        /// Builds the world at <paramref name="checkpoint"/>, one of this chapter's scenes' (<c>startPlay</c> →
        /// <c>resetWorld</c>, L8083, L8015), and puts D-17 there. The game is kept: the flags, seen moments, play time and
        /// options the service holds, or, the first time, the slot's (so a chapter begun over a save keeps its calm mode).
        /// Nothing is written. <paramref name="fromOpening"/>: play starts on the opening's last step (L8507), so the first
        /// <see cref="Step"/> is that step (the rules start the label beat there).
        /// </summary>
        public void Begin(string checkpoint, bool fromOpening = false)
        {
            if (!CanContinueAt(checkpoint, out var cp))
                throw new ArgumentException(Def.Id + " has no checkpoint '" + checkpoint + "' in its scenes.", nameof(checkpoint));
            KeepGame();
            Checkpoints.Restart(checkpoint);
            Start(cp, fromOpening);
        }

        /// <summary>
        /// Respawn at the current checkpoint (<c>startPlay(game.checkpoint)</c> when <c>respawnAt</c> passes, L8494): the
        /// whole world reloaded there (and its snapshot), D-17 in that checkpoint's scene, region and lane.
        /// </summary>
        public void Respawn()
        {
            string name = Checkpoints.Current.Name;
            if (!CanContinueAt(name, out var cp)) throw new InvalidOperationException(Def.Id + " cannot respawn at '" + name + "': not one of its scenes' checkpoints.");
            Checkpoints.Reload();
            Place(cp.X, cp.Y, cp.Facing, RegionOf(cp));
            OnBegin(cp.Name, false);
            Commit(placed: true);
        }

        /// <summary>
        /// Tests only (a scene replayed on its own from a recorded rest): <see cref="Begin"/> at <paramref name="checkpoint"/>,
        /// which may be another scene's, but with D-17 at rest at (<paramref name="x"/>, <paramref name="y"/>) in
        /// <paramref name="region"/> (a replay then hands over a moving D-17 with <see cref="D17Motor.SetState"/>); a chapter
        /// never needs this.
        /// </summary>
        internal void BeginAt(string checkpoint, double x, double y, int facing, int region)
        {
            KeepGame();
            Checkpoints.Restart(checkpoint);
            Steps = 0;
            _pendingOpening = false;
            Place(x, y, facing, region);
            OnBegin(checkpoint, false);
            Commit(placed: true);
        }

        private void KeepGame()
        {
            if (!_hasGame) Checkpoints.TryAdoptSlot();
            _hasGame = true;
        }

        private void Start(in CheckpointDef cp, bool fromOpening)
        {
            Steps = 0;
            _pendingOpening = fromOpening;
            Place(cp.X, cp.Y, cp.Facing, RegionOf(cp));
            OnBegin(cp.Name, fromOpening);
            Commit(placed: true);
        }

        private int RegionOf(in CheckpointDef cp) => cp.Region != 0 ? cp.Region : SceneOf(cp.Name)?.Region ?? Region;

        private void Place(double x, double y, int facing, int region)
        {
            _act = null;
            _endedTarget = null;
            RespawnAt = 0;
            SetRegion(region);
            Motor.Place(x, y, facing);
            _placed = true;
        }

        private void OnBegin(string checkpoint, bool fromOpening)
        {
            for (int i = 0; i < _rules.Length; i++) _rules[i].OnBegin(this, checkpoint, fromOpening);
        }

        // ---- What rules do -------------------------------------------------------------------------------------------
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

        /// <summary>Raise a cue for presentation this step.</summary>
        public void Cue(CueId id, int arg = 0) => _cues.Add(new Cue(id, arg));

        /// <summary>
        /// <c>die(how)</c>, L7432–L7442: unless he is already dying he lets go of everything, stops and plays the death
        /// (<see cref="D17Motor.Die"/>), which asks for the respawn at its cut; counted in <see cref="Deaths"/>. Returns
        /// whether he died. <paramref name="sinkRate"/> &gt; 0: he sinks meanwhile (DL-07's sump, <c>game.y −= dt · 0.8</c>,
        /// L7375), which the motor's death cannot do (#28): a <see cref="DeathAct"/> plays it instead.
        /// </summary>
        public bool Die(DeathKind how, double sinkRate = 0)
        {
            if (Motor.IsDead || _act is DeathAct) return false;
            Deaths++;
            if (sinkRate > 0) { DeathAct.Begin(this, how, sinkRate); return true; }
            _act = null;
            var item = Motor.Hold == HoldKind.Item ? Motor.Carried as CarriedItem : null;
            double x = X, y = Y;
            Motor.Die(DeathKinds.ToMotor(how));
            // releaseHolds puts what he carries on the floor at once, unanimated (L7425–L7428); the motor's drop is a
            // set-down applied at the next step, which Drop cancels.
            item?.Drop(x, Math.Max(0, y));
            return true;
        }

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

            if (_pendingOpening)
            {
                _pendingOpening = false;
                for (int i = 0; i < _rules.Length; i++) if (InPlay(i)) _rules[i].OnOpeningEnd(this);
            }

            if (!Exited || _act != null) StepPlayer(input, dt);                             // #4 (past the chapter, only the act that carries him out)
            Graph.Clock = Clock;                                                            // the prototype's game.clock timers
            Graph.Step(dt, Pose);                                                           // #5–#7
            for (int i = 0; i < _rules.Length; i++) if (InPlay(i)) _rules[i].AfterGraph(this);
            if (_act == null || !_act.OwnsPose) Sync.AfterMechanisms(Motor);                // escort start, #9 ride sync (L6399, L2959)
            Commit(placed: false);                                                          // the seam
        }

        private bool InPlay(int i) => i == _current || _rules[i].Always;

        private void StepPlayer(MotorInput input, double dt)
        {
            if (_act == null)
            {
                Motor.SlowWalkLimit = 0;                                                    // paceSlow is decided each step (L2077–L2083)
                for (int i = 0; i < _rules.Length && _act == null; i++) if (InPlay(i)) _rules[i].BeforeMotor(this, ref input);
            }
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
            for (int i = 0; i < _rules.Length; i++) if (InPlay(i)) _rules[i].AfterMotor(this, freeStep);
        }

        // ---- Scenes ----------------------------------------------------------------------------------------------------
        /// <summary>Commits the scene that holds him now; fires <see cref="SceneChanged"/> if it changed.</summary>
        private void Commit(bool placed)
        {
            int next = SceneAt(Region, X);
            if (next == _current) return;
            int from = _current;
            _current = next;
            var dir = placed ? ExitDir.None : next < 0 || next > from ? ExitDir.Right : ExitDir.Left;
            SceneChanged?.Invoke(from >= 0 ? _scenes[from] : null, next >= 0 ? _scenes[next] : null, dir);
        }

        /// <summary>The index of the scene that holds (<paramref name="region"/>, <paramref name="x"/>); −1 past the chapter.</summary>
        private int SceneAt(int region, double x)
        {
            int n = _scenes.Length, first = -1, pick = -1;
            for (int i = 0; i < n; i++)
            {
                var s = _scenes[i];
                if (s.Region != region) { if (first >= 0) break; continue; }
                if (first < 0) first = i;
                if (x >= s.X0 && (pick < 0 || s.X0 > _scenes[pick].X0)) pick = i;      // the last stretch that starts at or before x
            }
            if (first < 0) return region < _scenes[0].Region ? 0 : -1;               // before the chapter's first region, or past its last
            if (pick < 0) pick = first;                                               // left of the region's first scene
            if (x >= _scenes[pick].X1 && IsChapterEnd(pick)) return -1;              // right of its last: the chapter's end
            while (_rules[pick].HasLeft(this))
            {
                if (pick + 1 >= n || _scenes[pick + 1].Region != region) return -1;
                pick++;
            }
            return pick;
        }

        /// <summary>No scene after <paramref name="i"/> starts further on (only ones sharing its stretch, if any).</summary>
        private bool IsChapterEnd(int i)
        {
            for (int j = i + 1; j < _scenes.Length; j++) if (_scenes[j].Region != _scenes[i].Region || _scenes[j].X0 != _scenes[i].X0) return false;
            return true;
        }

        private int IndexOf(SceneDef scene)
        {
            for (int i = 0; i < _scenes.Length; i++) if (ReferenceEquals(_scenes[i], scene)) return i;
            throw new ArgumentException((scene?.Id ?? "null") + " is not a scene of " + Def.Id + ".", nameof(scene));
        }

        private LaneGeometry BuildLane()
        {
            var lane = new LaneGeometry();
            for (int i = 0; i < _scenes.Length;)
            {
                int region = _scenes[i].Region, end = i;
                var tables = new List<LaneTable>();
                var seams = new List<double>();
                for (; end < _scenes.Length && _scenes[end].Region == region; end++)
                {
                    var s = _scenes[end];
                    if (end > i && s.X0 == _scenes[end - 1].X0) continue;                // shares the stretch before it: one lane
                    if (end > i) seams.Add(s.X0);
                    tables.Add(s.Lane?.Invoke() ?? throw new InvalidOperationException(s.Id + " has no lane table."));
                }
                lane.AddRegion(region, tables.Count == 1 ? tables[0] : LaneTable.Join(Def.Id + " (region " + region + ")", tables.ToArray(), seams.ToArray()));
                for (int k = i; k < end; k++)
                {
                    var contributors = _scenes[k].LaneContributors?.Invoke(Graph);
                    if (contributors != null) foreach (var c in contributors) lane.AddContributor(region, c);
                }
                i = end;
            }
            return lane;
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
