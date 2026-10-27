using System;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Lifts
{
    public enum CounterweightLiftState { Still, Rising, Falling }

    public enum CounterweightLiftEvent
    {
        /// <summary>The winding ratchet ticks every <see cref="CounterweightLiftParams.TickStep"/> of rise (<c>gateTick</c>, L3186).</summary>
        Tick,
        /// <summary>It reached the landing (h = 1) rising (<c>clunk</c>, L3188).</summary>
        Arrive,
        /// <summary>It landed falling faster than <see cref="CounterweightLiftParams.CrashSpeed"/>; Value = speed, m/s. Sound volume and shake 0.55 · min(1, v / 3) (L3192–L3194).</summary>
        Crash,
        /// <summary>The crash startled D-17: near the shaft, not in an act, not on the platform (L3195).</summary>
        Startle,
        /// <summary>He stepped onto the unlatched platform: start the <c>Teeter</c> act; Value = the x he scrambles back to (L3278–L3281, L3417).</summary>
        Teeter,
    }

    public sealed class CounterweightLiftParams
    {
        /// <summary>The pan (an <see cref="ILoad"/>): the platform's target h is the pan's load (<c>panLoad</c>, L3026–L3029).</summary>
        public MechanismId Pan;
        /// <summary>Optional pawl (an <see cref="IEngageable"/>): while engaged the platform is held at the landing (L3182). Add it first.</summary>
        public MechanismId Pawl;
        /// <summary>Used only if <see cref="Pawl"/> is unwired: latched past this checkpoint.</summary>
        public string LatchedAfter;
        /// <summary>Travel, metres (<c>RISE</c>), and the landing's y (<c>DECK</c>): floor y = Deck − Rise · (1 − h) (L3021).</summary>
        public double Rise = 2.7, Deck = 1.6;
        /// <summary>Up at <c>PLAT_SPEED</c> m/s (L3011, L3185); down with accel 8 up to 3.4 m/s; a crash above 0.6 m/s (L3191–L3193).</summary>
        public double RiseSpeed = 0.6, FallAccel = 8, FallMax = 3.4, CrashSpeed = 0.6;
        /// <summary>His weight on the platform is taken off the pan's (<c>LOAD4.d17</c>, L3013, L3182).</summary>
        public double RiderLoad = 0.5;
        /// <summary>The shaft (<c>SHAFT</c>, L3011): he is on the platform inside it by 0.02, below Deck + 0.3, above its floor − 0.12 (L3030).</summary>
        public double ShaftX0, ShaftX1;
        /// <summary>While he teeters the platform dips this far, metres (L3182).</summary>
        public double LurchDip = 0.1;
        /// <summary>He scrambles back to this far outside the nearer shaft edge (L3279).</summary>
        public double TeeterBack = 0.28;
        public double TickStep = 0.04;
        /// <summary>A crash startles him within this distance of <see cref="StartleX"/> (L3195).</summary>
        public double StartleX, StartleRadius = 3.2;

        /// <summary>DL-08: Lift 2's platform, raised by the goods pan, held by the pawl (L3007–L3030, L3171–L3207).</summary>
        public static CounterweightLiftParams Dl08Platform() => new CounterweightLiftParams
        {
            Pan = "dl08.pan",
            Pawl = "dl08.pawl",
            LatchedAfter = "latched",                         // resetWorld: h = latched ? 1 : 0 (L8043)
            ShaftX0 = 33 + 52.8, ShaftX1 = 33 + 55.3,          // SHAFT = OFF3 + 52.8 … 55.3 = 85.8 … 88.3 (L3011)
            StartleX = 33 + 53.5,                              // 86.5 (L3195)
        };
    }

    /// <summary>
    /// A platform hung against a load pan (<c>dl08.platform</c>, Lift 2; §4.13f; L3171–L3207): it winds up slowly toward
    /// the pan's load and drops fast, crashing; a pawl holds it at the landing; stepping onto it unlatched makes it dip
    /// under him and he scrambles back (Teeter, L3278–L3281, L3329–L3336).
    /// Signals: <see cref="Position"/> = h, 0 (down in the sump) … 1 (at the landing), read by the pawl's bite window
    /// (h ≥ 0.985, L3305); <see cref="ILiftRide"/> with FloorY = <c>platTop()</c> (L3021).
    /// Inputs: the Teeter act calls <see cref="EndLurch"/> when he lands back on the deck (f22, L3335).
    /// Not ported here: the camera's "platform look" (<c>riseSeen</c>, L3187, L3208) needs the pan's trolley share and
    /// belongs to the camera rules (§4.17); the view's chain, drum, needle and lamps (L3198–L3220) read Position.
    /// </summary>
    public sealed class CounterweightLift : Lift
    {
        private readonly CounterweightLiftParams _p;
        private ILoad _pan;
        private IEngageable _pawl;
        private bool _latchedByCheckpoint, _lurch, _endLurch;
        private double _ticked;

        public CounterweightLift(MechanismId id, CounterweightLiftParams p) : base(id) { _p = p; }

        public CounterweightLiftState State => (CounterweightLiftState)StateCode;
        /// <summary>h, 0 … 1 (see the class summary).</summary>
        public override double Position => H;
        public double H { get; private set; }
        /// <summary>Fall speed, m/s (<c>p.v</c>; 0 while rising or still).</summary>
        public double FallSpeed { get; private set; }
        /// <summary>The platform dips under him while he teeters (<c>plat.lurch</c>).</summary>
        public bool Lurching => _lurch;
        public bool Latched => _pawl != null ? _pawl.Engaged : _latchedByCheckpoint;

        /// <summary>Floor y for an h (<c>platTop</c>, L3021).</summary>
        public double FloorAt(double h) => _p.Deck - _p.Rise * (1 - h);

        /// <summary>The Teeter act landed him back on the deck (f22, L3335): the platform stops dipping.</summary>
        public void EndLurch() => _endLurch = true;

        public override void Link(MechanismLinker link)
        {
            _pan = link.Read<ILoad>(_p.Pan) ?? throw new InvalidOperationException(Id + " needs a Pan.");
            _pawl = link.Read<IEngageable>(_p.Pawl);
        }

        public override void Reset(in Checkpoint cp)
        {
            _latchedByCheckpoint = cp.Past(_p.LatchedAfter);
            H = Latched ? 1 : 0;                                                                   // L8043
            FallSpeed = 0;
            _ticked = 0;
            _lurch = _endLurch = false;
            Init((int)CounterweightLiftState.Still);
            InitFloor(FloorAt(H));
        }

        /// <summary><c>onPlatform4</c> (L3030) for a given h.</summary>
        public bool OnPlatform(in PlayerPose p, double h)
            => p.X > _p.ShaftX0 + 0.02 && p.X < _p.ShaftX1 - 0.02 && p.Y < _p.Deck + 0.3 && p.Y > FloorAt(h) - 0.12;

        public override void Step(in StepContext ctx)
        {
            if (_endLurch) _lurch = false;                                                          // L3335 (act, #4)
            _endLurch = false;

            var pl = ctx.Player;
            double h = H, dt = ctx.Dt;
            bool latched = Latched;
            // updateTriggers4 (#4): onto the platform before the pawl is set, it drops under him and he scrambles back.
            if (!latched && !_lurch && !pl.Busy && OnPlatform(pl, h))                               // L3417
            {
                _lurch = true;                                                                     // L3280
                double back = pl.X < (_p.ShaftX0 + _p.ShaftX1) / 2 ? _p.ShaftX0 - _p.TeeterBack : _p.ShaftX1 + _p.TeeterBack;
                Emit(ctx, (int)CounterweightLiftEvent.Teeter, 0, back);                            // L3279
            }

            double pan = _pan.Load;
            double want = latched ? 1 : _lurch ? 1 - _p.LurchDip / _p.Rise
                : Smooth.Clamp(pan - (OnPlatform(pl, h) ? _p.RiderLoad : 0), 0, 1);               // L3182
            double before = h;
            if (want > h + 1e-4)
            {
                FallSpeed = 0;
                h = Math.Min(want, h + (_p.RiseSpeed / _p.Rise) * dt);                               // L3185
                if (Math.Abs(h - _ticked) > _p.TickStep) { _ticked = h; Emit(ctx, (int)CounterweightLiftEvent.Tick); }   // L3186
                if (h >= 1 - 1e-4 && before < 1 - 1e-4) Emit(ctx, (int)CounterweightLiftEvent.Arrive);                   // L3188
            }
            else if (want < h - 1e-4)
            {
                FallSpeed = Math.Min(_p.FallMax, FallSpeed + _p.FallAccel * dt);                     // L3190
                h = Math.Max(want, h - (FallSpeed / _p.Rise) * dt);
                if (h <= want + 1e-4 && FallSpeed > _p.CrashSpeed)                                   // L3191
                {
                    Emit(ctx, (int)CounterweightLiftEvent.Crash, 0, FallSpeed);
                    if (!pl.Busy && Math.Abs(pl.X - _p.StartleX) < _p.StartleRadius && !OnPlatform(pl, h))
                        Emit(ctx, (int)CounterweightLiftEvent.Startle);                             // L3195
                    FallSpeed = 0;
                }
                _ticked = h;
            }
            H = h;
            Enter(ctx, (int)(h > before ? CounterweightLiftState.Rising : h < before ? CounterweightLiftState.Falling : CounterweightLiftState.Still));
            MoveFloor(ctx, FloorAt(h));
            Carrying = OnPlatform(pl, h);
        }

        protected override void WriteLift(ISnapshotWriter w)
        {
            w.WriteDouble("h", H);
            w.WriteDouble("v", FallSpeed);
            w.WriteDouble("ticked", _ticked);
            w.WriteBool("latchedCp", _latchedByCheckpoint);
            w.WriteBool("lurch", _lurch);
            w.WriteBool("endLurch", _endLurch);
        }

        protected override void ReadLift(ISnapshotReader r)
        {
            H = r.ReadDouble("h");
            FallSpeed = r.ReadDouble("v");
            _ticked = r.ReadDouble("ticked");
            _latchedByCheckpoint = r.ReadBool("latchedCp");
            _lurch = r.ReadBool("lurch");
            _endLurch = r.ReadBool("endLurch");
        }
    }
}
