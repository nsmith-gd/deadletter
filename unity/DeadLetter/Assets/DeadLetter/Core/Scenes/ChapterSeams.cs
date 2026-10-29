using System;
using System.Collections.Generic;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Scenes.Dl17;

namespace DeadLetter.Core.Scenes
{
    /// <summary>
    /// Where one chapter hands D-17 to the next (#51, the interface agreed there): the running chapter's exit checkpoint and
    /// the lane x where its way out ends, the next chapter and the checkpoint it starts at, and the shift between their lane
    /// coordinates. Each chapter keeps its own datum (chapter 2's heights are above ring A, chapter 1's above the school
    /// floor), so a pose at the exit, plus <see cref="OffsetX"/> and <see cref="OffsetY"/>, is the same place in the next one.
    /// </summary>
    public sealed class ChapterSeam
    {
        public ChapterSeam(string from, string exit, double exitX, string to, string entry, double offsetX = 0, double offsetY = 0)
        {
            From = from ?? throw new ArgumentNullException(nameof(from));
            Exit = exit ?? throw new ArgumentNullException(nameof(exit));
            To = to ?? throw new ArgumentNullException(nameof(to));
            Entry = entry ?? throw new ArgumentNullException(nameof(entry));
            ExitX = exitX; OffsetX = offsetX; OffsetY = offsetY;
        }

        /// <summary>The chapter he leaves ("attendance").</summary>
        public string From { get; }
        /// <summary>The checkpoint that is current when he leaves it (its last: the save names it until the handover).</summary>
        public string Exit { get; }
        /// <summary>Lane x (the leaving chapter's) where its way out ends: past it, with no act running, the next chapter takes him.</summary>
        public double ExitX { get; }
        /// <summary>The chapter he enters ("someone_home").</summary>
        public string To { get; }
        /// <summary>The checkpoint its sim is begun at, and the save's once he is there.</summary>
        public string Entry { get; }
        /// <summary>The next chapter's x and y of a place = the leaving chapter's + these.</summary>
        public double OffsetX { get; }
        public double OffsetY { get; }

        public override string ToString() => From + "/" + Exit + " → " + To + "/" + Entry;
    }

    /// <summary>
    /// The seam table (#51): which chapter follows which, and where. <see cref="Next"/> is the agreed lookup; the rest is what
    /// a host needs around it (<see cref="Due"/> for when, <see cref="Span"/> for what to stream, <see cref="Origin"/> for where a
    /// chapter's datum is in the game's world).
    /// <list type="bullet">
    /// <item><b>attendance → someone_home</b> (DL-17 → DL-18). Chapter 1 ends at DL-17's stair door (<c>workshop</c> is current:
    /// DL-17's rules reach it again there, L5792) and walks up the stair (<see cref="Dl17StairAct"/>) to the stair head, x 347.17,
    /// where DL-18's lane begins (<see cref="Dl18Lane.StairHeadX"/> + HALF). Game x runs on unchanged; ring A's datum is the
    /// stair's top, 3.24 above the school floor (<see cref="Dl17Lane.StairTop"/>). Chapter 2 starts at <c>ring_a</c>, its first
    /// checkpoint. The exit is a lane x, not a checkpoint: <c>workshop</c> is reached at 324.6 (L5803), long before the end.</item>
    /// <item><b>prologue → attendance</b> (DL-11 → <c>school</c>) is not here yet: DL-07 to DL-11 are not in Core (#17), so the
    /// prologue has no exit to hand over from. Its row goes in when DL-11's end is ported.</item>
    /// </list>
    /// </summary>
    public static class ChapterSeams
    {
        private static readonly ChapterSeam[] Rows =
        {
            new ChapterSeam(ChapterDefs.AttendanceId, "workshop", Dl17StairAct.EndX, ChapterDefs.SomeoneHomeId, "ring_a",
                offsetY: -Dl17Lane.StairTop),
        };

        /// <summary>Every seam, in play order.</summary>
        public static IReadOnlyList<ChapterSeam> All => Rows;

        /// <summary>The seam out of <paramref name="chapterId"/> when <paramref name="checkpoint"/> is current, or null.</summary>
        public static ChapterSeam Next(string chapterId, string checkpoint)
        {
            for (int i = 0; i < Rows.Length; i++)
                if (Rows[i].From == chapterId && Rows[i].Exit == checkpoint) return Rows[i];
            return null;
        }

        /// <summary>The seam into <paramref name="chapterId"/>, or null (the first chapter, or one whose way in is not ported).</summary>
        public static ChapterSeam Into(string chapterId)
        {
            for (int i = 0; i < Rows.Length; i++) if (Rows[i].To == chapterId) return Rows[i];
            return null;
        }

        /// <summary>
        /// The seam <paramref name="sim"/> is at now, or null: he has left its last scene (<see cref="ChapterSim.Exited"/>), no
        /// act carries him any more (the way out has ended), he is at or past the seam's <see cref="ChapterSeam.ExitX"/>, and the
        /// checkpoint is the seam's exit.
        /// </summary>
        public static ChapterSeam Due(ChapterSim sim)
        {
            if (sim == null || !sim.Exited || sim.Act != null) return null;
            var seam = Next(sim.Def.Id, sim.Checkpoints.Current.Name);
            return seam != null && sim.X >= seam.ExitX ? seam : null;
        }

        /// <summary>
        /// The chapters joined to <paramref name="chapterId"/> by seams, in play order (it alone when none is): the ones a host
        /// streams scenes from, so a seam's both sides are loaded around it.
        /// </summary>
        public static string[] Span(string chapterId)
        {
            var list = new List<string> { chapterId };
            for (var s = Into(chapterId); s != null && !list.Contains(s.From); s = Into(s.From)) list.Insert(0, s.From);
            for (var s = Out(chapterId); s != null && !list.Contains(s.To); s = Out(s.To)) list.Add(s.To);
            return list.ToArray();
        }

        /// <summary>
        /// Where <paramref name="chapterId"/>'s lane coordinates are in the game's world: (0, 0) for the first chapter of its
        /// <see cref="Span"/>, each later one shifted by the seams before it (someone_home: y + 3.24, ring A over the school
        /// floor). A view, D-17 and the camera in that chapter are drawn at its lane position plus this.
        /// </summary>
        public static void Origin(string chapterId, out double x, out double y)
        {
            x = y = 0;
            var seen = new HashSet<string>();
            for (var s = Into(chapterId); s != null && seen.Add(s.From); s = Into(s.From)) { x -= s.OffsetX; y -= s.OffsetY; }
        }

        private static ChapterSeam Out(string chapterId)
        {
            for (int i = 0; i < Rows.Length; i++) if (Rows[i].From == chapterId) return Rows[i];
            return null;
        }
    }
}
