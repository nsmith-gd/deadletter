using DeadLetter.Core.Motor;

// =====================================================================================================================
// Interaction contracts between the D-17 motor (U-11) and the things he uses (U-10's mechanisms, items, pushables).
//
// Who does what:
//  * The motor owns D-17: approach to a stand point, turn into the set, step in along z, play the clip, fire the
//    clip-frame events from ClipTimings, step out. It never moves anything else except through these calls.
//  * The InteractionResolver decides what Use would do (port_architecture §4.9). Reach rules for items and pushables
//    are the prototype's and live in the resolver; anything else is an IStation that states its own stand point/reach.
//  * U-10 implements the interfaces below. Keep every call cheap and deterministic: they run inside the 60 Hz step.
//
// Implement:
//  ICarryable      a liftable item. OnLifted at Lift f22, OnSetDown at SetDown f14 (lane set-down never refuses).
//  IPlaceTarget    a context set-down while carrying (tray, carrier, peg, lift car): OnPlaced at f14.
//  IPushable       a push/pull/drag object (twins = two IPushables sharing one state, opposite Side). The motor moves it
//                  with MoveTo each step while held; U-10 owns tipping, detent side-effects and end-of-travel states.
//  IPresentTarget  something he turns to, steps in front of and presents to (DL-11 terminal): beats at Present f20–f50.
//  ISeat           a chair/bench he sits on (DL-15): OnSeated(true) after 0.4 s, OnSeated(false) when he gets up.
//  IUsable         any other fixed control (lever, crank, cord, button, valve): the motor runs approach/turn/step-in and
//                  plays Profile.Clip; OnActFrame is called every step with the clip frame until it returns true.
// =====================================================================================================================
namespace DeadLetter.Core.Interaction
{
    /// <summary>
    /// Interaction categories in the prototype's priority order inside <c>nearCh1</c> (L4204–L4257): earlier wins.
    /// <c>auditNear</c> (L1786–L1802) requires that no two categories answer at the same spot.
    /// </summary>
    public enum InteractionCategory { Item = 0, Curio = 1, Secret = 2, Voice = 3, Fixed = 4, Letter = 5, Push = 6 }

    /// <summary>What Use starts.</summary>
    public enum Verb { None, Lift, SetDown, Place, Grab, Release, Present, Sit, Use }

    /// <summary>What his hands are doing.</summary>
    public enum HoldKind { None, Item, Push }

    /// <summary>Present beats, in clip order (L3622–L3624).</summary>
    public enum PresentBeat { Lamp0, Lamp1, Lamp2, Nobody, Forward }

    /// <summary>The pose the resolver reasons about.</summary>
    public readonly struct InteractionQuery
    {
        public readonly double X, Y, Z;
        public readonly int Facing;
        public readonly bool Grounded;
        public readonly bool Busy;            // mantling or in an act: nothing answers (L4205)
        public readonly HoldKind Hold;
        public readonly ICarryable Carried;
        public readonly IPushable Pushed;

        public InteractionQuery(double x, double y, double z, int facing, bool grounded, bool busy,
            HoldKind hold, ICarryable carried, IPushable pushed)
        {
            X = x; Y = y; Z = z; Facing = facing; Grounded = grounded; Busy = busy;
            Hold = hold; Carried = carried; Pushed = pushed;
        }
    }

    /// <summary>Base of everything Use can act on.</summary>
    public interface IInteractable
    {
        InteractionCategory Category { get; }

        /// <summary>World-state conditions beyond reach (region, solved flags, phase). Reach is checked elsewhere.</summary>
        bool IsAvailable(in InteractionQuery q);
    }

    /// <summary>A liftable item (§4.10). Light items (coat, pole, tin) carry at a normal walk and allow jumps.</summary>
    public interface ICarryable : IInteractable
    {
        /// <summary>Lane x of the item's centre.</summary>
        double X { get; }
        /// <summary>Height it rests on; he must stand within 0.05 of it to lift (L4219).</summary>
        double BaseY { get; }
        /// <summary>Half-width, for the set-down flatness test (L4342).</summary>
        double Radius { get; }
        /// <summary>How far below the wrists it hangs when carried (L4261–L4268); Runtime attaches it there.</summary>
        double BelowWrist { get; }
        bool IsLight { get; }

        /// <summary>Lift f22: it leaves its rest and follows his hands (blend over 4 frames, see D17Motor.CarryBlend).</summary>
        void OnLifted();

        /// <summary>SetDown f14: it rests at lane x on <paramref name="baseY"/> (drops over 0.2 s in the view).</summary>
        void OnSetDown(double x, double baseY);
    }

