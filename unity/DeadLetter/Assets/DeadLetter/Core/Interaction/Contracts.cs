using DeadLetter.Core.Motor;

// =====================================================================================================================
// Interaction contracts between the D-17 motor (U-11) and the things he uses (U-10's mechanisms, items, pushables).
//
// Who does what:
//  * The motor owns D-17: approach to a stand point, turn into the set, step in along z, play the clip, fire the
//    clip-frame events from ClipTimings, chain a follow-up clip or hop, step out. It never moves anything else except
//    through these calls.
//  * The InteractionResolver decides what Use would do (port_architecture §4.9). Reach rules for items and pushables
//    are the prototype's and live in the resolver; a station answers the query itself (Offer): whether it answers from
//    his pose, where he stands, which way he faces. Nothing about a station is read without his pose (U-11 review).
//  * U-10 implements the interfaces below. Keep every call cheap and deterministic: they run inside the 60 Hz step.
//
// Implement:
//  ICarryable      a liftable item. OnLifted at Lift f22, OnSetDown at SetDown f14 (lane set-down never refuses),
//                  OnPlaced when a context set-down (IPlaceTarget) takes it.
//  IPlaceTarget    a context set-down while carrying (tray, carrier, deck, peg, lift car): OnPlaced at f14.
//  IPushable       a push/pull/drag object (twins = two IPushables sharing one state, opposite Side). The motor moves it
//                  with MoveTo each step while held; U-10 owns tipping, detent side-effects and end-of-travel states.
//  IPresentTarget  something he turns to, steps in front of and presents to (DL-11 terminal): beats at Present f20–f50.
//  ISeat           a chair/bench he sits on (DL-15): OnSeated(true) after 0.4 s, OnSeated(false) when he gets up.
//  IHideSpot       a recess he backs into and crouches in (DL-14b): PlayerPose.Hiding while the act runs.
//  IRide           something he boards with a hop and rides (DL-06 carriers): board, ride sync, alight.
//  IEscort         something that walks him back (DL-14b trolley): the motor's escorted act.
//  IUsable         any other fixed control (lever, crank, cord, button, valve): the motor runs approach/turn/step-in,
//                  asks ProfileFor again once he has stepped in, plays its clip; OnActFrame is called every step with
//                  the clip frame and answers Continue, Done, a follow-up clip (Then) or a hop (HopBy/HopTo).
// =====================================================================================================================
namespace DeadLetter.Core.Interaction
{
    /// <summary>
    /// Interaction categories in the prototype's priority order inside <c>nearCh1</c> (L4204–L4257): earlier wins.
    /// <c>auditNear</c> (L1786–L1802) requires that no two categories answer at the same spot.
    /// </summary>
    public enum InteractionCategory { Item = 0, Curio = 1, Secret = 2, Voice = 3, Fixed = 4, Letter = 5, Push = 6 }

    /// <summary>
    /// What an act is. The first nine are what Use starts; the rest are acts the motor starts itself or is told to
    /// play by a scene rule (board by a standing jump, alight, escorted, stuck, death, a quirk such as Flinch or
    /// CheckLabel). Append only: the value is read by Runtime and tests.
    /// </summary>
    public enum Verb { None, Lift, SetDown, Place, Grab, Release, Present, Sit, Use, Hide, Board, Alight, Escorted, Stuck, Death, Quirk }

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
        public readonly bool Busy;            // mantling, riding or in an act: nothing answers (L4205)
        public readonly HoldKind Hold;
        public readonly ICarryable Carried;
        public readonly IPushable Pushed;

        public InteractionQuery(double x, double y, double z, int facing, bool grounded, bool busy,
            HoldKind hold, ICarryable carried, IPushable pushed)
        {
            X = x; Y = y; Z = z; Facing = facing; Grounded = grounded; Busy = busy;
            Hold = hold; Carried = carried; Pushed = pushed;
        }

