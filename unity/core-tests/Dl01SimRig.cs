using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Bridges;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Drives;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Simulation.Replay;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-01 composed by hand for the U-18 harness (#15) until the U-20 slice's scene sim lands (#16): the real motor,
    /// resolver and U-10 mechanisms (the wiring of <see cref="Dl01SceneTests"/>, plus the cart), on the prototype's
    /// region-1 lane, with the three scene rules the script needs (the trench fail, the checkpoints, the door transit).
    /// <b>Interim:</b> once the slice's scene sim implements <see cref="ISimTarget"/>, the DL-01 replay tests switch to
    /// it and this rig is deleted. Constants cite index.html.
    /// </summary>
    internal sealed class Dl01SimRig : ISimTarget
    {
        private const double Dt = 1.0 / 60.0;
        // Region 1's lane (L281–L303).
        public const double LeftLimit = -0.3, RightLimit = 11.45, LockedLimit = 3.02;
        public const double StepX0 = 3.6, StepX1 = 4.4, StepH = 0.22;
        public const double DoorX0 = 10.0, DoorX1 = 10.8;
        private static readonly double[,] ShutterPath = { { 0.2, 1.6 }, { 2.0, 0.62 }, { 3.2, 0.6 }, { 3.4, 0.02 } };   // L275
        // Checkpoints and where each puts him (§5, L8057–L8082).
        private static double CheckpointX(string cp) => cp == "shutter" ? 2.9 : cp == "hall" ? 8.35 : cp == "door" ? 9.62 : 1.0;
        // The door transit (L2131–L2157): legs at WALK · 0.85 into the passage behind the wall and out at EMERGE_X.
        private const double TransitSpeed = 0.9 * 0.85, PassageZ = -1.25, EmergeX = 13.2;

        private static readonly TippingBridgeParams CartP = TippingBridgeParams.Dl01Cart();

        public readonly MechanismGraph Graph = new MechanismGraph();
        public readonly PulseSequencer Relay;
        public readonly Latch LatchM;
        public readonly Door Shutter;
        public readonly TippingBridge Cart;
        public readonly CrankActuator Crank;
        public readonly Door DoorM;
        public readonly D17Motor Motor;
        private readonly Lane _lane;

        private long _steps;
        private string _checkpoint;
        private string _actTarget;
        private bool _wasActing;
        private double _stuckT = -1, _respawnAt = -1;
        private int _transitStage = -1;
        private double _transitYaw, _transitX, _transitZ;
        private int _region = 1;
        // The opening hand-over (L8107–L8108, L3847–L3855): he checks his label (CheckLabel, 84 f), held 3.2 s more.
        public const double CheckLabelClip = 84 / 24.0, CheckLabelHold = 3.2, CheckLabelCancelAfter = 2.5;
        private double _labelT = -1, _labelEndAt = -1;

        public Dl01SimRig(string checkpoint = "start")
        {
            Relay = Graph.Add(new PulseSequencer("dl01.relay", PulseParams.Dl01Relay()));
            LatchM = Graph.Add(new Latch("dl01.latch", LatchParams.Dl01Latch()));
            Shutter = Graph.Add(new Door("dl01.shutter", DoorParams.Dl01Shutter()));
            Cart = Graph.Add(new TippingBridge("dl01.cart", CartP));
            Crank = Graph.Add(new CrankActuator("dl01.crank", CrankParams.Dl01Crank()));
            DoorM = Graph.Add(new Door("dl01.door", DoorParams.Dl01Door()));
            Graph.Build();
            var resolver = new InteractionResolver();
            resolver.Register(LatchM);
            resolver.Register(Cart);
            resolver.Register(Crank);
            _lane = new Lane(this);
            Motor = new D17Motor(MotorConfig.Prototype(), _lane, resolver);
            Restore(checkpoint);
        }

        private void Restore(string cp)
        {
            _checkpoint = cp;
            _labelT = cp == "start" && _steps == 0 ? 0 : -1;                 // only from the opening, once
            _labelEndAt = -1;
            Graph.Reset(DeadLetter.Core.Mechanisms.Checkpoint.Prototype(cp));
            Motor.Place(CheckpointX(cp), 0, 1);
            _stuckT = _respawnAt = -1;
            _actTarget = null;
            _wasActing = false;
        }

        // ---- ISimView ----------------------------------------------------------------------------------------------
        public double Clock => _steps * Dt;
        public double X => _transitStage >= 0 ? _transitX : Motor.X;
        public double Y => Motor.Y;
        public bool Grounded => Motor.Grounded;
        public bool Mantling => Motor.IsMantling;
        public string Act => _stuckT >= 0 ? DeadLetter.Core.Simulation.Replay.Scripts.Dl01WakeScript.TrenchStuck : _labelT >= 0 ? "CheckLabel" : Motor.IsActing ? _actTarget ?? Motor.ActVerb.ToString() : null;
        public HoldKind Hold => Motor.Hold;
        public bool Riding => false;
        public bool Playing => _respawnAt < 0;
        public bool InTransit => _transitStage >= 0;
        public int Region => _region;
        public string Checkpoint => _checkpoint;
        public string SceneName => _region == 1 ? "DL-01 The Wake" : "DL-02 The Sorting Hall";
        public string Near => !InTransit && _stuckT < 0 && Motor.PreviewUse(out var c) && c.Target is IMechanism m ? m.Id.ToString() : null;
        public int Deaths { get; private set; }
        public int Found => 0;
        public MechanismGraph Mechanisms => Graph;

        // ---- the step ----------------------------------------------------------------------------------------------
        public void Step(in MotorInput input)
        {
            _steps++;
            if (_respawnAt >= 0)
            {
                if (Clock >= _respawnAt) { Deaths++; Restore(_checkpoint); }   // respawn(): fade 1.3 s, then the checkpoint (L2997)
                Graph.Step(Dt, PlayerPose.Away);
                return;
            }
            if (_transitStage >= 0) { StepTransit(); Graph.Step(Dt, PlayerPose.Away); return; }

            if (_labelT >= 0 && StepHandover(input)) { Graph.Step(Dt, Pose(true)); return; }
            string near = Near;
            Motor.Step(_stuckT >= 0 ? MotorInput.None : input, Dt);
            if (Motor.IsActing && !_wasActing) _actTarget = near;
            if (!Motor.IsActing) _actTarget = null;
            _wasActing = Motor.IsActing;
            Graph.Step(Dt, Pose(Motor.IsActing || _stuckT >= 0));
            Rules();
        }

        private PlayerPose Pose(bool busy) =>
            new PlayerPose(Motor.X, Motor.Y, Motor.Z, Motor.Crouched, busy, Motor.Vx, Motor.Grounded, Motor.Hold != HoldKind.None);

        /// <summary>
        /// The hand-over quirk (<c>updateQuirk</c>, L3847–L3855): it plays out, then holds; after 2.5 s a move cancels
        /// it. Returns true while it still holds him. The bot never cancels it (its quirk has <c>cancel: false</c>).
        /// </summary>
        private bool StepHandover(in MotorInput input)
        {
            double t = _labelT;
            _labelT += Dt;
            bool moving = input.Move != 0 || input.JumpPressed;
            if (Clock - Dt > CheckLabelCancelAfter && moving && t > 0.3) { _labelT = -1; return false; }
            if (t >= CheckLabelClip - 0.05)
            {
                if (_labelEndAt < 0) _labelEndAt = Clock - Dt;
                if (Clock - Dt - _labelEndAt >= CheckLabelHold) { _labelT = -1; return false; }
            }
            return true;
        }

        /// <summary>DL-01's scene rules: checkpoints (L1677, L2065, L1890), the trench fail (L4764, L4519–L4523), the door (L2039).</summary>
        private void Rules()
        {
            if (_checkpoint == "start" && LatchM.State == LatchState.Released) _checkpoint = "shutter";
            if (Motor.X > CartP.PitX1 + 0.2 && Motor.Y > -0.05 && _checkpoint != "door" && _checkpoint != "hall") _checkpoint = "hall";
            if (Crank.State == CrankState.Done && _checkpoint == "hall") _checkpoint = "door";

            if (_stuckT >= 0)
            {
                _stuckT += Dt;
                if (_stuckT > 2.0) { _stuckT = -1; _respawnAt = Clock + 1.3; }
                return;
            }
            if (Mech.Emitted(Graph, "dl01.cart", TippingBridgeEvent.Stranded) && !Motor.IsActing) _stuckT = 0;

            if (DoorM.Position >= 1 && Motor.X > DoorX0 + 0.15 && Motor.X < DoorX1 - 0.15 && Motor.Grounded)
            {
                _transitStage = 0; _transitX = Motor.X; _transitZ = 0; _transitYaw = Motor.Yaw;
            }
        }

        private static readonly double[] LegYaw = { Math.PI, Math.PI / 2, 0, Math.PI / 2 };

        private void StepTransit()
        {
            double yaw = LegYaw[_transitStage];
            if (Math.Abs(_transitYaw - yaw) > 0.06)
            {
                double d = yaw - _transitYaw, s = 8.0 * Dt;                     // the motor's yaw rate (L7581)
                _transitYaw += Math.Abs(d) <= s ? d : Math.Sign(d) * s;
                return;
            }
            if (_transitStage == 3) { _transitStage = -1; Motor.Place(_transitX, 0, 1); _checkpoint = "room"; return; }
            double px = _transitStage == 0 ? (DoorX0 + DoorX1) / 2 : EmergeX, pz = _transitStage == 2 ? 0 : PassageZ;
            double dx = px - _transitX, dz = pz - _transitZ, dist = Math.Sqrt(dx * dx + dz * dz);
            if (dist < 0.01)
            {
                _transitX = px; _transitZ = pz; _transitStage++;
                if (_transitStage == 2) _region = 2;
                return;
            }
            double step = Math.Min(dist, TransitSpeed * Dt);
            _transitX += dx / dist * step; _transitZ += dz / dist * step;
        }

        /// <summary>Region 1's height field (<c>floorAt</c>/<c>surfaceAt</c>/<c>ceilingAt</c>/limits, L1620–L1769, L4139–L4146).</summary>
        private sealed class Lane : IMotorWorld
        {
            private readonly Dl01SimRig _r;
            public Lane(Dl01SimRig r) { _r = r; }

            public double SurfaceAt(double x, double refY)
            {
                double pit = _r.Cart.SurfaceAt(x);                                   // the trench, with or without the cart
                double h = double.IsNaN(pit) ? 0 : pit;
                if (x >= StepX0 && x <= StepX1) h = Math.Max(h, StepH);
                var c = CartP;
                if ((_r.Cart.State == TippingBridgeState.Free || _r.Cart.State == TippingBridgeState.AtLip) && Math.Abs(x - _r.Cart.X) <= c.Half)
                    h = Math.Max(h, c.Height);
                return h;
            }

            public double CeilingAt(double x, double refY)
            {
                double a = _r.Shutter.Position * Math.PI / 180, cs = Math.Cos(a), sn = Math.Sin(a);
                double h = x < 2.6 ? 2.45 : 4;
                double px = ShutterPath[0, 0], pz = ShutterPath[0, 1];
                double ox = 0.2, oz = 1.6;
                double x0 = ox + (px - ox) * cs - (pz - oz) * sn, z0 = oz + (px - ox) * sn + (pz - oz) * cs;
                for (int i = 1; i < ShutterPath.GetLength(0); i++)
                {
                    double qx = ShutterPath[i, 0] - ox, qz = ShutterPath[i, 1] - oz;
                    double x1 = ox + qx * cs - qz * sn, z1 = oz + qx * sn + qz * cs;
                    if (x >= Math.Min(x0, x1) && x <= Math.Max(x0, x1) && Math.Abs(x1 - x0) > 1e-4) h = Math.Min(h, z0 + (z1 - z0) * (x - x0) / (x1 - x0));
                    x0 = x1; z0 = z1;
                }
                return h;
            }

            public void Limits(double x, double y, out double left, out double right)
            {
                left = LeftLimit;
                right = _r.LatchM.State == LatchState.Released ? RightLimit : LockedLimit;
            }

            public bool IsRamp(double x) => false;

            public bool LedgeAhead(double x, double y, int dir, double range, double stepUp, out Ledge ledge) =>
                LaneProbe.ScanLedge(this, x, y, dir, range, stepUp, out ledge);
        }
    }
}
