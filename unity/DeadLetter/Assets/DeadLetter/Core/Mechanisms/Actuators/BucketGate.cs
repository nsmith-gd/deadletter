using System;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Actuators
{
    public enum GateBucketEvent
    {
        /// <summary>A weight left the carrier and is tumbling toward the bucket (<c>Sound.scrape</c>, <c>ch1.tumbledAt</c>, L5000).</summary>
        Tumbling,
        /// <summary>It landed in the bucket (<c>Sound.clank</c>, a thud 0.25 s later, shake 0.2, L5003). Index = weights now.</summary>
        Landed,
    }

    public sealed class GateBucketParams
    {
        /// <summary>The tumble from the carrier into the bucket, seconds (<c>T.t += dt / 0.7</c>, L4959).</summary>
        public double TumbleTime = 0.7;
        /// <summary>From this checkpoint on the bucket holds <see cref="FullCount"/> weights (<c>past(cp, 'gallery') ? 2 : 0</c>, L4099).</summary>
        public string FullAfter = "gallery";
        public int FullCount = 2;

        /// <summary>DL-07: the gallery gate's bucket at <c>HP.bucketX</c> = OFF3 + 39.0 (L3893, L4099, L4991–L5003).</summary>
        public static GateBucketParams Dl07Bucket() => new GateBucketParams();
    }

    /// <summary>
    /// The DL-07 gallery gate's counterweight bucket (§4.13d). A weight tipped toward it by the carrier line
    /// (<see cref="Routes.CarrierLineEvent.LoadToBucket"/>; the Runtime calls <see cref="Drop"/> for each, as it calls
    /// <c>CarrierLine.Place</c> for the loader) tumbles for 0.7 s, then counts (L4991–L5003). Weights never leave it.
    /// Signal: <see cref="Load"/> = the weights in it (the HUD pips, <c>Pips.set('bucket6', s.bucket)</c>, L4828).
    /// </summary>
    public sealed class GateBucket : Mechanism, ILoad
    {
        /// <summary>Most weights in the air at once (a carrier tips two, 0.18 s apart).</summary>
        public const int MaxTumbling = 4;

        private readonly GateBucketParams _p;
        private readonly double[] _tumble = new double[MaxTumbling];
        private readonly bool[] _announced = new bool[MaxTumbling];
        private int _tumbling;

        public GateBucket(MechanismId id, GateBucketParams p) : base(id)
        {
            _p = p ?? throw new ArgumentNullException(nameof(p));
            if (!(p.TumbleTime >= 0)) throw new ArgumentException("TumbleTime must be >= 0.", nameof(p));
        }

        /// <summary>Weights landed in the bucket.</summary>
        public int Weights { get; private set; }
        public double Load => Weights;
        /// <summary>Weights on their way in.</summary>
        public int Tumbling => _tumbling;

        /// <summary>A weight tumbles out of a carrier toward the bucket (between steps; it counts when it lands).</summary>
        public void Drop()
        {
            if (_tumbling == MaxTumbling) { Weights++; return; }       // never drop one: land the overflow at once
            _tumble[_tumbling] = 0;
            _announced[_tumbling] = false;
            _tumbling++;
        }

        public override void Reset(in Checkpoint cp)
        {
            Weights = cp.Past(_p.FullAfter) ? _p.FullCount : 0;           // L4099
            _tumbling = 0;
            Init(0);
        }

        public override void Step(in StepContext ctx)
        {
            for (int i = 0; i < _tumbling; i++)
            {
                if (!_announced[i]) { _announced[i] = true; Emit(ctx, (int)GateBucketEvent.Tumbling); }
                _tumble[i] += ctx.Dt;
                if (_tumble[i] < _p.TumbleTime - 1e-9) continue;
                Weights++;
                Emit(ctx, (int)GateBucketEvent.Landed, Weights);
                for (int j = i + 1; j < _tumbling; j++) { _tumble[j - 1] = _tumble[j]; _announced[j - 1] = _announced[j]; }
                _tumbling--;
                i--;
            }
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteLong("weights", Weights);
            w.WriteLong("n", _tumbling);
            for (int i = 0; i < _tumbling; i++) { w.WriteDouble("t" + i, _tumble[i]); w.WriteBool("seen" + i, _announced[i]); }
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            long n = r.ReadLong("n");
            if (n < 0 || n > MaxTumbling) throw new InvalidOperationException("Snapshot has " + n + " tumbling weights; '" + Id + "' holds " + MaxTumbling + ".");
            Weights = (int)r.ReadLong("weights");
            _tumbling = (int)n;
            for (int i = 0; i < _tumbling; i++) { _tumble[i] = r.ReadDouble("t" + i); _announced[i] = r.ReadBool("seen" + i); }
        }
    }

    public enum BucketGateState { Shut, Rising, Stalled, Open }

    public enum BucketGateEvent
    {
        /// <summary>It rose to a partial target and stalls there: strain, creak 0.6, shake 0.15, the bucket's pips flash (L4831). Index = weights.</summary>
        Strain,
        /// <summary>It reached the full opening.</summary>
        Opened,
    }

    public sealed class BucketGateParams
    {
        /// <summary>The weights (an <see cref="ILoad"/>, a count): <see cref="GateBucket"/>.</summary>
        public MechanismId Bucket;
        /// <summary>Lane x of the gate.</summary>
        public double X;
        /// <summary><c>gate6Target(b) = b ≥ 2 ? 1.4 : 0.38 · b</c> (L3892).</summary>
        public double OpenHeight = 1.4, PerWeight = 0.38;
        public int WeightsToOpen = 2;
        /// <summary>Rises at 0.45 m/s; it never comes down (L4829–L4830).</summary>
        public double RiseSpeed = 0.45;
        /// <summary>Below this the gate stops him (<c>s.gate6 &lt; 0.8</c>, L4179).</summary>
        public double PassHeight = 0.8;
        /// <summary>
        /// "Never a crouch gap" (L4825–L4826): a partial opening stays this far under his crouch height (CROUCH_H 0.58,
        /// L310) so it never looks like a gap he could duck through.
        /// </summary>
        public double CrouchHeight = 0.58, CrouchMargin = 0.1;

        /// <summary>DL-07: the gallery gate at <c>HP.gateX</c> = OFF3 + 41.9, on the bucket (L3892–L3893, L4825–L4837).</summary>
        public static BucketGateParams Dl07Gate() => new BucketGateParams { Bucket = "dl07.bucket", X = 33 + 41.9 };
    }

    /// <summary>
    /// The DL-07 gallery gate, hoisted by its bucket (§4.13d; L3892, L4825–L4837). Target = 1.4 m with 2 weights,
    /// 0.38 m per weight otherwise (never a crouch gap); it rises at 0.45 m/s toward the target and never falls. Reaching
    /// a partial target it stalls with a strain (<see cref="BucketGateEvent.Strain"/>). Signals: <see cref="Position"/> =
    /// height, metres; <see cref="Engaged"/> = fully open; <see cref="Blocks"/> = he cannot pass (L4179).
    /// </summary>
    public sealed class BucketGate : Mechanism, IPositionSource, IEngageable
    {
        private readonly BucketGateParams _p;
        private ILoad _bucket;

        public BucketGate(MechanismId id, BucketGateParams p) : base(id)
        {
            _p = p ?? throw new ArgumentNullException(nameof(p));
            if (p.WeightsToOpen < 1) throw new ArgumentException("WeightsToOpen must be >= 1.", nameof(p));
            double partial = p.PerWeight * (p.WeightsToOpen - 1);
            if (partial > p.CrouchHeight - p.CrouchMargin)
                throw new ArgumentException("A partial opening of " + partial + " m would be a crouch gap (crouch " + p.CrouchHeight + " m).", nameof(p));
        }

        public BucketGateState State => (BucketGateState)StateCode;
        /// <summary>Gate height, metres (<c>s.gate6</c>).</summary>
        public double Position { get; private set; }
        public bool Engaged => Position >= _p.OpenHeight - 1e-9;
        /// <summary>The gate stops him at its x (<c>gate6 &lt; 0.8</c>, L4179).</summary>
        public bool Blocks => Position < _p.PassHeight;
        public double Target => TargetFor(Weights);
        private int Weights => (int)Math.Floor(_bucket.Load + 1e-9);

        /// <summary><c>gate6Target</c> (L3892), with a partial opening held under the crouch gap.</summary>
        public double TargetFor(int weights)
        {
            if (weights >= _p.WeightsToOpen) return _p.OpenHeight;
            return Math.Min(_p.PerWeight * Math.Max(0, weights), _p.CrouchHeight - _p.CrouchMargin);
        }

        public override void Link(MechanismLinker link) => _bucket = link.Read<ILoad>(_p.Bucket)
            ?? throw new InvalidOperationException(Id + " needs a Bucket.");

        /// <summary>At the bucket's target, which is already reset (<c>gate6: past(cp, 'gallery') ? 1.4 : 0</c>, L4099).</summary>
        public override void Reset(in Checkpoint cp)
        {
            Position = Target;
            Init((int)Resting());
        }

        public override void Step(in StepContext ctx)
        {
            double target = Target;
            if (Position < target)                                                                   // L4829
            {
                Position = Math.Min(target, Position + _p.RiseSpeed * ctx.Dt);                      // L4830
                if (Position >= target)
                {
                    if (target < _p.OpenHeight) Emit(ctx, (int)BucketGateEvent.Strain, Weights);    // L4831
                    else Emit(ctx, (int)BucketGateEvent.Opened, Weights);
                    Enter(ctx, (int)Resting());
                }
                else Enter(ctx, (int)BucketGateState.Rising);
            }
        }

        private BucketGateState Resting()
            => Position >= _p.OpenHeight - 1e-9 ? BucketGateState.Open : Position > 0 ? BucketGateState.Stalled : BucketGateState.Shut;

        protected override void WriteFields(ISnapshotWriter w) => w.WriteDouble("y", Position);

        protected override void ReadFields(ISnapshotReader r) => Position = r.ReadDouble("y");
    }
}
