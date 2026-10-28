using DeadLetter.Core.Audio;
using DeadLetter.Core.Presentation;
using DeadLetter.Runtime.Settings;
using UnityEngine;
using UnityEngine.Audio;

namespace DeadLetter.Runtime.Audio
{
    /// <summary>
    /// The mix per place and under a directed moment (U-23, #34) on the U-16 mixer. Core's <see cref="MixState"/> decides the
    /// snapshot (<see cref="MixRules.SnapshotFor"/>: Depot, Halls, RationHall, SortingFloor …) and each group's offset (the
    /// moment duck); this only blends to the snapshot (<c>AudioMixerSnapshot.TransitionTo</c>) and writes each group's level
    /// = the options' (<see cref="AudioLevels.Decibels"/>) + the offset. While it runs it is the only writer of the group
    /// levels (<see cref="SettingsStore"/> defers to it), so the options and the duck never fight.
    /// <para>The snapshots are authored by hand in the AudioMixer (Unity has no API to make them): name each like its
    /// <see cref="MixSnapshot"/>. A missing one is skipped. Exposed parameters are outside the snapshots' control, so a
    /// snapshot carries what the director gives a place (reverb, EQ), never the volumes.</para>
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class AudioMixDirector : MonoBehaviour
    {
        [Tooltip("The U-16 mixer (exposed: Master, Music, SFX, Voice, Ambience).")]
        [SerializeField] private AudioMixer mixer;
        [Tooltip("One per place, named as MixSnapshot (Depot, Halls, RationHall, SortingFloor, Lower, UpOnly, RingC, School).")]
        [SerializeField] private AudioMixerSnapshot[] snapshots = new AudioMixerSnapshot[0];

        private readonly float[] _written = new float[AudioLevels.All.Length];
        private MixState _state;

        /// <summary>The running director (the last one enabled).</summary>
        public static AudioMixDirector Current { get; private set; }

        public AudioMixer Mixer => mixer;
        /// <summary>Bound to Core: it writes the levels every frame.</summary>
        public bool Driving => _state != null && mixer != null && isActiveAndEnabled;

        public void Bind(MixState state)
        {
            _state = state;
            for (int i = 0; i < _written.Length; i++) _written[i] = float.NaN;
        }

        /// <summary>Per frame after Core's <see cref="MixState.Update"/>: the snapshot's blend, then every group's level.</summary>
        public void Present()
        {
            if (!Driving) return;
            if (_state.SnapshotChanged)
            {
                AudioMixerSnapshot s = Find(MixRules.Name(_state.Snapshot));
                if (s != null) s.TransitionTo((float)_state.TransitionSeconds);
            }
            Refresh(force: false);
        }

        /// <summary>Writes every group's level (the options changed: <paramref name="force"/>).</summary>
        public void Refresh(bool force = true)
        {
            if (mixer == null) return;
            Core.Save.Settings options = SettingsStore.Current;
            for (int i = 0; i < AudioLevels.All.Length; i++)
            {
                AudioGroup g = AudioLevels.All[i];
                double baseDb = AudioLevels.Decibels(options, g);
                float db = (float)(_state != null ? _state.Decibels(baseDb, g) : baseDb);
                if (!force && Mathf.Abs(db - _written[i]) < 0.01f) continue;
                _written[i] = db;
                mixer.SetFloat(AudioLevels.ExposedParameter(g), db);
            }
        }

        private AudioMixerSnapshot Find(string name)
        {
            for (int i = 0; i < snapshots.Length; i++) if (snapshots[i] != null && snapshots[i].name == name) return snapshots[i];
            return null;
        }

        private void OnEnable() => Current = this;

        private void OnDisable()
        {
            if (Current == this) Current = null;
        }
    }
}
