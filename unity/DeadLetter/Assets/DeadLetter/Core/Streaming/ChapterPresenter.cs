using System;
using DeadLetter.Core.Audio;
using DeadLetter.Core.Camera;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Hazards;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Cycles;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Attendance;
using DeadLetter.Core.Scenes.Dl03;
using DeadLetter.Core.Scenes.Dl04;
using DeadLetter.Core.Scenes.Dl06;
using DeadLetter.Core.Scenes.Dl14;

namespace DeadLetter.Core.Streaming
{
    /// <summary>
    /// What the runtime's views read from a <see cref="ChapterSim"/> after each step, decided here so it is tested without
    /// Unity (port_architecture §3.1 #10–#11, presentation reading Core): the camera rig's input (his pose as the sim reports
    /// it, scene acts included; the framing signals; pushes; the label and moment shots), the ambience context, the clip a
    /// scene act shows, and whether the next step will place him somewhere else (a respawn the streamer must load first).
    /// One per chapter sim; it caches the scene objects it reads, so a step's reads allocate nothing.
    /// </summary>
    public sealed class ChapterPresenter
    {
        private const double Fps = 24;
        private static readonly ActId CheckLabelPhase = ActIds.Clip(ClipNames.CheckLabel);
        private static readonly ActId[] Legs = new ActId[8];

        private readonly ChapterSim _sim;
        private readonly Dl04Rules _dl04;
        private readonly Dl06Scanner _scanner;
        private readonly RacksReveal _reveal;
        // Chapter 1 (null elsewhere): the eased camera state, and what its signals read.
        private readonly AttendanceFramingState _att;
        private readonly CycleClock _lesson;
        private readonly Door _stairDoor;
        private double _attClock = double.NaN;
        private readonly System.Collections.Generic.Dictionary<int, string> _deathClips = new System.Collections.Generic.Dictionary<int, string>();

        static ChapterPresenter()
        {
            for (int i = 0; i < Legs.Length; i++) Legs[i] = ActIds.Leg(i);
        }

        public ChapterPresenter(ChapterSim sim)
        {
            _sim = sim ?? throw new ArgumentNullException(nameof(sim));
            var dl04 = sim.Def.Scene(Dl04Scene.Id);
            _dl04 = dl04 != null ? sim.RulesOf(dl04) as Dl04Rules : null;
            sim.Graph.TryGet("dl06.scanner", out _scanner);
            _reveal = sim.Def.Scene(Dl03Scene.Id) != null || dl04 != null ? sim.Shared<RacksReveal>() : null;
            if (sim.Def.Id == ChapterDefs.AttendanceId)
            {
                _att = new AttendanceFramingState();
                sim.Graph.TryGet("dl13.lesson", out _lesson);
                sim.Graph.TryGet("dl17.stairDoor", out _stairDoor);
                sim.Checkpoints.Reloaded += OnAttReloaded;
            }
        }

        /// <summary><c>resetAtt</c> at every checkpoint start and respawn (L8018): the eased state starts over, and eases from the next step.</summary>
        private void OnAttReloaded(Mechanisms.Checkpoint _)
        {
            _att.Reset();
            _attClock = _sim.Clock;
        }

        public ChapterSim Sim => _sim;

        // ---- Camera (§4.17; updateCamera L7787–L7804) --------------------------------------------------------------------

        /// <summary>The transit leg he is on (<see cref="ActIds.Leg"/>), or −1 outside a transit.</summary>
        public int TransitLeg
        {
            get
            {
                if (_sim.SceneActKind != ActIds.Transit) return -1;
                var phase = _sim.SceneActPhase;
                for (int i = 0; i < Legs.Length; i++) if (Legs[i] == phase) return i;
                return 0;
            }
        }

        /// <summary>
        /// The prologue's framing signals (<see cref="PrologueFraming"/>) from the sim: <c>dl02</c> (region 2, or the passage
        /// out of DL-01), <c>dl02.reveal</c> (the racks' slow pan after they light), <c>dl02.realised</c> and <c>dl06.pit</c>.
        /// </summary>
        public void UpdateSignals(FramingSignalTable signals)
        {
            if (signals == null) throw new ArgumentNullException(nameof(signals));
            signals.Set(PrologueFraming.Dl02, PrologueFraming.Dl02Signal(_sim.Region, TransitLeg, _sim.X));
            double reveal = _reveal != null && _reveal.Revealed && !_reveal.Pending ? PrologueFraming.RevealSignal(_sim.Clock - _reveal.Time) : 0;
            signals.Set(PrologueFraming.Dl02Reveal, reveal);
            signals.Set(PrologueFraming.Dl02Realised, _dl04 != null && _dl04.Realised && _sim.Region == 2 ? 1 : 0);
            signals.Set(PrologueFraming.Dl06Pit, _scanner != null ? PrologueFraming.PitSignal(InPitPhase, _scanner.T) : 0);
            if (_att != null) UpdateAttendanceSignals(signals);
        }

