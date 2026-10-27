using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Save;
using DeadLetter.Core.Simulation;

namespace DeadLetter.Core.Beings
{
    /// <summary>The trolley's modes (<c>B.mode</c>, L6370–L6393).</summary>
    public enum EscortState
    {
        /// <summary>Rolling along the rail at 1.1 m/s, looking ahead with its lamp.</summary>
        Patrol,
        /// <summary>Paused 1.2 s at an end of its patrol, turning round (still looking).</summary>
        Turn,
        /// <summary>Stood still after an escort: 2 s after taking him back, 6 s after keeping the figure (the window).</summary>
        Stop,
        /// <summary>Pushing the decoy (DL-14b's nudged figure) back to 262.2.</summary>
        EscortFigure,
        /// <summary>Walking him back to the dormitory door.</summary>
        EscortHim,
    }

    public enum EscortEvent
    {
        /// <summary>A wheel squeak (random, 2.5/s on patrol, 3/s pushing the figure; L6377, L6387).</summary>
        Squeak,
        /// <summary>It turned round at an end (servo whine, L6379).</summary>
        Turned,
        /// <summary>It saw him (L6397–L6403): two bells 0.26 s apart, <c>failAtt('14b')</c>, the <c>att_trolley</c> voice
        /// at Value = its x (reach 9, level 0.8). From now it asks for him (<see cref="IEscort.WantsEscort"/>): the pipeline
        /// starts the motor's escorted act, which drops what he holds (L6399–L6400) and walks him home.</summary>
        CaughtHim,
        /// <summary>He is back at the dormitory door: the motor's escorted act ended there, he faces +x (L6133). Value = his x.</summary>
        HimHome,
        /// <summary>It saw the figure first (L6405–L6409): two bells, the voice at Value = its x (level 0.7); the driver
        /// releases his push if he is pushing the figure.</summary>
        FigureSeen,
        /// <summary>The figure is back at 262.2: a bell, <c>progressAtt()</c>; it waits 6 s (L6388).</summary>
        FigureKept,
    }

    /// <summary>
    /// A thing the beam can find instead of him: DL-14b's figure, once nudged out of its bay (L6365–L6368). The figure's
    /// own mechanism implements it; it must step before the trolley (the prototype rolls it inside
    /// <c>updateTrolley14b</c>, before the trolley looks, L6359–L6362).
    /// </summary>
    public interface IDecoy
    {
        /// <summary>Lane x.</summary>
        double DecoyX { get; }
        /// <summary>On the rail and visible: free, or rolled fully out (<c>fig.state === 'free' || rolling &amp;&amp; out &gt;= 1</c>).</summary>
        bool DecoyInView { get; }
    }

    /// <summary>
    /// What the trolley tells the decoy (the figure reads it with <c>ReadAnyOrder</c>, one step behind): while
    /// <see cref="HoldsDecoy"/> it is no longer pushable and sits at <see cref="DecoyX"/> (<c>fig.state = 'escorted'</c>).
    /// </summary>
    public interface IDecoyEscort
    {
        bool HoldsDecoy { get; }
        double DecoyX { get; }
        /// <summary><c>fig.kept</c>: brought back to the keep point; never seen again.</summary>
        bool DecoyKept { get; }
    }