        /// <summary>Standing at (x, y), facing <paramref name="facing"/>, hands empty (tests, glint sweeps).</summary>
        public static InteractionQuery At(double x, double y = 0, int facing = 1)
            => new InteractionQuery(x, y, 0, facing, true, false, HoldKind.None, null, null);
    }

    /// <summary>Base of everything Use can act on.</summary>
    public interface IInteractable
    {
        InteractionCategory Category { get; }

        /// <summary>
        /// World-state conditions beyond reach (region, solved flags, phase) for items and pushables, whose reach the
        /// resolver applies. A station answers everything in <see cref="IStation.Offer"/>; its IsAvailable is Offer's verdict.
        /// </summary>
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

        /// <summary>SetDown f14 (or a hold dropped by an escort or a death): it rests at lane x on <paramref name="baseY"/>.</summary>
        void OnSetDown(double x, double baseY);

        /// <summary>SetDown f14 of a context set-down: <paramref name="target"/> has taken it (after its own OnPlaced).</summary>
        void OnPlaced(IPlaceTarget target);
    }

    /// <summary>
    /// Where he stands to use a station, as the station answers it for one query: the stand point, the depth he steps
    /// to, the facing during the act (it may depend on his side: the DL-01 crank faces him toward it, L1835) and the
    /// thing's own x for the in-front preference. Reach is not here: <see cref="IStation.Offer"/> refuses when out of
    /// reach, and the reach may be centred away from the stand point (DL-13 brake: stand 0.2 short of it, L5290).
    /// </summary>
    public readonly struct StationPose
    {
        public readonly double StandX;
        /// <summary>Depth he steps to (0 = stays on the lane). Unity z: + is into the set.</summary>
        public readonly double StandZ;
        /// <summary>Facing while using it: +1 / −1, or 0 to keep his current facing.</summary>
        public readonly int Face;
        /// <summary>Where the thing itself is, for the in-front preference.</summary>
        public readonly double AnchorX;

        public StationPose(double standX, int face, double standZ = 0, double anchorX = double.NaN)
        {
            StandX = standX; Face = face; StandZ = standZ;
            AnchorX = double.IsNaN(anchorX) ? standX : anchorX;
        }
    }

    /// <summary>Something with a stand point: the common shape of the fixed-control contracts.</summary>
    public interface IStation : IInteractable
    {
        /// <summary>
        /// Does it answer Use from <paramref name="q"/> (reach, floor, state), and where does he stand for it? Called by the
        /// resolver for every query (glints, hints, the overlap audit), so it must be cheap and must not change state that
        /// matters to the simulation; it may remember which of its parts answered, for the act that follows.
        /// </summary>
        bool Offer(in InteractionQuery q, out StationPose pose);
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
        /// <summary>Seconds since this clip started.</summary>
        public readonly double Time;
        public readonly MotorInput Input;
        /// <summary>The clip playing (the profile's, or a follow-up chained with <see cref="ActStep.Then"/>).</summary>
        public readonly string Clip;
        /// <summary>0 for the profile's clip, 1 for the first follow-up, and so on. Frames restart at 0 in each part.</summary>
        public readonly int Part;

        public ActFrame(double prevFrame, double frame, double time, MotorInput input, string clip = null, int part = 0)
        {
            PrevFrame = prevFrame; Frame = frame; Time = time; Input = input; Clip = clip; Part = part;
        }

        /// <summary>True on the one step where the clip passes <paramref name="frame"/> (the prototype's <c>f &gt;= n &amp;&amp; !a.flag</c>).</summary>
        public bool Crossed(double frame) => ClipClock.Crossed(PrevFrame, Frame, frame);
    }

    public enum ActStepKind
    {
        /// <summary>Keep playing this clip.</summary>
        Continue,
        /// <summary>The act is over: he steps back out to the lane (if he stepped in) and turns back.</summary>
        Done,
        /// <summary>Play a follow-up clip now, in the same act (latch Pull → Flinch, L1875); the station keeps getting frames.</summary>
        Then,
        /// <summary>Hop along an arc (Hop f8–f18, 0.38 high, done f23; <c>hopTo</c>, L2884–L2894), then the act is over (DL-18 strap).</summary>
        Hop,
    }

    /// <summary>A station's answer to one act frame.</summary>
    public readonly struct ActStep
    {
        public readonly ActStepKind Kind;
        /// <summary><see cref="ActStepKind.Then"/>: the follow-up clip and its crossfade.</summary>
        public readonly string Clip;
        public readonly double Fade;
        /// <summary><see cref="ActStepKind.Hop"/>: lane x offset (when <see cref="Relative"/>) or target x, and target y
        /// (NaN = the lane's support where he lands) and Unity z.</summary>
        public readonly double X, Y, Z;
        public readonly bool Relative;

        private ActStep(ActStepKind kind, string clip = null, double fade = 0, double x = 0, double y = double.NaN, double z = 0, bool relative = false)
        {
            Kind = kind; Clip = clip; Fade = fade; X = x; Y = y; Z = z; Relative = relative;
        }

        public static ActStep Continue => default;
        public static ActStep Done => new ActStep(ActStepKind.Done);
        /// <summary>Done when <paramref name="done"/>, else Continue.</summary>
        public static ActStep DoneIf(bool done) => done ? Done : Continue;
        /// <summary>Chain <paramref name="clip"/> (crossfade <paramref name="fade"/>), e.g. <c>Then("Flinch", 0.06)</c>.</summary>
        public static ActStep Then(string clip, double fade = 0.15) => new ActStep(ActStepKind.Then, clip, fade);
        /// <summary>Hop <paramref name="dx"/> along the lane, landing on the lane's support (DL-18: 0.4 back to the left).</summary>
        public static ActStep HopBy(double dx) => new ActStep(ActStepKind.Hop, ClipNames.Hop, 0.1, dx, double.NaN, 0, true);
        /// <summary>Hop to (x, y, z); y NaN = the lane's support at x.</summary>
        public static ActStep HopTo(double x, double y = double.NaN, double z = 0) => new ActStep(ActStepKind.Hop, ClipNames.Hop, 0.1, x, y, z);

        public bool IsDone => Kind == ActStepKind.Done;
    }

    /// <summary>A context set-down while carrying (tray, carrier, deck, lift car, peg). Category should be Item.</summary>
    public interface IPlaceTarget : IStation
    {
        bool Accepts(ICarryable item);
        /// <summary>SetDown or SetDownHigh (both: release f14, done f35).</summary>
        string Clip { get; }
        bool TurnIntoSet { get; }
        /// <summary>SetDown f14: the item is now the target's (the motor then calls the item's OnPlaced).</summary>
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
        /// <summary>
        /// How fast he gets it going, m/s² (<c>acc</c>): chapter 1 pushables 1.4 (L4690); the old holds 3 for the DL-03
        /// trolley, 1.3 for the DL-08 goods trolley and the DL-11 desk (L2332).
        /// </summary>
        double Accel { get; }
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
        /// <summary>
        /// At Max he lets go and it takes its end-of-travel state (chapter 1's pushables, L4723–L4735). False for the old
        /// holds (the DL-03 and DL-08 trolleys, the DL-11 desk): they stop there and stay in his hands (L2338–L2346).
        /// </summary>
        bool LetGoAtMax { get; }

        /// <summary>Every held step: its new x and velocity (m/s).</summary>
        void MoveTo(double x, double velocity);
        /// <summary>Teetering at the lip (true) or not (false); called each held step when TipsIntoPit.</summary>
        void SetAtLip(bool atLip);
        /// <summary>He let go (Jump, Use, an escort or a death). <paramref name="atLip"/>: it should tip in (L4688, L4312).</summary>
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

    /// <summary>A seat (DL-15, L5655–L5684). He steps to the pose's StandZ while approaching and faces its Face.</summary>
    public interface ISeat : IStation
    {
        void OnSeated(bool seated);
    }

    /// <summary>
    /// A recess he backs into, crouched, out of a beam's sight (DL-14b niche A and the emptied bay; <c>'att:hide'</c>,
    /// L5980, L6011, L6111–L6125). He walks to the pose's StandX keeping his facing, turns to the camera, backs in to
    /// <see cref="HideZ"/> at 0.6 m/s and crouches; any input after 0.3 s brings him out at 0.7 m/s. Category Fixed.
    /// </summary>
    public interface IHideSpot : IStation
    {
        /// <summary>Unity z he backs in to (+ into the set; <c>ATT3.hideZ</c> −0.62 negated, L5898).</summary>
        double HideZ { get; }
    }

    /// <summary>Where a ridden thing is taking him (see <see cref="IRide"/>).</summary>
    public enum RideStatus
    {
        /// <summary>Gone from under him (it sank, or tipped him out: the scene's rule takes him from there).</summary>
        Gone,
        /// <summary>Moving with him on it; he cannot get off here.</summary>
        Riding,
        /// <summary>On the floor line, docked or moving: Use or Jump hops him off where he is (L2971–L2974).</summary>
        CanHopOff,
        /// <summary>Stopped at its landing: he turns and alights onto it (L2970, L2953–L2957).</summary>
        Unloading,
    }

    /// <summary>
    /// Something he boards with a hop and rides (DL-06's carriers, L2854–L2994). The resolver offers a board (Fixed, after
    /// the levers: <c>nearUse3</c>, L2864–L2870), as does a standing jump beside it (L1964–L1966). The motor hops him on
    /// (Hop f8–f18 along an arc to the moving <see cref="RidePose"/>, on at f23), rides it (ride sync: the pipeline's step
    /// #9 calls <c>D17Motor.SyncRide</c> after the mechanisms, L2959–L2964) and alights. A token names the part he rides
    /// (a carrier's sequence number); the implementation records the callbacks and applies them in its Step.
    /// </summary>
    public interface IRide : IInteractable
    {
        /// <summary><c>boardable()</c>: the part he would hop onto from <paramref name="q"/>, and how far it is.</summary>
        bool OfferBoard(in InteractionQuery q, out int token, out double distance);
        /// <summary>Where he stands on it now: lane x, floor y, Unity z (<c>syncRide</c>, L2961–L2964). False when gone.</summary>
        bool RidePose(int token, out double x, out double y, out double z);
        RideStatus Status(int token);
        /// <summary>The height he alights to when it unloads him (the gallery, <c>GALLERY.h</c>, L2953).</summary>
        double AlightY(int token);
        /// <summary>The hop toward it started (its dock wait holds, L2702).</summary>
        void OnBoarding(int token);
        /// <summary>Hop f23: he is on (L2949–L2950).</summary>
        void OnMounted(int token);
        /// <summary>He is off (L2955, L2973).</summary>
        void OnAlighted();
    }

    /// <summary>The escorted walk (<c>a.what === 'escorted'</c>, L6126–L6134), as the escort asks for it.</summary>
    public readonly struct EscortWalk
    {
        /// <summary>He stands this long first (0.7 s), then walks at <see cref="Speed"/> toward <see cref="ToX"/>.</summary>
        public readonly double HoldSeconds, Speed, ToX;
        /// <summary>The act ends once x ≤ ArriveX (walking toward −x) or ≥ ArriveX (toward +x).</summary>
        public readonly double ArriveX;
        /// <summary>His facing on the walk, and after it.</summary>
        public readonly int Facing, EndFacing;

        public EscortWalk(double holdSeconds, double speed, double toX, double arriveX, int facing, int endFacing)
        {
            HoldSeconds = holdSeconds; Speed = speed; ToX = toX; ArriveX = arriveX; Facing = facing; EndFacing = endFacing;
        }
    }

    /// <summary>
    /// Something that takes hold of him and walks him somewhere (DL-14b's escort trolley; the attendant later). While
    /// <see cref="WantsEscort"/> and he is not already escorted, the pipeline starts the motor's escorted act after the
    /// mechanisms step (the prototype's trolley sets <c>game.act</c> in its update, L6399); the motor drops what he
    /// holds and walks him. The escort reads <c>PlayerPose.Escorted</c> and his x to follow.
    /// </summary>
    public interface IEscort
    {
        bool WantsEscort { get; }
        EscortWalk Walk { get; }
    }

    /// <summary>Any other fixed control: levers, cranks, cords, buttons, valves (§4.12).</summary>
    public interface IUsable : IStation
    {
        /// <summary>
        /// How to play the act. Asked when Use starts (turn into the set, crouch) and again when he has stepped in, just
        /// before the clip starts: the clip is the second answer's (DL-08's pawl picks LeverPull or LeverStuck from the
        /// platform at the end of step-in, L3305; DL-06's points from the belt, L2910).
        /// </summary>
        ActProfile ProfileFor(in InteractionQuery q);

        /// <summary>Called every step while a clip plays (with <see cref="ActFrame.Part"/>). Only record the frame; Step applies it.</summary>
        ActStep OnActFrame(in ActFrame frame);
    }
}
