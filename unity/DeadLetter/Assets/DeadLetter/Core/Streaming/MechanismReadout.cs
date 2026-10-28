using System;
using System.Globalization;
using DeadLetter.Core.Beings;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Hazards;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Bridges;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Cycles;
using DeadLetter.Core.Mechanisms.Docks;
using DeadLetter.Core.Mechanisms.Drives;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Mechanisms.Routes;
using DeadLetter.Core.Mechanisms.Water;
using DeadLetter.Core.Push;
using DeadLetter.Core.Scenes.Dl03;
using DeadLetter.Core.Scenes.Dl14b;
using DeadLetter.Core.Scenes.Dl15;
using DeadLetter.Core.Scenes.Dl16;
using DeadLetter.Core.Scenes.Dl17;

namespace DeadLetter.Core.Streaming
{
    /// <summary>A value a mechanism view reads from Core (<see cref="MechanismReadout"/>).</summary>
    public enum ViewChannel
    {
        None = 0,
        /// <summary><see cref="IPositionSource.Position"/>: a door's or gate's travel (m), a crank's progress.</summary>
        Position = 1,
        /// <summary>Lane x of a loose body or a cart (m).</summary>
        X = 2,
        /// <summary>Height of a body, a cart, a ram's face; a scale plate's dip (down is negative) (m).</summary>
        Y = 3,
        /// <summary>A lever's, wheel's, needle's or arm's angle (degrees).</summary>
        Angle = 4,
        /// <summary>Lamp <c>index</c>'s brightness (relay lamps, the press's tell lamp, a plate's sill lamps), ≥ 0.</summary>
        Lamp = 5,
        /// <summary>Depth into the set (Unity +z, three.js −z) of a drawer or a figure leaving its bay (m).</summary>
        Z = 6,
        /// <summary>Part <c>index</c>'s scale factor (a blind rolled up, the tree growing, water in a bed), absolute.</summary>
        Scale = 7,
        /// <summary>Part <c>index</c> shows (1) or not (0): a stream running, a blind rolled away, absolute.</summary>
        Shown = 8,
    }

    /// <summary>How a view applies a channel to its node (lane axes: x along the lane, y up, z into the set).</summary>
    public enum ViewMotion
    {
        None = 0,
        TranslateX = 1,
        TranslateY = 2,
        TranslateZ = 3,
        /// <summary>About lane z (the axis toward the camera): the sign three.js's <c>rotation.z</c> has (§0.2).</summary>
        RotateZ = 4,
        /// <summary>Scales the node's rest emission colour.</summary>
        Emission = 5,
        /// <summary>About lane x, with three.js's <c>rotateX</c> sign (a step folding down, a pawl dropping).</summary>
        RotateX = 6,
        /// <summary>About lane y (up), with three.js's <c>rotateY</c> sign (a door swinging open, the escort turning).</summary>
        RotateY = 7,
        /// <summary>Sets the node's y scale to its rest scale × the value (absolute, like <see cref="Emission"/>).</summary>
        ScaleY = 8,
        /// <summary>Sets the node's scale to its rest scale × the value on every axis (absolute).</summary>
        ScaleAll = 9,
        /// <summary>The node's renderers show while the value × scale is over 0.5 (absolute).</summary>
        Visible = 10,
    }

    /// <summary>One channel of one view: the value read, which lamp, how it moves the node and by how much per unit.</summary>
    public readonly struct ViewBinding : IEquatable<ViewBinding>
    {
        public readonly ViewChannel Channel;
        public readonly int Index;
        public readonly ViewMotion Motion;
        public readonly double Scale;

        public ViewBinding(ViewChannel channel, ViewMotion motion, double scale = 1, int index = 0)
        {
            Channel = channel; Motion = motion; Scale = scale; Index = index;
        }

        public bool Equals(ViewBinding o) => Channel == o.Channel && Index == o.Index && Motion == o.Motion && Scale == o.Scale;
        public override bool Equals(object obj) => obj is ViewBinding b && Equals(b);
        public override int GetHashCode() => ((int)Channel * 31 + Index) * 31 + (int)Motion;
        public override string ToString() => Channel + (Channel == ViewChannel.Lamp ? "[" + Index + "]" : "") + "→" + Motion + "×" + Scale.ToString("R", CultureInfo.InvariantCulture);
    }