    public sealed class EscortTrolleyParams
    {
        public double StartX = 270.0;                               // L5917
        public double PatrolX0 = 265.0, PatrolX1 = 274.9;           // ATT3.patrol, L5899
        public double Speed = 1.1, EscortSpeed = 0.8;               // L5899
        public double Beam = 2.6, LampDX = 0.35;                    // L5899, beam14b L6354–L6357
        public double Pause = 1.2;                                  // L5899
        /// <summary>It never sees through the dormitory wall: door.x1 + 0.1 (L5895, L6367).</summary>
        public double WallX = 263.0 + 0.1;
        /// <summary>He is seen below this height (L6367).</summary>
        public double SeeBelowY = 1.25;
        /// <summary>Hidden: in the hide act and stepped back past this depth (Unity z; three <c>game.z &lt; −0.4</c>, L5973).</summary>
        public double HiddenDepth = 0.4;
        /// <summary>The escorted act (the motor's): idle 0.7 s, then walked back to 263.45; it ends at ≤ 263.46 (L6130–L6133).</summary>
        public double HeroHold = 0.7, HeroHomeX = 263.45, HeroHomeArrive = 263.46;
        /// <summary>It follows 0.75–0.9 m behind him (L6132).</summary>
        public double FollowMin = 0.75, FollowMax = 0.9;
        public double CaughtStop = 2.0;                             // L6133, L6421
        /// <summary>The figure: it waits 0.8 s, pushes it 0.65 ahead to 262.2, then stops 6 s (L6384–L6388).</summary>
        public double FigureDelay = 0.8, FigureLead = 0.65, KeepX = 262.2, KeepStop = 6;
        public double SqueakPatrol = 2.5, SqueakEscort = 3;         // L6377, L6387
        /// <summary>The <c>game.region</c> it watches (region 6, L6366).</summary>
        public int Region = 6;
        /// <summary>The decoy it can be fooled by (optional).</summary>
        public MechanismId Decoy;
        /// <summary>From this checkpoint the figure was already kept (<c>passed = p('sickbay')</c>, L5917).</summary>
        public string KeptAfter = "sickbay";
        public ulong Seed = 0x7201_14B0UL;

        /// <summary>DL-14b Unaccompanied (L5897–L5900, L5917, L6352–L6421).</summary>
        public static EscortTrolleyParams Dl14b(MechanismId figure = default) => new EscortTrolleyParams { Decoy = figure };
    }

    /// <summary>
    /// The escort trolley (port_architecture §4.16, DL-14b; L5897–L5900, L5917, L6127–L6134, L6352–L6421): it patrols
    /// its rail, pausing and turning at each end, and looks ahead with its lamp. Whatever pupil-sized thing it finds in
    /// the beam — him, not tucked into a recess, or the nudged figure on the rail; the nearer wins — it rings for and
    /// takes back toward the dormitory: him to the door at 0.8 m/s, then it stops 2 s; the figure to 262.2, then it
    /// stops 6 s (the window to pass). The template for the attendant (rail patrol + beam sensor + escort).
    /// <para>The escorted walk is the motor's act (<see cref="IEscort"/>: <see cref="WantsEscort"/>, <see cref="Walk"/>); the
    /// trolley follows him 0.75–0.9 behind once he walks (L6132). If the act is not running while it holds him (a respawn
    /// cut it, or he is out of play), it stops 2 s (<c>updateEscortHim14b</c>, L6413, L6419–L6422).</para>
    /// <para>Inputs: <see cref="StepContext.Player"/> (x, y, z, hiding, escorted), <see cref="BeingSenses"/> (alive, region), the
    /// optional <see cref="IDecoy"/>. Signals: <see cref="IPositionSource.Position"/> = its x; <see cref="IDecoyEscort"/>; <see cref="IEscort"/>.</para>
    /// </summary>
    public sealed class EscortTrolley : Mechanism, IPositionSource, IDecoyEscort, IEscort
    {
        private readonly EscortTrolleyParams _p;
        private readonly BeingSenses _sense;
        private SimRng _rng;
        private IDecoy _decoy;

        private double _x, _mt, _stopFor;
        private int _dir;
        private double _decoyX;
        private bool _decoyHeld, _decoyKept;
        private double _heroT;
        private bool _heroHeld;

        public EscortTrolley(MechanismId id, EscortTrolleyParams p, BeingSenses senses) : base(id)
        {
            _p = p ?? throw new ArgumentNullException(nameof(p));
            _sense = senses ?? throw new ArgumentNullException(nameof(senses));
            _rng = SimRng.Xorshift(_p.Seed);
        }

