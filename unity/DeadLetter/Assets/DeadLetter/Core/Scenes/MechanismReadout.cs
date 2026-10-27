using System;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Bridges;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Drives;
using DeadLetter.Core.Mechanisms.Plates;

namespace DeadLetter.Core.Scenes
{
    /// <summary>
    /// The one place views read Core mechanism state (§4.13l: "Runtime MechanismViews read public state each frame"),
    /// so the Runtime view stays a single generic component and the mapping is testable headless. A scene port that
    /// needs a new value adds a <see cref="ViewChannel"/> and a case here.
    /// </summary>
    public static class MechanismReadout
    {
        /// <summary>True if <paramref name="m"/> can answer <paramref name="channel"/>.</summary>
        public static bool Supports(IMechanism m, ViewChannel channel)
        {
            switch (channel)
            {
                case ViewChannel.Position: return m is IPositionSource;
                case ViewChannel.LeverDeg: return m is Latch;
                case ViewChannel.WheelDeg: return m is CrankActuator;
                case ViewChannel.Lamp: return m is PulseSequencer;
                case ViewChannel.BridgeX:
                case ViewChannel.BridgeY:
                case ViewChannel.BridgeDipDeg: return m is TippingBridge;
                case ViewChannel.Needle: return m is LoadPlate;
                case ViewChannel.ShutterCounterweightY: return m is Door;
                default: return false;
            }
        }

        /// <summary>The raw value (before a view's offset and scale). Throws if the mechanism cannot answer.</summary>
        public static double Read(IMechanism m, ViewChannel channel, int index = 0)
        {
            switch (channel)
            {
                case ViewChannel.Position when m is IPositionSource p: return p.Position;
                case ViewChannel.LeverDeg when m is Latch l: return l.LeverDeg;
                case ViewChannel.WheelDeg when m is CrankActuator c: return c.WheelDeg;
                case ViewChannel.Lamp when m is PulseSequencer s: return index >= 0 && index < s.LampCount ? s.Value(index) : 0;
                case ViewChannel.BridgeX when m is TippingBridge b: return b.X;
                case ViewChannel.BridgeY when m is TippingBridge b: return b.ViewY;
                case ViewChannel.BridgeDipDeg when m is TippingBridge b: return b.DipRad * (180 / Math.PI);
                case ViewChannel.Needle when m is LoadPlate n: return n.Needle;
                case ViewChannel.ShutterCounterweightY when m is Door d: return Door.ShutterCounterweightY(d.Elapsed);
                default: throw new ArgumentException((m == null ? "null" : m.ToString()) + " cannot answer " + channel + ".");
            }
        }

        /// <summary>The value a view applies: <c>(Read + Offset) × Scale</c>.</summary>
        public static double Apply(MechanismViewDef def, IMechanism m) => (Read(m, def.Channel, def.Index) + def.Offset) * def.Scale;
    }

    /// <summary>Scene definitions by ID, for the Runtime host and the Editor builder.</summary>
    public static class SceneCatalog
    {
        public static readonly string[] Ids = { Prologue.Dl01Wake.SceneId };

        /// <summary>A new definition for <paramref name="id"/>, or null if the scene is not ported yet.</summary>
        public static SceneDefinition Create(string id)
        {
            switch (id)
            {
                case Prologue.Dl01Wake.SceneId: return new Prologue.Dl01Wake();
                default: return null;
            }
        }
    }
}
