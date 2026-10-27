using System;
using System.Collections.Generic;
using DeadLetter.Core.Camera;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Scenes
{
    /// <summary>
    /// Builds a <see cref="SceneDefinition"/> and runs it one fixed 60 Hz step at a time in the prototype's order
    /// (port_architecture §3.1, <c>step</c> L8491–L8528):
    /// <list type="number">
    /// <item>#1 clock; a pending respawn reloads the checkpoint (L8493–L8494).</item>
    /// <item>#3 input gate: a directed moment (or the opening) withholds control (<see cref="MomentDirector"/>); a pending
    /// respawn does too. When control comes back, <see cref="SceneDefinition.OnControlReturned"/> (DL-01's label check).</item>
    /// <item>#4 motor (acts feed their stations here); its <see cref="MotorEventKind.RespawnDue"/> (the stuck and death
    /// acts) schedules the reload, its shakes shake the camera.</item>
    /// <item>#5–#7 mechanisms (with <see cref="PlayerPose.Of"/> the motor), then the scene's own rules
    /// (<see cref="SceneDefinition.AfterMechanisms"/>); an <see cref="IEscort"/> that wants him starts the escorted act;
    /// #9 ride sync (<see cref="D17Motor.SyncRide"/>, and each <see cref="ILiftRide"/> that carries him).</item>
    /// <item>checkpoints (they are set inside the prototype's player and act updates, i.e. before the camera), cues,
    /// moment triggers, the exit.</item>
    /// <item>#10 camera (the opening move, then the lane rig).</item>
    /// </list>
    /// Everything is Core state, exposed read-only for Runtime adapters and tests. Allocation-free per step, except on a
    /// step that reaches a checkpoint (the save) or reloads. Deterministic: the same definition, save store contents and
    /// input sequence give the same states bit for bit.
    /// </summary>
    public sealed class SceneRunner
    {
        public const double StepSeconds = 1.0 / 60.0;
        private const int Fps = 24;

        private readonly CheckpointRule[] _rules;
        private readonly int[] _ruleIndex;
        private readonly IEngageable[] _ruleSource;
        private readonly CueRule[] _cueRules;
        private readonly IEngageable[] _cueWhen, _cueUnless;
        private readonly bool[] _cueHeard;
        private readonly MomentRule[] _momentRules;
        private readonly IEngageable[] _momentWhen;
        private readonly int[] _momentSeen;
        private readonly ILiftRide[] _lifts;
        private readonly IEscort[] _escorts;
        private readonly IEngageable _exitOpen;
        private readonly List<string> _cues = new List<string>(8);
        private readonly IMusicClock _music;

        private int _cpIndex;
        private bool _inStep, _carry;
        private double _respawnAt = double.NaN;
        private bool _opening, _skippedOpening;
        private double _openingStart;

        public SceneRunner(SceneDefinition definition, ISaveStore store, int slot = 0, IMusicClock music = null,
            MotorConfig motor = null, CameraConfig camera = null)
        {
            Definition = definition ?? throw new ArgumentNullException(nameof(definition));
            _music = music;
            MotorConfig mc = motor ?? MotorConfig.Prototype();

            Graph = new MechanismGraph();
            definition.AddMechanisms(Graph);
            Graph.Build();
            Graph.Reset(new Checkpoint(definition.CheckpointOrder, definition.FirstCheckpoint));   // a valid world before any load
            Resolver = new InteractionResolver(mc);
            definition.RegisterInteractables(Graph, Resolver);
            Lane = definition.BuildLane(Graph) ?? throw new InvalidOperationException(definition.Id + ": BuildLane returned null.");
            Motor = new D17Motor(mc, Lane, Resolver);
            Checkpoints = new CheckpointService(Graph, definition.CheckpointOrder, store ?? throw new ArgumentNullException(nameof(store)), slot, definition.Id);
            Checkpoints.Reloaded += OnReloaded;
            Moments = new MomentDirector(music);
            Camera = new CameraRig(camera ?? CameraConfig.Prototype, definition.BuildFraming());

            var rules = definition.CheckpointRules;
            _rules = new CheckpointRule[rules.Count];
            _ruleIndex = new int[rules.Count];
            _ruleSource = new IEngageable[rules.Count];
            for (int i = 0; i < rules.Count; i++)
            {
                _rules[i] = rules[i];
                _ruleIndex[i] = Checkpoints.IndexOf(rules[i].Checkpoint);
                if (rules[i].Kind == CheckpointRuleKind.Engaged) _ruleSource[i] = Engageable(rules[i].Source, "checkpoint " + rules[i].Checkpoint);
            }

            var cues = definition.Cues;
            _cueRules = new CueRule[cues.Count];
            _cueWhen = new IEngageable[cues.Count];
            _cueUnless = new IEngageable[cues.Count];
            _cueHeard = new bool[cues.Count];
            for (int i = 0; i < cues.Count; i++)
            {
                _cueRules[i] = cues[i];
                _cueWhen[i] = cues[i].WhenEngaged.IsNone ? null : Engageable(cues[i].WhenEngaged, "cue " + cues[i].Cue);
                _cueUnless[i] = cues[i].UnlessEngaged.IsNone ? null : Engageable(cues[i].UnlessEngaged, "cue " + cues[i].Cue);
            }

            var moments = definition.Moments;
            _momentRules = new MomentRule[moments.Count];
            _momentWhen = new IEngageable[moments.Count];
            _momentSeen = new int[moments.Count];
            for (int i = 0; i < moments.Count; i++)
            {
                _momentRules[i] = moments[i];
                _momentWhen[i] = moments[i].WhenEngaged.IsNone ? null : Engageable(moments[i].WhenEngaged, "moment " + moments[i].Moment.Name);
                _momentSeen[i] = Checkpoints.Seen.Resolve(moments[i].SeenKey);
            }

            var lifts = new List<ILiftRide>();
            var escorts = new List<IEscort>();
            for (int i = 0; i < Graph.Count; i++)
            {
                if (Graph[i] is ILiftRide lift) lifts.Add(lift);
                if (Graph[i] is IEscort escort) escorts.Add(escort);
            }
            _lifts = lifts.ToArray();
            _escorts = escorts.ToArray();

            SceneExit exit = definition.Exit;
            _exitOpen = exit == null || exit.OpenWhen.IsNone ? null : Engageable(exit.OpenWhen, "exit");

            for (int i = 0; i < definition.Spawns.Count; i++) Checkpoints.IndexOf(definition.Spawns[i].Checkpoint);   // typo guard
            OnReloaded(new Checkpoint(definition.CheckpointOrder, definition.FirstCheckpoint));
        }

        // ---- What the scene is made of ----------------------------------------------------------------------------
        public SceneDefinition Definition { get; }
        public MechanismGraph Graph { get; }
        public InteractionResolver Resolver { get; }
        public LaneGeometry Lane { get; }
        public D17Motor Motor { get; }
        public CheckpointService Checkpoints { get; }
        public MomentDirector Moments { get; }
        public CameraRig Camera { get; }
        /// <summary>Framing signals scene rules publish (<c>dl02</c>, <c>dl02.reveal</c>, …).</summary>
        public FramingSignalTable FramingSignals { get; } = new FramingSignalTable();

        // ---- State after the last step ------------------------------------------------------------------------------
        /// <summary>Steps since the runner was built (never reset; the moment and respawn clocks use it).</summary>
        public long Tick { get; private set; }
        /// <summary>Simulation seconds: <see cref="Tick"/> × <see cref="StepSeconds"/> (exact, no accumulation).</summary>
        public double Clock => Tick * StepSeconds;
        public string Checkpoint => Checkpoints.Current.Name;
        /// <summary>The checkpoint reached on the last step, or null.</summary>
        public string ReachedThisStep { get; private set; }
        /// <summary>The input the motor got on the last step, after the gate.</summary>
        public MotorInput GatedInput { get; private set; }
        /// <summary>The opening holds him (the camera runs the opening move).</summary>
        public bool InOpening => _opening;
        /// <summary>Opening clip frame (24 fps) while <see cref="InOpening"/>.</summary>
        public double OpeningFrame => _opening ? (Clock - _openingStart) * Fps : 0;
        /// <summary>True on the step control came back from the opening or a moment.</summary>
        public bool ControlReturnedThisStep { get; private set; }
        /// <summary>A moment started on the last step (the host starts its cue and Timeline), or null.</summary>
        public DirectedMoment MomentStartedThisStep { get; private set; }
        public bool RespawnPending => !double.IsNaN(_respawnAt);
        /// <summary>A reload happened at the start of the last step (respawn).</summary>
        public bool RespawnedThisStep { get; private set; }
        /// <summary>He stood in the exit once it was open. Set once per load; the host hands over to the next scene.</summary>
        public bool Exited { get; private set; }
        public bool ExitedThisStep { get; private set; }
        /// <summary>Cues to play, fired on the last step (the opening's, <see cref="CueRule"/>s, <see cref="Cue"/>).</summary>
        public IReadOnlyList<string> CuesThisStep => _cues;
        /// <summary>Viewport aspect the camera frames for (Runtime sets it; 0 = the config's).</summary>
        public double Aspect { get; set; }
        /// <summary>The act condition of the current moment before control may return (see <see cref="MomentDirector.GateInput"/>).</summary>
        public Func<bool> MomentActReady { get; set; }
        /// <summary>
        /// The parcel label's centre, prototype axes (for the label shot, L3735–L3741). Runtime sets it from the label's
        /// transform (SceneHost); null = an estimate on his chest from the motor (<see cref="EstimatedLabel"/>).
        /// </summary>
        public Func<Vec3> LabelCentre { get; set; }

        // ---- Lifecycle -------------------------------------------------------------------------------------------------
        /// <summary>
        /// Start over in this scene (<c>startOpening</c>/<c>clearLetters</c>, L8058–L8059): no flags, the first checkpoint,
        /// saved. With <paramref name="playOpening"/> and a scene opening, the opening holds him until its handover.
        /// </summary>
        public void NewGame(bool playOpening = true)
        {
            Checkpoints.NewGame();                                   // clears the seen moments too (clearLetters, L4133)
            if (playOpening && Definition.Opening != null) BeginOpening();
        }

        /// <summary>Continue from the save slot; false when it is empty or unreadable (the caller starts a new game).</summary>
        public bool Continue() => Checkpoints.TryContinue();

        /// <summary>Rebuild the world at the current checkpoint now (<c>startPlay(game.checkpoint)</c>, L8117).</summary>
        public void Respawn() => Checkpoints.Reload();

        /// <summary>
        /// Respawn after <paramref name="delay"/> s on the sim clock; control is withheld until then (L2998, L7451). The
        /// motor's stuck and death acts ask for this themselves (<see cref="MotorEventKind.RespawnDue"/>); call it directly
        /// only for a reload with no act of his (a fall onto the heap's fade, say). A pending respawn is not moved.
        /// </summary>
        public void RequestRespawn(double delay)
        {
            if (RespawnPending) return;
            _respawnAt = Clock + delay;
        }

        /// <summary>
        /// He is stuck (DL-01's trench, <c>trenchStuck</c>, L4764–L4766): the motor's stuck act (Flinch from 0.2 s), then
        /// at 2.0 s the 1.3 s fade and the reload at the checkpoint (L4521, L2997–L2999). Idempotent while stuck.
        /// </summary>
        public void Stuck() => Motor.BeginStuck();

        /// <summary><c>die(how)</c> (L7435–L7453): the death act (clip, shake, holds dropped), the cut after its hold, the reload 0.6 s later.</summary>
        public void Die(DeathKind how, double hold = double.NaN) => Motor.Die(how, hold);

        /// <summary>
        /// The opening's skip button (L8070–L8071): control now. The opening's moment jumps to its control-return state
        /// (<see cref="MomentDirector.Skip"/>): the wake plays on, and the next step reports
        /// <see cref="ControlReturnedThisStep"/> with <see cref="SceneDefinition.OnControlReturned"/> as from the opening.
        /// </summary>
        public void SkipOpening()
        {
            if (!_opening) return;
            Moments.Skip(Clock);
            _skippedOpening = true;
            EndOpening();
        }

        /// <summary>A once-only beat (a moment, <c>labelWake</c>) has played: kept in the save (<see cref="CheckpointService.Seen"/>).</summary>
        public void MarkSeen(string key) => Checkpoints.MarkSeen(key);
        public bool HasSeen(string key) => Checkpoints.HasSeen(key);

        /// <summary>Start a directed moment now (act-triggered moments call this from the scene's rules).</summary>
        public void StartMoment(DirectedMoment moment)
        {
            Moments.Start(moment, Clock, _music != null && _music.Running);
            MomentStartedThisStep = moment;
            Carry();
        }

        /// <summary>Queue a cue for the audio layer (this step; between steps, the next).</summary>
        public void Cue(string name)
        {
            _cues.Add(name);
            Carry();
        }

        private void Carry()
        {
            if (_inStep) return;
            if (!_carry) _cues.Clear();
            _carry = true;
        }

        /// <summary>Camera shake (calm mode disables it).</summary>
        public void Shake(double amount) => Camera.Shake(amount, Graph.Calm);

        // ---- The step --------------------------------------------------------------------------------------------------
        public void Step(in MotorInput raw)
        {
            // Cues and moments started between steps (NewGame's opening) are reported with the first step after.
            if (!_carry) { _cues.Clear(); MomentStartedThisStep = null; }
            _carry = false;
            _inStep = true;
            ReachedThisStep = null;
            ControlReturnedThisStep = false;
            RespawnedThisStep = false;
            ExitedThisStep = false;

            // #1 clock and respawn
            Tick++;
            if (RespawnPending && Clock >= _respawnAt - 1e-9) { Respawn(); RespawnedThisStep = true; }

            // #3 the gate: a pending respawn, then the opening or a moment
            MotorInput input = RespawnPending ? MotorInput.None : raw;
            input = Moments.GateInput(input, Clock, MomentActReady == null || MomentActReady());
            if (Moments.ControlReturned)
            {
                ControlReturnedThisStep = true;
                bool fromOpening = _opening || _skippedOpening;
                _skippedOpening = false;
                if (_opening) EndOpening();
                Definition.OnControlReturned(this, fromOpening);
            }
            GatedInput = input;

            // #4 motor (its shakes, and the stuck and death acts' respawn), #5–#7 mechanisms, then the scene's rules
            Motor.Step(input, StepSeconds);
            for (int i = 0; i < Motor.Events.Count; i++)
            {
                MotorEvent e = Motor.Events[i];
                if (e.Kind == MotorEventKind.Shake) Shake(e.Value);
                else if (e.Kind == MotorEventKind.RespawnDue) RequestRespawn(e.Value);
            }
            Graph.Step(StepSeconds, Pose());
            Definition.AfterMechanisms(this);

            // An escort that has caught him walks him (the trolley's game.act, L6399), then #9 ride sync (L2959–L2964).
            for (int i = 0; i < _escorts.Length; i++)
                if (_escorts[i].WantsEscort && !Motor.IsEscorted) Motor.BeginEscort(_escorts[i].Walk);
            Motor.SyncRide();
            for (int i = 0; i < _lifts.Length; i++)
                if (_lifts[i].Carrying) Motor.SnapToFloor(_lifts[i].FloorY);

            if (!_opening)
            {
                StepCheckpoints();
                StepCues();
                StepMoments();
                StepExit();
            }

            // #10 camera
            if (_opening) Camera.StepOpening(OpeningFrame, Definition.Opening.Chest, Aspect);
            else Camera.Step(CameraInput(), StepSeconds);
            _inStep = false;
        }

        /// <summary>D-17 as mechanisms see him (built from the motor after #4: <see cref="PlayerPose.Of"/>).</summary>
        public PlayerPose Pose() => PlayerPose.Of(Motor);

        /// <summary>The label's centre (<see cref="LabelCentre"/>, else <see cref="EstimatedLabel"/>), prototype axes.</summary>
        public Vec3 Label() => LabelCentre != null ? LabelCentre() : EstimatedLabel(Motor);

        /// <summary>The parcel label on his chest, estimated from the motor: 0.06 ahead of his centre at 0.42 (prototype z = −Unity z).</summary>
        public static Vec3 EstimatedLabel(D17Motor m) => new Vec3(m.X + m.Facing * 0.06, m.Y + 0.42, -m.Z);

        /// <summary>
        /// The label shot while he checks his label (<c>currentShot</c>, L3735–L3741): from f2 of CheckLabel, 0.27 in front
        /// of the label, 0.15 up and 0.05 toward the camera, 50 mm, ease 1.1 for a held check (the wake's) or 3.0. Null otherwise.
        /// </summary>
        public ShotRequest? LabelShot()
        {
            D17Motor m = Motor;
            if (m.ActVerb != Verb.Quirk || m.Clip != ClipNames.CheckLabel || !(m.ClipTime * Fps > 2)) return null;
            Vec3 l = Label();
            double fx = Math.Sin(m.Yaw), fz = Math.Cos(m.Yaw);
            var pos = new Vec3(l.X + fx * 0.27, l.Y + 0.15, l.Z + fz * 0.27 + 0.05);
            return new ShotRequest("label", pos, l, 50, double.IsNaN(m.QuirkHoldFor) ? 3.0 : 1.1);
        }

        /// <summary>The camera rig's input from Core state (L7668, L7787–L7804).</summary>
        public CameraRigInput CameraInput()
        {
            D17Motor m = Motor;
            CameraPush push = CameraPush.None;
            if (m.IsMantling) push = CameraPush.Mantle;
            // Acts push in once past their approach, except grab, the latch (its pull and flinch) and quirks (L7788's exclusions).
            else if (m.IsActing && m.ActPhase != ActPhase.Approach && m.ActVerb != Verb.Grab && m.ActVerb != Verb.Quirk
                && !(m.ActVerb == Verb.Use && (m.Clip == ClipNames.Pull || m.Clip == ClipNames.Flinch))) push = CameraPush.Act;
            return new CameraRigInput
            {
                X = m.X, Y = m.Y, Vx = m.Vx, Facing = m.Facing,
                NoLead = m.Hold != HoldKind.None || Exited,
                Push = push,
                Aspect = Aspect,
                Signals = FramingSignals,
                Shot = Definition.Shot(this),
            };
        }

        private void StepCheckpoints()
        {
            for (int i = 0; i < _rules.Length; i++)
            {
                if (_ruleIndex[i] <= _cpIndex) continue;
                CheckpointRule r = _rules[i];
                bool hit = r.Kind == CheckpointRuleKind.Engaged
                    ? _ruleSource[i].Engaged
                    : Motor.X > r.X && Motor.Y > r.MinY;
                if (hit && Checkpoints.Reach(r.Checkpoint))
                {
                    _cpIndex = _ruleIndex[i];
                    ReachedThisStep = r.Checkpoint;
                }
            }
        }

        private void StepCues()
        {
            for (int i = 0; i < _cueRules.Length; i++)
            {
                if (_cueHeard[i]) continue;
                CueRule c = _cueRules[i];
                if (!double.IsNaN(c.AfterX) && !(Motor.X > c.AfterX)) continue;
                if (_cueWhen[i] != null && !_cueWhen[i].Engaged) continue;
                if (_cueUnless[i] != null && _cueUnless[i].Engaged) continue;
                _cueHeard[i] = true;
                _cues.Add(c.Cue);
            }
        }

        private void StepMoments()
        {
            for (int i = 0; i < _momentRules.Length; i++)
            {
                if (Checkpoints.Seen.Get(_momentSeen[i])) continue;
                MomentRule m = _momentRules[i];
                if (!double.IsNaN(m.AfterX) && !(Motor.X > m.AfterX)) continue;
                if (_momentWhen[i] != null && !_momentWhen[i].Engaged) continue;
                Checkpoints.MarkSeen(m.SeenKey);                              // once per game, kept in the save (L945–L950)
                StartMoment(m.Moment);
            }
        }

        private void StepExit()
        {
            SceneExit e = Definition.Exit;
            if (Exited || e == null) return;
            if (_exitOpen != null && !_exitOpen.Engaged) return;
            if (e.RequireGrounded && !Motor.Grounded) return;
            if (!(Motor.X > e.X0 && Motor.X < e.X1)) return;
            Exited = ExitedThisStep = true;
        }

        private void BeginOpening()
        {
            SceneOpening o = Definition.Opening;
            _opening = true;
            _openingStart = Clock;
            StartMoment(o.Moment);
            if (o.Cue != null) Cue(o.Cue);
            Definition.OnOpeningStart(this);
            Camera.StepOpening(0, o.Chest, Aspect);
        }

        private void EndOpening()
        {
            _opening = false;
            CameraPose p = Camera.Pose;
            Camera.ContinueFrom(p.Position, p.Look);                // the side view starts where the opening's camera is (L8113)
        }

        /// <summary>The world was rebuilt at <paramref name="cp"/> (new game, continue, respawn): him, the camera, the clocks.</summary>
        private void OnReloaded(Checkpoint cp)
        {
            SpawnPoint s = SpawnAt(cp);
            Motor.Place(s.X, s.Y, s.Facing);
            Moments.End();
            _opening = false;
            _skippedOpening = false;
            _respawnAt = double.NaN;
            Exited = false;
            _cpIndex = Checkpoints.IndexOf(cp.Name);
            for (int i = 0; i < _cueRules.Length; i++) _cueHeard[i] = cp.Past(_cueRules[i].HeardAfter);
            CameraRigInput ci = CameraInput();
            Camera.SnapToFrame(ci);
            Camera.Step(ci, 0);
        }

        /// <summary>The checkpoint's spawn, or (a save made further on, in a scene this one hands over to) the scene's latest spawn before it.</summary>
        private SpawnPoint SpawnAt(Checkpoint cp)
        {
            if (Definition.HasSpawn(cp.Name)) return Definition.SpawnFor(cp.Name);
            var spawns = Definition.Spawns;
            SpawnPoint best = spawns[0];
            for (int i = 0; i < spawns.Count; i++) if (cp.Past(spawns[i].Checkpoint)) best = spawns[i];
            return best;
        }

        private IEngageable Engageable(MechanismId id, string what)
        {
            if (!Graph.TryGet<IEngageable>(id, out var e))
                throw new InvalidOperationException(Definition.Id + ": " + what + " reads " + id + ", which is not an engageable mechanism in the graph.");
            return e;
        }
    }
}