        public EscortState State => (EscortState)StateCode;
        /// <summary>Its x on the rail (<c>B.tx</c>).</summary>
        public double X => _x;
        public double Position => _x;
        /// <summary>+1 rolling/looking toward +x, −1 toward −x.</summary>
        public int Dir => _dir;
        /// <summary>Seconds in the current mode (<c>B.mt</c>).</summary>
        public double ModeTime => _mt;
        /// <summary>
        /// Its facing for the view: 0 = toward +x, 1 = toward −x, swinging through the 1.2 s turn with smoothstep
        /// (<c>placeTrolley14b</c>, L6424–L6427).
        /// </summary>
        public double Facing01
        {
            get
            {
                if (State == EscortState.Turn)
                {
                    double k = Maths.Smooth.Step(Math.Min(1, _mt / _p.Pause));
                    return _dir > 0 ? k : 1 - k;
                }
                return _dir > 0 ? 0 : 1;
            }
        }
        /// <summary>The beam's lit span on the lane, from 0.35 ahead of it for 2.6 m (<c>beam14b</c>, L6354–L6357).</summary>
        public double BeamLo => Math.Min(BeamA, BeamA + _dir * _p.Beam);
        public double BeamHi => Math.Max(BeamA, BeamA + _dir * _p.Beam);
        private double BeamA => _x + _dir * _p.LampDX;

        /// <summary>It has him: from the catch until he is home (or the act is cut).</summary>
        public bool HeroHeld => _heroHeld;
        /// <summary>Seconds of the escorted act it has seen (the follow starts at <see cref="EscortTrolleyParams.HeroHold"/>).</summary>
        public double HeroTime => _heroT;
        public bool WantsEscort => State == EscortState.EscortHim && _heroHeld;
        /// <summary>Stand 0.7 s, then walk at 0.8 m/s to the dormitory door, facing −x; done at ≤ 263.46, then face +x (L6127–L6133).</summary>
        public EscortWalk Walk => new EscortWalk(_p.HeroHold, _p.EscortSpeed, _p.HeroHomeX, _p.HeroHomeArrive, -1, +1);
        public bool HoldsDecoy => _decoyHeld;
        public double DecoyX => _decoyX;
        public bool DecoyKept => _decoyKept;

        public override void Link(MechanismLinker link) => _decoy = link.Read<IDecoy>(_p.Decoy);

        public override void Reset(in Checkpoint checkpoint)
        {
            Init((int)EscortState.Patrol);
            _x = _p.StartX; _dir = 1; _mt = 0; _stopFor = _p.CaughtStop;     // B.stopFor ?? 2
            _decoyKept = checkpoint.Past(_p.KeptAfter);
            _decoyHeld = false;
            _decoyX = _decoyKept ? _p.KeepX : 0;
            _heroHeld = false; _heroT = 0;
            _rng.Reseed((long)_p.Seed);
        }

        public override void Step(in StepContext ctx)
        {
            double dt = ctx.Dt;

            // The escorted act is the motor's (#4, L6127–L6134): it follows him once he walks, and stops when the act ends.
            if (State == EscortState.EscortHim && _heroHeld)
            {
                var pl = ctx.Player;
                if (!pl.Escorted || !_sense.Alive)                                                     // L6413, L6421
                {
                    _heroHeld = false;
                    if (_sense.Alive && pl.X <= _p.HeroHomeArrive) Emit(ctx, (int)EscortEvent.HimHome, 0, pl.X);   // L6133
                    ToStop(ctx, _p.CaughtStop);
                }
                else
                {
                    _heroT += dt;
                    if (_heroT >= _p.HeroHold)
                    {
                        _x = Math.Max(_x, pl.X + _p.FollowMin);                                        // L6132
                        _x = Math.Min(_x, pl.X + _p.FollowMax);
                    }
                }
            }

            // updateTrolley14b (#7), L6358–L6410.
            _mt += dt;
            switch (State)
            {
                case EscortState.Patrol:
                    _x += _dir * _p.Speed * dt;
                    if (_x >= _p.PatrolX1 && _dir > 0) { _x = _p.PatrolX1; Enter(ctx, (int)EscortState.Turn); _mt = 0; }
                    if (_x <= _p.PatrolX0 && _dir < 0) { _x = _p.PatrolX0; Enter(ctx, (int)EscortState.Turn); _mt = 0; }
                    if (_rng.NextDouble() < dt * _p.SqueakPatrol) Emit(ctx, (int)EscortEvent.Squeak);
                    break;
                case EscortState.Turn:
                    if (_mt > _p.Pause) { _dir = -_dir; Enter(ctx, (int)EscortState.Patrol); _mt = 0; Emit(ctx, (int)EscortEvent.Turned); }
                    break;
                case EscortState.Stop:
                    if (_mt > _stopFor) { _dir = 1; Enter(ctx, (int)EscortState.Patrol); _mt = 0; }
                    break;
                case EscortState.EscortFigure:
                    if (_mt > _p.FigureDelay)
                    {
                        _decoyX = Math.Max(_p.KeepX, _decoyX - _p.EscortSpeed * dt);
                        _x = _decoyX + _p.FigureLead;
                        if (_rng.NextDouble() < dt * _p.SqueakEscort) Emit(ctx, (int)EscortEvent.Squeak);
                        if (_decoyX <= _p.KeepX + 1e-3)
                        {
                            _decoyKept = true;
                            Emit(ctx, (int)EscortEvent.FigureKept, 0, _decoyX);
                            ToStop(ctx, _p.KeepStop);
                        }
                    }
                    return;
                case EscortState.EscortHim:
                    return;
            }
            if (State != EscortState.Patrol && State != EscortState.Turn) return;

            // Looking: him first if both are in the beam and he is nearer (L6394–L6410).
            var hero = ctx.Player;
            bool him = SeesHim(hero), it = SeesDecoy();
            double dHim = Math.Abs(hero.X - _x), dFig = it ? Math.Abs(_decoy.DecoyX - _x) : 0;
            if (him && (!it || dHim < dFig))
            {
                Enter(ctx, (int)EscortState.EscortHim); _mt = 0;
                _heroHeld = true; _heroT = 0;
                Emit(ctx, (int)EscortEvent.CaughtHim, 0, _x);
                return;
            }
            if (it)
            {
                Enter(ctx, (int)EscortState.EscortFigure); _mt = 0; _dir = -1;
                _decoyHeld = true; _decoyX = _decoy.DecoyX;
                Emit(ctx, (int)EscortEvent.FigureSeen, 0, _x);
            }
        }