    /// <summary>
    /// Reads the values a mechanism's art moves by (port_architecture §4.13l: views read state, never decide). A view
    /// resolves a reader once when it binds (<see cref="Reader"/>, a delegate over the mechanism) and samples it after each
    /// step, so a frame does no type tests and no string lookups. Values are absolute; a view moves its node by the change
    /// from the value the chapter starts with (the art is authored in that state), times the binding's scale.
    /// </summary>
    public static class MechanismReadout
    {
        private const double Deg = 180.0 / Math.PI;
        /// <summary>DL-17's drawer slides out 0.45 m (<c>ATT2.drawer.out</c>, L5529).</summary>
        private const double DrawerOut = 0.45;
        /// <summary>DL-14b's bay and rail, three.js z (<c>ATT3.bayZ</c>, <c>railZ</c>, L5898).</summary>
        private const double BayZ = -0.85, RailZ14b = -0.55;
        /// <summary>DL-14a's cord leaves its pulley at 3.10 m (art/ch1/dl14a.py HOOK_PULLEY): 2.215 m long with W1 down.</summary>
        private const double CordTop = 3.10;
        /// <summary>DL-13's tree: trunk, three branches, leaves, each growing in turn (L5432–L5433).</summary>
        private const int TreeParts = 5;

        /// <summary>Tree part <paramref name="i"/>'s growth, <c>clamp(tree · 5 − i, 0, 1)</c> (L5433).</summary>
        private static double TreePart(double tree, int i) => Smooth.Clamp(tree * 5 - i, 0, 1);

        /// <summary>Whether <paramref name="m"/> has <paramref name="channel"/> (lamp <paramref name="index"/>).</summary>
        public static bool Supports(IMechanism m, ViewChannel channel, int index = 0) => Reader(m, channel, index, null) != null;