        /// <summary>
        /// Chapter 1's framing signals (<see cref="AttendanceFraming"/>). <c>k13</c> and <c>k15</c> ease once per sim step
        /// (keyed on the clock, so a second call in the same step, e.g. after a placement, changes nothing).
        /// </summary>
        private void UpdateAttendanceSignals(FramingSignalTable signals)
        {
            if (_sim.Clock != _attClock)
            {
                _att.Step(_lesson != null && _lesson.On, _sim.X, _sim.Y, ChapterSim.StepSeconds);
                _attClock = _sim.Clock;
            }
            _att.Publish(signals);
            signals.Set(AttendanceFraming.Gallery, AttendanceFraming.GallerySignal(_sim.Y));
            signals.Set(AttendanceFraming.Duct, _sim.SceneActKind == DuctAct.Hatch ? 1 : 0);
            signals.Set(AttendanceFraming.Door17, _stairDoor != null ? Smooth.Step(_stairDoor.Position) : 0);
        }

        /// <summary>
        /// Chapter 1's push from the motor (L7788): mantling pushes in fully, and every act past its approach but a quirk
        /// pushes in. Of the kinds the prototype leaves out, only <c>'quirk'</c> happens here: <c>'grab'</c> is the
        /// trolleys' and DL-05's desk (chapter 1's pushables are <c>'grabPush'</c>, which pushes) and <c>'latch'</c> is
        /// DL-01's lever, so <see cref="D17Framing.Push"/>'s grab and Pull/Flinch exclusions are the prologue's, not these.
        /// </summary>
        private static CameraPush AttendanceMotorPush(D17Motor m)
        {
            if (m.IsMantling) return CameraPush.Mantle;
            if (m.IsActing && m.ActPhase != ActPhase.Approach && m.ActVerb != Verb.Quirk) return CameraPush.Act;
            return CameraPush.None;
        }

        /// <summary>
        /// Chapter 1's push during a scene act (L7788): every act there is the prototype's <c>att</c> or a motor act Core
        /// runs as a scene act, so it pushes in once past its approach; quirks never do.
        /// </summary>
        private CameraPush AttendanceActPush()
        {
            var kind = _sim.SceneActKind;
            if (kind == ActIds.Quirk || _sim.SceneActPhase == AttAct.Approach) return CameraPush.None;
            return CameraPush.Act;
        }

        private bool InPitPhase => _scanner != null && (_scanner.Phase == Dl06ScanPhase.Reveal || _scanner.Phase == Dl06ScanPhase.Check);

        /// <summary>
        /// The rig's input for this step: his pose as the sim reports it (a scene act that owns it included), no look-ahead
        /// while he holds something, rides a transit or has left the chapter, the motor's push (or the transit's and the
        /// realisation's), the slow follow (<c>paceSlow</c>, the pit reveal), <paramref name="signals"/> and the shot: the
        /// directed moment's (<see cref="MomentShot"/>) over the label check's (<see cref="LabelShot"/>).
        /// </summary>
        public CameraRigInput CameraInput(double aspect, FramingSignalTable signals)
        {
            var m = _sim.Motor;
            int leg = TransitLeg;
            CameraPush push;
            if (_sim.Act == null) push = _att != null ? AttendanceMotorPush(m) : D17Framing.Push(m);
            else if (leg == 0) push = CameraPush.Transit;
            else if (_sim.SceneActKind == RealiseAct.Realise) push = CameraPush.Realise;
            else if (_att != null) push = AttendanceActPush();
            else push = CameraPush.None;
            ShotRequest? shot = MomentShot();
            if (!shot.HasValue) shot = LabelShot();
            return new CameraRigInput
            {
                X = _sim.X, Y = _sim.Y, Vx = _sim.Vx, Facing = m.Facing,
                NoLead = m.Hold != HoldKind.None || leg >= 0 || _sim.Exited,
                Push = push,
                SlowFollow = m.SlowWalkLimit > 0 || (_scanner != null && _scanner.Phase == Dl06ScanPhase.Reveal),
                Aspect = aspect,
                Signals = signals,
                Shot = shot,
            };
        }

        /// <summary>The directed moment Core is running (DL-04's kin), or null (<see cref="MomentDirector"/>s are the scenes' own).</summary>
        public MomentDirector Moment => _dl04 != null && _dl04.Moment.Current != null ? _dl04.Moment : null;

        /// <summary>The director running the moment called <paramref name="name"/>, or null.</summary>
        public MomentDirector MomentNamed(string name)
        {
            var d = Moment;
            return d != null && d.Current.Name == name ? d : null;
        }

