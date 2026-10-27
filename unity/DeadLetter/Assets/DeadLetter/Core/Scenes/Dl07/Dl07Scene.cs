using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Routes;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Scenes.Dl06;

namespace DeadLetter.Core.Scenes.Dl07
{
    /// <summary>
    /// DL-07 The Heap (port_architecture §5; docs/scenes/DL-07_the_heap.md §1–9 and its passes): the sorting floor is DL-07's
    /// once the belt runs to the exit (<c>sceneName</c>, L8141). Carry a sorting weight to the dock and set it in a carrier
    /// (two per tub), send it up the ramp: at the landing the tub tips it into the bucket, and the gallery gate rises 0.38
    /// per weight, 1.4 with two. Ride a carrier up and hop off at the landing (<c>landing</c>), walk through the gate
    /// (<c>gallery</c>), under the letter on the rail, and on along the gallery, which gives way behind him (no way back),
    /// to the residential doorway into DL-08 (<c>REGION4_X</c>, region 4, <c>goods</c>). Off the gallery's left end the parcel
    /// slide takes him back down. Region 3; lines are index.html at 7b3c123.
    /// <para><b>The shared floor.</b> DL-07 has DL-06's span (<see cref="Dl06Scene.X0"/>–<see cref="Dl06Scene.X1"/>) and adds
    /// only the gallery's mechanisms (<see cref="GalleryMechanisms"/>): the floor's weights, levers and line are DL-06's
    /// definition's, built once (<see cref="Dl06Scene.FloorMechanisms"/>). Its rules extend <see cref="ReturnToSender06"/>
    /// (the scanner's acts, the tip's Startle, the ride into the chute go on while DL-07 holds him). Who holds him is
    /// <see cref="ReturnToSender06.HasLeft"/>: DL-07 from the belt running to the exit, from the gallery, or past
    /// <c>landing</c>. <see cref="Alone"/> builds the whole floor too, for DL-07 simulated on its own.</para>
    /// <para>Not ported here: picking up and posting the letter at MailSlot6, and the clock's key (<c>WindClock</c>, a curio
    /// at 73.38 on the gallery): the letters and curios systems' (§4.26, §4.19); the White's roll in the heap's sump the
    /// first time a weight drops in (<c>heapShown</c>, L4995): the White's (§4.15).</para>
    /// </summary>
    public static class Dl07Scene
    {
        public const string Id = "DL-07";

        /// <summary>The checkpoints (<see cref="ChapterDefs.PrologueCheckpoints"/>): <c>landing</c> when he hops off at the landing (L2955), <c>gallery</c> past the gate (L4948).</summary>
        public const string LandingCheckpoint = "landing", GalleryCheckpoint = "gallery", GoodsCheckpoint = "goods";
        /// <summary><c>gallery</c>: once he is on the gallery past <c>HP.gateX + 0.3</c> (L4948).</summary>
        public const double GalleryAt = Dl07Lane.GateX + 0.3;
        /// <summary>The slide: on the gallery, within 0.2 of its head, walking left (L4952).</summary>
        public const double SlideFrom = Dl07Lane.SlideHeadX + 0.2;
        /// <summary>The residential doorway: on the gallery past <c>REGION4_X</c> he is in region 4, DL-08's (L2044).</summary>
        public const double DoorwayX = Dl06Lane.Region4X;

        /// <summary>Clips the motor's table has no name for.</summary>
        public const string BrushOff = "BrushOff", Slide = "Slide";

        /// <summary>The scene definition in a chapter: DL-06's span, the gallery's mechanisms only.</summary>
        public static SceneDef Def() => new SceneDef
        {
            Id = Id,
            Title = "The Heap",
            X0 = Dl06Scene.X0, X1 = Dl06Scene.X1,                                                          // DL-06's floor (ChapterDef: a shared stretch)
            Region = Dl07Lane.Region,
            Mechanisms = GalleryMechanisms(),
            Lane = Dl06Lane.Table,                                                                          // the shared stretch: DL-06's table is the one built
            LaneContributors = Dl07Lane.Contributors,
            Interactables = Loader,
            Rules = () => new Heap07(),
        };

