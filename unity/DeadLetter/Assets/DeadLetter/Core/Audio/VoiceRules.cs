using System;

namespace DeadLetter.Core.Audio
{
    /// <summary>How a voice is asked to play (<c>Voice.play(v, opts)</c>).</summary>
    public struct VoicePlayOptions
    {
        /// <summary>Its level (<c>opts.level ?? v.level ?? 1</c>); 0 = 1.</summary>
        public double Level;
        /// <summary>Positional: the source's x and its reach (0 = not positional).</summary>
        public double X, Reach;
        /// <summary>DL-13's braked lesson: loop 0.35 s from this point (NaN = none). No chime, no end.</summary>
        public double StickAt;
        /// <summary>Lengths of the recordings in turn, if any exist; null = the placeholder (the lines' length).</summary>
        public double[] RecordedLengths;

        public static VoicePlayOptions At(double x, double reach, double level = 1) =>
            new VoicePlayOptions { X = x, Reach = reach, Level = level, StickAt = double.NaN };

        public static VoicePlayOptions Flat(double level = 1) =>
            new VoicePlayOptions { X = double.NaN, Level = level, StickAt = double.NaN };
    }

    /// <summary>One voice playing (or fading): what Runtime's <c>VoicePlayer</c> plays, on the audio clock.</summary>
    public sealed class VoicePlayback
    {
        public readonly VoiceDef Def;
        public readonly TreatmentDef Treatment;
        public readonly double Started, Level, X, Reach;
        /// <summary>The tannoy chime plays from <see cref="Started"/>; the voice itself from <see cref="VoiceAt"/>.</summary>
        public readonly bool Chime;
        public readonly double VoiceAt;
        /// <summary>The voice's length (recordings at the treatment's rate plus 0.15 s gaps, or the placeholder's).</summary>
        public readonly double Duration;
        /// <summary>When each subtitle line shows (absolute), spread over <see cref="Duration"/>.</summary>
        public readonly double[] LineAt;
        /// <summary>When it ends by itself and fades out over 1.2 s (∞ when stuck).</summary>
        public readonly double EndAt;
        public readonly bool Stuck;
        public readonly GainEnvelope Out = new GainEnvelope(0);

        internal VoicePlayback(VoiceDef def, TreatmentDef t, double now, in VoicePlayOptions o)
        {
            Def = def; Treatment = t; Started = now;
            Level = o.Level > 0 ? o.Level : 1;
            X = o.X; Reach = o.Reach;
            Stuck = !double.IsNaN(o.StickAt);
            Chime = t.Chime && !Stuck;
            VoiceAt = now + (Chime ? VoiceRules.ChimeLead : VoiceRules.PlainLead);   // L1074
            double dur = 0;
            if (o.RecordedLengths != null && o.RecordedLengths.Length > 0)
                foreach (double len in o.RecordedLengths) dur += len / t.PlaybackRate + VoiceRules.FileGap;   // L1090
            else dur = def.Length;   // L1095
            Duration = dur;
            // Subtitles spread over the real length (L1126–L1128): k = dur / total.
            double total = def.Length, k = total > 0 ? dur / total : 1, tt = VoiceAt - now;
            LineAt = new double[def.Lines.Length];
            for (int i = 0; i < def.Lines.Length; i++) { LineAt[i] = now + tt; tt += def.Lines[i].Seconds * k; }
            EndAt = Stuck ? double.PositiveInfinity : now + tt + VoiceRules.Tail;   // L1129
            Out.TargetAt(now, Level, VoiceRules.LevelTau);   // L1124
        }

        public bool Positional => !double.IsNaN(X) && Reach > 0;

        /// <summary>When the fade-out finishes and the sources stop (∞ while it plays).</summary>
        public double StopAt { get; internal set; } = double.PositiveInfinity;

        /// <summary>The subtitle line showing at <paramref name="t"/>, or −1 (before the first, or once stopped).</summary>
        public int LineIndexAt(double t)
        {
            if (StopAt < double.PositiveInfinity) return -1;   // stop() clears the subtitles at once (L1053)
            int idx = -1;
            for (int i = 0; i < LineAt.Length; i++) if (t >= LineAt[i]) idx = i;
            return idx;
        }
    }

    /// <summary>
    /// index.html's <c>Voice</c> timing (L1044–L1143), with no audio: one voice at a time, the chime lead, subtitles,
    /// the end, positional fading and the music duck. Runtime calls <see cref="Update"/> each frame with D-17's x.
    /// </summary>
    public sealed class VoiceRules
    {
        public const double ChimeLead = 1.35, PlainLead = 0.25;   // L1074
        public const double FileGap = 0.15;                     // L1090
        public const double Tail = 0.6, EndFade = 1.2;          // L1129
        public const double ReplaceFade = 0.3;                  // L1061
        public const double DefaultStopFade = 0.6;              // L1050
        public const double FarStopFade = 0.2, FarAfter = 1, FarGain = 0.001;   // L1140
        public const double LevelTau = 0.08, PositionTau = 0.15;                // L1124, L1139
        public const double StopTailSeconds = 0.3;              // L1056
        public const double StickLoop = 0.35;                   // L1088
        public const double MomentStopFade = 1.0;               // startMoment, L950
        /// <summary>Tannoys and cards (L6684–L6689, L6672).</summary>
        public const double DefaultTrigger = 2.5, TannoyReach = 9, CardReach = 6;

