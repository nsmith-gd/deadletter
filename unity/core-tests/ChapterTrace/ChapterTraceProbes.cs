using System.Collections.Generic;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// The chapter replay's probes, one per ported scene in lane order (<see cref="IChapterTraceProbe"/>). A newly ported
    /// scene adds its probe file and one line here.
    /// </summary>
    internal static class ChapterTraceProbes
    {
        /// <summary>The prologue's, DL-01 to DL-06 (fresh instances: a probe holds one replay's samples).</summary>
        public static IReadOnlyList<IChapterTraceProbe> Prologue() => new IChapterTraceProbe[]
        {
            new Dl01ChapterProbe(),
            new Dl02ChapterProbe(),
            new Dl03ChapterProbe(),
            new Dl04ChapterProbe(),
            new Dl05ChapterProbe(),
            new Dl06ChapterProbe(),
        };
    }
}