        /// <summary>
        /// A reader of <paramref name="channel"/> on <paramref name="m"/>, or null when it has no such value.
        /// <paramref name="calm"/> is the calm-mode flag a flickering lamp reads (null: off).
        /// </summary>
        public static Func<double> Reader(IMechanism m, ViewChannel channel, int index, Func<bool> calm)
        {
            if (m == null) return null;
            switch (channel)
            {
                case ViewChannel.Z:
                    switch (m)
                    {
                        case Dl17Drawer d: return () => -DrawerOut * Smooth.Step(d.Position);                 // L5840
                        case Dl14bFigure f: return () => -(BayZ + (RailZ14b - BayZ) * Smooth.Step(f.Out));      // L6432
                    }
                    return null;
                case ViewChannel.Scale:
                    switch (m)
                    {
                        case CycleClock c when index >= 0 && index < TreeParts && c.TrackIndex("tree") >= 0:
                        {
                            int tree = c.TrackIndex("tree");
                            return () => Math.Max(0.001, Smooth.Step(TreePart(c.Value(tree), index)));               // L5433
                        }
                        case PairedBlindDrive b when index == 0: return () => Math.Max(0.04, b.A);                  // L5443, L6278
                        case PairedBlindDrive b when index == 1: return () => Math.Max(0.04, b.B);
                        case PairedBlindDrive b when index == 2 && !double.IsNaN(b.HookY):
                            return () => Math.Max(0.05, (CordTop - (b.HookY + 0.135)) / 2.215);                       // L6286
                        case SluiceRig r when index == 0: return () => Math.Max(0.02, r.Tank);                      // L6307
                        case SluiceRig r when index >= 1 && index <= r.BedCount: return () => Math.Max(0.01, r.Bed(index - 1));   // L6309
                    }
                    return null;
                case ViewChannel.Shown:
                    switch (m)
                    {
                        case CycleClock c when index >= 0 && index < TreeParts && c.TrackIndex("tree") >= 0:
                        {
                            int tree = c.TrackIndex("tree");
                            return () => TreePart(c.Value(tree), index) > 0.01 ? 1 : 0;                            // L5433
                        }
                        case PairedBlindDrive b when index == 0: return () => b.A > 0.06 ? 1 : 0;                   // L5443
                        case PairedBlindDrive b when index == 1: return () => b.B > 0.06 ? 1 : 0;
                        case SluiceRig r when index >= 0 && index < r.BedCount: return () => r.Bed(index) > 0.01 ? 1 : 0;        // L6309
                        case SluiceRig r when index >= 10 && index < 10 + r.BedCount: return () => r.Fed(index - 10) ? 1 : 0;   // L6310
                        case SluiceRig r when index >= 20 && index < 23: return () => r.PipeFlow(index - 20) ? 1 : 0;           // L6315
                    }
                    return null;
                case ViewChannel.Position:
                    if (m is IPositionSource ps) return () => ps.Position;
                    return null;
                case ViewChannel.X:
                    switch (m)
                    {
                        case EscortTrolley e: return () => e.X;
                        case Dl14bFigure f: return () => f.X;
                        case TippingBridge b: return () => b.X;
                        case Cradle c: return () => c.Position;
                        case IPlateBody body: return () => body.X;
                    }
                    return null;
                case ViewChannel.Y:
                    switch (m)
                    {
                        case Dl15Figure f: return () => f.Base;
                        case PairedBlindDrive b when index == 0 && !double.IsNaN(b.HemY): return () => b.HemY;      // L6279
                        case PairedBlindDrive b when index == 1 && !double.IsNaN(b.HookY): return () => b.HookY;    // L6285
                        case SluiceRig r: return () => r.FloatY;                                                    // L6312
                        case CarriedItem i: return () => i.BaseY;
                        case Dl03Weight w: return () => w.BaseY;
                        case TippingBridge b: return () => b.ViewY;
                        case PeriodicCrusher p: return () => p.Face;
                        case WeighScale s: return () => -s.Dip;
                        case FollowerActuator f: return () => f.Position;
                    }
                    return null;
                case ViewChannel.Angle:
                    switch (m)
                    {
                        case Latch l when index == 1: return () => l.Engaged ? 90 : 0;                               // DL-16's latch dropping, L5838
                        case CycleBrake b: return () => b.Engaged ? 40 : 0;                                          // L5431, L6271
                        case CycleClock c when index == 0: return () => -360 * c.Dial;                              // L5430, L6272
                        case CycleClock c when index >= 1 && index <= c.TrackCount: return () => -90 * (1 - c.Value(index - 1));   // L5429
                        case WindCrank w: return () => w.SpinRad * Deg;                                              // L5447, L6277
                        case PairedBlindDrive b when index == 0: return () => b.WheelARad * Deg;                    // L5471
                        case PairedBlindDrive b when index == 1: return () => b.ClutchRad * Deg;                    // L5473
                        case PairedBlindDrive b when index == 2 || index == 3: return () => -90 * (1 - b.LedgeDeploy(index - 2));   // L5444
                        case Door d: return () => 90 * Smooth.Step(d.Position);                                      // the swing doors, L5832, L5841, L6283
                        case EscortTrolley e: return () => 180 * e.Facing01;                                         // L6424
                        case Dl15Figure f: return () => -0.18 * Smooth.Step(f.Lean) * Deg;                           // L5819
                        case PupilLift l: return () => -90 * Smooth.Step(1 - l.Y / 0.25);                            // L5824
                        case Dl16Lever l: return () => l.Engaged || l.Latched ? -35 : 0;                             // L5837
                        case Dl16Bridge b: return () => -90 * Smooth.Step(b.Position);                               // L5836
                        case Sluice s: return () => s.Engaged ? 0 : 80;                                              // L6303
                        case FloatLatch f: return () => f.ArmDeg;                                                    // L6314
                        case Latch l: return () => l.LeverDeg;
                        case CrankActuator c: return () => c.WheelDeg;
                        case PointsLever p: return () => p.ViewDeg;
                        case TippingBridge b: return () => b.DipRad * Deg;
                        case Cradle c: return () => c.ArmRad * Deg;
                        case PeriodicCrusher p: return () => p.WheelRad * Deg;
                        case WeighScale s: return () => s.Needle;
                    }
                    return null;
                case ViewChannel.Lamp:
                    switch (m)
                    {
                        // Chapter 1's lamps at their calm-mode levels: the prototype's blinks (sin of the game clock) are not read yet.
                        case PresenceStrip p when index == 0: return () => p.Present ? 5.5 : 0.05;                  // L5396
                        case PresenceStrip p when index == 1: return () => p.CoatOn || p.Present ? 5.5 : 0.05;      // L5397, blink = 1 (calm)
                        case CycleClock c when index == 0: return () => c.On ? 3 : 0.05;                             // L5415 (the seat's blink not read)
                        case CycleClock c when index == 1 && c.TrackCount > 0: return () => 0.15 + 4.5 * c.Value(0); // L6273
                        case SeatRow r when index >= 0 && index < r.Lamps: return () => r.Lit(index) ? 6 : 0.05;     // L5829, blink = 1
                        case PulseSequencer q when index >= 0 && index < q.LampCount: return () => q.Value(index);
                        case PeriodicCrusher p when index == 0: return () => p.Lamp(calm != null && calm());
                        case LoadPlate l when index >= 0: return () => l.SillLampLit(index) ? 1 : 0;
                    }
                    return null;
                default:
                    return null;
            }
        }
    }

