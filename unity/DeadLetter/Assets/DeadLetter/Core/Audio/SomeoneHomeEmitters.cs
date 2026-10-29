namespace DeadLetter.Core.Audio
{
    /// <summary>
    /// Chapter 2's emitters (region 7, DL-18 and DL-19; issue #57), in the prologue's kinds (<see cref="EmitterKind"/>) and
    /// chapter 2's lane x. No prototype: each cites its scene doc's §8. The relay boxes' 7 s click is not here: it plays
    /// in step with their pilot lamps (<see cref="Presentation.SomeoneHomeSounds"/>), which an emitter's own timer can't.
    /// </summary>
    public static class SomeoneHomeEmitters
    {
        /// <summary>The alarm clock ticks unless it is ringing (DL-18 §6: "rings 2 s, then idle").</summary>
        public const string ClockTicking = "clockTicking";

        public static readonly EmitterDef[] All =
        {
            new EmitterDef(7, 348.0, EmitterKind.Buzz, 0.15, 3, note: "the gallery's maintained lamp (DL-18 §8: its faint buzz)"),
            new EmitterDef(7, 350.4, EmitterKind.Buzz, 0.15, 3, note: "the gallery's other lamp"),
            new EmitterDef(7, 349.5, EmitterKind.Wind, 0.3, 5, note: "the shaft's air below the gallery (DL-18 §8)"),
            new EmitterDef(7, 351.95, EmitterKind.Tick, 0.5, 3.5, period: 1.0, condition: ClockTicking, note: "the alarm clock, the room's loudest thing (DL-18 §8)"),
            new EmitterDef(7, 358.0, EmitterKind.Wind, 0.25, 6, note: "the shaft's air at the terrace landing"),
            new EmitterDef(7, 372.0, EmitterKind.Wind, 0.3, 6, note: "the shaft open beyond the upper terrace's rail (DL-19 §3)"),
        };
    }
}