        /// <summary>
        /// The weights' set-down into a carrier (<c>nearUse</c>'s <c>loadCarrier</c> while he carries one on the floor,
        /// L4211; <c>loadableCarrier</c>, L4979–L4989): the line's <see cref="CarrierLine.Loader"/>.
        /// </summary>
        public static IInteractable[] Loader(MechanismGraph g) => new IInteractable[] { g.Get<CarrierLine>("dl06.line").Loader };

        /// <summary>DL-07 on its own (a one-scene chapter): DL-06's whole floor, then the gallery, with DL-07's rules.</summary>
        public static SceneDef Alone()
        {
            var floor = Dl06Scene.Floor(Id, "The Heap", () => new Heap07());
            var gallery = GalleryMechanisms();
            var all = new MechanismDef[floor.Mechanisms.Length + gallery.Length];
            floor.Mechanisms.CopyTo(all, 0);
            gallery.CopyTo(all, floor.Mechanisms.Length);
            floor.Mechanisms = all;
            floor.Interactables = g =>
            {
                var a = Dl06Scene.FloorInteractables(g);
                var b = Loader(g);
                var c = new IInteractable[a.Length + b.Length];
                a.CopyTo(c, 0);
                b.CopyTo(c, a.Length);
                return c;
            };
            floor.LaneContributors = g =>
            {
                var a = Dl06Lane.Contributors(g);
                var b = Dl07Lane.Contributors(g);
                var c = new ILaneContributor[a.Length + b.Length];
                a.CopyTo(c, 0);
                b.CopyTo(c, a.Length);
                return c;
            };
            return floor;
        }

        /// <summary>
        /// The gallery's mechanisms, after the floor's, in the prototype's order: who is up there (read by everything after),
        /// then <c>updateCh1</c> (#7): the weights tumbling into the bucket and where they go (L4823, L4957–L4962), the gate on
        /// the bucket (L4825–L4832), the letter on the rail (L4839–L4847); then <c>updateHazards</c>: the collapse (L7353–L7363).
        /// </summary>
        public static MechanismDef[] GalleryMechanisms() => new[]
        {
            new MechanismDef("dl07.gallery", () => new Dl07Gallery("dl07.gallery")),
            new MechanismDef("dl07.bucket", () => new GateBucket("dl07.bucket", BucketParams())),
            new MechanismDef("dl07.loading", () => new Dl07Loading("dl07.loading", "dl06.line", "dl07.bucket", "dl07.weight0", "dl07.weight1")),
            new MechanismDef("dl07.gate", () => new BucketGate("dl07.gate", BucketGateParams.Dl07Gate())),
            new MechanismDef("dl07.heapLetter", () => new Dl07HeapLetter("dl07.heapLetter")),
            new MechanismDef("dl07.collapse", () => new Dl07Collapse("dl07.collapse")),
        };

        /// <summary>The bucket, fed by the return line's tip at the landing (<c>carrierLoadTip(c, 'bucket')</c>, L2725, L4991).</summary>
        public static GateBucketParams BucketParams()
        {
            var p = GateBucketParams.Dl07Bucket();
            p.Feed = "dl06.line";
            return p;
        }
    }

