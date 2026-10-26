using UnityEngine;

namespace DeadLetter.Runtime
{
    /// <summary>
    /// The D-17 Animator contract. States are named exactly as the clips (Core <c>ClipNames</c> / <c>ClipTimings.All</c>)
    /// and are entered by <see cref="Animator.CrossFadeInFixedTime(int,float,int)"/> when Core changes clip; every state's
    /// Speed Multiplier must be bound to <see cref="ClipSpeed"/> (negative plays PushWalk backwards for pulling).
    /// The other parameters are optional conveniences for blend trees and layers; missing ones are skipped.
    /// </summary>
    public static class D17AnimatorParams
    {
        /// <summary>float: Core's clip time scale (speed / authored clip speed, L2057–L2061).</summary>
        public const string ClipSpeed = "ClipSpeed";
        /// <summary>float: |vx| in m/s.</summary>
        public const string Speed = "Speed";
        /// <summary>float: vy in m/s.</summary>
        public const string VerticalSpeed = "VerticalSpeed";
        /// <summary>bool.</summary>
        public const string Grounded = "Grounded";
        /// <summary>bool.</summary>
        public const string Crouched = "Crouched";
        /// <summary>bool: holding an item (light or heavy).</summary>
        public const string Carrying = "Carrying";
        /// <summary>bool.</summary>
        public const string Pushing = "Pushing";
        /// <summary>int: (int)Core MotorState.</summary>
        public const string State = "State";
        /// <summary>float 0–1: item blend from rest to the hands (Lift f22–f26).</summary>
        public const string CarryBlend = "CarryBlend";

        public static readonly int ClipSpeedId = Animator.StringToHash(ClipSpeed);
        public static readonly int SpeedId = Animator.StringToHash(Speed);
        public static readonly int VerticalSpeedId = Animator.StringToHash(VerticalSpeed);
        public static readonly int GroundedId = Animator.StringToHash(Grounded);
        public static readonly int CrouchedId = Animator.StringToHash(Crouched);
        public static readonly int CarryingId = Animator.StringToHash(Carrying);
        public static readonly int PushingId = Animator.StringToHash(Pushing);
        public static readonly int StateId = Animator.StringToHash(State);
        public static readonly int CarryBlendId = Animator.StringToHash(CarryBlend);
    }
}
