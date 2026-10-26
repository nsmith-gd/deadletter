using System;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Save;
using DeadLetter.Core.Simulation;

namespace DeadLetter.Core.Mechanisms.Routes
{
    public enum ReturnsBeltState { Idle, Warn, Run }

    public enum ReturnsBeltEvent
    {
        /// <summary>A warning bell (<c>Sound.alarmBell</c>, at 0, 0.9 and 1.8 s; L3222–L3223). Index = 0..2.</summary>
        Bell,
        /// <summary>The belt starts (<c>Sound.klaxon</c>, 2.7 s after the warning began; L3224).</summary>
        Klaxon,
        /// <summary>A crate starts down the chute (<c>Sound.scrape</c>, L3136). Index = crate type.</summary>
        CrateSpawned,
        /// <summary>A crate landed on the belt (<c>Sound.crateLand</c>, L3157). Index = type, Value = x.</summary>
        CrateLanded,
        /// <summary>A crate went out through the turn flaps (L3163). Index = type.</summary>
        CrateGone,
    }

    public enum CrateState { Chute, Belt, Turn }

    public sealed class ReturnsBeltParams
    {
        /// <summary>The pawl (an <see cref="IEngageable"/>): once it is set and he is past <see cref="TriggerX"/>, the warning starts (L3420).</summary>
        public MechanismId Trigger;
        public double TriggerX;
        /// <summary>The belt, lane x0..x1, and its speed toward −x, m/s; the deck height (<c>BELT4</c> L3015, <c>DECK</c> L3007).</summary>
        public double X0, X1, Speed = 0.32, Deck = 1.6;
        /// <summary>The chute: crates slide from its top (x, y, Unity z) to <see cref="ChuteX"/> on the deck over 0.75 s (L3015, L3150–L3157).</summary>
        public double ChuteX, ChuteTopX, ChuteTopY, ChuteTopZ, ChuteTime = 0.75;
        /// <summary>A crate turns off when its back edge reaches TurnX; it swings out through the flaps over 1.3 s and is gone at 1.45 (L3159–L3164).</summary>
        public double TurnX, TurnTime = 1.3, TurnOutZ = 1.75, GoneAt = 1.45;
        /// <summary>Warning bells, then the belt runs (L3221–L3224).</summary>
        public double[] Bells = { 0, 0.9, 1.8 };
        public double RunAt = 2.7, FirstAfterRun = 0.3, FirstAfterReset = 0.5;
        /// <summary>Spawn every 2.9 + r · 1.3 s, only with him 0.75 clear of the chute (or up off the deck by 0.55), the last crate off the chute and 1.25 down the belt (L3141–L3144).</summary>
        public double SpawnMin = 2.9, SpawnSpread = 1.3, ClearOfChute = 0.75, ClearAbove = 0.55, BehindLast = 1.25;
        /// <summary>Crate types (half-width, height) and their odds: 55 % small, 30 %, 15 % tall (<c>CRATES</c> L3016, L3130).</summary>
        public double[] CrateHalf = { 0.18, 0.21, 0.2 }, CrateHeight = { 0.18, 0.23, 0.42 }, CrateOdds = { 0.55, 0.85 };
        /// <summary>A crate is solid in the lane while its Unity z is below this (three z &gt; −0.25, L1733).</summary>
        public double SolidZ = 0.25;
        /// <summary>Running from this checkpoint (<c>belt4</c>, L7991, L8045).</summary>
        public string RunningAfter;
        public long Seed = 1;
        public int Capacity = 12;

        /// <summary>DL-08: the returns belt toward the tunnel (L3010–L3016, L3128–L3169, L3218–L3229, L3420, L3439).</summary>
        public static ReturnsBeltParams Dl08Belt()
        {
            const double off3 = 33;                                                   // OFF3, L274
            return new ReturnsBeltParams
            {
                Trigger = "dl08.pawl", TriggerX = off3 + 55.3 + 0.6,                  // SHAFT.x1 + 0.6, L3011, L3420
                X0 = off3 + 57.7, X1 = off3 + 64.6,                                   // BELT4, L3015
                ChuteX = off3 + 64.25, ChuteTopX = off3 + 64.3, ChuteTopY = 1.6 + 1.38, ChuteTopZ = 1.75,   // CHUTE4_X, CHUTE4_TOP (z −1.75 negated)
                TurnX = off3 + 58.0,                                                  // L3159
                RunningAfter = "cage",
            };
        }
    }

    /// <summary>One crate on a <see cref="ReturnsBelt"/>.</summary>
    public sealed class Crate
    {
        internal bool Active;
        public int Type { get; internal set; }
        public CrateState State { get; internal set; }
        public double X { get; internal set; }
        public double Y { get; internal set; }
        /// <summary>Unity z (+ into the set, toward the flaps).</summary>
        public double Z { get; internal set; }
        public double T { get; internal set; }
        public double Spin { get; internal set; }
        public double Half { get; internal set; }
        public double Height { get; internal set; }
    }

