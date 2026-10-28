using System;
using DeadLetter.Core.Beings;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using DeadLetter.Core.Scenes.Attendance;

namespace DeadLetter.Core.Scenes.Dl14b
{
    /// <summary>
    /// DL-14b Unaccompanied (port_architecture §5, §4.16; docs/chapter1_expansion_build.md): the night corridor. The escort
    /// trolley patrols its rail and looks ahead with its lamp; whatever pupil-sized thing it finds in the beam (him, out of
    /// a recess, or the figure in the bay once nudged out onto the rail; the nearer) it rings for and takes back to the
    /// dormitory. He hides in niche A, nudges the figure out, hides in the emptied bay while the trolley takes the figure
    /// back, and goes on up the stair to the sick bay. Region 6 from 263 to DL-15 at 278 (<c>sceneName</c>, L8136). Lines
    /// are index.html at 7b3c123 (<c>ATT3</c> L5897–L5900, <c>resetAtt3</c> L5917, <c>nearAtt3Fixed</c> L5989–L5991,
    /// <c>updateAtt3Act</c> L6103–L6135, <c>updateTrolley14b</c> L6358–L6422, <c>pushable14b</c> L6450–L6454).
    /// </summary>
    public static class Dl14bScene
    {
        public const string Id = "DL-14b";

        public const double X0 = 263, X1 = 278;

        /// <summary><c>ATT3.bayX</c> (L5898): the figure's bay, where he stands to nudge it (L6004, L5990).</summary>
        public const double BayX = 269.9, NudgeReach = 0.3;

        /// <summary>The scene definition.</summary>
        public static SceneDef Def()
        {
            var senses = new BeingSenses { Region = Dl14bLane.Region };
            return new SceneDef
            {
                Id = Id,
                Title = "Unaccompanied",
                X0 = X0, X1 = X1,
                Region = Dl14bLane.Region,                                                        // its checkpoint: corridor (DL-14a's door)
                // Step order = the prototype's updateTrolley14b (#7): the figure rolls out of its bay first, then the trolley
                // moves and looks (L6359–L6410). The recesses have no state.
                Mechanisms = new[]
                {
                    new MechanismDef("dl14b.figure", () => new Dl14bFigure("dl14b.figure")),
                    new MechanismDef("dl14b.trolley", () => new EscortTrolley("dl14b.trolley", EscortTrolleyParams.Dl14b("dl14b.figure"), senses)),
                    new MechanismDef("dl14b.nicheA", () => new HideSpot("dl14b.nicheA", HideSpotParams.Dl14bNicheA())),
                    new MechanismDef("dl14b.bay", () => new HideSpot("dl14b.bay", HideSpotParams.Dl14bBay("dl14b.figure"))),
                },
                Interactables = g => new IInteractable[] { new Dl14bFigureFace(g.Get<Dl14bFigure>("dl14b.figure")) },   // fig14br, L6455
                Lane = Dl14bLane.Table,
                LaneContributors = Dl14bLane.Contributors,
                Rules = () => new Dl14bRules(senses),
            };
        }
    }

    public enum Dl14bFigureState { Bay, Rolling, Free, Escorted }

    /// <summary>
    /// The figure in the corridor's bay (<c>f14b.fig</c>, L5917; <c>pushable14b</c>, L6450–L6454): it stands in its bay
    /// until nudged; then it rolls out onto the rail (<c>out</c> over 0.9 s), coasts a metre on, slowing, and stands free on
    /// the rail, where he can push it either way (0.35 m/s, 261.8–275.0, from 0.55 into the set) and the trolley can find it
    /// (<see cref="IDecoy"/>). Once the trolley holds it (<see cref="IDecoyEscort"/>), it is the trolley's, at its x, and
    /// never his again (<c>'escorted'</c>, kept at 262.2). Reset: in the bay; from <c>sickbay</c> free at 262.2, kept.
    /// The rolling is the prototype's, inside <c>updateTrolley14b</c> before the trolley looks (L6360–L6362): this steps
    /// before the trolley. Signals: <see cref="Engaged"/> = out of its bay (the bay is a hiding place then, L5991).
    /// </summary>
    public sealed class Dl14bFigure : Mechanism, IPushable, IDecoy, IEngageable, IPositionSource
    {
        /// <summary><c>ATT3.rail</c>, <c>railZ</c> (Unity +0.55), <c>keepX</c> (L5898–L5899); <c>pushable14b</c>'s gap and speed.</summary>
        public const double RailX0 = 261.8, RailX1 = 275.0, RailZ = 0.55, KeepX = 262.2, Gap = 0.6, Speed = 0.35;
        /// <summary>It rolls out over 0.9 s, then coasts a metre at 0.8 × max(0.25, what is left) m/s (L6361–L6362).</summary>
        public const double OutTime = 0.9, Coast = 1.0, CoastRate = 0.8, CoastMin = 0.25;

