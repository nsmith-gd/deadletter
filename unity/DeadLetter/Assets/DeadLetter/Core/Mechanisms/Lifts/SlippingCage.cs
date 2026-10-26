using System;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Lifts
{
    /// <summary>The prototype's <c>c.phase</c> (L5020–L5050), in order of a full ride.</summary>
    public enum SlippingCageState
    {
        /// <summary>At the top, waiting for him (<c>top</c>).</summary>
        Top,
        /// <summary>Too light (fewer than two plates): drops a hand's breadth and holds (<c>dip</c>).</summary>
        Dip,
        /// <summary>Hauls itself back up after a dip (<c>haulDip</c>).</summary>
        HaulDip,
        Settle,
        Lower,
        /// <summary>Entered: <c>persist.cageDanger = true</c> (L5037).</summary>
        Shudder,
        Slip,
        /// <summary>Caught once at landing + 0.35 (<c>stall</c>).</summary>
        Stall,
        /// <summary>The pawl bit: easing onto the landing (<c>bite</c>).</summary>
        Bite,
        /// <summary>Held at the landing (<c>caught</c>). Entered: <c>persist.cageDanger = false</c> (L5046).</summary>
        Caught,
        /// <summary>Hit the buffers in the sump (<c>crash</c>).</summary>
        Crash,
        /// <summary>Hauled back up after a crash (<c>haul</c>).</summary>
        Haul,
    }

    public enum SlippingCageEvent
    {
        /// <summary>He stepped in: start the cage act (<c>game.act = { kind: 'cage' }</c>). Index 0 = too light (dip), 1 = the full ride (L5022, L5032).</summary>
        RideStart,
        /// <summary>The dip bottoms out: crash 0.4, alarm bell, shake 0.4 (L5025).</summary>
        DipBang,
        /// <summary>The cage act ends; Index = <see cref="SlippingCage.QuirkNone"/>, <see cref="SlippingCage.QuirkStartle"/> (after a dip, L5029) or <see cref="SlippingCage.QuirkProud"/> (caught, L5094).</summary>
        RideEnd,
        /// <summary>He rode it into the buffers: <c>die('fall')</c> (L5044).</summary>
        Death,
    }

    public sealed class SlippingCageParams
    {
        /// <summary>The counterweight tray (an <see cref="ILoad"/>): Load = plates in the tray, 0 … 2 (L5016).</summary>
        public MechanismId Tray;
        /// <summary>The cage's pawl (a <see cref="CageCatch"/>, added before the cage). None: the cage can never be caught.</summary>
        public MechanismId Catch;
        /// <summary>Plates the counterweight needs before the cage will ride (L5020, L5031).</summary>
        public double PlatesNeeded = 2;
        /// <summary>The shaft; he is inside it 0.1 in from either side and within 0.05 of the floor (L5014).</summary>
        public double ShaftX0, ShaftX1, Inset = 0.1, FloorTolerance = 0.05;
        public double Top = 3.4, Landing = 1.6, Bottom = -0.1;
        /// <summary>Dip: 0.38 m with no plates, 0.22 with one, eased over 0.35 s, held to 1.6 s, hauled up at 0.4 m/s, ready 0.8 s later (L5023–L5029).</summary>
        public double DipEmpty = 0.38, DipOne = 0.22, DipTime = 0.35, DipHold = 1.6, HaulDipSpeed = 0.4, ReadyAfterDip = 0.8;
        /// <summary>Settle 0.04 m over 0.9 s, lower after 1.0 s at 0.32 m/s to Top − 0.55, shudder 0.7 s (L5036–L5038).</summary>
        public double SettleDrop = 0.04, SettleTime = 0.9, SettleHold = 1.0, LowerSpeed = 0.32, LowerBy = 0.55, ShudderTime = 0.7;
        /// <summary>Slip: accel 2.6 up to 1.6 m/s; caught once at Landing + 0.35; stall 0.75 s; slips again from 0.3 m/s (L5039–L5045).</summary>
        public double SlipAccel = 2.6, SlipMax = 1.6, CatchAbove = 0.35, StallTime = 0.75, StallSlip = 0.3;
        /// <summary>Bite: eases onto the landing at rate 9 for 0.5 s; his act ends 0.4 s after it is caught (L5046, L5094).</summary>
        public double BiteRate = 9, BiteTime = 0.5, ProudAfter = 0.4;
        /// <summary>Crash: held 1.4 s, hauled up at 0.7 m/s, ready 1.6 s later (L5047–L5048).</summary>
        public double CrashHold = 1.4, HaulSpeed = 0.7, ReadyAfterHaul = 1.6;
        /// <summary>Caught at the landing past this checkpoint (resetCh1, L4100).</summary>
        public string CaughtAfter;

        /// <summary>DL-09: the slipping cage (<c>CG</c>, L3899–L3900; L5007–L5096).</summary>
        public static SlippingCageParams Dl09Cage() => new SlippingCageParams
        {
            Tray = "dl09.tray",
            Catch = "dl09.cagePawl",
            ShaftX0 = 33 + 68.2, ShaftX1 = 33 + 69.8,           // CG.shaft = OFF3 + 68.2 … 69.8 = 101.2 … 102.8
            Top = 3.4, Landing = 1.6, Bottom = -0.1,             // CG.top, CG.landing = DECK, CG.bottom
            CaughtAfter = "landing8",
        };
    }

    /// <summary>
    /// The DL-09 slipping cage (<c>dl09.cage</c>; §4.13f; <c>updateCage</c> L5011–L5077, <c>updateCageAct</c> L5079–L5095).
    /// Too light (tray &lt; 2 plates) it dips and hauls back; loaded, it settles, lowers, shudders, slips, catches once
    /// just above the landing, stalls, and slips again; thrown inside [landing − 0.06, landing + 0.45] its pawl
    /// (<see cref="CageCatch"/>, <c>dl09.cagePawl</c>) bites and it eases onto the landing; otherwise it hits the buffers
    /// (death if he rides it) and is hauled back up.
    /// Signals: <see cref="Position"/> = the cage floor's y, metres (CageCatch's window is on it); <see cref="ILiftRide"/>
    /// carries him for the whole cage act (<c>game.y = c.y</c>, L5081), including the step it ends or kills him.
    /// Inputs (from the cage act, step #4, before the graph): <see cref="PullPawl"/> on Use; the boarding rule reads
    /// <see cref="PlayerPose.Grounded"/> and <see cref="PlayerPose.Holding"/> (<c>game.grounded &amp;&amp; !game.hold</c>, L5020/L5031).
    /// The view's lever, pawl, sheave, lamps and counterweight (L5052–L5076) read <see cref="Position"/>, State and the
    /// catch's <c>Thrown</c>.
    /// </summary>
    public sealed class SlippingCage : Lift
    {
        public const int QuirkNone = 0, QuirkStartle = 1, QuirkProud = 2;

        private readonly SlippingCageParams _p;
        private ILoad _tray;
        private CageCatch _catch;
        private double _t, _v, _readyIn;
        private bool _needExit, _caughtOnce, _riding;

        public SlippingCage(MechanismId id, SlippingCageParams p) : base(id) { _p = p; }

        public SlippingCageState State => (SlippingCageState)StateCode;
        /// <summary>The cage floor's y, metres (<c>c.y</c>).</summary>
        public override double Position => Y;
        public double Y { get; private set; }
        /// <summary>Slip speed, m/s, downward (<c>c.v</c>).</summary>
        public double SlipSpeed => _v;
        /// <summary>Seconds in the current phase (<c>c.t</c>).</summary>
        public double Elapsed => _t;
        /// <summary>He is in the cage act (the prototype's <c>game.act.kind === 'cage'</c>).</summary>
        public bool Riding => _riding;
        /// <summary>The y it catches once at (<c>catchY</c>, L5035).</summary>
        public double CatchY => _p.Landing + _p.CatchAbove;
        /// <summary>The phases in which Use throws the pawl (L5085).</summary>
        public bool PawlThrowable => _riding && IsThrowable(State);

        private static bool IsThrowable(SlippingCageState s)
            => s == SlippingCageState.Lower || s == SlippingCageState.Shudder || s == SlippingCageState.Slip || s == SlippingCageState.Stall;

        /// <summary>
        /// Use during the cage act (L5085): throws the pawl if the phase allows it. Forwards to the catch's
        /// <see cref="CageCatch.Throw"/>, which judges the window on this tick's start position, as the act did.
        /// </summary>
        public void PullPawl()
        {
            if (PawlThrowable && _catch != null) _catch.Throw();
        }

        public override void Link(MechanismLinker link)
        {
            _tray = link.Read<ILoad>(_p.Tray) ?? throw new InvalidOperationException(Id + " needs a Tray.");
            _catch = link.Read<CageCatch>(_p.Catch);
        }

        public override void Reset(in Checkpoint cp)
        {
            bool caught = cp.Past(_p.CaughtAfter);                                                 // L4100
            Y = caught ? _p.Landing : _p.Top;
            Init((int)(caught ? SlippingCageState.Caught : SlippingCageState.Top));
            _t = _v = 0;
            _readyIn = 0;                                                                         // readyAt: 0
            _needExit = _caughtOnce = _riding = false;
            InitFloor(Y);
        }

        public override void Step(in StepContext ctx)
        {
            double dt = ctx.Dt, y = Y;
            var pl = ctx.Player;
            bool grounded = pl.Grounded, holding = pl.Holding, wasRiding = _riding;
            _readyIn -= dt;                                                                       // game.clock += dt (#1)

            // The cage act (#4), before updateCage.
            if (_catch != null && _catch.Engaged && IsThrowable(State)) { Enter(ctx, (int)SlippingCageState.Bite); _t = 0; }   // L5089
            if (State == SlippingCageState.Caught && _riding && After(_t, _p.ProudAfter))                                       // L5094
                EndRide(ctx, QuirkProud);

            // updateCage (#7).
            _t += dt;                                                                             // L5013
            bool inside = pl.X > _p.ShaftX0 + _p.Inset && pl.X < _p.ShaftX1 - _p.Inset && Math.Abs(pl.Y - y) < _p.FloorTolerance;   // L5014
            double loaded = _tray.Load;
            if (!inside) _needExit = false;                                                       // L5019
            bool canBoard = inside && grounded && !pl.Busy && !holding && _readyIn < -Slack && !_needExit;
            if (State == SlippingCageState.Top && canBoard && loaded < _p.PlatesNeeded)           // L5020
            {
                Enter(ctx, (int)SlippingCageState.Dip); _t = 0;
                StartRide(ctx, 0);
            }
            if (State == SlippingCageState.Dip)
            {
                y = _p.Top - (loaded > 0 ? _p.DipOne : _p.DipEmpty) * Smooth.Step(_t / _p.DipTime);        // L5024
                if (After(_t, _p.DipTime) && !After(_t - dt, _p.DipTime)) Emit(ctx, (int)SlippingCageEvent.DipBang);   // L5025
                if (After(_t, _p.DipHold)) { Enter(ctx, (int)SlippingCageState.HaulDip); _t = 0; }  // L5026
            }
            else if (State == SlippingCageState.HaulDip)
            {
                y = Math.Min(_p.Top, y + _p.HaulDipSpeed * dt);                                    // L5028
                if (y >= _p.Top)
                {
                    Enter(ctx, (int)SlippingCageState.Top);
                    _needExit = true; _readyIn = _p.ReadyAfterDip;                                 // L5029
                    if (_riding) EndRide(ctx, QuirkStartle);
                }
            }
            if (State == SlippingCageState.Top && canBoard && loaded >= _p.PlatesNeeded)          // L5031
            {
                Enter(ctx, (int)SlippingCageState.Settle); _t = 0;
                _catch?.Rearm();                                                                  // c.thrown = false
                StartRide(ctx, 1);
            }

            double landing = _p.Landing, catchY = CatchY;
            switch (State)
            {
                case SlippingCageState.Settle:
                    y = _p.Top - _p.SettleDrop * Smooth.Step(_t / _p.SettleTime);                  // L5036
                    if (After(_t, _p.SettleHold)) { Enter(ctx, (int)SlippingCageState.Lower); _t = 0; }
                    break;
                case SlippingCageState.Lower:
                    y -= _p.LowerSpeed * dt;                                                       // L5037
                    if (y < _p.Top - _p.LowerBy) { Enter(ctx, (int)SlippingCageState.Shudder); _t = 0; }
                    break;
                case SlippingCageState.Shudder:
                    if (After(_t, _p.ShudderTime)) { Enter(ctx, (int)SlippingCageState.Slip); _t = 0; _v = 0; }   // L5038
                    break;
                case SlippingCageState.Slip:
                    _v = Math.Min(_p.SlipMax, _v + _p.SlipAccel * dt); y -= _v * dt;               // L5040
                    if (y <= catchY && !_caughtOnce)                                               // L5041
                    {
                        y = catchY; _caughtOnce = true;
                        Enter(ctx, (int)SlippingCageState.Stall); _t = 0;
                    }
                    if (y <= _p.Bottom)                                                            // L5042
                    {
                        y = _p.Bottom;
                        Enter(ctx, (int)SlippingCageState.Crash); _t = 0;
                        if (_riding) { _riding = false; Emit(ctx, (int)SlippingCageEvent.Death); }  // L5044
                    }
                    break;
                case SlippingCageState.Stall:
                    if (After(_t, _p.StallTime)) { Enter(ctx, (int)SlippingCageState.Slip); _t = 0; _v = _p.StallSlip; }   // L5045
                    break;
                case SlippingCageState.Bite:
                    y += (landing - y) * (1 - Smooth.DecayFactor(_p.BiteRate, dt));               // L5046, exact at 60 Hz (§3.1)
                    if (After(_t, _p.BiteTime)) { y = landing; Enter(ctx, (int)SlippingCageState.Caught); _t = 0; }
                    break;
                case SlippingCageState.Crash:
                    if (After(_t, _p.CrashHold)) { Enter(ctx, (int)SlippingCageState.Haul); _t = 0; }   // L5047
                    break;
                case SlippingCageState.Haul:
                    y = Math.Min(_p.Top, y + _p.HaulSpeed * dt);                                   // L5048
                    if (y >= _p.Top)
                    {
                        Enter(ctx, (int)SlippingCageState.Top); _t = 0; _caughtOnce = false; _readyIn = _p.ReadyAfterHaul;
                        if (_riding) EndRide(ctx, QuirkNone);
                    }
                    break;
            }

            Y = y;
            MoveFloor(ctx, y);
            Carrying = _riding || wasRiding;                                                      // the step it ends too (and his fall follows it, L5044)
        }

        private void StartRide(in StepContext ctx, int full)
        {
            _riding = true;
            Emit(ctx, (int)SlippingCageEvent.RideStart, full);
        }

        private void EndRide(in StepContext ctx, int quirk)
        {
            _riding = false;
            Emit(ctx, (int)SlippingCageEvent.RideEnd, quirk);
        }

        protected override void WriteLift(ISnapshotWriter w)
        {
            w.WriteDouble("y", Y);
            w.WriteDouble("t", _t);
            w.WriteDouble("v", _v);
            w.WriteDouble("readyIn", _readyIn);
            w.WriteBool("needExit", _needExit);
            w.WriteBool("caughtOnce", _caughtOnce);
            w.WriteBool("riding", _riding);
        }

        protected override void ReadLift(ISnapshotReader r)
        {
            Y = r.ReadDouble("y");
            _t = r.ReadDouble("t");
            _v = r.ReadDouble("v");
            _readyIn = r.ReadDouble("readyIn");
            _needExit = r.ReadBool("needExit");
            _caughtOnce = r.ReadBool("caughtOnce");
            _riding = r.ReadBool("riding");
        }
    }
}
