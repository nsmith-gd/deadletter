using System;

namespace DeadLetter.Core.Audio
{
    /// <summary>One music key of index.html's <c>Music</c> (L780–L943): a cue, or a looping ambience.</summary>
    public sealed class MusicTrack
    {
        /// <summary>The prototype's key (<c>wake</c>, <c>childP</c>, <c>lower_works</c>…).</summary>
        public readonly string Key;
        /// <summary>The file in <c>game/undelivered/assets/music/</c>, without <c>.mp3</c> (<c>FILES</c>, L783–L787).</summary>
        public readonly string File;
        /// <summary><c>LEVEL</c> (cues, L788) or <c>LOOPS[].level</c> (loops, L802–L803).</summary>
        public readonly double Level;
        public readonly bool IsLoop;
        /// <summary>The loop region in the padded source file (<c>LOOPS[].loop</c>); the importer trims the clip to it.</summary>
        public readonly double LoopStart, LoopEnd;
        /// <summary>The file's length in seconds (docs/unity/audio_inventory.md, Music). Runtime overrides it with the clip's.</summary>
        public readonly double Length;
        /// <summary><c>HAND[key][0]</c>: seconds into the cue where the scene's loop (or the queued cue) comes in; NaN = none.</summary>
        public readonly double HandoverAt;
        /// <summary><c>HAND[key][1]</c>: the cue opens with intro bars in the outgoing loop's texture.</summary>
        public readonly bool IntroBars;

        private MusicTrack(string key, string file, double level, bool loop, double loopStart, double loopEnd, double length,
            double handoverAt, bool introBars)
        {
            Key = key; File = file; Level = level; IsLoop = loop; LoopStart = loopStart; LoopEnd = loopEnd; Length = length;
            HandoverAt = handoverAt; IntroBars = introBars;
        }

        public bool HasHandover => !double.IsNaN(HandoverAt);

        /// <summary>The clip as imported: a cue plays whole; a loop is trimmed to [LoopStart, LoopEnd] so it loops natively.</summary>
        public double ClipLength => IsLoop ? LoopEnd - LoopStart : Length;

        /// <summary>The Unity asset name: loops get <c>_loop</c> because they are the trimmed region, not the file.</summary>
        public string AssetName => IsLoop ? File + "_loop" : File;

        internal static MusicTrack Cue(string key, string file, double level, double length, double hand = double.NaN, int intro = 0) =>
            new MusicTrack(key, file, level, false, 0, 0, length, hand, intro != 0);

        internal static MusicTrack Loop(string key, string file, double level, double start, double end, double length) =>
            new MusicTrack(key, file, level, true, start, end, length, double.NaN, false);
    }

    /// <summary>The score's tables, index.html L783–L803; lengths from docs/unity/audio_inventory.md.</summary>
    public static class MusicCatalog
    {
        public static readonly MusicTrack[] All =
        {
            // Cues: LEVEL (L788), HAND (L792–L793).
            MusicTrack.Cue("wake", "prologue_cue_wake", 0.9, 54.0, 48, 0),
            MusicTrack.Cue("hall", "prologue_cue_hall", 0.9, 38.0, 32, 1),
            MusicTrack.Cue("threshold", "prologue_cue_threshold", 0.9, 30.0, 24, 1),
            MusicTrack.Cue("racks", "prologue_cue_racks", 0.9, 42.0, 36, 1),
            MusicTrack.Cue("kin", "prologue_cue_kin", 0.9, 34.0, 28, 0),
            MusicTrack.Cue("dead", "prologue_cue_dead", 0.9, 46.0, 40, 0),
            MusicTrack.Cue("latch", "prologue_cue_latch", 0.9, 14.0, 8, 0),
            MusicTrack.Cue("refuge", "prologue_cue_refuge", 0.9, 30.0, 24, 0),
            MusicTrack.Cue("ringc", "prologue_cue_ringc", 0.9, 30.0, 24, 0),
            MusicTrack.Cue("childP", "prologue_cue_child", 0.9, 42.0, 36, 0),
            MusicTrack.Cue("window", "prologue_cue_window", 0.9, 26.0, 20, 0),
            MusicTrack.Cue("end", "prologue_cue_end", 0.9, 66.0, 60, 0),
            MusicTrack.Cue("child", "dl05_child", 0.6, 50.1),
            MusicTrack.Cue("endAtt", "dl01_end", 0.6, 100.0),
            // Loops: LOOPS (L799–L803), files padded 2 s at each end.
            MusicTrack.Loop("bed", "dl01_bed", 0.26, 2, 50, 52.0),
            MusicTrack.Loop("lower_works", "prologue_loop_lower_works", 0.9, 2, 34, 36.0),
            MusicTrack.Loop("order", "prologue_loop_order", 0.9, 2, 34, 36.0),
            MusicTrack.Loop("heaps", "prologue_loop_heaps", 0.9, 2, 34, 36.0),
            MusicTrack.Loop("failure", "prologue_loop_failure", 0.9, 2, 34, 36.0),
        };

