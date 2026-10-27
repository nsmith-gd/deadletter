using System;
using System.Collections.Generic;
using DeadLetter.Core.Audio;
using DeadLetter.Core.Cues;

namespace DeadLetter.Core.Streaming
{
    /// <summary>What a cue asks the presentation for (the prefix of its name, <see cref="CueId"/>).</summary>
    public enum CueKind
    {
        /// <summary>No prefix the runtime knows: logged once, otherwise ignored.</summary>
        Unknown,
        /// <summary><c>music:&lt;cue&gt;</c>: <c>Music.play(cue, fade)</c> (<see cref="MusicCues.Triggers"/> gives the fade).</summary>
        Music,
        /// <summary><c>moment:&lt;name&gt;</c>: a directed moment Core has started (its cue and Timeline are the runtime's).</summary>
        Moment,
        /// <summary><c>voice:&lt;id&gt;</c>: <c>Voice.play(id)</c> (<see cref="VoiceCatalog"/>).</summary>
        Voice,
        /// <summary><c>sound:&lt;name&gt;</c>: a one-shot; <see cref="CueRoute.Key"/> is the SFX bank key.</summary>
        Sound,
        /// <summary><c>shot:&lt;name&gt;</c>: an authored camera shot's start (a hint; the framing itself is Core's).</summary>
        Shot,
        /// <summary><c>shake</c>: a camera shake, argument in hundredths (<c>shake(0.25)</c> → 25).</summary>
        Shake,
    }

    /// <summary>One cue resolved for dispatch: its kind, the asset or catalogue key, and a music cue's fade-in.</summary>
    public readonly struct CueRoute
    {
        public readonly CueKind Kind;
        /// <summary>Music: the cue key ("hall"). Moment: its name ("kin"). Voice: the voice ID. Sound: the SFX bank key ("d17_worried"). Shot: its name.</summary>
        public readonly string Key;
        /// <summary>Music only: seconds of fade-in.</summary>
        public readonly double FadeIn;

        public CueRoute(CueKind kind, string key, double fadeIn = 0) { Kind = kind; Key = key; FadeIn = fadeIn; }
    }

    /// <summary>
    /// Resolves <see cref="ChapterSim"/>'s typed cues (<see cref="Scenes.ChapterSim.Cues"/>) to what the runtime plays, once
    /// per cue: the first sight of a <see cref="CueId"/> parses its name and caches the route by its integer, so dispatching a
    /// step's cues afterwards is a dictionary read and allocates nothing.
    /// </summary>
    public sealed class CueRoutes
    {
        private readonly Dictionary<int, CueRoute> _routes = new Dictionary<int, CueRoute>();

        /// <summary>The route of <paramref name="id"/> (cached after the first call).</summary>
        public CueRoute Resolve(CueId id)
        {
            if (_routes.TryGetValue(id.Value, out var r)) return r;
            r = Parse(id.IsNone ? "" : id.Name);
            _routes.Add(id.Value, r);
            return r;
        }

        /// <summary>Parses a cue name ("music:hall", "sound:setDownHigh", "shake").</summary>
        public static CueRoute Parse(string name)
        {
            if (string.IsNullOrEmpty(name)) return new CueRoute(CueKind.Unknown, "");
            if (name == "shake") return new CueRoute(CueKind.Shake, name);
            int colon = name.IndexOf(':');
            if (colon <= 0 || colon == name.Length - 1) return new CueRoute(CueKind.Unknown, name);
            string prefix = name.Substring(0, colon), key = name.Substring(colon + 1);
            switch (prefix)
            {
                case "music": return new CueRoute(CueKind.Music, key, MusicFadeIn(key));
                case "moment": return new CueRoute(CueKind.Moment, key);
                case "voice": return new CueRoute(CueKind.Voice, key);
                case "sound": return new CueRoute(CueKind.Sound, SoundKey(key));
                case "shot": return new CueRoute(CueKind.Shot, key);
                default: return new CueRoute(CueKind.Unknown, name);
            }
        }

        /// <summary>The fade-in of <c>Music.play(cue)</c> where the prototype plays it (<see cref="MusicCues.Triggers"/>), else the default 1.2 s.</summary>
        public static double MusicFadeIn(string cue)
        {
            foreach (var t in MusicCues.Triggers)
                if (t.Kind == MusicTriggerKind.Play && string.Equals(t.Cue, cue, StringComparison.Ordinal)) return t.FadeIn;
            return MusicCues.DefaultFadeIn;
        }

        /// <summary>
        /// The SFX bank key of <c>Sound.&lt;name&gt;()</c>: <see cref="SfxKeys.Simple"/>, or the call that takes an argument
        /// (<c>setDown</c>/<c>setDownHigh</c> → <see cref="SfxKeys.SetDown"/>). An unmapped name is returned as is (the bank
        /// then warns that it has no such key).
        /// </summary>
        public static string SoundKey(string name)
        {
            if (name == "setDown") return SfxKeys.SetDown(false);
            if (name == "setDownHigh") return SfxKeys.SetDown(true);
            return SfxKeys.Simple.TryGetValue(name, out string key) ? key : name;
        }
    }
}