        /// <summary>The moment's camera shot (<c>currentShot</c>'s moment branches, L3702–L3721) on the sim clock, or null.</summary>
        public ShotRequest? MomentShot()
        {
            var d = Moment;
            if (d == null) return null;
            double? t = d.ShotTime(d.Current.Name, _sim.Clock);
            if (!t.HasValue) return null;
            if (d.Current == PrologueMoments.Kin) return MomentShots.Kin(_sim.X, t.Value);
            if (d.Current == PrologueMoments.Refuge) return MomentShots.Refuge(_sim.X, _sim.Y, t.Value);
            return null;
        }

        /// <summary>
        /// The label shot while he checks his label (<c>currentShot</c>, L3735–L3741): the motor's quirk
        /// (<see cref="D17Framing.LabelShot"/>), or a scene act playing CheckLabel (the wake's label beat, DL-05's label, DL-06's
        /// check) from f2, held (ease 1.1), framed on the label estimated from the sim's pose.
        /// </summary>
        public ShotRequest? LabelShot()
        {
            if (_sim.Act == null) return D17Framing.LabelShot(_sim.Motor);
            bool checking = (_sim.SceneActKind == ActIds.Quirk && _sim.SceneActPhase == CheckLabelPhase)
                            || (_sim.SceneActKind == Dl06ScanAct.Scanner && _sim.SceneActPhase == Dl06ScanAct.Check);
            if (!checking || !(_sim.Act.T * Fps > 2)) return null;
            int facing = _sim.Motor.Facing;
            var label = new Vec3(_sim.X + facing * 0.06, _sim.Y + 0.42, -_sim.Z);
            double fx = Math.Sin(_sim.Yaw), fz = Math.Cos(_sim.Yaw);
            var pos = new Vec3(label.X + fx * 0.27, label.Y + 0.15, label.Z + fz * 0.27 + 0.05);
            return new ShotRequest("label", pos, label, 50, 1.1);
        }

        // ---- Audio ------------------------------------------------------------------------------------------------------

        /// <summary><c>sceneAmbience()</c>'s inputs for the prologue's ported scenes (L8147–L8162).</summary>
        public AmbienceContext Ambience() => new AmbienceContext
        {
            Region = _sim.Region,
            X = _sim.X,
            Revealed = _reveal != null && _reveal.Revealed,
            PastScanned = _sim.Checkpoints.Current.Past(Dl06Scene.ScannedCheckpoint),
        };

        // ---- D-17's clip during a scene act ------------------------------------------------------------------------------

        /// <summary>
        /// The clip D-17 shows while a scene act holds him (the motor's clip otherwise: null). Its time is
        /// <paramref name="seconds"/> into the clip when it starts (NaN: from the top). A quirk plays its phase (the clip),
        /// a death its <c>Death&lt;Kind&gt;</c>, the realisation <c>Realise</c>, a transit walks, DL-06's chute slides and
        /// falls; DL-06's check is CheckLabel; other acts keep the motor's clip (it stands meanwhile).
        /// </summary>
        public string ActClip(out double seconds)
        {
            seconds = double.NaN;
            var act = _sim.Act;
            if (act == null) return null;
            var kind = act.Kind;
            var phase = act.Phase;
            if (kind == ActIds.Quirk) { seconds = act.T; return phase.Name; }
            if (kind == ActIds.Death) { seconds = act.T; return DeathClip(phase); }
            if (kind == RealiseAct.Realise) { seconds = act.T; return "Realise"; }
            if (kind == ActIds.Transit) return ClipNames.Walk;
            if (kind == Scenes.Dl17.Dl17StairAct.Stair) { seconds = act.T; return ClipNames.Walk; }   // up the stair to ring A
            if (kind == Dl06ScanAct.Scanner) { if (phase == Dl06ScanAct.Check) { seconds = act.T; return ClipNames.CheckLabel; } return ClipNames.Idle; }
            if (kind == Dl06ChuteFallAct.ChuteKind) return phase == Dl06ChuteFallAct.Chute ? "Slide" : phase == Dl06ChuteFallAct.Air ? ClipNames.Fall : ClipNames.Land;
            return null;
        }

        /// <summary><c>Death&lt;Kind&gt;</c> for a death act's phase (its kind), built once per kind.</summary>
        private string DeathClip(ActId phase)
        {
            if (!_deathClips.TryGetValue(phase.Value, out string clip)) _deathClips.Add(phase.Value, clip = "Death" + phase.Name);
            return clip;
        }

        // ---- Placement -----------------------------------------------------------------------------------------------------

        /// <summary>
        /// The scene the next <see cref="ChapterSim.Step"/> will put him in by respawning (<c>respawnAt</c> passes then, L8494),
        /// or null when it will not respawn him. The streamer loads it before letting that step run.
        /// </summary>
        public SceneDef PendingRespawnScene()
        {
            double at = _sim.RespawnAt;
            if (!(at > 0) || !(_sim.Clock + ChapterSim.StepSeconds >= at)) return null;   // the same sum Step compares
            return _sim.SceneOf(_sim.Checkpoints.Current.Name);
        }
    }
}
