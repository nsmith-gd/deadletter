namespace DeadLetter.Core.Motor
{
    /// <summary>What D-17 is doing, for the Animator, the camera and the tests.</summary>
    public enum MotorState
    {
        Grounded,
        Crouched,
        Airborne,
        /// <summary>The authored 56-frame climb (L1906–L1947).</summary>
        Mantling,
        /// <summary>An act other than present/sit: lift, set down, place, grab, a fixed control, the shove.</summary>
        Acting,
        /// <summary>Holding a heavy item (light items show as Grounded/Airborne with <c>D17Motor.Hold == Item</c>).</summary>
        Carrying,
        Pushing,
        Sitting,
        Presenting,
    }

    /// <summary>Act phases (port_architecture §3.3): approach → turn → in → clip → out.</summary>
    public enum ActPhase { None, Approach, Turn, StepIn, Clip, SitUp, StepOut }

    public enum MotorEventKind
    {
        /// <summary>Name = new clip, Value = crossfade seconds.</summary>
        ClipChanged,
        /// <summary>Value = take-off velocity (JUMP_V).</summary>
        Jump,
        /// <summary>Value = drop height (peakY − support).</summary>
        Land,
        Bonk,
        /// <summary>Value = ledge height above his feet.</summary>
        MantleStart,
        MantleEnd,
        /// <summary>Value = loudness (stepSounds, L2069–L2075).</summary>
        Footstep,
        /// <summary>Value = camera shake amount (L2027).</summary>
        Shake,
        /// <summary>Value = noise to the White (L2028).</summary>
        Noise,
        /// <summary>Name = verb.</summary>
        ActStart,
        /// <summary>Name = clip event name from ClipTimings (e.g. "sound", "attach", "lamp0").</summary>
        ActEvent,
        ActEnd,
        PickedUp,
        SetDown,
        Placed,
        Grabbed,
        /// <summary>Value = 1 when it should tip in.</summary>
        Released,
        Seated,
        Stood,
    }

    /// <summary>Something that happened during one step. Runtime turns these into sound, shake and clip changes.</summary>
    public readonly struct MotorEvent
    {
        public readonly MotorEventKind Kind;
        public readonly string Name;
        public readonly double Value;

        public MotorEvent(MotorEventKind kind, string name, double value)
        {
            Kind = kind; Name = name; Value = value;
        }

        public override string ToString() => Kind + (Name != null ? ":" + Name : "") + "=" + Value.ToString("R");
    }

    /// <summary>Clip-frame comparisons with a tolerance, so accumulated step time never misses a threshold by 1e-15.</summary>
    public static class ClipClock
    {
        public const double Epsilon = 1e-6;

        /// <summary>The prototype's <c>f &gt;= n</c>.</summary>
        public static bool Reached(double frame, double threshold) => frame + Epsilon >= threshold;

        /// <summary>True on the one step where the clip passes <paramref name="threshold"/>.</summary>
        public static bool Crossed(double prevFrame, double frame, double threshold)
            => prevFrame + Epsilon < threshold && frame + Epsilon >= threshold;
    }
}
