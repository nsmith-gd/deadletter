using System;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Beings
{
    /// <summary>The White's states (<c>white.state</c>, L7050, L7122–L7180).</summary>
    public enum WhiteState { Away, Patrol, Listen, Approach, Surface, Slap, Strike, Sink, Lured, Flee }

    public enum WhiteEvent
    {
        /// <summary>It heard a sound (makeNoise accepted, L7101). Index 1 if it was his; Value = where it will look.</summary>
        Heard,
        /// <summary>A ring on the water where it swims near the surface (≥ 0.18 s apart, L7144, L7215). Value = x, size 0.12.</summary>
        Ripple,
        /// <summary>A first sighting (L7272, L7372, L4996). Index = water index; Value = splash (0 = silent).</summary>
        Shown,
        /// <summary>Hunt water, first find: hiss, hiss off 0.9 s later, splash 1, shake 0.4, his Startle quirk; it sinks (L7150–L7152).</summary>
        Warn,
        /// <summary>Scare water: the slap lands (splash 1.2, shake 0.6). The driver knocks him back (<c>knockBack</c>, L7189)
        /// toward Index (±1), and runs the water's onScare (<c>ch1.scared</c>, L7329). L7158.</summary>
        Slap,
        /// <summary>Hunt water: the jaws close (frame 14). The driver kills him: <c>die('grabbed', {hold: Value})</c>,
        /// held at the JawTip bone (Runtime). L7161–L7163.</summary>
        Grab,
        /// <summary>0.25 s into the grab: it drags him back and under (clip WhiteDrag, splash 1.5). L7164.</summary>
        Drag,
    }

    /// <summary>Its clips (<c>whiteClip</c>, L7086–L7092; tracks shifted −1/24 s, L7058–L7062). Swim, Glide and Nose loop.</summary>
    public enum WhiteClip { None, Glide, Swim, Listen, Surface, Sink, Roll, Slap, Lunge, Drag, Nose }

    public sealed class WhiteParams
    {
        /// <summary>The waters it can be in, in the prototype's <c>WATERS</c> order (the first active one wins, L7107).</summary>
        public WaterBody[] Waters = new WaterBody[0];
        /// <summary>Seed of its patrol RNG (replaces Math.random at L7136, §9 #11).</summary>
        public ulong Seed = 0x5EED_0FF1CE_D17UL;

        public double GlideSpeed = 0.25, ApproachSpeed = 1.25;          // WHITE_SPEED, L7051
        public double Depth = 0.32;                                     // WHITE_DEPTH, L7051
        public double FleeSpeed = 2, FleeDepth = 1.2;                   // L7125
        public double HearRange = 2.5;                                  // ± 2.5·loud past the water, L7099
        public double HeardInset = 0.3;                                 // heard x clamped 0.3 inside, L7101
        public double RunNear = 1.4;                                    // L7119 (pass 3: 1.4 m, not 2.2)
        public double RunSpeed = (0.9 + 1.6) / 2;                       // (WALK + RUN) / 2, L7120, L304
        public double RunCooldown = 0.35;                               // L7120
        public double RunLoud = 1;                                      // L7120
        public double PatrolRetarget = 6, PatrolArrive = 0.1, PatrolInset = 0.4;   // L7136
        public double HeardFresh = 0.2;                                 // L7138
        public double ListenSpeed = 0.05, ListenGlimpse = 0.3, Listen = 0.7;       // L7140–L7141
        public double ApproachDepth = 0.14, SurfaceArrive = 0.2;        // L7143, L7145
        public double RippleLead = 0.4, RippleSize = 0.12, RippleGap = 0.18;       // L7144, L7215
        public double SurfaceDepth = 0.02, SurfaceSpeed = 0.1;          // L7147
        public double SurfaceTimeoutGlimpse = 1.6, SurfaceTimeout = 2.2;           // L7154
        public double SlapHit = 0.35, SlapGiveUp = 1.3;                 // L7158–L7159
        public double StrikeHit = 0.56, StrikeGiveUp = 2.4;             // L7161, L7175
        public double GrabHold = 1.6, DragAfter = 0.25;                 // L7163–L7164
        public double SinkSpeed = 0.1, SinkTime = 1.2;                  // L7177–L7178
        public double LureNose = 0.5, LureArrive = 0.15, NoseDepth = 0.12;         // L7129–L7130
        public double LureBreakRange = 2.2, LureBreakFresh = 0.1;       // L7132
        public double BodyLength = 2.5, BodyInset = 0.15;               // L7183–L7186
        public double RiseRate = 2.5;                                   // y eases at min(1, dt·2.5), L7187
        public double TurnBelow = 0.2;                                  // turns only 0.2 under the surface, L7194
        public double CarefulMargin = 2.0;                              // wantsRun, L1925

        /// <summary>Chapter 1's three waters (heap, sump, lane), as the prototype's single White uses them.</summary>
        public static WhiteParams Chapter1() => new WhiteParams { Waters = new[] { WaterBody.Heap(), WaterBody.Sump7(), WaterBody.Lane9() } };

        /// <summary>DL-11 The Child at the Address: the flooded lane only.</summary>
        public static WhiteParams Dl11() => new WhiteParams { Waters = new[] { WaterBody.Lane9() } };
    }

    /// <summary>
    /// The White (port_architecture §4.15; L7040–L7198, L7234–L7273, L7326–L7330, L4996): something blind in the flood
    /// water that hunts by sound and never leaves the water. A port of <c>makeNoise</c>, <c>lureWhite</c>,
    /// <c>scareWhite</c> and <c>updateWhite</c>; the ripples, the Animator and the JawTip follow are Runtime
    /// (<c>WhiteView</c>, <c>RipplePool</c>), fed by <see cref="Clip"/> and the events.
    /// <para>Inputs: <see cref="StepContext.Player"/> (x, y), <see cref="BeingSenses"/> (speed, footing, alive, region,
    /// upper) and its <see cref="NoiseBus"/> (sounds, lures, scares, sighting cues), read at the start of Step in the
    /// order posted. Add it to the graph after every mechanism that posts noise (the prototype's <c>updateWhite</c> is
    /// step #8); a noise posted after it steps is dropped when the bus clears.</para>
    /// <para>Outputs: <see cref="WhiteEvent.Slap"/> (knock him back), <see cref="WhiteEvent.Grab"/> (kill him, death
    /// <c>grabbed</c>), <see cref="WantsCareful"/> (the motor's no-auto-run-by-the-water rule, L1925).</para>
    /// <para>Its time is its own clock (the prototype's <c>game.clock</c>), restarted by Reset; every timer is relative
    /// to it. <see cref="Warned"/> is a <c>persist</c> flag (L7150): it outlives Reset (respawn) and is cleared by
    /// <see cref="NewGame"/>; U-14 saves it.</para>
    /// <para>Deliberate deviations: on a respawn the prototype's White carries on where it was (nothing resets it); Core
    /// derives it from the checkpoint like every mechanism (§4.28): away, then patrolling from the water's centre. Its
    /// <c>y</c> easing <c>min(1, dt·2.5)</c> is the exact 60 Hz decay. The drag clip is kept (the prototype re-asserts
    /// WhiteLunge the same frame, L7162 vs L7164).</para>
    /// </summary>
    public sealed class WhiteBrain : Mechanism
    {
        private readonly WhiteParams _p;
        private readonly BeingSenses _sense;
        private readonly BeingRng _rng;

        private int _water = -1;
        private double _x, _y = -1, _tx;
        private int _facing = 1, _bodyFacing = 1;
        private double _t, _clock;
        private bool _heard, _heardHim;
        private double _heardX, _heardLoud, _heardAt;
        private bool _lure;
        private double _lureX, _lureUntil;
        private int _lureDir;
        private double _fleeUntil, _lastNoise = -9, _lastRipple = -9;
        private bool _hit;
        private double _heldT = -1;
        private long _shown;
        private WhiteClip _clip;
        private double _clipFade;

        public WhiteBrain(MechanismId id, WhiteParams p, BeingSenses senses) : base(id)
        {
            _p = p ?? throw new ArgumentNullException(nameof(p));
            _sense = senses ?? throw new ArgumentNullException(nameof(senses));
            if (_p.Waters.Length > 63) throw new ArgumentException("At most 63 waters per White.", nameof(p));
            _rng = new BeingRng(_p.Seed);
        }

        public WhiteState State => (WhiteState)StateCode;
        /// <summary>The water it is in (null: away).</summary>
        public WaterBody Water => _water >= 0 ? _p.Waters[_water] : null;
        /// <summary>Its snout's lane x.</summary>
        public double X => _x;
        public double Y => _y;
        /// <summary>Where it is swimming to.</summary>
        public double TargetX => _tx;
        /// <summary>+1 facing +x (yaw 0), −1 facing −x (yaw π).</summary>
        public int Facing => _facing;
        /// <summary>The way the body model faces: it only turns while deep (L7194).</summary>
        public int BodyFacing => _bodyFacing;
        /// <summary>Seconds in the current state (<c>white.t</c>).</summary>
        public double StateTime => _t;
        /// <summary>Its clock: seconds since Reset.</summary>
        public double Clock => _clock;
        public WhiteClip Clip => _clip;
        /// <summary>Crossfade seconds for <see cref="Clip"/> (0.3 by default, slap 0.1, lunge 0.08, drag 0.1).</summary>
        public double ClipFade => _clipFade;
        public bool HasHeard => _heard;
        public double HeardX => _heardX;
        public bool Lured => _lure && _clock < _lureUntil;
        public bool Fleeing => _clock < _fleeUntil;
        /// <summary><c>persist.warned</c>: the hunt water has warned him once; it strikes from now on.</summary>
        public bool Warned { get; set; }

        /// <summary>Start over (<c>clearLetters</c> clears <c>persist</c>, L4133).</summary>
        public void NewGame() => Warned = false;

        /// <summary>
        /// <c>wantsRun</c>'s careful rule (L1925): within 2 m of scare or hunt water, auto-run walks. The driver sets
        /// <c>D17Motor.Careful</c> from this before the motor steps (it reads last step's water, as the prototype does).
        /// </summary>
        public bool WantsCareful(double heroX)
        {
            if (_water < 0) return false;
            var w = _p.Waters[_water];
            return w.Part != WaterPart.Glimpse && heroX > w.X0 - _p.CarefulMargin && heroX < w.X1 + _p.CarefulMargin;
        }

        public override void Reset(in Checkpoint checkpoint)
        {
            Init((int)WhiteState.Away);
            _water = -1;
            _x = 0; _y = -1; _tx = 0;                       // the prototype's initial white (L7049–L7050)
            _facing = 1; _bodyFacing = 1;
            _t = 0; _clock = 0;
            _heard = false; _heardHim = false; _heardX = 0; _heardLoud = 0; _heardAt = 0;
            _lure = false; _lureX = 0; _lureUntil = 0; _lureDir = 0;
            _fleeUntil = 0; _lastNoise = -9; _lastRipple = -9;
            _hit = false; _heldT = -1;
            _shown = 0;                                      // sumpShown/heapShown/whiteShown live in game.ch1 (L4110)
            _clip = WhiteClip.None; _clipFade = 0;
            _rng.Seed(_p.Seed);
        }

        public override void Step(in StepContext ctx)
        {
            double dt = ctx.Dt;
            _clock += dt;
            var hero = ctx.Player;

            // The death act's follow (#4): 0.25 s after the grab it drags him under (L7164).
            if (_heldT >= 0)
            {
                _heldT += dt;
                if (_heldT > _p.DragAfter) { _heldT = -1; SetClip(WhiteClip.Drag, 0.1); Emit(ctx, (int)WhiteEvent.Drag, 0, 1.5); }
            }

            // Noises and cues made earlier this step (motor #4, mechanisms #6–#7), against last step's water.
            var bus = _sense.Noises;
            for (int i = 0; i < bus.Count; i++) Sense(ctx, bus[i]);

            // The lane's first sighting (updateRingC #7, before updateWhite; L7271–L7272).
            if (_water >= 0)
            {
                var sw = _p.Waters[_water];
                if (!double.IsNaN(sw.ShowWhenHeroPastX) && hero.X > sw.ShowWhenHeroPastX) Show(ctx, _water);
            }

            // Which water (L7110–L7111).
            int wi = SelectWater(hero.X);
            if (wi != _water)
            {
                _water = wi; _heard = false; _lure = false;
                SetState(ctx, wi >= 0 ? WhiteState.Patrol : WhiteState.Away);
                _x = wi >= 0 ? _p.Waters[wi].Centre : 0;
            }
            if (_water < 0) return;
            var w = _p.Waters[_water];
            _t += dt;

            // His own noise: running near the water (L7117–L7121). (Landing comes from the motor, through the bus.)
            if (_sense.Alive)
            {
                bool near = hero.X > w.X0 - _p.RunNear && hero.X < w.X1 + _p.RunNear;
                if (near && _sense.Grounded && Math.Abs(_sense.Vx) > _p.RunSpeed && _clock - _lastNoise > _p.RunCooldown)
                    MakeNoise(ctx, hero.X, _p.RunLoud, _sense.Region, true);
            }

            double surf = w.Y, ty = surf - _p.Depth, speed = _p.GlideSpeed;
            bool glimpse = w.Part == WaterPart.Glimpse;
            var st = State;
            if (st == WhiteState.Flee)                                                                       // L7125
            {
                ty = surf - _p.FleeDepth; speed = _p.FleeSpeed; _tx = _x;
                if (_clock > _fleeUntil) SetState(ctx, WhiteState.Patrol);
            }
            else if (st == WhiteState.Lured && !Lured)                                                       // L7126–L7127
            {
                _lure = false; SetState(ctx, WhiteState.Sink);
            }
            else if (Lured && st != WhiteState.Strike)                                                       // L7128–L7133
            {
                if (st != WhiteState.Lured) SetState(ctx, WhiteState.Lured);
                int ldir = _lureDir != 0 ? _lureDir : (_lureX >= _x ? 1 : -1);
                _tx = _lureX - _p.LureNose * ldir; speed = _p.ApproachSpeed;
                if (Math.Abs(_x - _tx) < _p.LureArrive) { ty = surf - _p.NoseDepth; _facing = ldir > 0 ? 1 : -1; SetClip(WhiteClip.Nose); }
                else SetClip(WhiteClip.Swim);
                // Running nearby still turns it: the bell holds it, it doesn't deafen it.
                if (_heard && _heardHim && _heardLoud >= 1 && _clock - _heardAt < _p.LureBreakFresh && Math.Abs(hero.X - _x) < _p.LureBreakRange)
                {
                    _lure = false; SetState(ctx, WhiteState.Approach);
                }
            }
            else if (st == WhiteState.Patrol)                                                                // L7135–L7138
            {
                if (_t > _p.PatrolRetarget || Math.Abs(_x - _tx) < _p.PatrolArrive)
                {
                    double a = w.X0 + _p.PatrolInset, b = w.X1 - _p.PatrolInset;
                    _tx = a + (b - a) * _rng.NextDouble();
                    _t = 0;
                }
                SetClip(WhiteClip.Glide);
                if (_heard && _clock - _heardAt < _p.HeardFresh) SetState(ctx, WhiteState.Listen);
            }
            else if (st == WhiteState.Listen)                                                                // L7139–L7141
            {
                SetClip(WhiteClip.Listen); speed = _p.ListenSpeed;
                if (_t > (glimpse ? _p.ListenGlimpse : _p.Listen)) SetState(ctx, WhiteState.Approach);
            }
            else if (st == WhiteState.Approach)                                                              // L7142–L7145
            {
                _tx = _heard ? _heardX : _x; speed = _p.ApproachSpeed; ty = surf - _p.ApproachDepth;
                SetClip(WhiteClip.Swim);
                int side = Smooth.Sign(_tx - _x); if (side == 0) side = 1;
                Ripple(ctx, _x + _p.RippleLead * side);
                if (Math.Abs(_x - _tx) < _p.SurfaceArrive) SetState(ctx, WhiteState.Surface);
            }
            else if (st == WhiteState.Surface)                                                               // L7146–L7155
            {
                ty = surf - _p.SurfaceDepth; speed = _p.SurfaceSpeed;
                SetClip(glimpse ? WhiteClip.Roll : WhiteClip.Surface);
                double d = hero.X - _x;
                bool exposed = w.HeroNear(hero.X, hero.Y) && Math.Abs(d) < w.Reach && _sense.Alive;
                if (w.Part == WaterPart.Hunt && exposed && !Warned)
                {
                    Warned = true; Emit(ctx, (int)WhiteEvent.Warn); SetState(ctx, WhiteState.Sink);
                }
                else if (!glimpse && exposed)
                {
                    _facing = d >= 0 ? 1 : -1;
                    SetState(ctx, w.Part == WaterPart.Scare ? WhiteState.Slap : WhiteState.Strike);
                }
                else if (_t > (glimpse ? _p.SurfaceTimeoutGlimpse : _p.SurfaceTimeout)) SetState(ctx, WhiteState.Sink);
            }
            else if (st == WhiteState.Slap)                                                                  // L7156–L7159
            {
                ty = surf + w.LedgeH - 0.25; speed = 0; SetClip(WhiteClip.Slap, 0.1);
                if (_t > _p.SlapHit && !_hit)
                {
                    _hit = true;
                    int dir = Smooth.Sign(hero.X - _x); if (dir == 0) dir = -1;
                    Emit(ctx, (int)WhiteEvent.Slap, dir, 1.2);
                }
                if (_t > _p.SlapGiveUp) { _hit = false; SetState(ctx, WhiteState.Sink); }
            }
            else if (st == WhiteState.Strike)                                                                // L7160–L7176
            {
                ty = surf + w.LedgeH - 0.25; speed = 0;
                if (_clip != WhiteClip.Drag) SetClip(WhiteClip.Lunge, 0.08);
                if (_t > _p.StrikeHit && !_hit)                                                             // jaws close at frame 14
                {
                    _hit = true; _heldT = 0;
                    Emit(ctx, (int)WhiteEvent.Grab, 0, _p.GrabHold);
                }
                if (_t > _p.StrikeGiveUp) { _hit = false; SetState(ctx, WhiteState.Sink); }
            }
            else if (st == WhiteState.Sink)                                                                  // L7177–L7179
            {
                SetClip(WhiteClip.Sink); speed = _p.SinkSpeed;
                if (_t > _p.SinkTime) { _heard = false; SetState(ctx, WhiteState.Patrol); }
            }

            // Swim, then keep the whole body in the water: the snout leads, the tail trails (L7181–L7186).
            _x += Smooth.Clamp(_tx - _x, -speed * dt, speed * dt);
            double body = _p.BodyLength * w.Scale;
            double lo = _facing > 0 ? w.X0 + body : w.X0 + _p.BodyInset, hi = _facing > 0 ? w.X1 - _p.BodyInset : w.X1 - body;
            _x = lo <= hi ? Smooth.Clamp(_x, lo, hi) : w.Centre + _facing * body / 2;
            _y = ty + (_y - ty) * Smooth.DecayFactor(_p.RiseRate, dt);                                       // L7187
            var now = State;
            if (now == WhiteState.Patrol || now == WhiteState.Approach || now == WhiteState.Flee
                || (Lured && Math.Abs(_x - _tx) >= _p.LureArrive))                                           // L7188–L7190
            {
                int dir = Smooth.Sign(_tx - _x);
                if (dir != 0) _facing = dir;
            }
            if (_y < w.Y - _p.TurnBelow) _bodyFacing = _facing;                                              // L7194
        }

        private void Sense(in StepContext ctx, in NoiseEvent e)
        {
            switch (e.Kind)
            {
                case NoiseKind.Sound: MakeNoise(ctx, e.X, e.Loud, e.Region, e.FromHim); break;
                case NoiseKind.Lure:                                                                         // L7105
                    if (_water < 0) return;
                    _lure = true; _lureX = e.X; _lureDir = e.Dir; _lureUntil = _clock + e.Seconds;
                    break;
                case NoiseKind.Scare:                                                                        // L7106
                    _fleeUntil = _clock + e.Seconds;
                    if (State != WhiteState.Away) SetState(ctx, WhiteState.Flee);
                    break;
                case NoiseKind.Show:
                    if (_water >= 0 && _p.Waters[_water].Id == e.Water) Show(ctx, _water);
                    break;
            }
        }

        /// <summary><c>makeNoise</c>, L7096–L7103.</summary>
        private void MakeNoise(in StepContext ctx, double x, double loud, int region, bool him)
        {
            if (_water < 0) return;
            var w = _p.Waters[_water];
            if (w.Region != region || State == WhiteState.Flee || _clock < _fleeUntil) return;
            if (x < w.X0 - _p.HearRange * loud || x > w.X1 + _p.HearRange * loud) return;
            if (Lured && loud < 1) return;                                                                  // a bell drowns out a footstep
            _heard = true;
            _heardX = Smooth.Clamp(x, w.X0 + _p.HeardInset, w.X1 - _p.HeardInset);
            _heardLoud = loud; _heardAt = _clock; _heardHim = him;
            _lastNoise = _clock;
            Emit(ctx, (int)WhiteEvent.Heard, him ? 1 : 0, _heardX);
        }

        /// <summary>A first sighting: it surfaces at the water's ShowX, once per water until Reset.</summary>
        private void Show(in StepContext ctx, int wi)
        {
            long bit = 1L << wi;
            var w = _p.Waters[wi];
            if ((_shown & bit) != 0 || double.IsNaN(w.ShowX)) return;
            _shown |= bit;
            _x = w.ShowX; _tx = _x;
            if (w.ShowClearsHeard) _heard = false;
            SetState(ctx, WhiteState.Surface);
            Emit(ctx, (int)WhiteEvent.Shown, wi, w.ShowSplash);
        }

        private int SelectWater(double heroX)
        {
            var ws = _p.Waters;
            for (int i = 0; i < ws.Length; i++)
            {
                var w = ws[i];
                if (w.Region == _sense.Region && (!w.LowerOnly || !_sense.Upper) && heroX < w.ActiveBelowX) return i;
            }
            return -1;
        }

        /// <summary><c>spawnRipple</c>'s gate (L7213–L7216); the pool of 25 is Runtime's.</summary>
        private void Ripple(in StepContext ctx, double x)
        {
            if (_clock - _lastRipple < _p.RippleGap) return;
            _lastRipple = _clock;
            Emit(ctx, (int)WhiteEvent.Ripple, 0, x);
        }

        /// <summary><c>setWhite</c>, L7107: the state clock restarts even when the state is the same.</summary>
        private void SetState(in StepContext ctx, WhiteState s)
        {
            _t = 0;
            Enter(ctx, (int)s);
        }

        private void SetClip(WhiteClip c, double fade = 0.3)
        {
            if (_clip == c) return;
            _clip = c; _clipFade = fade;
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteLong("water", _water);
            w.WriteDouble("x", _x); w.WriteDouble("y", _y); w.WriteDouble("tx", _tx);
            w.WriteLong("facing", _facing); w.WriteLong("bodyFacing", _bodyFacing);
            w.WriteDouble("t", _t); w.WriteDouble("clock", _clock);
            w.WriteBool("heard", _heard); w.WriteBool("heardHim", _heardHim);
            w.WriteDouble("heardX", _heardX); w.WriteDouble("heardLoud", _heardLoud); w.WriteDouble("heardAt", _heardAt);
            w.WriteBool("lure", _lure); w.WriteDouble("lureX", _lureX); w.WriteDouble("lureUntil", _lureUntil); w.WriteLong("lureDir", _lureDir);
            w.WriteDouble("fleeUntil", _fleeUntil); w.WriteDouble("lastNoise", _lastNoise); w.WriteDouble("lastRipple", _lastRipple);
            w.WriteBool("hit", _hit); w.WriteDouble("heldT", _heldT);
            w.WriteLong("shown", _shown); w.WriteBool("warned", Warned);
            w.WriteLong("clip", (long)_clip); w.WriteDouble("clipFade", _clipFade);
            w.WriteLong("rng", _rng.State);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            _water = (int)r.ReadLong("water");
            _x = r.ReadDouble("x"); _y = r.ReadDouble("y"); _tx = r.ReadDouble("tx");
            _facing = (int)r.ReadLong("facing"); _bodyFacing = (int)r.ReadLong("bodyFacing");
            _t = r.ReadDouble("t"); _clock = r.ReadDouble("clock");
            _heard = r.ReadBool("heard"); _heardHim = r.ReadBool("heardHim");
            _heardX = r.ReadDouble("heardX"); _heardLoud = r.ReadDouble("heardLoud"); _heardAt = r.ReadDouble("heardAt");
            _lure = r.ReadBool("lure"); _lureX = r.ReadDouble("lureX"); _lureUntil = r.ReadDouble("lureUntil"); _lureDir = (int)r.ReadLong("lureDir");
            _fleeUntil = r.ReadDouble("fleeUntil"); _lastNoise = r.ReadDouble("lastNoise"); _lastRipple = r.ReadDouble("lastRipple");
            _hit = r.ReadBool("hit"); _heldT = r.ReadDouble("heldT");
            _shown = r.ReadLong("shown"); Warned = r.ReadBool("warned");
            _clip = (WhiteClip)r.ReadLong("clip"); _clipFade = r.ReadDouble("clipFade");
            _rng.State = r.ReadLong("rng");
        }
    }
}
