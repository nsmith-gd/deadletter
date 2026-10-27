using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Camera
{
    /// <summary>
    /// What the lane camera reads from D-17's motor (step #10, <c>updateCamera</c> L7787–L7804, <c>currentShot</c>
    /// L3735–L3741), so any scene simulator builds the same <see cref="CameraRigInput"/>. Scene-specific pushes (a transit,
    /// the <c>realise</c> act) and shots stay the simulator's: it overrides the fields it owns.
    /// </summary>
    public static class D17Framing
    {
        private const double Fps = 24;

        /// <summary>
        /// The push the motor implies (L7788–L7791): mantling pushes in fully; acts push in once past their approach,
        /// except grab, quirks and the latch's pull and flinch (the exclusions of L7788). <see cref="CameraPush.None"/> otherwise.
        /// </summary>
        public static CameraPush Push(D17Motor m)
        {
            if (m.IsMantling) return CameraPush.Mantle;
            if (m.IsActing && m.ActPhase != ActPhase.Approach && m.ActVerb != Verb.Grab && m.ActVerb != Verb.Quirk
                && !(m.ActVerb == Verb.Use && (m.Clip == ClipNames.Pull || m.Clip == ClipNames.Flinch))) return CameraPush.Act;
            return CameraPush.None;
        }

        /// <summary>
        /// The rig input from the motor: x, y, vx, facing, no look-ahead while he holds something (or
        /// <paramref name="noLead"/>: exiting, a transit), and <see cref="Push"/>. The caller sets Signals, Shot, SlowFollow.
        /// </summary>
        public static CameraRigInput Input(D17Motor m, double aspect = 0, bool noLead = false)
            => new CameraRigInput
            {
                X = m.X, Y = m.Y, Vx = m.Vx, Facing = m.Facing,
                NoLead = m.Hold != HoldKind.None || noLead,
                Push = Push(m),
                Aspect = aspect,
            };

        /// <summary>The parcel label on his chest, estimated from the motor: 0.06 ahead of his centre at 0.42 (prototype z = −Unity z).</summary>
        public static Vec3 EstimatedLabel(D17Motor m) => new Vec3(m.X + m.Facing * 0.06, m.Y + 0.42, -m.Z);

        /// <summary>
        /// The label shot while he checks his label (<c>currentShot</c>, L3735–L3741): from f2 of CheckLabel, 0.27 in front
        /// of the label, 0.15 up and 0.05 toward the camera, 50 mm, ease 1.1 for a held check (the wake's, a quirk with its
        /// own hold) or 3.0. Null otherwise. <paramref name="label"/> is the label's centre in prototype axes (Runtime reads
        /// the label's transform); null = <see cref="EstimatedLabel"/>.
        /// </summary>
        public static ShotRequest? LabelShot(D17Motor m, Vec3? label = null)
        {
            if (m.ActVerb != Verb.Quirk || m.Clip != ClipNames.CheckLabel || !(m.ClipTime * Fps > 2)) return null;
            Vec3 l = label ?? EstimatedLabel(m);
            double fx = Math.Sin(m.Yaw), fz = Math.Cos(m.Yaw);
            var pos = new Vec3(l.X + fx * 0.27, l.Y + 0.15, l.Z + fz * 0.27 + 0.05);
            return new ShotRequest("label", pos, l, 50, double.IsNaN(m.QuirkHoldFor) ? 3.0 : 1.1);
        }
    }
}
