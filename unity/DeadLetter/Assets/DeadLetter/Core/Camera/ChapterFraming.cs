using System;
using DeadLetter.Core.Scenes;

namespace DeadLetter.Core.Camera
{
    /// <summary>
    /// The framing track for a chapter (issue #50; the interface posted on #1): the prologue's
    /// (<see cref="PrologueFraming"/>) or chapter 1's (<see cref="AttendanceFraming"/>). Null for a chapter whose framing
    /// is not transcribed yet; <c>GameHost</c> then logs an error naming the chapter and stands the prologue's track in.
    /// <para>Chapter 2 (<c>someone_home</c>, #47) has none yet: docs/scenes/DL-18 and DL-19 §7 give x ranges and focal lengths
    /// (32, 40, 38, 30 mm), not framing volumes or <c>CAM_</c> data, and the rig frames at a fixed 35 mm.</para>
    /// </summary>
    public static class ChapterFraming
    {
        public static FramingTrack For(string chapterId)
        {
            switch (chapterId)
            {
                case ChapterDefs.PrologueId: return PrologueFraming.Build();
                case ChapterDefs.AttendanceId: return AttendanceFraming.Build();
                case ChapterDefs.SomeoneHomeId: return null;                                    // no framing data yet (see above)
                default: return null;
            }
        }

        /// <summary>
        /// What a host uses when <see cref="For"/> has no track for <paramref name="chapterId"/>: the prologue's, said
        /// through <paramref name="log"/> (the side view then frames the prologue's lane, not this chapter's).
        /// </summary>
        public static FramingTrack Fallback(string chapterId, Action<string> log)
        {
            log?.Invoke("chapter '" + chapterId + "' has no framing yet (ChapterFraming.For returned null). The camera stands in the " +
                        "prologue's track, which frames the prologue's lane, not this chapter's.");
            return PrologueFraming.Build();
        }
    }
}
