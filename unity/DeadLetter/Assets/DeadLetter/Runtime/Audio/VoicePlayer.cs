using System;
using System.Collections.Generic;
using DeadLetter.Core.Audio;
using DeadLetter.Runtime.Camera;
using UnityEngine;
using UnityEngine.Audio;

namespace DeadLetter.Runtime.Audio
{
    /// <summary>
    /// Voice cards, tannoys and the radio (port_architecture §4.25) through the Voice mixer group. Core's
    /// <see cref="VoiceRules"/> owns the timing (one voice at a time, the chime lead, subtitles, the end, positional fade,
    /// the music duck) and <see cref="TannoyRules"/> when a tannoy speaks; this plays clips:
    /// <list type="bullet">
    /// <item>the tannoy chime (<c>voice_tannoy_chime</c>) and the treatment's crackle bed (<c>voice_crackle_*</c>), rendered;</item>
    /// <item>the recording <c>voice_&lt;file&gt;</c> if one has been imported, at the treatment's tape rate;</item>
    /// <item>otherwise a placeholder <c>voice_placeholder_&lt;treatment&gt;</c> looped for the line's length, if the bank has
    /// one. Until recordings exist (decision on #20) there is no voice DSP: the chain will be baked offline.</item>
    /// </list>
    /// Subtitles go out through <see cref="SubtitleChanged"/> (null text = clear).
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class VoicePlayer : MonoBehaviour
    {
        [SerializeField] private SfxBank bank;
        [Tooltip("Master > Voice.")]
        [SerializeField] private AudioMixerGroup voiceGroup;
        [Tooltip("Ducks under a voice (0.4).")]
        [SerializeField] private MusicDirector music;
        [Tooltip("Voices and tannoys wait while a moment's shot holds (voicesHeld, L958).")]
        [SerializeField] private DirectedMomentPlayer moments;
        [Tooltip("Run the tannoys of VoiceCatalog.Placements from AudioWorld (region, x, conditions).")]
        [SerializeField] private bool driveTannoys = true;

        private sealed class Slot
        {
            public VoicePlayback Playback;
            public AudioSource Chime, Crackle;
            public readonly List<AudioSource> Voice = new List<AudioSource>();
            public double VoiceEndsAt;
        }

        private readonly VoiceRules _rules = new VoiceRules();
        private readonly Slot[] _slots = new Slot[2];
        private readonly Dictionary<string, TannoyState> _tannoys = new Dictionary<string, TannoyState>();
        private readonly HashSet<string> _found = new HashSet<string>();
        private int _line = -1;
        private VoicePlayback _shown;
        private bool _ducked;

        /// <summary>(who, text) when a subtitle line shows; (null, null) when it clears.</summary>
        public event Action<string, string> SubtitleChanged;

        /// <summary><c>game.mode === 'play'</c>: tannoys only speak in play.</summary>
        public bool InPlay { get; set; } = true;

        public string Playing => _rules.Playing;
        public VoiceRules Rules => _rules;

        private static double Now => AudioSettings.dspTime;

        private void Awake()
        {
            for (int i = 0; i < _slots.Length; i++)
            {
                var s = new Slot();
                s.Chime = NewSource("Voice " + i + " chime", false);
                s.Crackle = NewSource("Voice " + i + " crackle", true);
                _slots[i] = s;
            }
        }

        /// <summary><c>Voice.play</c>: <paramref name="id"/> from <see cref="VoiceCatalog"/> with <paramref name="options"/>.</summary>
        public bool Play(string id, VoicePlayOptions options)
        {
            VoiceDef def = VoiceCatalog.Find(id);
            if (def == null) { Debug.LogWarning("[Audio] Unknown voice id " + id, this); return false; }
            List<AudioClip> recordings = Recordings(def);
            if (recordings.Count > 0)
            {
                options.RecordedLengths = new double[recordings.Count];
                for (int i = 0; i < recordings.Count; i++) options.RecordedLengths[i] = recordings[i].length;
            }
            double now = Now;
            _rules.Play(def, now, options);
            Bind(_rules.Current, recordings, now);
            return true;
        }

        /// <summary>A card he has wound (or a loose one he reads): positional at its x with its reach, level 1; the first
        /// hearing plays <c>found</c> (L6672–L6673).</summary>
        public bool PlayCard(string id)
        {
            VoicePlacement p = VoiceCatalog.FindPlacement(id);
            VoicePlayOptions o = p != null ? VoicePlayOptions.At(p.X, p.EffectiveReach) : VoicePlayOptions.Flat();
            bool ok = Play(id, o);
            if (ok && _found.Add(id) && SfxPlayer.Current != null) SfxPlayer.Current.Play(SfxKeys.Simple["found"]);
            return ok;
        }

        /// <summary><c>Voice.stop(fade)</c>.</summary>
        public void Stop(double fade = VoiceRules.DefaultStopFade) => _rules.Stop(Now, fade);

        private void Update()
        {
            double now = Now;
            AudioWorld world = AudioWorld.Current;
            double px = world != null ? world.ListenerX : 0;

            if (driveTannoys && world != null && InPlay) UpdateTannoys(world, px);
            _rules.Update(now, px);

            bool duck = _rules.Ducking;
            if (duck != _ducked) { _ducked = duck; if (music != null) music.Duck(duck); }

            for (int i = 0; i < _slots.Length; i++)
            {
                Slot s = _slots[i];
                if (s.Playback == null) continue;
                if (s.Playback != _rules.Current && s.Playback != _rules.Fading) { Release(s); continue; }
                float pan = s.Playback.Positional && world != null ? world.PanForX(s.Playback.X) : 0f;
                float v = Mathf.Clamp01((float)s.Playback.Out.ValueAt(now));
                SetVolume(s, v, pan);
                if (s.Voice.Count > 0 && s.Voice[0].loop && now >= s.VoiceEndsAt) s.Voice[0].Stop();   // placeholder length
            }
            UpdateSubtitle(now);
        }

        private void UpdateTannoys(AudioWorld world, double px)
        {
            bool held = moments != null && moments.VoicesHeld;
            double clock = Time.timeAsDouble;
            foreach (VoicePlacement p in VoiceCatalog.Placements)
            {
                if (p.Kind != VoicePlacementKind.Tannoy) continue;
                if (!_tannoys.TryGetValue(p.Id, out TannoyState st)) _tannoys[p.Id] = st = new TannoyState();
                if (!TannoyRules.Update(p, st, world.region, world.upper, world.Condition(p.Condition), px, clock,
                        _rules.Playing != null, held, out double level)) continue;
                Play(p.Id, VoicePlayOptions.At(p.X, p.EffectiveReach, level));
                _found.Add(p.Id);
            }
        }

        private void Bind(VoicePlayback pb, List<AudioClip> recordings, double now)
        {
            // The voice just replaced fades on in its slot (0.3 s); this one takes the other.
            Slot s = _slots[0].Playback != null && _slots[0].Playback == _rules.Fading ? _slots[1] : _slots[0];
            if (s.Playback != null) Release(s);
            s.Playback = pb;
            TreatmentDef t = pb.Treatment;

            AudioClip crackle = bank != null ? bank.First(t.CrackleKey) : null;
            if (crackle != null) { s.Crackle.clip = crackle; s.Crackle.volume = 0f; s.Crackle.Play(); }

            if (pb.Chime)
            {
                AudioClip chime = bank != null ? bank.First("voice_tannoy_chime") : null;
                if (chime != null) { s.Chime.clip = chime; s.Chime.volume = 0f; s.Chime.PlayScheduled(now); }
            }

            if (recordings.Count > 0)
            {
                double at = pb.VoiceAt;
                for (int i = 0; i < recordings.Count; i++)
                {
                    AudioSource src = VoiceSource(s, i);
                    src.clip = recordings[i];
                    src.loop = false;
                    src.pitch = (float)t.PlaybackRate;
                    src.PlayScheduled(at);
                    at += recordings[i].length / t.PlaybackRate + VoiceRules.FileGap;
                }
                s.VoiceEndsAt = at;
            }
            else
            {
                AudioClip placeholder = bank != null ? bank.First("voice_placeholder_" + VoiceCatalog.Name(t.Id)) : null;
                if (placeholder != null)
                {
                    AudioSource src = VoiceSource(s, 0);
                    src.clip = placeholder;
                    src.loop = true;
                    src.pitch = 1f;
                    src.PlayScheduled(pb.VoiceAt);
                }
                s.VoiceEndsAt = pb.VoiceAt + pb.Duration;
            }
        }

        private List<AudioClip> Recordings(VoiceDef def)
        {
            var list = new List<AudioClip>();
            if (bank == null) return list;
            foreach (string f in def.Files)
            {
                AudioClip c = bank.First("voice_" + f);
                if (c != null) list.Add(c);
            }
            return list;
        }

        private void UpdateSubtitle(double now)
        {
            VoicePlayback c = _rules.Current;
            int line = c != null ? c.LineIndexAt(now) : -1;
            if (c == _shown && line == _line) return;
            _shown = c;
            _line = line;
            if (SubtitleChanged == null) return;
            if (c == null || line < 0) SubtitleChanged(null, null);
            else SubtitleChanged(c.Def.Lines[line].Who ?? c.Def.Who, c.Def.Lines[line].Text);
        }

        private static void SetVolume(Slot s, float v, float pan)
        {
            s.Chime.volume = v; s.Chime.panStereo = pan;
            s.Crackle.volume = v; s.Crackle.panStereo = pan;
            for (int i = 0; i < s.Voice.Count; i++) { s.Voice[i].volume = v; s.Voice[i].panStereo = pan; }
        }

        private static void Release(Slot s)
        {
            s.Chime.Stop();
            s.Crackle.Stop();
            for (int i = 0; i < s.Voice.Count; i++) s.Voice[i].Stop();
            s.Playback = null;
        }

        private AudioSource VoiceSource(Slot s, int i)
        {
            while (s.Voice.Count <= i) s.Voice.Add(NewSource("Voice line " + s.Voice.Count, false));
            return s.Voice[i];
        }

        private AudioSource NewSource(string name, bool loop)
        {
            var go = new GameObject(name);
            go.transform.SetParent(transform, false);
            AudioSource a = go.AddComponent<AudioSource>();
            a.playOnAwake = false;
            a.loop = loop;
            a.spatialBlend = 0f;
            a.outputAudioMixerGroup = voiceGroup;
            return a;
        }
    }
}
