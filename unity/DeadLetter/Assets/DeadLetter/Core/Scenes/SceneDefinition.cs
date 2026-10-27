using System;
using System.Collections.Generic;
using DeadLetter.Core.Camera;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;

namespace DeadLetter.Core.Scenes
{
    /// <summary>Where D-17 stands when the world is rebuilt at a checkpoint (<c>CHECKPOINTS[cp].x/y</c>, L7975–L8014).</summary>
    public readonly struct SpawnPoint
    {
        public readonly string Checkpoint;
        public readonly double X, Y;
        public readonly int Facing;
        public SpawnPoint(string checkpoint, double x, double y = 0, int facing = 1) { Checkpoint = checkpoint; X = x; Y = y; Facing = facing; }
    }

    public enum CheckpointRuleKind
    {
        /// <summary>He is past a place: x &gt; <see cref="CheckpointRule.X"/> and y &gt; <see cref="CheckpointRule.MinY"/> (a <c>CHK_</c> trigger).</summary>
        PlayerPast,
        /// <summary>A mechanism is engaged (a state trigger: the latch released, the door fully open).</summary>
        Engaged,
    }

    /// <summary>
    /// What sets a checkpoint (§5's checkpoint column). Evaluated by <see cref="SceneRunner"/> after the mechanisms each
    /// step, in list order; only a checkpoint later than the current one counts (<see cref="Save.CheckpointService.Reach"/>).
    /// </summary>
    public sealed class CheckpointRule
    {
        public string Checkpoint;
        public CheckpointRuleKind Kind;
        public double X, MinY = double.NegativeInfinity;
        public MechanismId Source;
        /// <summary>The prototype line that sets it.</summary>
        public string Cite;

        public static CheckpointRule Past(string checkpoint, double x, double minY, string cite)
            => new CheckpointRule { Checkpoint = checkpoint, Kind = CheckpointRuleKind.PlayerPast, X = x, MinY = minY, Cite = cite };

        public static CheckpointRule When(string checkpoint, MechanismId engaged, string cite)
            => new CheckpointRule { Checkpoint = checkpoint, Kind = CheckpointRuleKind.Engaged, Source = engaged, Cite = cite };
    }

    /// <summary>
    /// A one-shot cue (music, a voice) the audio layer plays: fired once when its condition holds, re-armed on every
    /// reload unless the checkpoint is past <see cref="HeardAfter"/>. All set conditions must hold.
    /// </summary>
    public sealed class CueRule
    {
        public string Cue;
        /// <summary>x &gt; AfterX (NaN = no place condition).</summary>
        public double AfterX = double.NaN;
        public MechanismId WhenEngaged;
        public MechanismId UnlessEngaged;
        /// <summary>Already heard when the world is rebuilt at or after this checkpoint (null = never).</summary>
        public string HeardAfter;
        public string Cite;
    }

    /// <summary>
    /// A directed moment started by a place or a state, once per game (<c>seen</c>, L945–L950). Moments started by an
    /// act (DL-04's realise, DL-10's UP) are started from <see cref="SceneDefinition.AfterMechanisms"/> with
    /// <see cref="SceneRunner.StartMoment"/>.
    /// </summary>
    public sealed class MomentRule
    {
        public DirectedMoment Moment;
        public double AfterX = double.NaN;
        public MechanismId WhenEngaged;
        public string Cite;
    }

    /// <summary>
    /// A scene's opening: a directed moment that holds him from a new game until control is handed over (DL-01: the
    /// 480-frame wake, L269, L8503–L8507; acceptance "control by 0:20"). The camera runs
    /// <see cref="CameraRig.StepOpening"/> from <see cref="Chest"/>; the cue plays from the first step.
    /// </summary>
    public sealed class SceneOpening
    {
        public DirectedMoment Moment;
        public string Cue;
        /// <summary>Opening length in 24 fps frames (the camera's clock).</summary>
        public double Frames;
        /// <summary>The label's centre on frame 0 of the Opening clip, prototype axes (<c>captureChest</c>, L7649–L7657).</summary>
        public Vec3 Chest;
    }

    /// <summary>The way on to the next scene (a walk-through seam, §7): standing grounded in [X0, X1] once the source is engaged.</summary>
    public sealed class SceneExit
    {
        public string NextScene;
        public double X0, X1;
        public MechanismId OpenWhen;
        public bool RequireGrounded = true;
        public string Cite;
    }

