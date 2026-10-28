using DeadLetter.Core.Scenes;

namespace DeadLetter.Core.Camera
{
    /// <summary>
    /// The framing track for a chapter (issue #50; the interface posted on #1): the prologue's
    /// (<see cref="PrologueFraming"/>) or chapter 1's (<see cref="AttendanceFraming"/>). Null for a chapter whose framing
    /// is not transcribed yet; <c>GameHost</c> then logs and falls back to the prologue's track.
    /// </summary>
    public static class ChapterFraming
    {
        public static FramingTrack For(string chapterId)
        {
            switch (chapterId)
            {
                case ChapterDefs.PrologueId: return PrologueFraming.Build();
                case ChapterDefs.AttendanceId: return AttendanceFraming.Build();
                default: return null;
            }
        }
    }
}
