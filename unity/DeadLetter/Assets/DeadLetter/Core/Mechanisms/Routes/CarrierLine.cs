using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Routes
{
    /// <summary>The line's state mirrors its belt (the stop lever).</summary>
    public enum CarrierLineState { Stopped, Running }

    /// <summary>A carrier's phase (<c>c.state</c>, L2693–L2751).</summary>
    public enum CarrierState { Rise, Dock, Move, Unload, TipLoad, Tip, Back, Sink }

    /// <summary>Where a carrier goes after the junction (<c>c.route</c>; None until it passes the junction).</summary>
    public enum CarrierRoute { None, Chute, Exit }

    public enum CarrierLineEvent
    {
        /// <summary>A carrier came up the dispatch hatch (<c>Sound.hatchLift</c>, L2680). Index = its Seq.</summary>
        Spawned,
        /// <summary>It reached the dock and waits 3.4 s (<c>Sound.bell</c>, L2699). Index = Seq.</summary>
        Docked,
        /// <summary>It took the points at the junction (<c>Sound.clack(0.4)</c>, L2709). Index = Seq, Value = (int)route.</summary>
        Junction,
        /// <summary>A ridden exit carrier stopped at the landing: he alights onto the gallery (L2710, L2970). Index = Seq.</summary>
        Unload,
        /// <summary>It reached the chute's end and tips (<c>Sound.clank</c>, L2714). Index = Seq.</summary>
        Tip,
        /// <summary>Its parcels slid down the chute onto the heap (L2729–L2732; the falling parcels are the view's). Index = Seq, Value = parcels.</summary>
        PayloadDumped,
        /// <summary>It tipped D-17 out with the post: he goes down the chute onto the heap (<c>tipOut</c>, L2733, L2978–L2982). Index = Seq.</summary>
        RiderTipped,
        /// <summary>The tip banged down near him on the floor: shake 0.25 and the Startle quirk (L2735). Index = Seq.</summary>
        Startle,
        /// <summary>A weight tumbles out at the landing toward the gallery gate's bucket (<c>carrierLoadTip(c, 'bucket')</c>, L4991–L5001). Index = load code.</summary>
        LoadToBucket,
        /// <summary>A weight went down the chute: lost; it is back by its home <see cref="CarrierLineParams.LostReturns"/> s later (L5004). Index = load code, Value = seconds.</summary>
        LoadLost,
        /// <summary>A weight was set in a carrier (two per tub; the parcels make way; L4445–L4452). Index = load code, Value = Seq.</summary>
        LoadPlaced,
        /// <summary>The carrier left before the weight went in: it lies on the floor at his feet (L4453). Index = load code.</summary>
        LoadRefused,
        /// <summary>It started down a return lift (<c>Sound.clunk</c> + <c>hatchLift</c>, L2716, L2741). Index = Seq.</summary>
        Sinking,
        /// <summary>It sank out of sight and was removed (L2747). Index = Seq.</summary>
        Removed,
    }

    public sealed class CarrierLineParams
    {
        /// <summary>The belt (an <see cref="IEngageable"/>, engaged = running): the stop lever.</summary>
        public MechanismId Belt;
        /// <summary>The points (an <see cref="IEngageable"/>, engaged = exit).</summary>
        public MechanismId Points;
        /// <summary>Optional <see cref="IEngageable"/>: while engaged and the line is empty, a carrier rises (the scan's HATCH beat, L2802).</summary>
        public MechanismId Hatch;

        /// <summary>The common run (hatch, dock, junction) and the two routes after it, (x, y) pairs (L2471–L2472).</summary>
        public double[] Common, Chute, Exit;
        /// <summary>Point indices: the dock and the junction on <see cref="Common"/>, the landing on <see cref="Exit"/> (L2475–L2476).</summary>
        public int DockPoint = 2, JunctionPoint = 3, LandingPoint = 6;
        /// <summary>Chute carriers come back to the return lift at this x (<c>RETURN3_X</c>, L2477).</summary>
        public double ReturnX;
        public double DockX;

        public double RiseSpeed = 0.6, BeltSpeed = 0.6, DockWait = 3.4, SpawnEvery = 6.0, SpawnClear = 1.4, Gap = 0.8;   // L2459, L2696–L2698
        public double BackSpeed = 0.5, SinkSpeed = 0.6, SinkDelay = 0.3, SinkDepth = 1.0, UnloadWait = 1.0;          // L2720, L2740–L2746
        /// <summary>A ridden carrier waits at least this long at the dock (<c>c.wait = max(c.wait, 0.9)</c>, L2950).</summary>
        public double BoardWait = 0.9;
        /// <summary>Tip-load into the bucket: 62° over 0.6 s, back from 1.2 s over 0.5, weight out at 0.4, on at 1.8 (L2723–L2727).</summary>
        public double TipLoadDeg = 62, TipLoadOut = 0.4, TipLoadEnd = 1.8;
        /// <summary>Chute tip: 68° over 0.7 s, back from 1.6 s over 0.5, contents out at 0.35, bang at 0.5, back at 2.1 (L2728–L2737).</summary>
        public double TipDeg = 68, TipOut = 0.35, TipBang = 0.5, TipEnd = 2.1;
        /// <summary>The second weight follows the first after 0.18 s (<c>setTimeout(..., 180)</c>, L4992).</summary>
        public double SecondLoadDelay = 0.18, LostReturns = 4;
        /// <summary>The carrier's floor above its rail point (<c>CARRIER_FLOOR</c>, L2459); the rail's Unity z (RAIL_Z −0.55 negated, L2456).</summary>
        public double Floor = 0.14, RailZ = 0.55;
        /// <summary>Boarding: a carrier on the floor (y ≤ 0.2) within 0.5 of him (L2854–L2862).</summary>
        public double BoardReach = 0.5, OnFloorY = 0.2;
        /// <summary>Loading: the docked carrier within 0.7 of the dock, or, belt stopped, a moving one within 0.6 (L4985).</summary>
        public double LoadReachDock = 0.7, LoadReachMoving = 0.6;
        /// <summary>The bang startles him if he is on the floor (y below this) past this x (L2735).</summary>
        public double StartleFromX, StartleBelowY = 1.0;
        /// <summary>Most carriers alive at once.</summary>
        /// <remarks>A ridden carrier held at the landing queues the rest back to the hatch (~14 at 0.8 apart).</remarks>
        public int Capacity = 24;
        /// <summary>Payload: none with p 0.2, else 1 + floor(r · 2.2) parcels of 0.12 + r · 0.08 (L2667–L2673).</summary>
        public double EmptyChance = 0.2;

        /// <summary>DL-06/07: the return line, hatch 63.5 → dock 64.0 → junction 67.6 → chute tip 69.5, or up the ramp to the landing 72.7 and the return 74.3 (L2455–L2478).</summary>
        public static CarrierLineParams Dl06Line()
        {
            const double off3 = 33;                                                          // OFF3, L274
            double hatch = off3 + 30.5, dock = off3 + 31.0, junction = off3 + 34.6, tip = off3 + 36.5;   // L2457
            return new CarrierLineParams
            {
                Belt = "dl06.stopLever", Points = "dl06.points",
                Common = new[] { hatch, -0.75, hatch, 0, dock, 0, junction, 0 },
                Chute = new[] { hatch, -0.75, hatch, 0, dock, 0, junction, 0, tip, 0 },
                Exit = new[] { hatch, -0.75, hatch, 0, dock, 0, junction, 0, off3 + 35.25, 0.32, off3 + 38.5, 1.6, off3 + 39.7, 1.6, off3 + 41.3, 1.6 },   // BLADE_END, RAMP_TOP, LANDING_X, RETURN_X
                ReturnX = off3 + 35.9, DockX = dock,                                         // RETURN3_X, L2477
                StartleFromX = off3 + 34.8,
            };
        }
    }

    /// <summary>
    /// One carrier on a <see cref="CarrierLine"/>. Signals: <see cref="Position"/> = rail x, metres, for ride sync
    /// (§3.1 step 9: D-17 rides at (<see cref="Position"/>, <see cref="RideY"/>, <see cref="CarrierLineParams.RailZ"/>), L2961–L2964).
    /// </summary>
    public sealed class Carrier : IPositionSource
    {
        public const int MaxParcels = 3;

        internal bool Active;
        public int Seq { get; internal set; }
        public CarrierState State { get; internal set; }
        public CarrierRoute Route { get; internal set; }
        /// <summary>Arc length along its route, metres.</summary>
        public double S { get; internal set; }
        /// <summary>Rail point x, y (metres), and the segment's angle (radians; 0 while rising).</summary>
        public double Position { get; internal set; }
        public double Y { get; internal set; }
        public double Angle { get; internal set; }
        /// <summary>Velocity this step, m/s (x, y).</summary>
        public double VelocityX { get; internal set; }
        public double VelocityY { get; internal set; }
        /// <summary>Tub tip about its pivot, radians: + toward the gallery bucket, − into the chute.</summary>
        public double TipRad { get; internal set; }
        /// <summary>Where D-17 stands when riding it (<c>root.y + CARRIER_FLOOR</c>).</summary>
        public double RideY { get; internal set; }
        public bool Ridden { get; internal set; }
        public double Wait { get; internal set; }
        public double T { get; internal set; }
        /// <summary>Load codes in the tub (0 = empty); a second goes in beside the first.</summary>
        public int Load1 { get; internal set; }
        public int Load2 { get; internal set; }
        /// <summary>The parcels it came with (hidden once a weight is in).</summary>
        public int Parcels { get; internal set; }
        public bool ParcelsHidden { get; internal set; }
        internal readonly double[] ParcelSize = new double[MaxParcels], ParcelZ = new double[MaxParcels], ParcelYaw = new double[MaxParcels];
        public double ParcelSizeOf(int i) => ParcelSize[i];
        public double ParcelZOf(int i) => ParcelZ[i];
        public double ParcelYawOf(int i) => ParcelYaw[i];
        internal double FloorY;
        internal bool Banged;
        internal int Second;
        internal double SecondIn;
        internal bool SecondToBucket;

        internal void Write(ISnapshotWriter w, string k)
        {
            w.WriteLong(k + "seq", Seq); w.WriteLong(k + "state", (int)State); w.WriteLong(k + "route", (int)Route);
            w.WriteDouble(k + "s", S); w.WriteDouble(k + "x", Position); w.WriteDouble(k + "y", Y); w.WriteDouble(k + "ang", Angle);
            w.WriteDouble(k + "vx", VelocityX); w.WriteDouble(k + "vy", VelocityY); w.WriteDouble(k + "tip", TipRad); w.WriteDouble(k + "rideY", RideY);
            w.WriteBool(k + "ridden", Ridden); w.WriteDouble(k + "wait", Wait); w.WriteDouble(k + "t", T);
            w.WriteLong(k + "load1", Load1); w.WriteLong(k + "load2", Load2);
            w.WriteLong(k + "parcels", Parcels); w.WriteBool(k + "hidden", ParcelsHidden);
            for (int i = 0; i < MaxParcels; i++)
            {
                w.WriteDouble(k + "ps" + i, ParcelSize[i]); w.WriteDouble(k + "pz" + i, ParcelZ[i]); w.WriteDouble(k + "py" + i, ParcelYaw[i]);
            }
            w.WriteDouble(k + "floorY", FloorY); w.WriteBool(k + "banged", Banged);
            w.WriteLong(k + "second", Second); w.WriteDouble(k + "secondIn", SecondIn); w.WriteBool(k + "secondBucket", SecondToBucket);
        }

        internal void Read(ISnapshotReader r, string k)
        {
            Active = true;
            Seq = (int)r.ReadLong(k + "seq"); State = (CarrierState)r.ReadLong(k + "state"); Route = (CarrierRoute)r.ReadLong(k + "route");
            S = r.ReadDouble(k + "s"); Position = r.ReadDouble(k + "x"); Y = r.ReadDouble(k + "y"); Angle = r.ReadDouble(k + "ang");
            VelocityX = r.ReadDouble(k + "vx"); VelocityY = r.ReadDouble(k + "vy"); TipRad = r.ReadDouble(k + "tip"); RideY = r.ReadDouble(k + "rideY");
            Ridden = r.ReadBool(k + "ridden"); Wait = r.ReadDouble(k + "wait"); T = r.ReadDouble(k + "t");
            Load1 = (int)r.ReadLong(k + "load1"); Load2 = (int)r.ReadLong(k + "load2");
            Parcels = (int)r.ReadLong(k + "parcels"); ParcelsHidden = r.ReadBool(k + "hidden");
            for (int i = 0; i < MaxParcels; i++)
            {
                ParcelSize[i] = r.ReadDouble(k + "ps" + i); ParcelZ[i] = r.ReadDouble(k + "pz" + i); ParcelYaw[i] = r.ReadDouble(k + "py" + i);
            }
            FloorY = r.ReadDouble(k + "floorY"); Banged = r.ReadBool(k + "banged");
            Second = (int)r.ReadLong(k + "second"); SecondIn = r.ReadDouble(k + "secondIn"); SecondToBucket = r.ReadBool(k + "secondBucket");
        }
    }

    /// <summary>
    /// The DL-06/07 return line (§4.13h, L2452–L2995): carriers rise at the hatch every 6 s while the belt runs and
    /// nothing is in the first 1.4 m, wait 3.4 s at the dock, run at 0.6 m/s keeping 0.8 apart, take the points at the
    /// junction, and either tip into the chute (then back to the return lift and down) or climb the ramp to the
    /// landing (ridden ones stop there; loaded ones tip their weight toward the gallery bucket) and sink at the return.
    /// D-17 boards, rides and alights through <see cref="BeginBoard"/>, <see cref="Mount"/>, <see cref="Alight"/>
    /// (his hop acts are the motor's); ride sync reads <see cref="Ride"/> after the graph has stepped (§3.1 step 9).
    /// Weights are set in through <see cref="Loader"/>. The dock, the chute and the route board are this mechanism's
    /// outputs (<see cref="DockLit"/>, <see cref="CarrierLineEvent.Tip"/>, <see cref="Route"/>/<see cref="Running"/>).
    /// Signals: <see cref="Engaged"/> = the belt runs.
    /// </summary>
    public sealed class CarrierLine : Mechanism, IEngageable
    {
        private readonly CarrierLineParams _p;
        private readonly RoutePath _common, _chute, _exit;
        private readonly double _sDock, _sJunction, _sLanding, _sReturn;
        private readonly Carrier[] _all;
        private readonly int[] _live;
        private int _count, _seq, _boarding = -1, _mount = -1, _placeCode, _placeSeq = -1;
        private bool _alight;
        private double _clock, _lastSpawn;
        private IEngageable _belt, _points, _hatch;
        private ICarryable[] _loads = new ICarryable[0];

        public CarrierLine(MechanismId id, CarrierLineParams p) : base(id)
        {
            _p = p;
            _common = new RoutePath(p.Common);
            _chute = new RoutePath(p.Chute);
            _exit = new RoutePath(p.Exit);
            _sDock = _common.LengthTo(p.DockPoint);                                       // S_DOCK, L2475
            _sJunction = _common.LengthTo(p.JunctionPoint);                               // S_JUNCTION
            _sLanding = _exit.LengthTo(p.LandingPoint);                                   // S_LANDING
            _sReturn = _sJunction + (p.ReturnX - _common.X(p.JunctionPoint));             // S_RETURN3, L2477
            _all = new Carrier[p.Capacity];
            for (int i = 0; i < _all.Length; i++) _all[i] = new Carrier();
            _live = new int[p.Capacity];
            Loader = new CarrierLoader(this);
        }

        public CarrierLineState State => (CarrierLineState)StateCode;
        public bool Running => _belt.Engaged;
        public bool Engaged => Running;
        /// <summary>Where the points send the next carrier (<c>game.route</c>; the route board and floor arrows show it).</summary>
        public CarrierRoute Route => _points.Engaged ? CarrierRoute.Exit : CarrierRoute.Chute;
        /// <summary>The dock lamp flashes while a carrier waits there (L2840).</summary>
        public bool DockLit { get { for (int i = 0; i < _count; i++) if (At(i).State == CarrierState.Dock) return true; return false; } }
        public int Count => _count;
        /// <summary>The i-th live carrier, in spawn order.</summary>
        public Carrier At(int i) => _all[_live[i]];
        /// <summary>The carrier he rides, or null (<c>game.riding</c>).</summary>
        public Carrier Ride { get { for (int i = 0; i < _count; i++) if (At(i).Ridden) return At(i); return null; } }
        /// <summary>The line's clock, seconds since the graph was built (the prototype's <c>game.clock</c> for spawns).</summary>
        public double Clock => _clock;
        public double SDock => _sDock;
        public double SJunction => _sJunction;
        public double SLanding => _sLanding;
        public double SReturn => _sReturn;
        public double SEnd(CarrierRoute r) => r == CarrierRoute.Exit ? _exit.Length : r == CarrierRoute.Chute ? _chute.Length : _common.Length;

        /// <summary>The weights' place target: the docked carrier, or a stopped one beside him (L4979–L4989).</summary>
        public CarrierLoader Loader { get; }

        /// <summary>The items a carrier accepts as loads (DL-07's two weights); load code = index + 1.</summary>
        public void SetLoadItems(params ICarryable[] items) => _loads = items ?? new ICarryable[0];

        public int LoadCodeOf(ICarryable item)
        {
            for (int i = 0; i < _loads.Length; i++) if (ReferenceEquals(_loads[i], item)) return i + 1;
            return 0;
        }

        public Carrier FindBySeq(int seq)
        {
            for (int i = 0; i < _count; i++) if (At(i).Seq == seq) return At(i);
            return null;
        }

        /// <summary><c>boardable()</c> (L2854–L2862): the nearest carrier on the floor within reach that is docked, moving or unloading.</summary>
        public Carrier FindBoardable(double x)
        {
            Carrier best = null;
            double bd = 0;
            for (int i = 0; i < _count; i++)
            {
                var c = At(i);
                if ((c.State != CarrierState.Dock && c.State != CarrierState.Move && c.State != CarrierState.Unload) || c.Y > _p.OnFloorY) continue;
                double d = Math.Abs(c.Position - x);
                if (d < _p.BoardReach && (best == null || d < bd)) { best = c; bd = d; }
            }
            return best;
        }

        // ---- Input (the motor's board / alight acts; recorded here, applied at the top of Step) ----------------------
        /// <summary>The board hop started toward <paramref name="c"/>: its dock wait holds while he hops (L2702).</summary>
        public void BeginBoard(Carrier c) => _boarding = c?.Seq ?? -1;
        /// <summary>Hop f23: he is on (<c>game.riding = c; c.ridden = true</c>, L2949–L2950).</summary>
        public void Mount(Carrier c) { _mount = c?.Seq ?? -1; }
        /// <summary>He is off (the hop from a docked/moving carrier, or the end of the landing alight; L2955, L2973).</summary>
        public void Alight() { _alight = true; }

        public override void Link(MechanismLinker link)
        {
            _belt = link.Read<IEngageable>(_p.Belt) ?? throw new InvalidOperationException(Id + " needs a Belt.");
            _points = link.Read<IEngageable>(_p.Points) ?? throw new InvalidOperationException(Id + " needs Points.");
            _hatch = link.Read<IEngageable>(_p.Hatch);
        }

        /// <summary>No carriers until the belt runs (L8030); the clock and the carrier sequence carry on.</summary>
        public override void Reset(in Checkpoint cp)
        {
            for (int i = 0; i < _all.Length; i++) _all[i].Active = false;
            _count = 0;
            _lastSpawn = -100;                                                             // L8032
            _boarding = _mount = _placeSeq = -1;
            _placeCode = 0;
            _alight = false;
            Init((int)(Running ? CarrierLineState.Running : CarrierLineState.Stopped));
        }

        public override void Step(in StepContext ctx)
        {
            double dt = ctx.Dt;
            _clock += dt;
            bool run = _belt.Engaged;
            Enter(ctx, (int)(run ? CarrierLineState.Running : CarrierLineState.Stopped));
            ApplyInput(ctx);

            if (_hatch != null && _hatch.Engaged && _count == 0) Spawn(ctx);                                    // L2802
            if (run && !DockLit && _clock - _lastSpawn > _p.SpawnEvery && !AnyBefore(_p.SpawnClear)) Spawn(ctx);   // L2696

            for (int i = 0; i < _count; i++)
            {
                var c = At(i);
                double px = c.Position, py = c.Y;
                if (c.Second != 0)
                {
                    c.SecondIn -= dt;
                    if (c.SecondIn <= 1e-9) { int code = c.Second; c.Second = 0; TipLoad(ctx, code, c.SecondToBucket); }
                }
                if (StepCarrier(ctx, c, run)) { Remove(ctx, i); i--; continue; }
                c.VelocityX = (c.Position - px) / dt;
                c.VelocityY = (c.Y - py) / dt;
                c.RideY = c.Y + _p.Floor;
            }
        }

        /// <summary>One carrier, <c>updateCarriers</c> L2697–L2751. Returns true when it has sunk out of sight.</summary>
        private bool StepCarrier(in StepContext ctx, Carrier c, bool run)
        {
            double dt = ctx.Dt;
            switch (c.State)
            {
                case CarrierState.Rise:
                    c.S = Math.Min(_sDock, c.S + _p.RiseSpeed * dt);                                              // L2698
                    if (c.S >= _sDock - 1e-4) { c.State = CarrierState.Dock; c.Wait = _p.DockWait; Emit(ctx, (int)CarrierLineEvent.Docked, c.Seq); }
                    break;
                case CarrierState.Dock:
                    if (run && _boarding != c.Seq) c.Wait -= dt;                                                    // L2702
                    if (run && c.Wait <= 0) c.State = CarrierState.Move;                                            // L2703
                    break;
                case CarrierState.Move:
                    if (run) MoveOn(ctx, c);
                    break;
                case CarrierState.Unload:
                    if (!c.Ridden)
                    {
                        c.T += dt;
                        if (c.T > _p.UnloadWait + 1e-9 && run) { c.State = c.Load1 != 0 ? CarrierState.TipLoad : CarrierState.Move; c.T = 0; }   // L2719
                    }
                    break;
                case CarrierState.TipLoad:
                    c.T += dt;
                    c.TipRad = Deg(_p.TipLoadDeg) * Smooth.Step(c.T / 0.6) * (1 - Smooth.Step((c.T - 1.2) / 0.5));   // L2724
                    if (c.T > _p.TipLoadOut + 1e-9 && c.Load1 != 0) TipLoads(ctx, c, true);                         // L2725
                    if (c.T > _p.TipLoadEnd + 1e-9) { c.State = CarrierState.Move; c.TipRad = 0; }                  // L2726
                    break;
                case CarrierState.Tip:
                    c.T += dt;
                    c.TipRad = -Deg(_p.TipDeg) * Smooth.Step(c.T / 0.7) * (1 - Smooth.Step((c.T - 1.6) / 0.5));       // L2729
                    if (c.T > _p.TipOut + 1e-9 && c.Parcels > 0) { Emit(ctx, (int)CarrierLineEvent.PayloadDumped, c.Seq, c.Parcels); c.Parcels = 0; }   // L2730–L2732
                    if (c.T > _p.TipOut + 1e-9 && c.Ridden) { c.Ridden = false; Emit(ctx, (int)CarrierLineEvent.RiderTipped, c.Seq); }   // L2733
                    if (c.T > _p.TipOut + 1e-9 && c.Load1 != 0) TipLoads(ctx, c, false);                            // L2734
                    if (c.T > _p.TipBang + 1e-9 && !c.Banged)                                                      // L2735
                    {
                        c.Banged = true;
                        if (ctx.Player.X > _p.StartleFromX && ctx.Player.Y < _p.StartleBelowY) Emit(ctx, (int)CarrierLineEvent.Startle, c.Seq);
                    }
                    if (c.T > _p.TipEnd + 1e-9) { c.State = CarrierState.Back; c.T = 0; }                          // L2736
                    break;
                case CarrierState.Back:
                    c.S = Math.Max(_sReturn, c.S - _p.BackSpeed * dt);                                            // L2740
                    if (c.S <= _sReturn + 1e-4) { c.State = CarrierState.Sink; c.FloorY = 0; c.T = 0; Emit(ctx, (int)CarrierLineEvent.Sinking, c.Seq); }
                    break;
                case CarrierState.Sink:
                    c.T += dt;                                                                                      // L2744–L2747
                    c.Y = c.FloorY - _p.SinkSpeed * Math.Max(0, c.T - _p.SinkDelay);
                    return c.Y < c.FloorY - _p.SinkDepth;
            }

            var path = PathOf(c.Route);
            path.At(c.S, out double x, out double y, out double ang);                                             // L2749–L2751
            c.Position = x;
            c.Y = y;
            c.Angle = c.State == CarrierState.Rise ? 0 : ang;
            if (c.State == CarrierState.Back) c.TipRad = 0;
            return false;
        }

        /// <summary>The belt moves it on (L2705–L2717).</summary>
        private void MoveOn(in StepContext ctx, Carrier c)
        {
            var ahead = Ahead(c);
            double next = c.S + _p.BeltSpeed * ctx.Dt;
            if (ahead != null && ahead.S - next < _p.Gap) next = Math.Max(c.S, ahead.S - _p.Gap);                 // L2707
            if (c.Route == CarrierRoute.None && next >= _sJunction)                                                 // L2709
            {
                c.Route = Route;
                Emit(ctx, (int)CarrierLineEvent.Junction, c.Seq, (int)c.Route);
            }
            if (c.Route == CarrierRoute.Exit && c.Ridden && c.S < _sLanding && next >= _sLanding)                  // L2710
            {
                next = _sLanding; c.State = CarrierState.Unload; c.T = 0;
                Emit(ctx, (int)CarrierLineEvent.Unload, c.Seq);
            }
            if (c.Route == CarrierRoute.Exit && c.Load1 != 0 && !c.Ridden && c.S < _sLanding && next >= _sLanding) // L2711
            {
                next = _sLanding; c.State = CarrierState.TipLoad; c.T = 0;
            }
            c.S = next;
            if (c.Route != CarrierRoute.None && c.S >= SEnd(c.Route))                                              // L2713–L2716
            {
                c.S = SEnd(c.Route); c.T = 0;
                if (c.Route == CarrierRoute.Chute) { c.State = CarrierState.Tip; Emit(ctx, (int)CarrierLineEvent.Tip, c.Seq); }
                else { c.State = CarrierState.Sink; c.FloorY = _exit.Y(_exit.Count - 1); Emit(ctx, (int)CarrierLineEvent.Sinking, c.Seq); }
            }
        }

        /// <summary><c>carrierAhead</c> (L2684–L2692): the nearest carrier ahead on a shared stretch, not sinking.</summary>
        private Carrier Ahead(Carrier c)
        {
            Carrier best = null;
            for (int i = 0; i < _count; i++)
            {
                var o = At(i);
                if (o == c || o.S <= c.S || o.State == CarrierState.Sink) continue;
                bool shared = c.S < _sJunction || o.Route == c.Route;
                if (shared && (best == null || o.S < best.S)) best = o;
            }
            return best;
        }

        /// <summary><c>carrierLoadTip</c> (L4991–L5004): the first weight now, the second 0.18 s later.</summary>
        private void TipLoads(in StepContext ctx, Carrier c, bool bucket)
        {
            if (c.Load2 != 0) { c.Second = c.Load2; c.SecondIn = _p.SecondLoadDelay; c.SecondToBucket = bucket; c.Load2 = 0; }
            int code = c.Load1;
            c.Load1 = 0;
            TipLoad(ctx, code, bucket);
        }

        private void TipLoad(in StepContext ctx, int code, bool bucket)
        {
            if (bucket) Emit(ctx, (int)CarrierLineEvent.LoadToBucket, code);
            else Emit(ctx, (int)CarrierLineEvent.LoadLost, code, _p.LostReturns);
        }

        private void ApplyInput(in StepContext ctx)
        {
            if (_mount >= 0)
            {
                var c = FindBySeq(_mount);
                if (c != null) { c.Ridden = true; c.Wait = Math.Max(c.Wait, _p.BoardWait); }                        // L2950
                _mount = -1; _boarding = -1;
            }
            if (_alight)
            {
                for (int i = 0; i < _count; i++) At(i).Ridden = false;
                _alight = false;
            }
            if (_placeSeq >= 0)
            {
                var c = FindBySeq(_placeSeq);
                if (c != null && (c.State == CarrierState.Dock || c.State == CarrierState.Move))                   // L4446
                {
                    if (c.Load1 != 0) c.Load2 = _placeCode; else c.Load1 = _placeCode;                                // L4449–L4450
                    c.ParcelsHidden = true;
                    Emit(ctx, (int)CarrierLineEvent.LoadPlaced, _placeCode, c.Seq);
                }
                else Emit(ctx, (int)CarrierLineEvent.LoadRefused, _placeCode);                                       // L4453
                _placeSeq = -1; _placeCode = 0;
            }
        }

        private bool AnyBefore(double s)
        {
            for (int i = 0; i < _count; i++) if (At(i).S < s) return true;
            return false;
        }

        /// <summary><c>spawnCarrier</c> (L2660–L2682), with the payload from the clock-seeded LCG (L2666–L2673).</summary>
        private void Spawn(in StepContext ctx)
        {
            int slot = -1;
            for (int i = 0; i < _all.Length; i++) if (!_all[i].Active) { slot = i; break; }
            if (slot < 0) throw new InvalidOperationException(Id + ": more than " + _all.Length + " carriers.");
            var c = _all[slot];
            var rng = new RouteRng(_count * 7 + (long)Math.Floor(_clock * 13));
            int n = rng.Next() < _p.EmptyChance ? 0 : 1 + (int)Math.Floor(rng.Next() * 2.2);
            for (int k = 0; k < Carrier.MaxParcels; k++) c.ParcelSize[k] = c.ParcelZ[k] = c.ParcelYaw[k] = 0;
            for (int k = 0; k < n; k++)
            {
                c.ParcelSize[k] = 0.12 + rng.Next() * 0.08;
                c.ParcelZ[k] = -(rng.Next() - 0.5) * 0.15;                                                       // Unity z (negated)
                c.ParcelYaw[k] = (rng.Next() - 0.5) * 0.6;
            }
            c.Active = true;
            c.Seq = _seq++;
            c.State = CarrierState.Rise;
            c.Route = CarrierRoute.None;
            c.S = 0; c.Wait = 0; c.T = 0; c.TipRad = 0;
            c.Ridden = false; c.Banged = false;
            c.Load1 = c.Load2 = c.Second = 0; c.SecondIn = 0; c.SecondToBucket = false;
            c.Parcels = n; c.ParcelsHidden = false;
            c.FloorY = 0;
            _common.At(0, out double x, out double y, out _);
            c.Position = x; c.Y = y; c.Angle = 0; c.VelocityX = c.VelocityY = 0; c.RideY = y + _p.Floor;
            _live[_count++] = slot;
            _lastSpawn = _clock;
            Emit(ctx, (int)CarrierLineEvent.Spawned, c.Seq);
        }

        private void Remove(in StepContext ctx, int i)
        {
            var c = At(i);
            c.Active = false;
            Emit(ctx, (int)CarrierLineEvent.Removed, c.Seq);
            for (int k = i; k < _count - 1; k++) _live[k] = _live[k + 1];
            _count--;
        }

        private RoutePath PathOf(CarrierRoute r) => r == CarrierRoute.Chute ? _chute : r == CarrierRoute.Exit ? _exit : _common;

        private static double Deg(double d) => d * Math.PI / 180;

        // ---- Loading (IPlaceTarget through Loader) -------------------------------------------------------------------
        internal Carrier Loadable(double x, double y)
        {
            if (y > _p.OnFloorY) return null;                                                   // !game.upper, L4211
            bool run = _belt.Engaged;
            Carrier best = null;
            double bd = 0;
            for (int i = 0; i < _count; i++)
            {
                var c = At(i);
                if ((c.Load1 != 0 && c.Load2 != 0) || c.Ridden || c.Y > _p.OnFloorY) continue;   // L4983
                bool ok = c.State == CarrierState.Dock ? Math.Abs(x - _p.DockX) < _p.LoadReachDock
                    : !run && c.State == CarrierState.Move && Math.Abs(x - c.Position) < _p.LoadReachMoving;   // L4985
                double d = Math.Abs(x - c.Position);
                if (ok && (best == null || d < bd)) { best = c; bd = d; }
            }
            return best;
        }

        internal double StandFor(Carrier c) => c.State == CarrierState.Dock ? _p.DockX : c.Position;   // L4361
        internal double ReachFor(Carrier c) => c.State == CarrierState.Dock ? _p.LoadReachDock : _p.LoadReachMoving;

        internal void Place(int seq, int code) { _placeSeq = seq; _placeCode = code; }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("clock", _clock);
            w.WriteDouble("lastSpawn", _lastSpawn);
            w.WriteLong("seq", _seq);
            w.WriteLong("boarding", _boarding); w.WriteLong("mount", _mount); w.WriteBool("alight", _alight);
            w.WriteLong("placeSeq", _placeSeq); w.WriteLong("placeCode", _placeCode);
            w.WriteLong("n", _count);
            for (int i = 0; i < _count; i++) At(i).Write(w, "c" + i + ".");
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            _clock = r.ReadDouble("clock");
            _lastSpawn = r.ReadDouble("lastSpawn");
            _seq = (int)r.ReadLong("seq");
            _boarding = (int)r.ReadLong("boarding"); _mount = (int)r.ReadLong("mount"); _alight = r.ReadBool("alight");
            _placeSeq = (int)r.ReadLong("placeSeq"); _placeCode = (int)r.ReadLong("placeCode");
            for (int i = 0; i < _all.Length; i++) _all[i].Active = false;
            _count = (int)r.ReadLong("n");
            for (int i = 0; i < _count; i++) { _all[i].Read(r, "c" + i + "."); _live[i] = i; }
        }
    }

    /// <summary>
    /// The weights' context set-down into a carrier (DL-07, L4359–L4361, L4441–L4456, L4979–L4989): the docked carrier
    /// (stand at the dock) or, with the belt stopped, a carrier standing on the floor line beside him (stand at it).
    /// SetDownHigh, turned into the set. The stand point is the carrier chosen by the latest <see cref="IsAvailable"/>.
    /// </summary>
    public sealed class CarrierLoader : IPlaceTarget
    {
        private readonly CarrierLine _line;
        private int _seq = -1;
        private double _stand, _reach;

        internal CarrierLoader(CarrierLine line) { _line = line; }

        public InteractionCategory Category => InteractionCategory.Item;
        public double StandX => _stand;
        public double Reach => _reach;
        public double StandZ => 0;
        public int Face => +1;
        public double AnchorX => _stand;
        public string Clip => "SetDownHigh";
        public bool TurnIntoSet => true;

        public bool IsAvailable(in InteractionQuery q)
        {
            var c = _line.Loadable(q.X, q.Y);
            if (c == null) { _seq = -1; return false; }
            _seq = c.Seq; _stand = _line.StandFor(c); _reach = _line.ReachFor(c);
            return true;
        }

        public bool Accepts(ICarryable item) => _line.LoadCodeOf(item) != 0;

        /// <summary>SetDown f14: recorded; the line takes it (or refuses it, if the carrier has gone) on its next step.</summary>
        public void OnPlaced(ICarryable item) => _line.Place(_seq, _line.LoadCodeOf(item));
    }
}