    /// <summary>Something with a fixed stand point: the common shape of the fixed-control contracts.</summary>
    public interface IStation : IInteractable
    {
        /// <summary>Where he stands to use it.</summary>
        double StandX { get; }
        /// <summary>Use answers when |x − StandX| &lt; Reach (e.g. lever 0.38, crank 0.36, cord 0.22; §4.9).</summary>
        double Reach { get; }
        /// <summary>Depth he steps to (0 = stays on the lane). Unity z: + is into the set.</summary>
        double StandZ { get; }
        /// <summary>Facing while using it: +1 / −1, or 0 to keep his current facing.</summary>
        int Face { get; }
        /// <summary>Where the thing itself is, for the in-front preference. Usually StandX.</summary>
        double AnchorX { get; }
    }

    /// <summary>How the motor plays a fixed-control act.</summary>
    public readonly struct ActProfile
    {
        public readonly string Clip;
        /// <summary>Turn to face into the set (yaw π) before the clip, and back after.</summary>
        public readonly bool TurnIntoSet;
        /// <summary>Approach and act crouched (DL-01 latch).</summary>
        public readonly bool Crouch;

        public ActProfile(string clip, bool turnIntoSet = false, bool crouch = false)
        {
            Clip = clip; TurnIntoSet = turnIntoSet; Crouch = crouch;
        }
    }

    /// <summary>One step of a fixed-control act.</summary>
    public readonly struct ActFrame
    {
        /// <summary>Clip frame at the previous step and now (24 fps, unwrapped for loops: stroke = floor(f / 24)).</summary>
        public readonly double PrevFrame, Frame;
        /// <summary>Seconds since the clip started.</summary>
        public readonly double Time;
        public readonly MotorInput Input;

        public ActFrame(double prevFrame, double frame, double time, MotorInput input)
        {
            PrevFrame = prevFrame; Frame = frame; Time = time; Input = input;
        }

        /// <summary>True on the one step where the clip passes <paramref name="frame"/> (the prototype's <c>f &gt;= n &amp;&amp; !a.flag</c>).</summary>
        public bool Crossed(double frame) => ClipClock.Crossed(PrevFrame, Frame, frame);
    }

    /// <summary>A context set-down while carrying (tray, carrier, lift car, peg). Category should be Item.</summary>
    public interface IPlaceTarget : IStation
    {
        bool Accepts(ICarryable item);
        /// <summary>SetDown or SetDownHigh (both: release f14, done f35).</summary>
        string Clip { get; }
        bool TurnIntoSet { get; }
        /// <summary>SetDown f14: the item is now the target's.</summary>
        void OnPlaced(ICarryable item);
    }

    /// <summary>
    /// A push/pull/drag object (§4.11). He stands at <c>X − Side·Gap</c> facing <c>Side</c>; his hands carry it within
    /// [Min, Max]. Jump or Use lets go.
    /// </summary>
    public interface IPushable : IInteractable
    {
        double X { get; }
        int Side { get; }
        double Gap { get; }
        double Speed { get; }
        double Min { get; }
        /// <summary>Current end of travel (the prototype's <c>max()</c> can depend on state, L4278–L4281).</summary>
        double Max { get; }
        double FloorY { get; }
        /// <summary>Depth he steps to while approaching (the courier, L4461).</summary>
        double Z { get; }
        /// <summary>Grip reach with him in front of the stand point (default 0.34, L4254).</summary>
        double ForwardReach { get; }
        /// <summary>Grip reach with him behind the stand point (cart 0.2, L4274).</summary>
        double BackReach { get; }
        /// <summary>The cart and the duct: they teeter at Max (the pit lip) and can be tipped in (L4686).</summary>
        bool TipsIntoPit { get; }
        /// <summary>Stops at the next detent (Min or Max) and he lets go (L4717–L4722).</summary>
        bool HasDetents { get; }

        /// <summary>Every held step: its new x and velocity (m/s).</summary>
        void MoveTo(double x, double velocity);
        /// <summary>Teetering at the lip (true) or not (false); called each held step when TipsIntoPit.</summary>
        void SetAtLip(bool atLip);
        /// <summary>He let go (Jump or Use). <paramref name="atLip"/>: it should tip in (L4688, L4312).</summary>
        void OnReleased(bool atLip);
        /// <summary>Held into the lip for 0.45 s: a last shove, it tips in (L4708–L4715).</summary>
        void OnShoved();
        /// <summary>Reached Max (not tipping, not detents): the end-of-travel state (cradle, set, plate; L4723–L4735).</summary>
        void OnTravelEnd();
    }

    /// <summary>Something he turns to, steps in front of, and presents to (DL-11 terminal, L3603–L3625).</summary>
    public interface IPresentTarget : IStation
    {
        void OnPresentBeat(PresentBeat beat);
    }

    /// <summary>A seat (DL-15, L5655–L5684). He steps to StandZ while approaching and faces Face.</summary>
    public interface ISeat : IStation
    {
        void OnSeated(bool seated);
    }

    /// <summary>Any other fixed control: levers, cranks, cords, buttons, valves (§4.12).</summary>
    public interface IUsable : IStation
    {
        ActProfile Profile { get; }

        /// <summary>Called every step while the clip plays. Return true when the act is over (he then steps out/turns back).</summary>
        bool OnActFrame(in ActFrame frame);
    }
}