        public VoicePlayback Current { get; private set; }
        /// <summary>The last voice stopped, still fading (Runtime keeps its sources until <see cref="VoicePlayback.StopAt"/>).</summary>
        public VoicePlayback Fading { get; private set; }

        /// <summary><c>Voice.playing()</c>.</summary>
        public string Playing => Current?.Def.Id;

        /// <summary>The music steps back while a voice plays (<c>Music.duck</c>, L1052, L1064).</summary>
        public bool Ducking => Current != null;

        /// <summary><c>Voice.play(v, opts)</c>, L1059–L1131: stops the voice playing (0.3 s) and starts this one.</summary>
        public VoicePlayback Play(VoiceDef def, double now, VoicePlayOptions options)
        {
            if (def == null) throw new ArgumentNullException(nameof(def));
            Stop(now, ReplaceFade);
            Current = new VoicePlayback(def, VoiceCatalog.Treatment(def.Treat), now, options);
            return Current;
        }

        /// <summary><c>Voice.stop(fade)</c>, L1050–L1057.</summary>
        public void Stop(double now, double fade = DefaultStopFade)
        {
            VoicePlayback c = Current;
            if (c == null) return;
            Current = null;
            c.Out.TargetAt(now, 0, fade / 4);
            c.StopAt = now + fade + StopTailSeconds;
            Fading = c;
        }

        /// <summary>
        /// Every frame: the end (L1129) and positional fading (<c>Voice.update</c>, L1136–L1141): level × max(0, 1 − |x −
        /// v.x| / reach) with τ 0.15; once that is ≤ 0.001 and the voice is over 1 s old it stops (0.2 s). Returns true on
        /// the frame the voice ended by itself (for <c>onEnd</c>).
        /// </summary>
        public bool Update(double now, double px)
        {
            if (Fading != null && now >= Fading.StopAt) Fading = null;
            VoicePlayback c = Current;
            if (c == null) return false;
            if (now >= c.EndAt) { Stop(now, EndFade); return true; }
            if (c.Positional)
            {
                double g = c.Level * Math.Max(0, 1 - Math.Abs(px - c.X) / c.Reach);
                if (Math.Abs(c.Out.Destination - g) > 1e-9) c.Out.TargetAt(now, g, PositionTau);
                if (g <= FarGain && now - c.Started > FarAfter) Stop(now, FarStopFade);
            }
            return false;
        }
    }

    /// <summary>A tannoy's memory (<c>v.last</c>, <c>v.away</c>, <c>v.played</c>).</summary>
    public sealed class TannoyState
    {
        public double Last = double.NaN;
        public bool Away, Played;
    }

    /// <summary><c>updateTannoys</c> (index.html L6679–L6692) and the voice-card act (L6656–L6677).</summary>
    public static class TannoyRules
    {
        public const double ReplayAfter = 150, FirstLevel = 0.85, ReplayLevel = 0.5;

        /// <summary>
        /// One tannoy, one frame. Returns true when it should play now, at <paramref name="level"/> (0.85 the first time,
        /// 0.5 after), positional at its x with its reach. It plays once as he passes, and again only after he has gone
        /// beyond its reach and come back more than 150 s later; never over another voice or a moment's shot.
        /// </summary>
        public static bool Update(VoicePlacement v, TannoyState s, int region, bool upper, bool condition, double px, double clock,
            bool voicePlaying, bool voicesHeld, out double level)
        {
            level = 0;
            if (v.Kind != VoicePlacementKind.Tannoy || v.Region != region) return false;
            if (v.Deck != EmitterDeck.Any && (v.Deck == EmitterDeck.Upper) != upper) return false;
            if (!condition) return false;
            double d = Math.Abs(px - v.TriggerX);
            bool near = d < v.TriggerDistance;
            if (d > v.EffectiveReach) s.Away = true;
            if (!near || voicePlaying || voicesHeld) return false;
            if (double.IsNaN(s.Last) || (s.Away && clock - s.Last > ReplayAfter))
            {
                s.Last = clock;
                s.Away = false;
                level = s.Played ? ReplayLevel : FirstLevel;
                s.Played = true;
                return true;
            }
            return false;
        }
    }

    /// <summary>The voice-card act's beats (<c>updateVoiceAct</c>, L6656–L6677), in seconds from the act's start.</summary>
    public static class VoiceCardAct
    {
        /// <summary>A wound player: ratchet at 0.25 and 0.7 s, the voice at 1.2 s.</summary>
        public const double Ratchet1 = 0.25, Ratchet2 = 0.7, WoundVoiceAt = 1.2;
        /// <summary>A loose card: a tap at once, the voice at 0.9 s.</summary>
        public const double LooseVoiceAt = 0.9;
        /// <summary><c>voiceHere</c>: he stands within 0.22 of its stand x (L6652).</summary>
        public const double StandTolerance = 0.22;

        public static double VoiceAt(bool loose) => loose ? LooseVoiceAt : WoundVoiceAt;

        /// <summary>Whether a card is in reach to wind (<c>voiceHere</c>, L6648–L6655).</summary>
        public static bool Here(VoicePlacement v, int region, bool upper, double px, string playing)
        {
            if (v.Kind != VoicePlacementKind.Card || double.IsNaN(v.StandX) || v.Region != region) return false;
            if (v.Deck != EmitterDeck.Any && (v.Deck == EmitterDeck.Upper) != upper) return false;
            return Math.Abs(px - v.StandX) < StandTolerance && playing != v.Id;
        }
    }
}