    /// <summary>
    /// DL-07's rules, on DL-06's (<see cref="ReturnToSender06"/>: the floor's acts and cues go on while DL-07 holds him):
    /// the gallery (<c>game.upper</c>) for the scanner, the letter and the collapse; the landing (up onto the gallery,
    /// <c>landing</c>, BrushOff, L2955); <c>gallery</c> past the gate (L4948); the slide off the gallery's left end
    /// (L4952–L4955, <see cref="Dl07SlideAct"/>); the residential doorway into region 4 and <c>goods</c> (L2044); the bucket's
    /// and the gate's and the collapse's shakes. DL-07 never hands the floor back by state: it ends at the doorway.
    /// <para><b>Always.</b> The floor goes back to DL-06 whenever the route or the belt does (<c>sceneName</c>, L8141), but
    /// what the gallery's rules do happens whoever holds him, as the prototype's update functions run every step: a carrier
    /// already on the ramp still tips its weight into the bucket, and one he rides still unloads him at the landing. So these
    /// rules run every step, guarded as the prototype guards them (region 3, the gallery); what they inherit from DL-06's
    /// runs only while DL-07 holds him (DL-06's own rules run it otherwise).</para>
    /// </summary>
    public sealed class Heap07 : ReturnToSender06
    {
        public override bool Always => true;

        /// <summary>DL-07 holds him (the step's scene): DL-06's inherited hooks run here, else in DL-06's rules.</summary>
        private static bool Holds(ChapterSim sim) => sim.Current != null && sim.Current.Id == Dl07Scene.Id;

        /// <summary>The bucket takes a weight: shake 0.2 (L5002); the gate stalls: 0.15 (L4831); the collapse hits: 0.6 (L7361).</summary>
        public const int BucketShake = 20, StrainShake = 15, CollapseShake = 60;

        private Dl07Gallery _gallery;
        private Dl07Collapse _collapse;
        private bool _left, _landed, _goods;

        public Dl07Gallery Gallery => _gallery;
        public BucketGate Gate { get; private set; }
        public GateBucket Bucket { get; private set; }
        public Dl07Loading Loading { get; private set; }
        public Dl07HeapLetter Letter { get; private set; }
        public Dl07Collapse Collapse => _collapse;

        public override void OnBegin(ChapterSim sim, string checkpoint, bool fromOpening)
        {
            base.OnBegin(sim, checkpoint, fromOpening);
            var g = sim.Graph;
            _gallery = g.Get<Dl07Gallery>("dl07.gallery");
            Gate = g.Get<BucketGate>("dl07.gate");
            Bucket = g.Get<GateBucket>("dl07.bucket");
            Loading = g.Get<Dl07Loading>("dl07.loading");
            Letter = g.Get<Dl07HeapLetter>("dl07.heapLetter");
            _collapse = g.Get<Dl07Collapse>("dl07.collapse");
            Func<bool> onGallery = () => sim.Region == Dl07Lane.Region && _gallery.Upper;                  // game.region === 3 && game.upper
            Letter.OnGallery = onGallery;                                                                 // L4840
            _collapse.OnGallery = onGallery;                                                              // L7355
            _left = _landed = _goods = false;
        }

        /// <summary><c>game.upper</c>: the gallery's.</summary>
        protected override bool Upper(ChapterSim sim) => _gallery != null && _gallery.Upper;

        /// <summary>DL-07 ends at the doorway (region 4), not by state.</summary>
        public override bool HasLeft(ChapterSim sim) => false;

        /// <summary>The slide is asked for in <c>updateCh1</c> with this step's <c>input.left</c> (L4952): kept here for <see cref="AfterGraph"/>.</summary>
        public override void BeforeMotor(ChapterSim sim, ref MotorInput input)
        {
            if (Holds(sim)) base.BeforeMotor(sim, ref input);
            _left = input.Move < 0 && !input.MoveIsAnalog;
        }

