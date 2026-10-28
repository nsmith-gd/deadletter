using System;
using System.Globalization;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Hazards;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Bridges;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Docks;
using DeadLetter.Core.Mechanisms.Drives;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Mechanisms.Routes;
using DeadLetter.Core.Push;
using DeadLetter.Core.Scenes.Dl03;

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
                case ViewChannel.Position:
                    if (m is IPositionSource ps) return () => ps.Position;
                    return null;
                case ViewChannel.X:
                    switch (m)
                    {
                        case TippingBridge b: return () => b.X;
                        case Cradle c: return () => c.Position;
                        case IPlateBody body: return () => body.X;
                    }
                    return null;
                case ViewChannel.Y:
                    switch (m)
                    {
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
                        case PulseSequencer q when index >= 0 && index < q.LampCount: return () => q.Value(index);
                        case PeriodicCrusher p when index == 0: return () => p.Lamp(calm != null && calm());
                        case LoadPlate l when index >= 0: return () => l.SillLampLit(index) ? 1 : 0;
                        case Cradle c when index == 0: return () => Cradle.SeatedLamp(c.SeatedFor, calm != null && calm());
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