        /// <summary>Files in <c>assets/music/</c> the game never plays (the old score; the two cues ringc replaced). Not imported.</summary>
        public static readonly string[] Unreferenced =
        {
            "dl01_dead", "dl01_hall", "dl01_kin", "dl01_racks", "dl01_threshold", "dl01_wake", "dl04_latch", "dl04_refuge",
            "prologue_collapse", "prologue_lastcar",
        };

        public static MusicTrack Find(string key)
        {
            if (key == null) return null;
            for (int i = 0; i < All.Length; i++) if (All[i].Key == key) return All[i];
            return null;
        }
    }

    /// <summary>Where the game starts each cue (port_architecture §4.24, "Cue triggers"). Scene rules call the model with these.</summary>
    public sealed class CueTrigger
    {
        public readonly string Cue;
        /// <summary>The <c>Music.play</c> fade-in (s); <see cref="MusicTriggerKind.Moment"/> cues start at full level.</summary>
        public readonly double FadeIn;
        public readonly MusicTriggerKind Kind;
        public readonly string Where;
        public readonly int Line;

        public CueTrigger(string cue, MusicTriggerKind kind, double fadeIn, string where, int line)
        {
            Cue = cue; Kind = kind; FadeIn = fadeIn; Where = where; Line = line;
        }
    }

    public enum MusicTriggerKind { Play, Moment, Queue }

    public static class MusicCues
    {
        public const double DefaultFadeIn = 1.2;

        public static readonly CueTrigger[] Triggers =
        {
            new CueTrigger("wake", MusicTriggerKind.Play, 0.6, "the opening starts (after the intertitle)", 8068),
            new CueTrigger("hall", MusicTriggerKind.Play, DefaultFadeIn, "DL-01: first x > HALL_X + 0.2 before the bulkhead opens", 2066),
            new CueTrigger("threshold", MusicTriggerKind.Play, DefaultFadeIn, "DL-01: bulkhead fully open", 1890),
            new CueTrigger("racks", MusicTriggerKind.Play, 0.6, "DL-04: the reveal through the DL-03 gate", 2403),
            new CueTrigger("kin", MusicTriggerKind.Moment, 0, "DL-04: first realise past the gate", 1958),
            new CueTrigger("dead", MusicTriggerKind.Play, 0.15, "DL-06: scanner rejects", 2801),
            new CueTrigger("latch", MusicTriggerKind.Play, 0.15, "DL-08: the pawl latches", 3125),
            new CueTrigger("refuge", MusicTriggerKind.Moment, 0, "DL-09: x > AWE_X", 3433),
            new CueTrigger("ringc", MusicTriggerKind.Moment, 0, "DL-10: UP with the case loaded", 4588),
            new CueTrigger("childP", MusicTriggerKind.Play, DefaultFadeIn, "DL-11: the desk's marks revealed", 3547),
            new CueTrigger("window", MusicTriggerKind.Moment, 0, "the end: the landing's look up the well", 2105),
            new CueTrigger("end", MusicTriggerKind.Queue, 2.0, "finish(): 5.2 s after window, else queued", 8188),
            new CueTrigger("child", MusicTriggerKind.Play, 2.5, "DL-14: the window peel (3 s at DL-15's dismissal, L5734)", 5474),
            new CueTrigger("endAtt", MusicTriggerKind.Queue, 2.0, "chapter one's finish()", 8187),
        };

        /// <summary>
        /// <c>finish()</c>, L8186–L8189: after the lit window the end cue starts 5.2 s later at a 2 s fade; otherwise it
        /// follows whatever is playing.
        /// </summary>
        public static void Finish(MusicDirectorModel music, double now, bool chapterOne)
        {
            if (music == null) throw new ArgumentNullException(nameof(music));
            string endCue = chapterOne ? "endAtt" : "end";
            if (music.Playing == "window") music.PlayAfter(endCue, now, 5.2, 2.0);
            else if (music.Playing != endCue) music.Queue(endCue, now);
        }

        /// <summary>
        /// <c>startPlay</c>, L8089–L8091: on a checkpoint (re)start any cue but the wake gives way over 2 s; the pause level
        /// lifts. The caller then applies the bed (chapter one) or <see cref="AmbienceRules.Apply"/>.
        /// </summary>
        public static void CheckpointStart(MusicDirectorModel music, double now, bool fromOpening)
        {
            if (music == null) throw new ArgumentNullException(nameof(music));
            if (!fromOpening && music.Playing != "wake") music.Stop(now, 2);
            music.SetPaused(false, now);
        }
    }
}
