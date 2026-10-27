using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Bridges
{
    public enum TippingBridgeState
    {
        /// <summary>On the floor, pushable (<c>state 'free'</c>).</summary>
        Free,
        /// <summary>Held at the pit's lip with its front wheels over, teetering (<c>s.lip</c>).</summary>
        AtLip,
        /// <summary>Tipping in nose-first over <see cref="TippingBridgeParams.FallTime"/> s (<c>'falling'</c>, <c>tipInto</c>).</summary>
        Falling,
        /// <summary>Settled in the pit: a bridge (<c>'bridge'</c>).</summary>
        Bridge,
    }

    public enum TippingBridgeEvent
    {
        /// <summary>It goes over the lip (<c>tipOver</c>: <c>Sound.scrape</c>, L4741).</summary>
        Tip,
        /// <summary>It lands in the pit: thud and shake (Value = shake). The cart at drop 0.8 (L4757), the duct when settled (L4855).</summary>
        Land,
        /// <summary>The duct's splash: noise of <see cref="TippingBridgeParams.NoiseLevel"/> at the pit's middle for the White, unless the bell holds it (L4855). Value = level, Index = 0.</summary>
        Splash,
        /// <summary>
        /// He is in the pit with no bridge and not in an act: the cart's trench is too deep to climb (<c>trenchStuck</c>:
        /// flinch, respawn after 2.0 s; L4764–L4766, L4519–L4523); the duct's water turns him back (<c>waterFlinch</c> to
        /// Value = back x; L4860–L4862). Emitted each step the condition holds; the act it starts is the motor's.
        /// </summary>
        Stranded,
    }

    public sealed class TippingBridgeParams
    {
        /// <summary>Push: start x (= Min), grip gap, speed, back reach (L4274, L4285).</summary>
        public double StartX, Gap, Speed = 0.55, BackReach = 0.34, ForwardReach = 0.34;
        public int Side = +1;
        /// <summary>Half-length and height of the thing.</summary>
        public double Half, Height;
        /// <summary>The pit: lane x0..x1, floor y.</summary>
        public double PitX0, PitX1, PitFloor;
        /// <summary>It stops with its front wheels over the lip: Max = PitX0 − Half + LipOver (L4274, L4285).</summary>
        public double LipOver = 0.38;
        /// <summary>Where it settles: PitX0 + Half + SettleGap (cart 0.02, duct 0; L4757, L4855).</summary>
        public double SettleGap;
        /// <summary>Tip time and when it lands (<c>drop += dt / 0.9</c>; cart lands at 0.8, duct at 1; L4757, L4855).</summary>
        public double FallTime = 0.9, LandAt = 1, LandShake = 0.4;
        /// <summary>Noise level of the splash; 0 = none.</summary>
        public double NoiseLevel;
        /// <summary>Stranded: he is grounded below StrandBelowY with StrandFrom &lt; x &lt; StrandTo; Value = BackX (NaN = respawn).</summary>
        public double StrandFrom, StrandTo, StrandBelowY, BackX = double.NaN;
        /// <summary>A bridge from this checkpoint (§4.28: <c>past(cp, 'hall')</c>, L4094).</summary>
        public string BridgeAfter;

        /// <summary>Push range end (the lip).</summary>
        public double MaxX => PitX0 - Half + LipOver;
        public double SettleX => PitX0 + Half + SettleGap;

        /// <summary>DL-01: the depot cart (0.55 high) tips into the drain trench 6.6–8.0 at −0.8 and settles at 7.27 (L283, L3885, L4094, L4274, L4756–L4766).</summary>
        public static TippingBridgeParams Dl01Cart() => new TippingBridgeParams
        {
            StartX = 5.9, Gap = 0.97, Speed = 0.55, BackReach = 0.2,               // CART1, PUSH_SPEED L325, back 0.2 L4274
            Half = 0.65, Height = 0.55,
            PitX0 = 6.6, PitX1 = 8.0, PitFloor = -0.8,                                // PIT, L283
            LipOver = 0.38, SettleGap = 0.02,
            LandAt = 0.8, LandShake = 0.4,
            StrandFrom = 6.6 + 0.1, StrandTo = 8.0 - 0.1, StrandBelowY = -0.8 + 0.05,  // L4764
            BridgeAfter = "hall",
        };

        /// <summary>DL-11: the duct (0.26 high) tips into the flood 149.1–150.6 at −0.25 and settles at 149.85, its top at 0.01 (L3902–L3903, L4108, L4285, L4854–L4862).</summary>
        public static TippingBridgeParams Dl11Duct() => new TippingBridgeParams
        {
            StartX = 54 + 94.0, Gap = 1.10, Speed = 0.45,                              // DUCT9, OFF5 = 54
            Half = 0.75, Height = 0.26,
            PitX0 = 54 + 95.1, PitX1 = 54 + 96.6, PitFloor = -0.25,                    // DIP9
            LipOver = 0.4, SettleGap = 0,
            LandAt = 1, LandShake = 0.3, NoiseLevel = 1.5,
            StrandFrom = 54 + 95.1 - 0.17 * 0.6, StrandTo = 54 + 96.6, StrandBelowY = 0.02,   // x + HALF·0.6 > x0, L4860
            BackX = 54 + 95.1 - 0.35,
            BridgeAfter = "bedroom",
        };
    }

    /// <summary>
    /// A bridge made by tipping (§4.13j): a pushable that stops teetering at a pit's lip; let go there, or shoved on for
    /// 0.45 s (the motor's rule), it tips nose-first over 0.9 s and settles in the pit as a bridge (<c>tipInto</c>,
    /// L4738–L4750; the cart L4756–L4766, the duct L4854–L4862). Implements U-11's <see cref="IPushable"/>: the motor
    /// moves it while held; <see cref="OnReleased"/>/<see cref="OnShoved"/> only record the tip, which Step applies.
    /// Signals: <see cref="Engaged"/> = a bridge; <see cref="Position"/> = x, metres.
    /// </summary>
    public sealed class TippingBridge : Mechanism, IPushable, IEngageable, IPositionSource
    {
        private readonly TippingBridgeParams _p;
        private bool _lip, _tip, _landed;
        private double _x0tip;

        public TippingBridge(MechanismId id, TippingBridgeParams p) : base(id) { _p = p; }

        public TippingBridgeState State => (TippingBridgeState)StateCode;
        public bool Engaged => State == TippingBridgeState.Bridge;
        public double Position => X;
        /// <summary>Tip progress, 0..1 (<c>s.drop</c>).</summary>
        public double Drop { get; private set; }
        /// <summary>The view's y offset and nose dip, radians (<c>tipInto</c>, L4743–L4750; the lip's teeter is the view's, L4737).</summary>
        public double ViewY { get; private set; }
        public double DipRad { get; private set; }
        /// <summary>Push velocity, m/s (<c>s.v</c>).</summary>
        public double Velocity { get; private set; }

        // ---- IPushable ----------------------------------------------------------------------------------------------
        public InteractionCategory Category => InteractionCategory.Push;
        public double X { get; private set; }
        public int Side => _p.Side;
        public double Gap => _p.Gap;
        public double Speed => _p.Speed;
        public double Min => _p.StartX;
        public double Max => _p.MaxX;
        public double FloorY => 0;
        public double Z => 0;
        public double ForwardReach => _p.ForwardReach;
        public double BackReach => _p.BackReach;
        public bool TipsIntoPit => true;
        public bool HasDetents => false;

        /// <summary>Only while on the floor (<c>p.state().state !== 'free'</c> skips it, L4296).</summary>
        public bool IsAvailable(in InteractionQuery q) => State == TippingBridgeState.Free || State == TippingBridgeState.AtLip;

        /// <summary>The motor owns its x while held (<c>s.x = tx</c>, L4697).</summary>
        public void MoveTo(double x, double velocity) { X = x; Velocity = velocity; }
        public void SetAtLip(bool atLip) => _lip = atLip;
        public void OnReleased(bool atLip) { if (atLip) _tip = true; else _lip = false; }
        public void OnShoved() => _tip = true;
        public void OnTravelEnd() { }

        /// <summary>The pit floor with or without the bridge in it (<c>floorAt</c>, L4139–L4140); NaN outside the pit.</summary>
        public double SurfaceAt(double x)
        {
            if (x <= _p.PitX0 || x >= _p.PitX1) return double.NaN;
            return Engaged ? _p.PitFloor + _p.Height : _p.PitFloor;
        }

        public override void Reset(in Checkpoint cp)
        {
            bool bridge = cp.Past(_p.BridgeAfter);
            Init((int)(bridge ? TippingBridgeState.Bridge : TippingBridgeState.Free));
            X = bridge ? _p.SettleX : _p.StartX;
            ViewY = bridge ? _p.PitFloor : 0;
            Drop = 0; DipRad = 0; Velocity = 0;
            _lip = _tip = _landed = false;
            _x0tip = X;
        }

        public override void Step(in StepContext ctx)
        {
            if (_tip && (State == TippingBridgeState.Free || State == TippingBridgeState.AtLip))           // tipOver, L4741
            {
                Enter(ctx, (int)TippingBridgeState.Falling);
                Drop = 0; _x0tip = X; _lip = false; _landed = false; Velocity = 0;
                Emit(ctx, (int)TippingBridgeEvent.Tip);
            }
            _tip = false;

            if (State == TippingBridgeState.Free || State == TippingBridgeState.AtLip)
                Enter(ctx, (int)(_lip ? TippingBridgeState.AtLip : TippingBridgeState.Free));

            if (State == TippingBridgeState.Falling)
            {
                Drop = Math.Min(1, Drop + ctx.Dt / _p.FallTime);                                          // L4757, L4855
                if (_p.LandAt < 1 && Drop >= _p.LandAt && !_landed) { _landed = true; Emit(ctx, (int)TippingBridgeEvent.Land, 0, _p.LandShake); }
                if (Drop >= 1)
                {
                    Enter(ctx, (int)TippingBridgeState.Bridge);
                    X = _p.SettleX; ViewY = _p.PitFloor; DipRad = 0;
                    if (!_landed) { _landed = true; Emit(ctx, (int)TippingBridgeEvent.Land, 0, _p.LandShake); }
                    if (_p.NoiseLevel > 0) Emit(ctx, (int)TippingBridgeEvent.Splash, 0, _p.NoiseLevel);
                }
                else TipInto();
            }

            var pl = ctx.Player;
            // Grounded: the prototype strands him only once he has landed (game.grounded, L4764, L4860), not while he falls past StrandBelowY.
            if (State != TippingBridgeState.Bridge && !pl.Busy && pl.Grounded && pl.X > _p.StrandFrom && pl.X < _p.StrandTo && pl.Y < _p.StrandBelowY)   // L4764, L4860
                Emit(ctx, (int)TippingBridgeEvent.Stranded, 0, _p.BackX);
        }

        /// <summary><c>tipInto</c> (L4743–L4750) with t = drop: the nose drops, it slides to where it lands, a small bounce.</summary>
        private void TipInto()
        {
            double t = Drop, k = Smooth.Step(Math.Min(1, t / 0.75));
            double dip = t < 0.5 ? -0.5 * Math.Sin(t / 0.5 * Math.PI / 2)
                : -0.5 * (1 - Smooth.Step((t - 0.5) / 0.35)) + (t > 0.85 ? 0.05 * Math.Sin((t - 0.85) / 0.15 * Math.PI) : 0);
            X = _x0tip + (_p.SettleX - _x0tip) * k;
            ViewY = _p.PitFloor * k * k - Math.Abs(Math.Sin(dip)) * _p.Half * 0.45 * (1 - k);
            DipRad = dip;
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("x", X); w.WriteDouble("v", Velocity);
            w.WriteDouble("drop", Drop); w.WriteDouble("viewY", ViewY); w.WriteDouble("dip", DipRad);
            w.WriteDouble("x0tip", _x0tip);
            w.WriteBool("lip", _lip); w.WriteBool("tip", _tip); w.WriteBool("landed", _landed);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            X = r.ReadDouble("x"); Velocity = r.ReadDouble("v");
            Drop = r.ReadDouble("drop"); ViewY = r.ReadDouble("viewY"); DipRad = r.ReadDouble("dip");
            _x0tip = r.ReadDouble("x0tip");
            _lip = r.ReadBool("lip"); _tip = r.ReadBool("tip"); _landed = r.ReadBool("landed");
        }
    }
}