        /// <summary><c>seenHim</c>, L6364–L6368.</summary>
        private bool SeesHim(in PlayerPose hero)
        {
            if (_sense.Region != _p.Region || !_sense.Alive) return false;
            if (hero.Hiding && hero.Z > _p.HiddenDepth) return false;
            if (hero.Escorted) return false;                                                           // L6368
            double a = BeamLo, b = BeamHi;
            return hero.X > Math.Max(a, _p.WallX) && hero.X < b && hero.Y < _p.SeeBelowY;
        }

        /// <summary><c>seenFig</c>, L6369.</summary>
        private bool SeesDecoy()
        {
            if (_decoy == null || _decoyKept || _decoyHeld || !_decoy.DecoyInView) return false;
            double x = _decoy.DecoyX;
            return x > BeamLo && x < BeamHi;
        }

        private void ToStop(in StepContext ctx, double seconds)
        {
            Enter(ctx, (int)EscortState.Stop); _mt = 0; _stopFor = seconds;
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("x", _x); w.WriteLong("dir", _dir); w.WriteDouble("mt", _mt); w.WriteDouble("stopFor", _stopFor);
            w.WriteDouble("decoyX", _decoyX); w.WriteBool("decoyHeld", _decoyHeld); w.WriteBool("decoyKept", _decoyKept);
            w.WriteDouble("heroT", _heroT); w.WriteBool("heroHeld", _heroHeld);
            _rng.Write(w, "rng");
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            _x = r.ReadDouble("x"); _dir = (int)r.ReadLong("dir"); _mt = r.ReadDouble("mt"); _stopFor = r.ReadDouble("stopFor");
            _decoyX = r.ReadDouble("decoyX"); _decoyHeld = r.ReadBool("decoyHeld"); _decoyKept = r.ReadBool("decoyKept");
            _heroT = r.ReadDouble("heroT"); _heroHeld = r.ReadBool("heroHeld");
            _rng.Read(r, "rng");
            // The escorted act is the motor's, and the motor is not in the snapshot (a reload places him afresh): a
            // restored hold would start the escort over. End it as a cut act does (L6413, L6421): he is let go and it
            // stops for B.stopFor, without the event, which belongs to the run that was cut.
            if (_heroHeld)
            {
                _heroHeld = false; _heroT = 0;
                if (State == EscortState.EscortHim) { Init((int)EscortState.Stop); _mt = 0; _stopFor = _p.CaughtStop; }
            }
        }
    }
}