    /// <summary>
    /// The default view of each art mechanism type and part (the <c>MECH_&lt;Type&gt;_&lt;id&gt;[__&lt;part&gt;]</c> nodes of
    /// docs/unity/asset_conventions.md; <c>Type</c> is the art's name, e.g. <c>Press</c> for Core's <c>PeriodicCrusher</c>):
    /// the channels that move the node. The Editor's scene builder copies them onto each node's view; the director tunes
    /// scales and pivots on the component. A node with no binding stays where the art put it (a rail, a frame).
    /// <para>The axes and signs are the prototype's (a shutter rises by its travel, a counterweight falls by it, a lever
    /// turns by its angle about lane z); none has been checked against the art in Unity yet.</para>
    /// </summary>
    public static class MechanismViewBindings
    {
        private static readonly ViewBinding[] None = new ViewBinding[0];

        /// <summary>The bindings for a node of art type <paramref name="type"/> and part <paramref name="part"/> ("" for the root).</summary>
        public static ViewBinding[] For(string type, string part)
        {
            part = part ?? "";
            switch (type)
            {
                // ---- Chapter 1 (conventions.py MECHANISMS, index.html L5378–L6434) -------------------------------------
                case "CarriedItem":
                    return new[] { new ViewBinding(ViewChannel.X, ViewMotion.TranslateX), new ViewBinding(ViewChannel.Y, ViewMotion.TranslateY) };
                case "PresenceStrip":
                    return part == "AttLampPresent" ? Lamp(0) : part == "AttLampCoat" ? Lamp(1) : None;
                case "CycleBrake":
                    return part.Length == 0 ? One(ViewChannel.Angle, ViewMotion.RotateX) : None;
                case "CycleClock":
                    if (part == "AttDialHand" || part == "Att14aDialHand") return One(ViewChannel.Angle, ViewMotion.RotateZ);
                    if (TryLampIndex(part, "AttStep", out int step) && step >= 1 && step <= 3)
                        return new[] { new ViewBinding(ViewChannel.Angle, ViewMotion.RotateX, 1, step) };
                    if (part == "AttLessonLamp") return Lamp(0);
                    if (part == "Att14aSunLamp") return Lamp(1);
                    int tree = Array.IndexOf(TreeParts, part);
                    return tree >= 0 ? new[] { new ViewBinding(ViewChannel.Scale, ViewMotion.ScaleAll, 1, tree), new ViewBinding(ViewChannel.Shown, ViewMotion.Visible, 1, tree) } : None;
                case "WindCrank":
                case "Dl16Lever":
                case "Dl16Bridge":
                case "FloatLatch":
                    return part.Length == 0 ? One(ViewChannel.Angle, ViewMotion.RotateZ) : None;
                case "PairedBlindDrive":
                    switch (part)
                    {
                        case "AttBlindA": case "Att14aBlindW1": return Blind(0);
                        case "AttBlindB": case "Att14aBlindW2": return Blind(1);
                        case "AttWheelA": return new[] { new ViewBinding(ViewChannel.Angle, ViewMotion.RotateZ, 1, 0) };
                        case "AttClutch": return new[] { new ViewBinding(ViewChannel.Angle, ViewMotion.RotateZ, 1, 1) };
                        case "AttLedgeA": return new[] { new ViewBinding(ViewChannel.Angle, ViewMotion.RotateX, 1, 2) };
                        case "AttLedgeB": return new[] { new ViewBinding(ViewChannel.Angle, ViewMotion.RotateX, 1, 3) };
                        case "Att14aHemW1": return new[] { new ViewBinding(ViewChannel.Y, ViewMotion.TranslateY, 1, 0) };
                        case "Att14aCordHook": return new[] { new ViewBinding(ViewChannel.Y, ViewMotion.TranslateY, 1, 1) };
                        case "Att14aCord": return new[] { new ViewBinding(ViewChannel.Scale, ViewMotion.ScaleY, 1, 2) };
                        default: return None;                                       // AttChain, AttPanelPeel: ArtExportTests.Chapter1Unbound
                    }
                case "Dl14bFigure":
                    return new[] { new ViewBinding(ViewChannel.X, ViewMotion.TranslateX), new ViewBinding(ViewChannel.Z, ViewMotion.TranslateZ) };
                case "EscortTrolley":                                               // the cone turns about the trolley's centre: set its pivot
                    return new[] { new ViewBinding(ViewChannel.X, ViewMotion.TranslateX), new ViewBinding(ViewChannel.Angle, ViewMotion.RotateY) };
                case "Dl15Figure":
                    return new[]
                    {
                        new ViewBinding(ViewChannel.X, ViewMotion.TranslateX),
                        new ViewBinding(ViewChannel.Y, ViewMotion.TranslateY),
                        new ViewBinding(ViewChannel.Angle, ViewMotion.RotateZ),
                    };
                case "PupilLift":
                    if (part.Length == 0) return One(ViewChannel.Position, ViewMotion.TranslateY);
                    if (part == "Att15LiftCW") return One(ViewChannel.Position, ViewMotion.TranslateY, -1);
                    if (part == "Att15LiftGate") return new[] { new ViewBinding(ViewChannel.Position, ViewMotion.TranslateY), new ViewBinding(ViewChannel.Angle, ViewMotion.RotateY) };
                    return None;                                                    // its lamps: ArtExportTests.Chapter1Unbound
                case "SeatRow":
                    return TryLampIndex(part, "Att15Lamp", out int seat) && seat >= 1 && seat <= 3 ? Lamp(seat - 1) : None;
                case "CounterweightRack":
                    return part.Length == 0 ? One(ViewChannel.Position, ViewMotion.TranslateY) : None;
                case "Dumbwaiter":
                    return part.Length == 0 ? One(ViewChannel.Position, ViewMotion.TranslateY)
                        : part == "Att16aCW" ? One(ViewChannel.Position, ViewMotion.TranslateY, -1) : None;
                case "Dl17Drawer":
                    return One(ViewChannel.Z, ViewMotion.TranslateZ);
                case "Sluice":
                    return One(ViewChannel.Angle, ViewMotion.RotateX);
                case "SluiceRig":
                    if (part == "Att17TankWater") return new[] { new ViewBinding(ViewChannel.Scale, ViewMotion.ScaleY, 1, 0) };
                    if (part == "Att17Float") return One(ViewChannel.Y, ViewMotion.TranslateY);
                    if (TryLampIndex(part, "Att17Water", out int bed) && bed >= 1 && bed <= 3)
                        return new[] { new ViewBinding(ViewChannel.Scale, ViewMotion.ScaleY, 1, bed), new ViewBinding(ViewChannel.Shown, ViewMotion.Visible, 1, bed - 1) };
                    if (TryLampIndex(part, "Att17Stream", out int stream) && stream >= 1 && stream <= 3)
                        return new[] { new ViewBinding(ViewChannel.Shown, ViewMotion.Visible, 1, 10 + stream - 1) };
                    if (part.StartsWith("Att17PipeFlow", StringComparison.Ordinal) && part.Length == "Att17PipeFlow".Length + 1)
                        return new[] { new ViewBinding(ViewChannel.Shown, ViewMotion.Visible, 1, 20 + part[part.Length - 1] - 'A') };
                    return None;
                case "Dl12Peg":
                case "Dl16aTin":
                case "SluiceValve":
                    return None;                                                    // ArtExportTests.Chapter1Static / Chapter1Unbound
                // ---- The prologue ----------------------------------------------------------------------------------------
                case "Door":
                    if (part.StartsWith("Counterweight", StringComparison.Ordinal)) return One(ViewChannel.Position, ViewMotion.TranslateY, -1);
                    if (part == "ShutterRail" || part == "Pulley") return None;
                    return One(ViewChannel.Position, ViewMotion.TranslateY);
                case "PlateDoor":
                case "FollowerActuator":
                    return part.Length == 0 ? One(ViewChannel.Position, ViewMotion.TranslateY) : None;
                case "Latch":
                case "CrankActuator":
                case "PointsLever":
                    return part.Length == 0 || type == "Latch" ? One(ViewChannel.Angle, ViewMotion.RotateZ) : None;
                case "PulseSequencer":
                    return TryLampIndex(part, "RelayLamp", out int lamp) ? new[] { new ViewBinding(ViewChannel.Lamp, ViewMotion.Emission, 1, lamp) } : None;
                case "TippingBridge":
                    return new[]
                    {
                        new ViewBinding(ViewChannel.X, ViewMotion.TranslateX),
                        new ViewBinding(ViewChannel.Y, ViewMotion.TranslateY),
                        new ViewBinding(ViewChannel.Angle, ViewMotion.RotateZ),
                    };
                case "Press":
                    return part.Length == 0 ? One(ViewChannel.Y, ViewMotion.TranslateY)
                        : part == "PressFlywheel" ? One(ViewChannel.Angle, ViewMotion.RotateZ) : None;
                case "Carryable":
                    return new[] { new ViewBinding(ViewChannel.X, ViewMotion.TranslateX), new ViewBinding(ViewChannel.Y, ViewMotion.TranslateY) };
                case "Pushable":
                case "Draggable":
                    return One(ViewChannel.X, ViewMotion.TranslateX);
                case "Cradle":
                    return part == "CradleArmL" ? One(ViewChannel.Angle, ViewMotion.RotateZ)
                        : part == "CradleArmR" ? One(ViewChannel.Angle, ViewMotion.RotateZ, -1) : None;
                case "WeighScale":
                    return part.Length == 0 ? One(ViewChannel.Y, ViewMotion.TranslateY) : One(ViewChannel.Angle, ViewMotion.RotateZ);
                default:
                    return None;
            }
        }

