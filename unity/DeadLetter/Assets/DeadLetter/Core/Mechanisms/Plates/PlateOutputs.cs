using DeadLetter.Core.Mechanisms.Actuators;

namespace DeadLetter.Core.Mechanisms.Plates
{
    /// <summary>
    /// The one-way outputs of plates, as <see cref="Door"/>s (timed mode): no new type is needed for them. The
    /// two-way bay door is a <see cref="PlateDoor"/>; the follower gates are <see cref="FollowerActuator"/>s.
    /// </summary>
    public static class PlateOutputs
    {
        /// <summary>DL-05: the hatch winds up to <c>RH5.onDrum</c> 0.64 at 0.22 m/s once served; Open = clunk and 0.15 shake (L3453, L4916–L4917).</summary>
        public static DoorParams Dl05Hatch() => new DoorParams { Trigger = "dl05.weighIn", Duration = 0.64 / 0.22, Travel = 0.64 };

        /// <summary>DL-05: the SERVED flag drops over 0.5 s (the view eases it 1 − (1 − f)³ over −90°, L4918–L4919).</summary>
        public static DoorParams Dl05ServedFlag() => new DoorParams { Trigger = "dl05.weighIn", Duration = 0.5 };

        /// <summary>
        /// DL-10: the car gate draws shut 0.8 s after the suitcase is loaded, over 1.4 s; Opening = creak, Open = slam and
        /// 0.12 shake; each leaf slides <c>UO.gate</c> 0.56 (L3461, L4623–L4627). ID proposed: <c>dl10.carGate</c> (§5 lists none).
        /// </summary>
        public static DoorParams Dl10CarGate() => new DoorParams { Trigger = "dl10.carPlate", Delay = 0.8, Duration = 1.4 };
    }
}