        /// <summary>
        /// #4's tail: hopped off at the landing, he is on the gallery (<c>game.upper = true</c>, <c>landing</c>, BrushOff;
        /// L2955, at the end of the alight act in <c>updatePlayer</c>; while the motor cannot keep him on the carrier through
        /// that hop, <see cref="Dl07LandingHopAct"/> plays it from its first step); past <c>REGION4_X</c> on the gallery he is in
        /// region 4, DL-08's, at <c>goods</c> (L2044, free movement only). The checkpoints are reached at the step's end
        /// (<see cref="AfterGraph"/>), so each one's snapshot is the world with the step's mechanisms applied.
        /// </summary>
        public override void AfterMotor(ChapterSim sim, bool freeStep)
        {
            if (Holds(sim)) base.AfterMotor(sim, freeStep);
            var m = sim.Motor;
            if (sim.Region != Dl07Lane.Region) return;
            if (AlightedAtLanding(m))
            {
                Landed(sim);
                SceneQuirk.Start(sim, Dl07Scene.BrushOff, cancel: true);                                  // playQuirk('BrushOff')
            }
            else if (m.IsActing && m.ActVerb == Verb.Alight && m.ActPhase == ActPhase.Hop && m.Ride != null)
                sim.StartAct(new Dl07LandingHopAct(this, m));                                                // #32: the hop on the carrier (see the act)
            if (freeStep && _gallery.Upper && sim.X > Dl07Scene.DoorwayX)
            {
                sim.SetRegion(Dl07Lane.Region + 1);
                _goods = true;                                                                              // dl4.entered: game.checkpoint = 'goods'
            }
        }

        public override void AfterGraph(ChapterSim sim)
        {
            if (Holds(sim)) base.AfterGraph(sim);
            var log = sim.Graph.Log;
            if (log.Has("dl07.bucket", MechanismEventKind.Event, (int)GateBucketEvent.Landed)) sim.Cue(Shake, BucketShake);       // L5002
            if (log.Has("dl07.gate", MechanismEventKind.Event, (int)BucketGateEvent.Strain)) sim.Cue(Shake, StrainShake);         // L4831
            if (log.Has("dl07.collapse", MechanismEventKind.Event, (int)CollapseEvent.Hit)) sim.Cue(Shake, CollapseShake);        // L7361
            if (_landed) { _landed = false; sim.Checkpoints.Reach(Dl07Scene.LandingCheckpoint); }                                 // L2955
            if (_goods) { _goods = false; sim.Checkpoints.Reach(Dl07Scene.GoodsCheckpoint); }                                     // L2044
            if (sim.Region != Dl07Lane.Region || !_gallery.Upper) { _left = false; return; }
            // updateCh1 (#7): past the gate (L4948), and the slide off the gallery's left end (L4952–L4955).
            double x = sim.X;
            bool left = _left;
            _left = false;                                                                                   // this step's input only
            if (x > Dl07Scene.GalleryAt) sim.Checkpoints.Reach(Dl07Scene.GalleryCheckpoint);
            if (!sim.Busy && sim.Grounded && x < Dl07Scene.SlideFrom && left)
                sim.StartAct(new Dl07SlideAct(_gallery, sim.X, sim.Y, sim.Z, sim.Yaw, sim.Config.YawRate));
        }

        /// <summary>
        /// Up on the gallery at the landing (L2955): <c>game.upper</c> from this step's mechanisms, and <c>landing</c> at the
        /// step's end (<see cref="AfterGraph"/>: the checkpoint's snapshot is the world with him up there).
        /// </summary>
        internal void Landed(ChapterSim sim)
        {
            _gallery.Arrive();
            _landed = true;
        }

        /// <summary>The motor ended its alight hop at the landing this step (<c>LeaveRide("landing")</c>).</summary>
        private static bool AlightedAtLanding(D17Motor m)
        {
            var ev = m.Events;
            for (int i = 0; i < ev.Count; i++)
                if (ev[i].Kind == MotorEventKind.Alighted && ev[i].Name == "landing") return true;
            return false;
        }
    }