        /// <summary>
        /// The bindings for mechanism <paramref name="id"/>'s node: <see cref="For(string, string)"/>, except where one
        /// mechanism of a type moves unlike the rest. Chapter 1's doors swing open about their hinge (<c>rotateY</c>: DL-14a's
        /// and DL-17's by 90°, DL-15's by 95°; L6283, L5841, L5832) where the prologue's <c>Door</c>s rise; DL-16's latch drops
        /// a quarter turn once the rack latches it (L5838), where DL-01's lever follows the Pull clip.
        /// </summary>
        public static ViewBinding[] For(string type, string id, string part)
        {
            if (type == "Door" && string.IsNullOrEmpty(part))
            {
                switch (id)
                {
                    case "dl14a.door":
                    case "dl17.stairDoor":
                        return One(ViewChannel.Angle, ViewMotion.RotateY);
                    case "dl15.classDoor":
                        return One(ViewChannel.Angle, ViewMotion.RotateY, 95.0 / 90.0);
                }
            }
            if (type == "Latch" && id == "dl16.latch" && string.IsNullOrEmpty(part))
                return new[] { new ViewBinding(ViewChannel.Angle, ViewMotion.RotateZ, 1, 1) };
            return For(type, part);
        }

        /// <summary>DL-13's tree, in growing order (L5432).</summary>
        private static readonly string[] TreeParts = { "AttTreeTrunk", "AttTreeBranch1", "AttTreeBranch2", "AttTreeBranch3", "AttTreeLeaves" };

        private static ViewBinding[] Lamp(int index) => new[] { new ViewBinding(ViewChannel.Lamp, ViewMotion.Emission, 1, index) };

        /// <summary>A blind: rolled up into its pelmet by its y scale, gone once nearly up (L5443, L6278).</summary>
        private static ViewBinding[] Blind(int index) => new[]
        {
            new ViewBinding(ViewChannel.Scale, ViewMotion.ScaleY, 1, index),
            new ViewBinding(ViewChannel.Shown, ViewMotion.Visible, 1, index),
        };

        private static ViewBinding[] One(ViewChannel c, ViewMotion m, double scale = 1) => new[] { new ViewBinding(c, m, scale) };

        /// <summary>"RelayLamp2" → 2.</summary>
        private static bool TryLampIndex(string part, string stem, out int index)
        {
            index = 0;
            if (!part.StartsWith(stem, StringComparison.Ordinal) || part.Length == stem.Length) return false;
            return int.TryParse(part.Substring(stem.Length), NumberStyles.None, CultureInfo.InvariantCulture, out index);
        }
    }
}