    /// <summary>Which Core value a view reads (see <see cref="MechanismReadout"/>).</summary>
    public enum ViewChannel
    {
        /// <summary><see cref="IPositionSource.Position"/> (a door's metres, a shutter's degrees, a crank's 0..1).</summary>
        Position,
        /// <summary><c>Latch.LeverDeg</c>.</summary>
        LeverDeg,
        /// <summary><c>CrankActuator.WheelDeg</c>.</summary>
        WheelDeg,
        /// <summary><c>PulseSequencer.Value(Index)</c>, 0..strength.</summary>
        Lamp,
        /// <summary><c>TippingBridge.X</c>, <c>ViewY</c>, <c>DipRad</c> in degrees.</summary>
        BridgeX, BridgeY, BridgeDipDeg,
        /// <summary><c>LoadPlate.Needle</c>, 0..1.</summary>
        Needle,
        /// <summary>DL-01's shutter counterweight y from <c>Door.Elapsed</c> (<see cref="Mechanisms.Actuators.Door.ShutterCounterweightY"/>).</summary>
        ShutterCounterweightY,
    }

    /// <summary>How a view applies its value to the node (Unity axes; a z-rotation has the same sign in three.js and Unity).</summary>
    public enum ViewMotion { TranslateX, TranslateY, RotateZ, Emission }

    /// <summary>
    /// One channel of a mechanism's view: on the art node <see cref="NodeName"/>, apply
    /// <c>(value + Offset) × Scale</c> of <see cref="Channel"/> read from <see cref="Source"/> as <see cref="Motion"/>.
    /// Several channels on one node compose in list order (rotations about their pivots first, then translations).
    /// The SceneBuilder adds one <c>MechanismView</c> per node; Runtime does the rest.
    /// </summary>
    public sealed class MechanismViewDef
    {
        /// <summary>Core class name, as in the art's <c>MECH_&lt;Type&gt;_…</c> (docs/unity/asset_conventions.md).</summary>
        public string Type;
        /// <summary>The node's mechanism ID (<c>dl01.shutter</c>).</summary>
        public MechanismId Node;
        /// <summary>The node's part (<c>ShutterRail</c>), null for the mechanism's root or anchor.</summary>
        public string Part;
        /// <summary>The mechanism read (defaults to <see cref="Node"/>: the latch's lever also swings with the shutter).</summary>
        public MechanismId Source;
        public ViewChannel Channel;
        public int Index;
        public ViewMotion Motion;
        public double Scale = 1, Offset;
        /// <summary>Rotation pivot, Unity world/lane axes; NaN = the node's own origin at rest.</summary>
        public Vec3 Pivot = new Vec3(double.NaN, double.NaN, double.NaN);
        public string Cite;

        public MechanismId ReadFrom => Source.IsNone ? Node : Source;

        /// <summary><c>MECH_&lt;Type&gt;_&lt;scene&gt;_&lt;name&gt;[__&lt;part&gt;]</c>, the U-12 convention (same as #24's <c>ArtNames.Mechanism</c>).</summary>
        public string NodeName => "MECH_" + Type + "_" + Node.Value.Replace('.', '_') + (string.IsNullOrEmpty(Part) ? "" : "__" + Part);

        public static MechanismViewDef On(string type, MechanismId node, string part, ViewChannel channel, ViewMotion motion, string cite)
            => new MechanismViewDef { Type = type, Node = node, Part = part, Channel = channel, Motion = motion, Cite = cite };

        public MechanismViewDef Scaled(double scale, double offset = 0) { Scale = scale; Offset = offset; return this; }
        public MechanismViewDef About(double x, double y, double z) { Pivot = new Vec3(x, y, z); return this; }
        public MechanismViewDef Reading(MechanismId source) { Source = source; return this; }
        public MechanismViewDef Lamp(int index) { Index = index; return this; }
    }