    /// <summary>
    /// The hop off a carrier onto the gallery at the landing (<c>game.act = { kind: 'alight' }</c>, L2951–L2956), as the
    /// prototype shows it: he stays where the carrier holds him until the hop's last frame, then stands on the deck. The
    /// prototype keeps <c>game.riding</c> through the hop, so its ride sync (#9, <c>syncRide</c>, L2959–L2964) puts him back on
    /// the carrier after every step of <c>hopTo</c>'s arc; the motor deliberately does not sync during an act and flies the arc
    /// (Core/Motor's <c>SyncRide</c>: "a deliberate difference"), 0.38 high and back to z 0, 37 steps before the prototype
    /// does (#17182–#17218 in the prologue trace). Until the motor can keep him on the ride through its alight hop (#32), this
    /// act stands in from the hop's first step: it steps the motor (its alight act, clip, yaw and the ride's release run as
    /// they would) and reports the ride's pose (<see cref="IRide.RidePose"/>) until the motor's act ends, where the motor's
    /// pose is the prototype's (the deck, z 0). It then does the landing's end (<see cref="Heap07.Landed"/>, and BrushOff
    /// after it, <c>playQuirk</c>), which the rules' <see cref="SceneRules.AfterMotor"/> cannot see while it runs. Named as the
    /// motor's act is (<c>Alight:Hop</c>).
    /// </summary>
    public sealed class Dl07LandingHopAct : SceneAct
    {
        public static readonly ActId AlightKind = ActId.Of("Alight"), HopPhase = ActId.Of("Hop");

        private readonly Heap07 _rules;

        /// <param name="m">The motor, on the step its alight hop started (he is where the carrier holds him).</param>
        public Dl07LandingHopAct(Heap07 rules, D17Motor m) : base(AlightKind, HopPhase)
        {
            _rules = rules ?? throw new ArgumentNullException(nameof(rules));
            X = m.X; Y = m.Y; Z = m.Z; Yaw = m.Yaw; _grounded = m.Grounded;
        }

        public override bool OwnsPose => true;
        private bool _grounded = true;
        public override bool PoseGrounded => _grounded;

        public override bool Step(ChapterSim sim, in MotorInput input, double dt)
        {
            var m = sim.Motor;
            T += dt;
            m.Step(input, dt);
            Yaw = m.Yaw;
            _grounded = m.Grounded;
            if (m.Ride != null && m.IsActing && m.Ride.RidePose(m.RideToken, out double x, out double y, out double z))
            {
                X = x; Y = y; Z = z;                                                                        // syncRide, L2963
                return true;
            }
            X = m.X; Y = m.Y; Z = m.Z;                                                                      // the hop's end: on the deck (L2953)
            _rules.Landed(sim);
            if (!m.IsActing && m.Hold == HoldKind.None && m.Ride == null && m.Grounded)                    // playQuirk('BrushOff')'s own conditions
            {
                SceneQuirk.Stop(sim);
                Next = new QuirkAct(Dl07Scene.BrushOff, QuirkAct.ClipSeconds(Dl07Scene.BrushOff), cancel: true, startClock: sim.Clock);
            }
            return false;
        }
    }

    /// <summary>
    /// Down the parcel slide (<c>game.act = { kind: 'slide' }</c>, L4496–L4509; §4.8): from the gallery's left end, sitting,
    /// along the slide's 13-point polyline (<c>HP.slide</c>, L3894) to the sorting floor: speed from 0.4 m/s, gaining
    /// <c>9.8 · sin(slope)</c> and losing 0.6 m/s² along it, held to 0.5–3.0 m/s; he faces −x, eases out to the slide's z
    /// (<c>HP.slideZ</c> 0.42, three.js sign) at rate 8 and tips to its slope at rate 10 (<see cref="Pitch"/>). At the end he
    /// is on the floor 0.1 short of its foot, down from the gallery (<c>game.upper = false</c>), grounded, with the
    /// <c>Land</c> clip. It owns his pose; the rules start it in <c>updateCh1</c>'s place (#7), so its first step is the next
    /// step's #4. Its phase is "act" (the prototype's).
    /// </summary>
    public sealed class Dl07SlideAct : SceneAct
    {
        /// <summary>The slide's polyline, (x, y) from its head on the gallery to its foot on the floor (<c>HP.slide</c>, OFF3 + x, L3894).</summary>
        public static readonly double[] Points =
        {
            33 + 38.85, 1.6, 33 + 38.762, 1.6, 33 + 38.62, 1.575, 33 + 38.48, 1.525, 33 + 38.376, 1.46, 33 + 37.266, 0.528, 33 + 36.95, 0.33,
            33 + 36.6, 0.18, 33 + 36.25, 0.09, 33 + 35.98, 0.06, 33 + 35.78, 0.06, 33 + 35.72, 0.03, 33 + 35.70, 0.0,
        };
        /// <summary>Start speed, clamp, drag, gravity (L4499, L4503); his z on the slide, Unity sign (HP.slideZ 0.42, L3893); the eases (L4506–L4507).</summary>
        public const double V0 = 0.4, VMin = 0.5, VMax = 3.0, Drag = 0.6, Gravity = 9.8, SlideZ = -0.42, ZRate = 8, PitchRate = 10, EndBack = 0.1;