        private IDecoyEscort _escort;
        private Dl14bFigureState _state;
        private double _x, _out, _coast;
        private bool _nudge;

        public Dl14bFigure(MechanismId id) : base(id) { }

        public Dl14bFigureState State => _escort != null && _escort.HoldsDecoy ? Dl14bFigureState.Escorted : _state;
        /// <summary>0 in its bay .. 1 on the rail (<c>fig.out</c>).</summary>
        public double Out => _out;
        /// <summary>Kept at 262.2 by the trolley (<c>fig.kept</c>).</summary>
        public bool Kept => _escort != null && _escort.DecoyKept;

        /// <summary>The nudge's push, 0.6 s into it (L6105): it starts rolling at its next step.</summary>
        public void Nudge() => _nudge = true;

        // ---- IDecoy / IEngageable / IPositionSource ----------------------------------------------------------------
        /// <summary>Its own x: the trolley reads it as it looks and takes it from here when it sees it (then the trolley's x is the figure's).</summary>
        public double DecoyX => _x;
        public bool DecoyInView => State == Dl14bFigureState.Free || (State == Dl14bFigureState.Rolling && _out >= 1);   // L6369
        public bool Engaged => State != Dl14bFigureState.Bay;
        public double Position => X;

        // ---- IPushable (its left face; Dl14bFigureFace is its right) -----------------------------------------------
        public InteractionCategory Category => InteractionCategory.Push;
        public double X => State == Dl14bFigureState.Escorted ? _escort.DecoyX : _x;
        public int Side => 1;
        double IPushable.Gap => Gap;
        double IPushable.Speed => Speed;
        public double Accel => 1.4;
        public double Min => RailX0;
        public double Max => RailX1;
        public double FloorY => 0;
        public double Z => RailZ;
        public double ForwardReach => 0.34;
        public double BackReach => 0.34;
        public bool TipsIntoPit => false;
        public bool HasDetents => false;
        public bool LetGoAtMax => true;

        /// <summary><c>avail: fig().state === 'free'</c> (L6452).</summary>
        public bool IsAvailable(in InteractionQuery q) => State == Dl14bFigureState.Free;
        public void MoveTo(double x, double velocity) => _x = x;
        public void SetAtLip(bool atLip) { }
        public void OnReleased(bool atLip) { }
        public void OnShoved() { }
        public void OnTravelEnd() { }

        public override void Link(MechanismLinker link) => _escort = link.ReadAnyOrder<IDecoyEscort>("dl14b.trolley")
            ?? throw new InvalidOperationException(Id + " needs dl14b.trolley.");

        public override void Reset(in Checkpoint cp)
        {
            bool passed = cp.Past("sickbay");                                                        // L5917
            _x = passed ? KeepX : Dl14bScene.BayX;
            _state = passed ? Dl14bFigureState.Free : Dl14bFigureState.Bay;
            _out = passed ? 1 : 0;
            _coast = 0;
            _nudge = false;
            Init((int)_state);
        }

        public override void Step(in StepContext ctx)
        {
            if (_nudge) { _nudge = false; if (_state == Dl14bFigureState.Bay) _state = Dl14bFigureState.Rolling; }   // L6105
            if (State == Dl14bFigureState.Rolling)                                                   // L6360–L6362
            {
                if (_out < 1) { _out = Math.Min(1, _out + ctx.Dt / OutTime); if (_out >= 1) _coast = Coast; }
                else
                {
                    double step = Math.Min(_coast, ctx.Dt * CoastRate * Math.Max(CoastMin, _coast));
                    _x += step; _coast -= step;
                    if (_coast <= 1e-3) _state = Dl14bFigureState.Free;
                }
            }
            Enter(ctx, (int)State);
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteLong("state", (int)_state); w.WriteDouble("x", _x); w.WriteDouble("out", _out); w.WriteDouble("coast", _coast); w.WriteBool("nudge", _nudge);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            _state = (Dl14bFigureState)r.ReadLong("state"); _x = r.ReadDouble("x"); _out = r.ReadDouble("out"); _coast = r.ReadDouble("coast"); _nudge = r.ReadBool("nudge");
        }
    }

    /// <summary>The figure's right face (<c>fig14br</c>, side −1, L6455): the same figure, pushed the other way.</summary>
    public sealed class Dl14bFigureFace : IPushable
    {
        public Dl14bFigureFace(Dl14bFigure of) { Base = of ?? throw new ArgumentNullException(nameof(of)); }