    /// <summary>
    /// A scene port (U-20/21/22): everything Core needs to run one prototype scene, as plain C# data with an
    /// <c>L</c> citation per value (port_architecture §5 row, §6). One sealed subclass per scene under
    /// <c>Core/Scenes/&lt;Chapter&gt;/</c>; <see cref="SceneRunner"/> builds and runs it; the Editor's SceneBuilder
    /// turns it into a <c>.unity</c> file. See docs/unity/scene_port_guide.md.
    /// <para>§6.2 wants positions to come from the Blender sidecar once U-12 emits it (<c>COL_</c>, <c>CHK_</c>,
    /// <c>CAM_</c>); until then they are transcribed here, and a validator can diff the two.</para>
    /// <para>Lists are built once (in the constructor) and returned as arrays: the runner reads them every step.</para>
    /// </summary>
    public abstract class SceneDefinition
    {
        private static readonly MomentRule[] NoMoments = new MomentRule[0];
        private static readonly CueRule[] NoCues = new CueRule[0];

        /// <summary>The scene's name in saves and the Unity scene (<c>DL-01</c>).</summary>
        public abstract string Id { get; }
        /// <summary>The art region: <c>Assets/Art/&lt;ArtRegion&gt;/&lt;ArtRegion&gt;.prefab</c> (asset_conventions.md).</summary>
        public abstract string ArtRegion { get; }
        /// <summary>The scene's lane x-range, for streaming (§7).</summary>
        public abstract double LaneX0 { get; }
        public abstract double LaneX1 { get; }
        /// <summary>The checkpoint a new game started in this scene begins at.</summary>
        public abstract string FirstCheckpoint { get; }
        /// <summary>The checkpoint order (<c>CP_ORDER</c>, L3976) the scene's names belong to.</summary>
        public virtual IReadOnlyList<string> CheckpointOrder => Checkpoint.PrototypeOrder;

        /// <summary>Adds the scene's mechanisms <b>in the prototype's update order</b> (§3.1 #5–#7; the graph steps in Add order).</summary>
        public abstract void AddMechanisms(MechanismGraph graph);
        /// <summary>Registers what D-17 can use, push or lift (the graph is built and reset).</summary>
        public abstract void RegisterInteractables(MechanismGraph graph, InteractionResolver resolver);
        /// <summary>The lane: static boxes plus contributors reading the (built) graph.</summary>
        public abstract LaneGeometry BuildLane(MechanismGraph graph);
        /// <summary>The camera's framing track. The prologue shares one track (Core state is global, §7).</summary>
        public virtual FramingTrack BuildFraming() => PrologueFraming.Build();

        public abstract IReadOnlyList<SpawnPoint> Spawns { get; }
        public abstract IReadOnlyList<CheckpointRule> CheckpointRules { get; }
        public virtual IReadOnlyList<CueRule> Cues => NoCues;
        public virtual IReadOnlyList<MomentRule> Moments => NoMoments;
        public virtual SceneOpening Opening => null;
        public abstract SceneExit Exit { get; }
        public abstract IReadOnlyList<MechanismViewDef> Views { get; }

        /// <summary>
        /// The scene's bespoke rules, once per step after the mechanisms (§3.1 #6–#9): shakes and respawns from mechanism
        /// events, ride sync, act-triggered moments. Must not allocate. Read <c>runner.Graph.Log</c> for this step's events.
        /// </summary>
        public virtual void AfterMechanisms(SceneRunner runner) { }

        /// <summary>The opening starts (a new game, after the reset): rewind scene clocks to the opening's (DL-01: the relay, L8061).</summary>
        public virtual void OnOpeningStart(SceneRunner runner) { }

        /// <summary>An authored shot for this step (label checks, moment shots; <c>currentShot</c>, L3698–L3809), or null.</summary>
        public virtual ShotRequest? Shot(SceneRunner runner) => null;

        /// <summary>The spawn for <paramref name="checkpoint"/>; throws when the scene has none (a checkpoint of another scene).</summary>
        public SpawnPoint SpawnFor(string checkpoint)
        {
            var spawns = Spawns;
            for (int i = 0; i < spawns.Count; i++) if (string.Equals(spawns[i].Checkpoint, checkpoint, StringComparison.Ordinal)) return spawns[i];
            throw new ArgumentException(Id + " has no spawn for checkpoint '" + checkpoint + "'.", nameof(checkpoint));
        }

        public bool HasSpawn(string checkpoint)
        {
            var spawns = Spawns;
            for (int i = 0; i < spawns.Count; i++) if (string.Equals(spawns[i].Checkpoint, checkpoint, StringComparison.Ordinal)) return true;
            return false;
        }
    }
}