        /// <summary>The slide's kind (its view's mechanism, the prototype's <c>a.kind</c>).</summary>
        public static readonly ActId SlideKind = ActId.Of("dl07.slide");

        private readonly Dl07Gallery _gallery;
        private readonly double _yawRate, _len;
        private double _d, _v;

        public Dl07SlideAct(Dl07Gallery gallery, double x, double y, double z, double yaw, double yawRate) : base(SlideKind, ActIds.Act)
        {
            _gallery = gallery ?? throw new ArgumentNullException(nameof(gallery));
            X = x; Y = y; Z = z; Yaw = yaw; _yawRate = yawRate;
            _v = V0;
            for (int i = 2; i < Points.Length; i += 2) _len += Seg(i);
        }

        public override bool OwnsPose => true;
        /// <summary>His tip to the slide's slope, radians (<c>game.pitch</c>; the view's).</summary>
        public double Pitch { get; private set; }
        /// <summary>Metres along the slide.</summary>
        public double Distance => _d;
        public double Speed => _v;

        public override bool Step(ChapterSim sim, in MotorInput input, double dt)
        {
            T += dt;
            int i = 2;
            double d = _d;
            while (i < Points.Length - 2 && d > Seg(i)) { d -= Seg(i); i += 2; }                                          // L4500
            double ax = Points[i - 2], ay = Points[i - 1], bx = Points[i], by = Points[i + 1], seg = Seg(i);
            double k = Math.Min(1, d / seg), slope = Math.Atan2(ay - by, ax - bx);                                         // L4501
            _v = Math.Min(VMax, Math.Max(VMin, _v + Gravity * Math.Sin(slope) * dt - Drag * dt));                          // L4502
            _d += _v * dt;                                                                                                  // L4503
            X = ax + (bx - ax) * k; Y = ay + (by - ay) * k;                                                                 // L4504, facing = −1
            Z += (SlideZ - Z) * Math.Min(1, dt * ZRate);                                                                    // L4505
            Pitch += (slope - Pitch) * Math.Min(1, dt * PitchRate);                                                         // L4506
            Yaw = Smooth.MoveTowards(Yaw, -Math.PI / 2, _yawRate * dt);                                                      // updateCharacter: facing −1
            if (_d >= _len)                                                                                                 // L4508
            {
                X = Points[Points.Length - 2] - EndBack; Y = 0; Z = 0; Pitch = 0;
                _gallery.Leave();                                                                                           // game.upper = false
                sim.Motor.Place(X, Y, -1, Yaw);                                                                             // grounded, at rest, facing −x
                return false;
            }
            return true;
        }

        private static double Seg(int i)
        {
            double dx = Points[i] - Points[i - 2], dy = Points[i + 1] - Points[i - 1];
            return Math.Sqrt(dx * dx + dy * dy);                                                                            // Math.hypot
        }
    }
}