        public Dl14bFigure Base { get; }
        public InteractionCategory Category => InteractionCategory.Push;
        public bool IsAvailable(in InteractionQuery q) => Base.IsAvailable(q);
        public double X => Base.X;
        public int Side => -1;
        public double Gap => Dl14bFigure.Gap;
        public double Speed => Dl14bFigure.Speed;
        public double Accel => Base.Accel;
        public double Min => Base.Min;
        public double Max => Base.Max;
        public double FloorY => Base.FloorY;
        public double Z => Base.Z;
        public double ForwardReach => Base.ForwardReach;
        public double BackReach => Base.BackReach;
        public bool TipsIntoPit => false;
        public bool HasDetents => false;
        public bool LetGoAtMax => true;
        public void MoveTo(double x, double velocity) => Base.MoveTo(x, velocity);
        public void SetAtLip(bool atLip) { }
        public void OnReleased(bool atLip) { }
        public void OnShoved() { }
        public void OnTravelEnd() { }
    }

    /// <summary>
    /// DL-14b's rules: the trolley's senses (region 6; out of play once a respawn is pending, L6366), the nudge that sends
    /// the figure out of its bay (<c>'att:nudge14b'</c>, L5990, a fixed control: it gives way to anything Use would lift),
    /// and the trolley's voice (<c>att_trolley</c>, L6401, L6408).
    /// <para>The senses are filled after each step for the next (the prototype reads <c>game.respawnAt</c> as it looks):
    /// nothing in DL-14b kills him, so the lag never shows.</para>
    /// </summary>
    public sealed class Dl14bRules : SceneRules
    {
        public static readonly CueId VoiceTrolley = CueId.Of("voice:att_trolley");
        private static readonly MechanismId TrolleyId = "dl14b.trolley";

        private readonly BeingSenses _senses;
        private Dl14bFigure _fig;

        public Dl14bRules(BeingSenses senses) { _senses = senses; }

        public override bool Always => true;

        public override void OnBegin(ChapterSim sim, string checkpoint, bool fromOpening)
        {
            _fig = sim.Graph.Get<Dl14bFigure>("dl14b.figure");
            Sense(sim);
        }

        public override void BeforeMotor(ChapterSim sim, ref MotorInput input)
        {
            var m = sim.Motor;
            if (!input.UsePressed || m.IsActing || m.IsMantling || m.Ride != null || !m.Grounded || m.Hold != HoldKind.None || sim.Region != Dl14bLane.Region) return;
            if (!(m.Y < 0.05 && _fig.State == Dl14bFigureState.Bay && Math.Abs(m.X - Dl14bScene.BayX) < Dl14bScene.NudgeReach)) return;   // L5990
            if (m.PreviewUse(out var c) && c.Category < InteractionCategory.Fixed) return;            // an item, a curio ... answers first (L4204–L4229)
            input = MotorInput.None;
            sim.StartAct(new NudgeAct(sim, _fig));
        }

        public override void AfterGraph(ChapterSim sim)
        {
            var log = sim.Graph.Log;
            if (log.Has(TrolleyId, MechanismEventKind.Event, (int)EscortEvent.CaughtHim) || log.Has(TrolleyId, MechanismEventKind.Event, (int)EscortEvent.FigureSeen)) sim.Cue(VoiceTrolley);
            Sense(sim);
        }

        private void Sense(ChapterSim sim)
        {
            _senses.Region = sim.Region;
            _senses.Alive = !(sim.RespawnAt > 0) && !sim.Motor.IsDead;
        }
    }

    /// <summary>
    /// He nudges the figure out of its bay (<c>'att:nudge14b'</c>, L6027, L6103–L6106): to the bay facing +1, Nudge turned
    /// into the set; 0.6 s in it starts rolling out; at 1.4 s he is done.
    /// </summary>
    public sealed class NudgeAct : AttAct
    {
        public static readonly ActId Bay = ActId.Of("dl14b.figure"), Nudge = ActIds.Clip(ClipNames.Nudge);
        private readonly Dl14bFigure _fig;
        private bool _done;

        public NudgeAct(ChapterSim sim, Dl14bFigure fig) : base(sim, Bay, Dl14bScene.BayX, 1) { _fig = fig; }

        protected override void OnArrive() { FaceSet(Math.PI); Phase = Nudge; }

        protected override bool OnClip(double dt)
        {
            if (T > 0.6 && !_done) { _done = true; _fig.Nudge(); }
            return !(T > 1.4);
        }
    }
}
