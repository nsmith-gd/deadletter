using System;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Routes;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Scenes.Dl07
{
    /// <summary>Where D-17 is in region 3: down on the sorting floor, or up on the gallery (<c>game.upper</c>).</summary>
    public enum GalleryLevel { Floor, Upper }

    /// <summary>
    /// The gallery (§5 DL-07: "same floor + gallery 71.85–80.4 (r3, upper)"): whether D-17 is up on it, the prototype's
    /// <c>game.upper</c>. Up from every checkpoint from <c>landing</c> until the Attendance chapter's (<c>c.upper</c>, L7987–L7997,
    /// <c>resetWorld</c> L8032, L8039: there he stands on the deck at <c>GALLERY.h</c>); up when he hops off a carrier at the
    /// landing (L2955); down at the end of the slide (L4508). Signals: <see cref="Engaged"/> = up (the lane's
    /// <see cref="GalleryLane"/>, the scanner's <c>!game.upper</c>, the letter and the collapse through the rules).
    /// Region-free, as every mechanism is: who asks also checks <c>game.region === 3</c>.
    /// </summary>
    public sealed class Dl07Gallery : Mechanism, IEngageable
    {

        /// <summary>Up from this checkpoint (<c>landing</c>) until, not including, <see cref="UpperUntil"/> (<c>school</c>).</summary>
        public const string UpperAfter = "landing", UpperUntil = "school";

        private bool _arrive, _leave;

        public Dl07Gallery(MechanismId id) : base(id) { }

        public GalleryLevel State => (GalleryLevel)StateCode;
        public bool Upper => State == GalleryLevel.Upper;
        public bool Engaged => Upper;

        /// <summary>He has hopped off a carrier onto the gallery (the landing's alight, L2955): up from this step's mechanisms.</summary>
        public void Arrive() { _arrive = true; _leave = false; }
        /// <summary>He has slid down to the sorting floor (L4508): down from this step's mechanisms.</summary>
        public void Leave() { _leave = true; _arrive = false; }

        public override void Reset(in Checkpoint cp)
        {
            Init((int)(cp.Past(UpperAfter) && !cp.Past(UpperUntil) ? GalleryLevel.Upper : GalleryLevel.Floor));     // game.upper = !!c.upper, L8032
            _arrive = _leave = false;
        }

        public override void Step(in StepContext ctx)
        {
            if (_arrive) Enter(ctx, (int)GalleryLevel.Upper);
            if (_leave) Enter(ctx, (int)GalleryLevel.Floor);
            _arrive = _leave = false;
        }

        protected override void WriteFields(ISnapshotWriter w) { w.WriteBool("arrive", _arrive); w.WriteBool("leave", _leave); }
        protected override void ReadFields(ISnapshotReader r) { _arrive = r.ReadBool("arrive"); _leave = r.ReadBool("leave"); }
    }

    public enum Dl07LoadingEvent
    {
        /// <summary>A weight lost down the chute stands by its home again (L5004). Index = load code.</summary>
        Returned,
    }

    /// <summary>
    /// Where the sorting weights go once he sets them in a carrier (§5 DL-07: "carry weights → load carriers (two per tub) →
    /// bucket"; L4441–L4456, L4957–L4962, L4991–L5005): it follows the return line's loads and the bucket and moves the
    /// weights (<c>dl07.weight0</c>, <c>dl07.weight1</c>, load codes 1 and 2) as the prototype's receivers do, within the
    /// step: into the carrier at SetDownHigh f14 (<see cref="ItemState.InCarrier"/>; refused, on the floor at his feet,
    /// L4453), out of it as it tips toward the bucket (<see cref="ItemState.Tumble"/>), into the bucket as it lands
    /// (<see cref="ItemState.Gone"/>, <see cref="InBucket"/>), or down the chute (<see cref="ItemState.Gone"/>) and back on the
    /// floor at its home 4 s later (L5004). It steps after the line and the bucket and reads their log. Weights in the bucket
    /// stay there; every reset puts both on the floor at home (<c>resetCh1</c>, L4098, as their own Reset does).
    /// <para>The 4 s return is a <c>setTimeout</c> in the prototype, which runs at the start of the step it falls due (before
    /// #4): here the weight is back at this step's mechanisms, after #4, so for that one step's #4 it is not yet solid.</para>
    /// </summary>
    public sealed class Dl07Loading : Mechanism
    {
        public const int Weights = 2;

        private readonly MechanismId _line, _bucket;
        private readonly MechanismId[] _weightIds;
        private readonly CarriedItem[] _w = new CarriedItem[Weights];
        private readonly double[] _back = new double[Weights];
        private readonly bool[] _inBucket = new bool[Weights];
        private readonly int[] _tumbling = new int[GateBucket.MaxTumbling];
        private int _nTumbling;
        private CarrierLine _l;
        private GateBucket _b;

        public Dl07Loading(MechanismId id, MechanismId line, MechanismId bucket, MechanismId weight0, MechanismId weight1) : base(id)
        {
            _line = line; _bucket = bucket;
            _weightIds = new[] { weight0, weight1 };
        }

        /// <summary>Weight <paramref name="i"/> (0 or 1) is in the bucket (<c>it.state === 'bucket'</c>; else gone down the chute while <see cref="ItemState.Gone"/>).</summary>
        public bool InBucket(int i) => _inBucket[i];
        /// <summary>Seconds until weight <paramref name="i"/> lost down the chute is back by its home (0: not lost).</summary>
        public double ReturnsIn(int i) => _back[i];
        /// <summary>The tumble of weight <paramref name="i"/> toward the bucket, 0..1 (the prototype's <c>T.t</c>); NaN when it is not tumbling.</summary>
        public double TumbleOf(int i)
        {
            for (int k = 0; k < _nTumbling; k++) if (_tumbling[k] == i) return _b.TumbleSeconds(k) / _b.TumbleTime;
            return double.NaN;
        }

        public override void Link(MechanismLinker link)
        {
            _l = link.Read<CarrierLine>(_line) ?? throw new InvalidOperationException(Id + " needs the line.");
            _b = link.Read<GateBucket>(_bucket) ?? throw new InvalidOperationException(Id + " needs the bucket.");
            for (int i = 0; i < Weights; i++) _w[i] = link.Read<CarriedItem>(_weightIds[i]) ?? throw new InvalidOperationException(Id + " needs " + _weightIds[i] + ".");
            _l.SetLoadItems(_w[0], _w[1]);                                                     // load codes 1, 2: HP.weights' order
        }

        public override void Reset(in Checkpoint cp)
        {
            for (int i = 0; i < Weights; i++) { _back[i] = 0; _inBucket[i] = false; }
            _nTumbling = 0;
            Init(0);
        }

        public override void Step(in StepContext ctx)
        {
            // A weight lost down the chute is back by its home 4 s on (setTimeout 4000 from the tip's step, L5004).
            for (int i = 0; i < Weights; i++)
            {
                if (!(_back[i] > 0)) continue;
                _back[i] -= ctx.Dt;
                if (_back[i] > 1e-9) continue;
                _back[i] = 0;
                _w[i].Take(ctx, ItemState.Floor, _w[i].Params.HomeX, 0);                                                              // L5004: x: it.home, base: 0
                Emit(ctx, (int)Dl07LoadingEvent.Returned, i + 1);
            }
            var log = ctx.Log;
            for (int k = 0; k < log.Count; k++)
            {
                var e = log[k];
                if (e.Kind != MechanismEventKind.Event) continue;
                if (e.Id == _line)
                {
                    int i = e.Index - 1;
                    if (i < 0 || i >= Weights) continue;
                    var w = _w[i];
                    switch ((CarrierLineEvent)e.Code)
                    {
                        case CarrierLineEvent.LoadPlaced: w.Take(ctx, ItemState.InCarrier, w.X, w.BaseY); break;                     // L4447
                        case CarrierLineEvent.LoadRefused: w.Take(ctx, ItemState.Floor, ctx.Player.X, 0); break;                     // L4453
                        case CarrierLineEvent.LoadToBucket:                                                                           // L4999
                            w.Take(ctx, ItemState.Tumble, w.X, w.BaseY);
                            if (_nTumbling < _tumbling.Length) _tumbling[_nTumbling++] = i;
                            break;
                        case CarrierLineEvent.LoadLost: w.Take(ctx, ItemState.Gone, w.X, w.BaseY); _back[i] = e.Value; break;         // L5004
                    }
                }
                else if (e.Id == _bucket && e.Code == (int)GateBucketEvent.Landed && _nTumbling > 0)                                 // L4962, L5002
                {
                    int i = _tumbling[0];
                    for (int j = 1; j < _nTumbling; j++) _tumbling[j - 1] = _tumbling[j];
                    _nTumbling--;
                    _inBucket[i] = true;
                    _w[i].Take(ctx, ItemState.Gone, _w[i].X, _w[i].BaseY);
                }
            }
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            for (int i = 0; i < Weights; i++) { w.WriteDouble("back" + i, _back[i]); w.WriteBool("bucket" + i, _inBucket[i]); }
            w.WriteLong("n", _nTumbling);
            for (int k = 0; k < _nTumbling; k++) w.WriteLong("t" + k, _tumbling[k]);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            for (int i = 0; i < Weights; i++) { _back[i] = r.ReadDouble("back" + i); _inBucket[i] = r.ReadBool("bucket" + i); }
            long n = r.ReadLong("n");
            if (n < 0 || n > _tumbling.Length) throw new InvalidOperationException("Snapshot has " + n + " tumbling weights; '" + Id + "' holds " + _tumbling.Length + ".");
            _nTumbling = (int)n;
            for (int k = 0; k < _nTumbling; k++) _tumbling[k] = (int)r.ReadLong("t" + k);
        }
    }

    public enum HeapLetterState
    {
        /// <summary>Caught by twine on the gallery's front rail (<c>'rail'</c>, its start, L3907).</summary>
        Rail,
        /// <summary>He passed under it: it drops to the deck over <see cref="Dl07HeapLetter.FallSeconds"/> (<c>'fallingRail'</c>).</summary>
        Falling,
        /// <summary>Flat on the deck at <see cref="Dl07HeapLetter.X"/>, to be picked up (<c>'floor'</c>).</summary>
        Floor,
    }

    public enum HeapLetterEvent
    {
        /// <summary>It lands on the deck.</summary>
        Landed,
    }

    /// <summary>
    /// The chapter's secret letter on the gallery's rail (§5 DL-07 "heap letter"; §4.26; scene doc §2 "The letter"): the
    /// first time D-17 is on the gallery within 0.5 of it, it falls to the deck in 0.6 s (L4839–L4847, in <c>updateCh1</c>,
    /// #7). Its state is the letters system's and outlives a respawn (<c>letterState</c>, L4125); a reset sets the fall's
    /// clock to −1 (<c>resetCh1</c>: <c>heapT: -1</c>, L4111), so a fall cut short restarts a second late. Picking it up and
    /// posting it at MailSlot6 (<c>pickLetter</c>, <c>postLetter</c>, slot 6 at 77.2 upper) are the letters system's (§4.26),
    /// not ported here, as DL-02's tube letter.
    /// </summary>
    public sealed class Dl07HeapLetter : Mechanism, IPositionSource
    {
        /// <summary><c>LETTERS[1].x</c> = OFF3 + 43.4 (L3907); it falls when he is within 0.5 (L4840).</summary>
        public const double X = Dl06Lane.Off3 + 43.4, Reach = 0.5;
        /// <summary><c>t = min(1, heapT / 0.6)</c> (L4842).</summary>
        public const double FallSeconds = 0.6;

        public Dl07HeapLetter(MechanismId id) : base(id) { Init((int)HeapLetterState.Rail); T = -1; }

        /// <summary>He is on the gallery in region 3 (<c>game.region === 3 &amp;&amp; game.upper</c>): the rules' (default never).</summary>
        public Func<bool> OnGallery = () => false;

        public HeapLetterState State => (HeapLetterState)StateCode;
        /// <summary>Seconds into the fall (<c>s.heapT</c>; −1 after a reset).</summary>
        public double T { get; private set; }
        /// <summary>The fall's progress, 0..1, for the view (L4843–L4844: it drops by t² to the deck and turns flat by smooth(t)).</summary>
        public double Fall => State == HeapLetterState.Floor ? 1 : State == HeapLetterState.Falling ? Math.Max(0, Math.Min(1, T / FallSeconds)) : 0;
        public double Position => Fall;

        public override void Reset(in Checkpoint cp) => T = -1;                                                 // L4111

        public override void Step(in StepContext ctx)
        {
            if (State == HeapLetterState.Rail && OnGallery() && Math.Abs(ctx.Player.X - X) < Reach)            // L4840
            {
                Enter(ctx, (int)HeapLetterState.Falling);
                T = 0;
            }
            if (State == HeapLetterState.Falling)                                                                // L4841–L4846
            {
                T += ctx.Dt;
                if (Math.Min(1, T / FallSeconds) >= 1)
                {
                    Enter(ctx, (int)HeapLetterState.Floor);
                    Emit(ctx, (int)HeapLetterEvent.Landed);
                }
            }
        }

        protected override void WriteFields(ISnapshotWriter w) => w.WriteDouble("t", T);
        protected override void ReadFields(ISnapshotReader r) => T = r.ReadDouble("t");
    }

    public enum CollapseState
    {
        /// <summary>Whole (<c>s.collapse === 0</c>): it sags under him (<see cref="Dl07Collapse.SagRad"/>).</summary>
        Intact,
        /// <summary>Swinging down on its hinge, then falling (<c>1</c>).</summary>
        Falling,
        /// <summary>Gone, torn grating at both ends (<c>2</c>); from <c>goods</c> on it is already gone.</summary>
        Gone,
    }

    public enum CollapseEvent
    {
        /// <summary>It gives way: creak 0.8 and a groan (L7355).</summary>
        Give,
        /// <summary>It has swung down and hits: clank, chain 0.6, shake 0.6; the torn edges show (L7361).</summary>
        Hit,
        /// <summary>It lands below: thud, tumble; the panel is hidden (L7362).</summary>
        Landed,
    }

    /// <summary>
    /// The gallery collapse (§5 DL-07, §4.25 table; scene doc Pass 2 "The gallery collapse"; L7318, L7353–L7369): once he is
    /// on the gallery past <c>GALLERY6.trigger</c> 80.35, the panel behind him (78.95–80.05) swings −62° on its hinge in 0.45
    /// s, then falls; it is gone at 1.6 s. Not lethal: a one-way. From the moment it gives way the lane walls him past it
    /// (<see cref="Dl07Lane.CollapseWall"/>, L4181: <see cref="Engaged"/>), so there is no way back; from <c>goods</c> on it is
    /// gone from the start (L4110). In <c>updateHazards</c> (#10, after <c>updateCh1</c>).
    /// </summary>
    public sealed class Dl07Collapse : Mechanism, IEngageable
    {
        /// <summary>The swing (−62° over 0.45 s), the fall from then (½ g t²), gone at 1.6 s (L7357–L7362); <c>GRAVITY</c> 9.8 (L306).</summary>
        public const double SwingDeg = -62, SwingSeconds = 0.45, GoneAt = 1.6, Gravity = 9.8, SagDeg = -3, SagOver = 0.8;
        public const string GoneAfter = "goods";

        private bool _hit;

        public Dl07Collapse(MechanismId id) : base(id) { }

        /// <summary>He is on the gallery in region 3 (<c>game.region === 3 &amp;&amp; game.upper</c>): the rules' (default never).</summary>
        public Func<bool> OnGallery = () => false;

        public CollapseState State => (CollapseState)StateCode;
        /// <summary>It has given way (<c>s.collapse</c> truthy, L4181): no way back.</summary>
        public bool Engaged => State != CollapseState.Intact;
        /// <summary>Seconds since it gave way (<c>s.collapseT</c>).</summary>
        public double T { get; private set; }
        /// <summary>The panel's swing about its hinge, radians (the view's; L7357).</summary>
        public double SwingRad => State == CollapseState.Intact ? 0 : SwingDeg * Math.PI / 180 * Smooth.Step(T / SwingSeconds);
        /// <summary>How far it has dropped, metres (L7357).</summary>
        public double Drop => State == CollapseState.Falling && T > SwingSeconds ? 0.5 * Gravity * (T - SwingSeconds) * (T - SwingSeconds) : 0;
        /// <summary>The sag under him at <paramref name="x"/> while it is whole and he is on it (−3° · smooth((x − x0) / 0.8), L7366).</summary>
        public static double SagRad(double x) => x > Dl07Lane.CollapseX0 && x < Dl07Lane.CollapseX1 ? SagDeg * Math.PI / 180 * Smooth.Step((x - Dl07Lane.CollapseX0) / SagOver) : 0;

        public override void Reset(in Checkpoint cp)
        {
            Init((int)(cp.Past(GoneAfter) ? CollapseState.Gone : CollapseState.Intact));                     // L4110
            T = 0;
            _hit = false;
        }

        public override void Step(in StepContext ctx)
        {
            if (State == CollapseState.Intact && OnGallery() && ctx.Player.X > Dl07Lane.CollapseTrigger)         // L7355
            {
                Enter(ctx, (int)CollapseState.Falling);
                T = 0;
                Emit(ctx, (int)CollapseEvent.Give);
            }
            if (State != CollapseState.Falling) return;
            T += ctx.Dt;                                                                                         // L7357
            if (T > SwingSeconds && !_hit) { _hit = true; Emit(ctx, (int)CollapseEvent.Hit); }                   // L7361
            if (T > GoneAt) { Enter(ctx, (int)CollapseState.Gone); Emit(ctx, (int)CollapseEvent.Landed); }      // L7362
        }

        protected override void WriteFields(ISnapshotWriter w) { w.WriteDouble("t", T); w.WriteBool("hit", _hit); }
        protected override void ReadFields(ISnapshotReader r) { T = r.ReadDouble("t"); _hit = r.ReadBool("hit"); }
    }
}
