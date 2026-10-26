using System;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Drives
{
    public enum PairedBlindState
    {
        /// <summary>Both blinds at their targets.</summary>
        Still,
        /// <summary>The chain is running: a blind is travelling.</summary>
        Winding,
        /// <summary>Running while A is held (the pole through A's wheel, the bag on W1's cord): the clutch slips, B moves alone.</summary>
        Slipping,
    }

    public enum PairedBlindEvent
    {
        /// <summary>A wind reached the chain. Index = winds so far, Value = 1 if A was held (L5367–L5372, L6087–L6092).</summary>
        Wind,
        /// <summary>A wind sent A up (DL-14a: the light gown on W1's hook rides up with it, <c>A.liftedGown</c>, L6090).</summary>
        ARaised,
        /// <summary>DL-14a: a second wind or later with W1 free: they only swap (<c>failAtt('14a')</c>, L6091).</summary>
        WrongTry,
        /// <summary>The first time the chain runs against the jam: he looks round at wheel A 1.0–3.6 s later (<c>rattleAt</c>, L5451–L5452).</summary>
        FirstSlip,
        /// <summary>Grinding where the chain drags the locked wheel: every 0.32 s of slipping (<c>Sound.scrape</c>, L5458–L5459).</summary>
        Grind,
        /// <summary>B passed <see cref="PairedBlindParams.PeelAt"/>: the panel peels (1.6 s), and the <c>child</c> cue plays (L5474).</summary>
        Peel,
    }

    /// <summary>What an unheld wind does (the two scenes differ only when both blinds are down).</summary>
    public enum PairedBlindRule
    {
        /// <summary>DL-14: A goes up as B comes down only from (A down, B up); from anything else A comes down as B goes up (L5369–L5370).</summary>
        SwapFromADown,
        /// <summary>DL-14a: decided by A alone: A up → A comes down, B goes up; A down → A goes up, B comes down (L6089–L6090).</summary>
        SwapByA,
    }

    public sealed class PairedBlindParams
    {
        /// <summary>The crank (an <see cref="IPositionSource"/> counting winds; see <see cref="WindCrank"/>).</summary>
        public MechanismId Crank;
        /// <summary>Holds A (an <see cref="IEngageable"/>): DL-14's window pole through A's wheel, DL-14a's bag on W1's cord hook.</summary>
        public MechanismId Hold;
        public PairedBlindRule Rule = PairedBlindRule.SwapFromADown;
        /// <summary>Full travel time, seconds: <c>b.a += sign · min(|Δ|, dt / 2.2)</c> (L5439–L5440, L6221–L6222).</summary>
        public double Travel = 2.2;
        /// <summary>DL-14a: while held, A is pulled fully down at once (<c>A.t1 = 1; A.w1 = 1</c>, L6223). DL-14's pole holds A wherever it is.</summary>
        public bool HoldPullsADown;
        /// <summary>DL-14a counts a wind after the first with W1 free as a wrong try (L6091).</summary>
        public bool CountWrongTries;

        /// <summary>A blind counts as down (a ledge out, the room dark) at ≥ this (<c>attOut</c> L5243; <c>w &lt; 0.95</c> leaks, L6224).</summary>
        public double OutAt = 0.95;
        /// <summary>The ledge hinges down with <c>smooth((v − 0.75) / 0.25)</c> (L5441).</summary>
        public double LedgeFrom = 0.75, LedgeSpan = 0.25;
        /// <summary>Ledges (lane x0..x1, top h), solid only once out and to someone already above <see cref="LedgeAMinY"/> (L5261–L5262). Empty = none.</summary>
        public double LedgeAX0 = double.NaN, LedgeAX1 = double.NaN, LedgeAH, LedgeAMinY;
        public double LedgeBX0 = double.NaN, LedgeBX1 = double.NaN, LedgeBH, LedgeBMinY;

        /// <summary>B past this peels the panel over <see cref="PeelTime"/> s (L5474–L5475). Infinity = no panel.</summary>
        public double PeelAt = double.PositiveInfinity, PeelTime = 1.6;
        /// <summary>The clutch behind A spins at this rate, rad/s, while slipping (L5473). Grind every <see cref="GrindEvery"/> s (L5459); ≤ 0 = silent.</summary>
        public double ClutchRate = 9, GrindEvery = 0.32;

        /// <summary>DL-14a: W1's cord hook and W1's hem follow A: <c>hook14a</c>, <c>hem14a</c> (L5933–L5934). NaN = none.</summary>
        public double HookUp = double.NaN, HookDown = double.NaN, HemUp = double.NaN, HemDown = double.NaN;

        /// <summary>From this checkpoint both are down (and the panel peeled), with <see cref="DoneWinds"/> winds counted.</summary>
        public string DoneAfter;
        public int DoneWinds;

        /// <summary>
        /// DL-14 The Window: one chain, blinds A and B; the pole left through A's wheel holds A up, so the first wind sends
        /// B down alone and peels the panel; ledges A (236.4–237.6, 1.1) and B (237.8–239.0, 1.6) fold out when down
        /// (L291, L5237–L5238, L5261–L5262, L5364–L5376, L5437–L5475).
        /// </summary>
        public static PairedBlindParams Dl14Blinds() => new PairedBlindParams
        {
            Crank = "dl14.crank", Hold = "dl14.pole", Rule = PairedBlindRule.SwapFromADown,
            LedgeAX0 = 236.4, LedgeAX1 = 237.6, LedgeAH = 1.1, LedgeAMinY = 0.5,          // ATT.ledgeA, L291; game.y > 0.5, L5261
            LedgeBX0 = 237.8, LedgeBX1 = 239.0, LedgeBH = 1.6, LedgeBMinY = 1.0,          // ATT.ledgeB, L291; game.y > 1.0, L5262
            PeelAt = 0.9,                                                                  // B.b > 0.9, L5474
            DoneAfter = "hatch14", DoneWinds = 3,                                          // resetAtt, L5237–L5238
        };

        /// <summary>
        /// DL-14a Lights Out: the same drive (W1 = A, W2 = B); the laundry bag on W1's cord hook holds W1 down so W2 goes
        /// alone; the light gown does not, and rides up with W1 (L5886–L5893, L5914, L6083–L6092, L6219–L6224).
        /// </summary>
        public static PairedBlindParams Dl14aBlinds() => new PairedBlindParams
        {
            Crank = "dl14a.crank", Hold = "dl14a.hook", Rule = PairedBlindRule.SwapByA,
            HoldPullsADown = true, CountWrongTries = true, GrindEvery = 0,
            HookUp = 2.0, HookDown = 0.75, HemUp = 3.21, HemDown = 1.93,                  // ATT3 hookUp/hookDown, roller/hemDown, L5890–L5893
            DoneAfter = "corridor", DoneWinds = 0,                                         // dark = p('corridor'), L5914
        };
    }

    /// <summary>
    /// Two outputs on one chain (§4.13g, the "Paired outputs" rule): each wind of the crank sends one blind down and the
    /// other up; with A held, the clutch behind A's wheel slips and B goes the other way alone (the jam). Positions are
    /// 0 (rolled up) .. 1 (down). DL-14's clutch, ledges and peel panel and DL-14a's cord hook are outputs of this one
    /// mechanism (<see cref="ClutchRad"/>, <see cref="LedgeDeploy"/>, <see cref="Peel"/>, <see cref="HookY"/>), as the
    /// prototype keeps them in one update (L5437–L5475).
    /// Signals: <see cref="Engaged"/> = both blinds down (DL-14a's night light reads it as "no leak", L6224).
    /// </summary>
    public sealed class PairedBlindDrive : Mechanism, IEngageable
    {
        private readonly PairedBlindParams _p;
        private IPositionSource _crank;
        private IEngageable _hold;
        private double _seenWinds, _clutch, _grindT, _grindAt;
        private bool _peeled, _slipSeen;

        public PairedBlindDrive(MechanismId id, PairedBlindParams p) : base(id) { _p = p; }

        public PairedBlindState State => (PairedBlindState)StateCode;
        /// <summary>Blind A (W1) and B (W2), 0 up .. 1 down, and where the chain is taking them.</summary>
        public double A { get; private set; }
        public double B { get; private set; }
        public double TargetA { get; private set; }
        public double TargetB { get; private set; }
        public int Winds { get; private set; }
        /// <summary>A held by the jam this step.</summary>
        public bool Held { get; private set; }
        /// <summary>Running against the jam (<c>s.rattle</c>): sparks, heat, the pole rattling (L5449–L5466).</summary>
        public bool Slipping => State == PairedBlindState.Slipping;
        public bool Engaged => A >= _p.OutAt && B >= _p.OutAt;
        /// <summary>Clutch angle, radians: turns with wheel A (A · 6) unless held, plus its own spin while slipping (L5473).</summary>
        public double ClutchRad => (Held ? 0 : A * 6) + _clutch;
        /// <summary>Wheel A's angle, radians, while free (it keeps its last angle while held; L5471).</summary>
        public double WheelARad => A * 6;
        /// <summary>Panel peel, 0..1 (the view rotates it −2.68 · smooth(peel) about its hinge, L5476).</summary>
        public double Peel { get; private set; }
        public bool Peeled => _peeled;
        /// <summary>DL-14a: W1's cord hook height (<c>hook14a</c>) and hem height (<c>hem14a</c>), metres.</summary>
        public double HookY => _p.HookUp - (_p.HookUp - _p.HookDown) * A;
        public double HemY => _p.HemUp - (_p.HemUp - _p.HemDown) * A;

        /// <summary>Ledge i (0 = A, 1 = B) is out, and solid (<c>attOut</c>, L5261–L5262).</summary>
        public bool LedgeOut(int i) => (i == 0 ? A : B) >= _p.OutAt;
        /// <summary>Ledge i's fold-out, 0 (flat to the wall) .. 1 (L5441).</summary>
        public double LedgeDeploy(int i) => Smooth.Step(((i == 0 ? A : B) - _p.LedgeFrom) / _p.LedgeSpan);

        /// <summary><c>surfaceAtt</c>'s ledge terms (L5261–L5262): the ledges are boards in the air, solid once out to someone already above their min y.</summary>
        public double SurfaceAt(double x, double y, double h)
        {
            if (LedgeOut(0) && y > _p.LedgeAMinY && x >= _p.LedgeAX0 && x <= _p.LedgeAX1) h = Math.Max(h, _p.LedgeAH);
            if (LedgeOut(1) && y > _p.LedgeBMinY && x >= _p.LedgeBX0 && x <= _p.LedgeBX1) h = Math.Max(h, _p.LedgeBH);
            return h;
        }

        public override void Link(MechanismLinker link)
        {
            _crank = link.Read<IPositionSource>(_p.Crank) ?? throw new InvalidOperationException(Id + " needs a Crank.");
            _hold = link.Read<IEngageable>(_p.Hold);
        }

        public override void Reset(in Checkpoint cp)
        {
            bool done = cp.Past(_p.DoneAfter);
            double v = done ? 1 : 0;
            A = B = TargetA = TargetB = v;
            Winds = done ? _p.DoneWinds : 0;
            _peeled = done && !double.IsInfinity(_p.PeelAt);
            Peel = _peeled ? 1 : 0;
            _clutch = _grindT = _grindAt = 0;
            _slipSeen = false;
            Held = _hold != null && _hold.Engaged;
            _seenWinds = _crank.Position;
            Init((int)PairedBlindState.Still);
        }

        public override void Step(in StepContext ctx)
        {
            Held = _hold != null && _hold.Engaged;
            if (_crank.Position > _seenWinds) { _seenWinds = _crank.Position; Wind(ctx); }
            else if (_crank.Position < _seenWinds) _seenWinds = _crank.Position;

            double step = ctx.Dt / _p.Travel;
            A += Smooth.Sign(TargetA - A) * Math.Min(Math.Abs(TargetA - A), step);              // L5439, L6221
            B += Smooth.Sign(TargetB - B) * Math.Min(Math.Abs(TargetB - B), step);              // L5440, L6222
            if (_p.HoldPullsADown && Held) { TargetA = 1; A = 1; }                             // L6223

            bool winding = Math.Abs(A - TargetA) > 1e-3 || Math.Abs(B - TargetB) > 1e-3;       // L5446
            bool slip = winding && Held;                                                        // s.rattle, L5449
            Enter(ctx, (int)(slip ? PairedBlindState.Slipping : winding ? PairedBlindState.Winding : PairedBlindState.Still));
            if (slip)
            {
                if (!_slipSeen) { _slipSeen = true; Emit(ctx, (int)PairedBlindEvent.FirstSlip); }   // L5451
                _clutch += ctx.Dt * _p.ClutchRate;                                               // L5473
                if (_p.GrindEvery > 0)
                {
                    _grindT += ctx.Dt;                                                           // L5458
                    if (_grindT - _grindAt > _p.GrindEvery) { _grindAt = _grindT; Emit(ctx, (int)PairedBlindEvent.Grind); }   // L5459
                }
            }

            if (B > _p.PeelAt && !_peeled) { _peeled = true; Emit(ctx, (int)PairedBlindEvent.Peel); }   // L5474
            if (_peeled) Peel = Math.Min(1, Peel + ctx.Dt / _p.PeelTime);                           // L5475
        }

        /// <summary>One wind of the chain (L5366–L5372, L6086–L6092).</summary>
        private void Wind(in StepContext ctx)
        {
            Winds++;
            bool aWasDown = TargetA > 0.5;
            if (Held) TargetB = TargetB > 0.5 ? 0 : 1;                                         // the clutch slips: B alone
            else if (_p.Rule == PairedBlindRule.SwapFromADown)
            {
                if (TargetA > 0.5 && TargetB < 0.5) { TargetA = 0; TargetB = 1; }             // A goes up as B comes down
                else { TargetA = 1; TargetB = 0; }                                             // A comes down as B goes up
            }
            else
            {
                if (TargetA < 0.5) { TargetA = 1; TargetB = 0; }
                else { TargetA = 0; TargetB = 1; }
            }
            Emit(ctx, (int)PairedBlindEvent.Wind, Winds, Held ? 1 : 0);
            if (aWasDown && TargetA < 0.5) Emit(ctx, (int)PairedBlindEvent.ARaised);
            if (_p.CountWrongTries && Winds > 1 && !Held) Emit(ctx, (int)PairedBlindEvent.WrongTry);
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("a", A); w.WriteDouble("b", B);
            w.WriteDouble("ta", TargetA); w.WriteDouble("tb", TargetB);
            w.WriteLong("winds", Winds);
            w.WriteBool("held", Held);
            w.WriteDouble("seen", _seenWinds);
            w.WriteDouble("clutch", _clutch);
            w.WriteDouble("grindT", _grindT); w.WriteDouble("grindAt", _grindAt);
            w.WriteBool("slipSeen", _slipSeen);
            w.WriteBool("peeled", _peeled); w.WriteDouble("peel", Peel);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            A = r.ReadDouble("a"); B = r.ReadDouble("b");
            TargetA = r.ReadDouble("ta"); TargetB = r.ReadDouble("tb");
            Winds = (int)r.ReadLong("winds");
            Held = r.ReadBool("held");
            _seenWinds = r.ReadDouble("seen");
            _clutch = r.ReadDouble("clutch");
            _grindT = r.ReadDouble("grindT"); _grindAt = r.ReadDouble("grindAt");
            _slipSeen = r.ReadBool("slipSeen");
            _peeled = r.ReadBool("peeled"); Peel = r.ReadDouble("peel");
        }
    }
}