    /// <summary>
    /// DL-08's returns belt (§4.13h): after the pawl is set and he is past the shaft, warning bells at 0, 0.9, 1.8 s and a
    /// klaxon at 2.7 s; then crates slide down the chute (0.75 s) and ride the belt toward him at 0.32 m/s and leave
    /// through the turn flaps (L3128–L3169, L3218–L3229). He is carried back while on it (<see cref="CarryVelocity"/>,
    /// read by the motor, L3439, L1998); crates are solid while in the lane (<see cref="SurfaceAt"/>, L1733). The crate
    /// choices use <see cref="SimRng"/> (seeded, snapshotted) for the prototype's <c>Math.random</c>.
    /// Signals: <see cref="Engaged"/> = running.
    /// </summary>
    public sealed class ReturnsBelt : Mechanism, IEngageable
    {
        private readonly ReturnsBeltParams _p;
        private readonly Crate[] _all;
        private readonly int[] _live;
        private int _count;
        private IEngageable _trigger;
        private SimRng _rng;
        private double _t, _next;

        public ReturnsBelt(MechanismId id, ReturnsBeltParams p) : base(id)
        {
            _p = p;
            _all = new Crate[p.Capacity];
            for (int i = 0; i < _all.Length; i++) _all[i] = new Crate();
            _live = new int[p.Capacity];
            _rng = SimRng.Lcg(p.Seed);
        }

        public ReturnsBeltState State => (ReturnsBeltState)StateCode;
        public bool Engaged => State == ReturnsBeltState.Run;
        public int Count => _count;
        public Crate At(int i) => _all[_live[i]];
        /// <summary>Seconds until the next crate may come (<c>b.next</c>).</summary>
        public double Next => _next;
        /// <summary>The turn flaps' swing, 0..1 (L3146–L3148).</summary>
        public double FlapSwing { get; private set; }

        /// <summary><c>beltCarry4</c> (L3439): −Speed on the belt while it runs (the caller checks he is grounded), else 0.</summary>
        public double CarryVelocity(double x) => Engaged && x > _p.X0 && x < _p.X1 ? -_p.Speed : 0;

        /// <summary>The crates' tops in the lane (<c>surfaceAt</c>, L1733).</summary>
        public double SurfaceAt(double x, double h)
        {
            for (int i = 0; i < _count; i++)
            {
                var c = At(i);
                if (c.State != CrateState.Chute && c.Z < _p.SolidZ && Math.Abs(x - c.X) <= c.Half) h = Math.Max(h, _p.Deck + c.Height);
            }
            return h;
        }

        public override void Link(MechanismLinker link) => _trigger = link.Read<IEngageable>(_p.Trigger);

        /// <summary><c>game.belt4 = { state: c.belt4 ? 'run' : 'idle', t: 0, next: 0.5 }</c>, crates cleared (L8045–L8046).</summary>
        public override void Reset(in Checkpoint cp)
        {
            _rng = SimRng.Lcg(_p.Seed);   // the same checkpoint replays the same sounds and crates
            Init((int)(cp.Past(_p.RunningAfter) ? ReturnsBeltState.Run : ReturnsBeltState.Idle));
            _t = 0;
            _next = _p.FirstAfterReset;
            for (int i = 0; i < _all.Length; i++) _all[i].Active = false;
            _count = 0;
            FlapSwing = 0;
        }

