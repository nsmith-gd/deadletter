using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Scenes
{
    /// <summary>
    /// The handover from one chapter's sim to the next one's (#51, the agreed interface): D-17 walks on from where he left
    /// the first, in the second's world, with the game (flags, seen moments, play time, options) carried and the slot saved
    /// at the second's entry checkpoint. Each chapter stays its own <see cref="ChapterSim"/>: the first's mechanisms are not
    /// carried, only him.
    /// </summary>
    public static class ChapterHandover
    {
        /// <summary>
        /// Hands D-17 from <paramref name="from"/> (at its seam: <see cref="ChapterSeams.Due"/>) to <paramref name="to"/>, a sim
        /// of the seam's next chapter over the same save store. <paramref name="to"/> is built at the seam's entry checkpoint
        /// (<see cref="ChapterSim.Arrive"/>) with <paramref name="from"/>'s game, and D-17 is put there as he was:
        /// <list type="bullet">
        /// <item>his pose (shifted by the seam's offsets into <paramref name="to"/>'s lane coordinates), velocity, facing, yaw,
        /// crouch, ground, jump timers and clip, so he keeps walking (an act owning his pose hands over its pose, at rest);</item>
        /// <item>his hold: what he carries comes with him only when <paramref name="to"/> has a carryable mechanism of the same
        /// ID (its state is copied from his); otherwise he arrives empty-handed. He carries nothing over either seam today.</item>
        /// </list>
        /// The game clock runs on (<see cref="ChapterSim.Clock"/>). Then the entry is saved (<see cref="CheckpointService.Recapture"/>),
        /// with <paramref name="from"/>'s held write flushed first, so a Continue from here starts the new chapter. Returns the seam.
        /// </summary>
        public static ChapterSeam Carry(ChapterSim from, ChapterSim to)
        {
            if (from == null) throw new ArgumentNullException(nameof(from));
            if (to == null) throw new ArgumentNullException(nameof(to));
            var seam = ChapterSeams.Next(from.Def.Id, from.Checkpoints.Current.Name)
                ?? throw new InvalidOperationException(from.Def.Id + " has no seam at '" + from.Checkpoints.Current.Name + "'.");
            if (seam.To != to.Def.Id) throw new ArgumentException("The seam " + seam + " goes to " + seam.To + ", not " + to.Def.Id + ".", nameof(to));

            var pose = PoseOf(from);
            pose.X += seam.OffsetX;
            pose.Y += seam.OffsetY;
            if (!double.IsNaN(pose.PeakY)) pose.PeakY += seam.OffsetY;
            var game = from.Checkpoints.ToModel();
            from.Checkpoints.Flush();

            to.Clock = from.Clock;
            to.Arrive(game, seam.Entry, pose);
            CarryHold(from, to);
            to.Checkpoints.Recapture();
            return seam;
        }

        /// <summary>His free-movement state in <paramref name="sim"/> (the motor's, or a pose-owning act's at rest).</summary>
        private static MotorSnapshot PoseOf(ChapterSim sim)
        {
            var m = sim.Motor;
            if (sim.Act != null && sim.Act.OwnsPose)
            {
                var rest = MotorSnapshot.AtRest(sim.X, sim.Y, m.Facing);
                rest.Z = sim.Z; rest.Yaw = sim.Yaw; rest.Grounded = sim.Grounded;
                return rest;
            }
            if (m.CanCapture) return m.Capture();
            // A hold, an act, a mantle or a ride is not in a snapshot: take what is (the hold follows in CarryHold).
            return new MotorSnapshot
            {
                X = m.X, Y = m.Y, Z = m.Z, Vx = m.Vx, Vy = m.Vy, Facing = m.Facing, Yaw = m.Yaw, Grounded = m.Grounded, Crouched = m.Crouched,
                Coyote = m.Coyote, JumpBuffer = m.JumpBuffer, LandTimer = m.LandTimer, PeakY = m.PeakY,
                Clip = m.Clip, ClipTime = m.ClipTime, ClipTimeScale = m.ClipTimeScale,
            };
        }

        private static void CarryHold(ChapterSim from, ChapterSim to)
        {
            if (from.Motor.Hold != HoldKind.Item || !(from.Motor.Carried is IMechanism held)) return;
            if (!to.Graph.TryGet(held.Id, out IMechanism same) || !(same is ICarryable item)) return;
            var state = new MemorySnapshot();
            held.Snapshot(state);
            same.Restore(state);
            to.Motor.TakeItem(item);
        }
    }
}
