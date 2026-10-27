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
        /// <summary>On something he boarded (a carrier): ride sync places him; Use or Jump hops off where it allows (L2966–L2974).</summary>
        Riding,
        /// <summary>The death act: the clip holds, then the cut (L7432–L7453).</summary>
        Dead,
    }

    /// <summary>How he dies (<c>DEATH</c>, L7421–L7424): the clip, how long it holds before the cut, and the shake.</summary>
    public enum DeathKind { Crush, Shock, Grabbed, Fall }

    /// <summary>Act phases (port_architecture §3.3): approach → turn → in → clip → out.</summary>
    public enum ActPhase { None, Approach, Turn, StepIn, Clip, SitUp, StepOut, Hop }

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
        /// <summary>The death act started. Name = the <see cref="DeathKind"/>, Value = seconds it holds before the cut.</summary>
        Death,
        /// <summary>
        /// The act wants the checkpoint reloaded in Value seconds: the stuck act at 2.0 s (<c>respawn()</c>'s 1.3 s fade,
        /// L4521, L2997–L2999), the death act at its cut (0.6 s, L7451). Name = "stuck" or "death". The scene simulator
        /// schedules the reload (<c>respawnAt = clock + Value</c>; <see cref="MotorEvents.RespawnDue"/>).
        /// </summary>
        RespawnDue,
        /// <summary>Board hop f23: he is on (Name = null, Value = token).</summary>
        Mounted,
        /// <summary>He is off what he rode (Name = "hop", "landing" or "gone").</summary>
        Alighted,
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

    /// <summary>Queries over a motor's <see cref="D17Motor.Events"/> for a scene simulator (Core/Motor/README.md).</summary>
    public static class MotorEvents
    {
        /// <summary>
        /// The stuck or death act asked for the checkpoint reload this step (<see cref="MotorEventKind.RespawnDue"/>):
        /// <paramref name="delay"/> = seconds from now (1.3 the stuck fade, 0.6 the death cut). The simulator sets its
        /// <c>respawnAt</c> to clock + delay unless one is pending, and withholds input until then.
        /// </summary>
        public static bool RespawnDue(this D17Motor m, out double delay)
        {
            var e = m.Events;
            for (int i = 0; i < e.Count; i++)
                if (e[i].Kind == MotorEventKind.RespawnDue) { delay = e[i].Value; return true; }
            delay = 0;
            return false;
        }

        /// <summary>
        /// The largest camera shake the motor asked for this step (a hard landing, a death); 0 = none. The rig keeps the
        /// largest pending shake (<c>CameraRig.Shake</c>), so the max is what one call per event would leave.
        /// </summary>
        public static double Shake(this D17Motor m)
        {
            var e = m.Events;
            double s = 0;
            for (int i = 0; i < e.Count; i++) if (e[i].Kind == MotorEventKind.Shake && e[i].Value > s) s = e[i].Value;
            return s;
        }

        /// <summary>True if an event of <paramref name="kind"/> (and <paramref name="name"/>, if given) is in this step's events.</summary>
        public static bool Has(this D17Motor m, MotorEventKind kind, string name = null)
        {
            var e = m.Events;
            for (int i = 0; i < e.Count; i++)
                if (e[i].Kind == kind && (name == null || e[i].Name == name)) return true;
            return false;
        }
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