        public override void Step(in StepContext ctx)
        {
            double dt = ctx.Dt;
            if (State == ReturnsBeltState.Idle && _trigger != null && _trigger.Engaged && ctx.Player.X > _p.TriggerX && !ctx.Player.Busy)   // L3420
            {
                Enter(ctx, (int)ReturnsBeltState.Warn);
                _t = 0;
            }
            if (State == ReturnsBeltState.Warn)                                                   // L3221–L3224
            {
                double prev = _t;
                _t += dt;
                for (int k = 0; k < _p.Bells.Length; k++) if (prev <= _p.Bells[k] + 1e-9 && _t > _p.Bells[k] + 1e-9) Emit(ctx, (int)ReturnsBeltEvent.Bell, k);
                if (_t > _p.RunAt + 1e-9) { Enter(ctx, (int)ReturnsBeltState.Run); _next = _p.FirstAfterRun; Emit(ctx, (int)ReturnsBeltEvent.Klaxon); }
            }

            bool run = State == ReturnsBeltState.Run;                                              // updateCrates, L3138–L3168
            if (run)
            {
                _next -= dt;
                Crate last = _count > 0 ? At(_count - 1) : null;
                bool clear = Math.Abs(ctx.Player.X - _p.ChuteX) > _p.ClearOfChute || ctx.Player.Y > _p.Deck + _p.ClearAbove;
                if (_next <= 0 && clear && (last == null || (last.State != CrateState.Chute && last.X < _p.ChuteX - _p.BehindLast)))
                {
                    Spawn(ctx);
                    _next = _p.SpawnMin + _rng.NextDouble() * _p.SpawnSpread;
                }
            }
            double swing = 0;
            for (int i = 0; i < _count; i++)
            {
                var c = At(i);
                if (c.State == CrateState.Turn) swing = Math.Max(swing, Math.Sin(Math.PI * Smooth.Clamp((c.T - 0.45) / 0.9, 0, 1)));
            }
            FlapSwing = swing;

            for (int i = 0; i < _count; i++)
            {
                var c = At(i);
                switch (c.State)
                {
                    case CrateState.Chute:
                    {
                        c.T += dt / _p.ChuteTime;
                        double k = Math.Min(1, c.T);
                        c.X = _p.ChuteTopX + (_p.ChuteX - _p.ChuteTopX) * k;
                        c.Z = _p.ChuteTopZ * (1 - k);
                        c.Y = _p.ChuteTopY + (_p.Deck - _p.ChuteTopY) * k + 0.04 * Math.Sin(Math.PI * k);
                        if (k >= 1) { c.State = CrateState.Belt; c.Y = _p.Deck; Emit(ctx, (int)ReturnsBeltEvent.CrateLanded, c.Type, c.X); }
                        break;
                    }
                    case CrateState.Belt:
                        if (run) c.X -= _p.Speed * dt;
                        if (c.X - c.Half <= _p.TurnX) { c.State = CrateState.Turn; c.T = 0; }
                        break;
                    case CrateState.Turn:
                        c.T += dt;
                        c.Z = _p.TurnOutZ * Smooth.Step(c.T / _p.TurnTime);
                        if (c.T > _p.GoneAt + 1e-9)
                        {
                            Emit(ctx, (int)ReturnsBeltEvent.CrateGone, c.Type);
                            c.Active = false;
                            for (int k = i; k < _count - 1; k++) _live[k] = _live[k + 1];
                            _count--; i--;
                        }
                        break;
                }
            }
        }

        /// <summary><c>spawnCrate</c> (L3129–L3137).</summary>
        private void Spawn(in StepContext ctx)
        {
            int slot = -1;
            for (int i = 0; i < _all.Length; i++) if (!_all[i].Active) { slot = i; break; }
            if (slot < 0) throw new InvalidOperationException(Id + ": more than " + _all.Length + " crates.");
            double r = _rng.NextDouble();
            int type = r < _p.CrateOdds[0] ? 0 : r < _p.CrateOdds[1] ? 1 : 2;
            var c = _all[slot];
            c.Active = true;
            c.Type = type;
            c.Half = _p.CrateHalf[type];
            c.Height = _p.CrateHeight[type];
            c.X = _p.ChuteX; c.Y = _p.ChuteTopY; c.Z = _p.ChuteTopZ;
            c.State = CrateState.Chute; c.T = 0;
            c.Spin = (_rng.NextDouble() - 0.5) * 0.4;
            _live[_count++] = slot;
            Emit(ctx, (int)ReturnsBeltEvent.CrateSpawned, type);
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("t", _t);
            w.WriteDouble("next", _next);
            _rng.Write(w, "rng");
            w.WriteDouble("flaps", FlapSwing);
            w.WriteLong("n", _count);
            for (int i = 0; i < _count; i++)
            {
                var c = At(i);
                string k = "c" + i + ".";
                w.WriteLong(k + "type", c.Type); w.WriteLong(k + "state", (int)c.State);
                w.WriteDouble(k + "x", c.X); w.WriteDouble(k + "y", c.Y); w.WriteDouble(k + "z", c.Z);
                w.WriteDouble(k + "t", c.T); w.WriteDouble(k + "spin", c.Spin);
            }
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            _t = r.ReadDouble("t");
            _next = r.ReadDouble("next");
            _rng.Read(r, "rng");
            FlapSwing = r.ReadDouble("flaps");
            for (int i = 0; i < _all.Length; i++) _all[i].Active = false;
            _count = (int)r.ReadLong("n");
            for (int i = 0; i < _count; i++)
            {
                var c = _all[i];
                string k = "c" + i + ".";
                c.Active = true;
                c.Type = (int)r.ReadLong(k + "type"); c.State = (CrateState)r.ReadLong(k + "state");
                c.Half = _p.CrateHalf[c.Type]; c.Height = _p.CrateHeight[c.Type];
                c.X = r.ReadDouble(k + "x"); c.Y = r.ReadDouble(k + "y"); c.Z = r.ReadDouble(k + "z");
                c.T = r.ReadDouble(k + "t"); c.Spin = r.ReadDouble(k + "spin");
                _live[i] = i;
            }
        }
    }
}
