using System;
using System.Collections.Generic;
using UnityEngine;

namespace DeadLetter.Runtime.Audio
{
    /// <summary>
    /// The prototype's sound names → clips (port_architecture §4.23). Built by <c>Dead Letter → Audio → Import Audio</c>
    /// from <c>art/sfx/out/</c> and the referenced music (Core <c>SfxCatalog</c> decides the keys and takes); a sound
    /// designer can swap a clip here later without code changes. Keys: <c>DeadLetter.Core.Audio.SfxKeys</c>,
    /// <c>MusicCatalog</c>, <c>EmitterRules.BankKey</c>, <c>TreatmentDef.CrackleKey</c>.
    /// </summary>
    [CreateAssetMenu(menuName = "Dead Letter/Audio/Sfx Bank", fileName = "SfxBank")]
    public sealed class SfxBank : ScriptableObject
    {
        [Serializable]
        public sealed class Sound
        {
            public string key;
            [Tooltip("Continuous layer (plays looping).")]
            public bool loop;
            [Tooltip("One clip per take; SfxPlayer picks one each play.")]
            public AudioClip[] takes = new AudioClip[0];
        }

        [Serializable]
        public sealed class Music
        {
            [Tooltip("The prototype's music key (wake, childP, lower_works…).")]
            public string key;
            [Tooltip("The cue, or the loop trimmed to its loop region.")]
            public AudioClip clip;
        }

        [SerializeField] private List<Sound> sounds = new List<Sound>();
        [SerializeField] private List<Music> music = new List<Music>();

        [NonSerialized] private Dictionary<string, Sound> _sounds;
        [NonSerialized] private Dictionary<string, AudioClip> _music;

        public IReadOnlyList<Sound> Sounds => sounds;
        public IReadOnlyList<Music> MusicClips => music;

        public Sound Find(string key)
        {
            if (key == null) return null;
            if (_sounds == null) Index();
            return _sounds.TryGetValue(key, out Sound s) ? s : null;
        }

        /// <summary>The first take of <paramref name="key"/>, or null.</summary>
        public AudioClip First(string key)
        {
            Sound s = Find(key);
            return s != null && s.takes != null && s.takes.Length > 0 ? s.takes[0] : null;
        }

        public AudioClip MusicClip(string key)
        {
            if (key == null) return null;
            if (_music == null) Index();
            return _music.TryGetValue(key, out AudioClip c) ? c : null;
        }

        /// <summary>Replaces the contents (the importer). Keeps existing order-independent lookups consistent.</summary>
        public void SetContents(List<Sound> newSounds, List<Music> newMusic)
        {
            sounds = newSounds ?? new List<Sound>();
            music = newMusic ?? new List<Music>();
            _sounds = null;
            _music = null;
        }

        private void OnEnable()
        {
            _sounds = null;
            _music = null;
        }

        private void OnValidate()
        {
            _sounds = null;
            _music = null;
        }

        private void Index()
        {
            _sounds = new Dictionary<string, Sound>(StringComparer.Ordinal);
            if (sounds != null)
                foreach (Sound s in sounds)
                    if (s != null && !string.IsNullOrEmpty(s.key)) _sounds[s.key] = s;
            _music = new Dictionary<string, AudioClip>(StringComparer.Ordinal);
            if (music != null)
                foreach (Music m in music)
                    if (m != null && !string.IsNullOrEmpty(m.key) && m.clip != null) _music[m.key] = m.clip;
        }
    }
}
