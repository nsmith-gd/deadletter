using System;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Scenes
{
    /// <summary>
    /// The running game across chapters (#51): the current chapter's <see cref="ChapterSim"/> and the handover to the next at
    /// its seam (<see cref="ChapterSeams"/>, <see cref="ChapterHandover"/>), all over one save store. A host steps <see cref="Sim"/>
    /// and, after each step, calls <see cref="TryHandOver"/>; when that returns true it rebinds its views to the new sim.
    /// Which chapter a Continue builds is the slot's (<see cref="ContinueChapter"/>).
    /// </summary>
    public sealed class GameSession
    {
        private readonly ISaveStore _store;
        private readonly MotorConfig _config;

        /// <param name="store">Where the slot is saved (null = nowhere), shared by every chapter's sim.</param>
        /// <param name="config">The motor tuning for every chapter's sim (null = the prototype's).</param>
        public GameSession(ChapterDef chapter, ISaveStore store = null, MotorConfig config = null)
        {
            _store = store;
            _config = config;
            Sim = new ChapterSim(chapter ?? throw new ArgumentNullException(nameof(chapter)), config, store);
        }

        /// <summary>The chapter being played.</summary>
        public ChapterSim Sim { get; private set; }

        /// <summary>The seam the sim is at now (<see cref="ChapterSeams.Due"/>), or null.</summary>
        public ChapterSeam Seam => ChapterSeams.Due(Sim);

        /// <summary>
        /// At a seam: builds the next chapter's sim, hands D-17 over (<see cref="ChapterHandover.Carry"/>) and makes it
        /// <see cref="Sim"/>; <paramref name="from"/> is the one he left (no longer stepped). False, and nothing changes,
        /// when no seam is due.
        /// </summary>
        public bool TryHandOver(out ChapterSim from)
        {
            from = null;
            var seam = Seam;
            if (seam == null) return false;
            var next = ChapterDefs.Create(seam.To) ?? throw new InvalidOperationException("The seam " + seam + " names no chapter '" + seam.To + "'.");
            var to = new ChapterSim(next, _config, _store);
            to.Checkpoints.MinSecondsBetweenWrites = Sim.Checkpoints.MinSecondsBetweenWrites;
            ChapterHandover.Carry(Sim, to);
            from = Sim;
            Sim = to;
            return true;
        }

        /// <summary>
        /// The chapter a Continue from <paramref name="slot"/> builds: the slot's (<see cref="SaveModel.ChapterId"/>), when it is
        /// a chapter Core has and its checkpoint is one of that chapter's scenes'. Null for an empty, options-only or unreadable
        /// slot, or one no chapter can continue (the host then starts its own).
        /// </summary>
        public static string ContinueChapter(ISaveStore store, int slot = 0)
        {
            if (store == null || !store.TryLoad(slot, out var m) || m == null || m.OptionsOnly) return null;
            var def = ChapterDefs.Create(m.ChapterId);
            if (def == null || !def.Checkpoints.TryGet(m.Checkpoint, out var cp) || def.Scene(cp.Scene) == null) return null;
            return def.Id;
        }
    }
}
