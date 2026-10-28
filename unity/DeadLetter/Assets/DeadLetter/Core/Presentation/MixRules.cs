using System;
using DeadLetter.Core.Audio;

namespace DeadLetter.Core.Presentation
{
    /// <summary>
    /// The mixer snapshot of each place (U-23, #34). The web build has no per-region mix beyond the ambience map
    /// (audio_map.md, question 4), so every snapshot's trims are 0 dB: the snapshots exist so the director can give a place
    /// its own room (reverb, EQ) in the AudioMixer, and Core decides which one is current. Names are the AudioMixer
    /// snapshots' (<see cref="MixRules.Name"/>).
    /// </summary>
    public enum MixSnapshot
    {
        /// <summary>Region 1, DL-01.</summary>
        Depot,
        /// <summary>Region 2 outside the Ration Hall: DL-02 to DL-04.</summary>
        Halls,
        /// <summary>Region 2's Ration Hall zone, DL-05 (<see cref="LightZone.Ration"/>).</summary>
        RationHall,
        /// <summary>Region 3, DL-06/07.</summary>
        SortingFloor,
        /// <summary>Region 4 below Up Only: DL-08/09.</summary>
        Lower,
        /// <summary>Region 4's Up Only zone, DL-10.</summary>
        UpOnly,
        /// <summary>Region 5, DL-11.</summary>
        RingC,
        /// <summary>Region 6, chapter one.</summary>
        School,
    }

    /// <summary>The mix's decisions: the snapshot per region and zone, the per-group trims, and the duck under a directed moment.</summary>
    public static class MixRules
    {
        /// <summary>Crossing into another place's snapshot (s); a placement snaps (0).</summary>
        public const double SnapshotTransition = 2.0;
        /// <summary>
        /// Under a directed moment's shot (DL-04's kin; <see cref="Cues.MomentDirector.VoicesHeld"/>: the same window that holds
        /// the voices and the distant machinery off) the SFX and the emitters give the cue room: −6 dB and −9 dB, down in
        /// <see cref="DuckDownTau"/>, back with <see cref="DuckUpTau"/> (the music's own duck under a voice: τ 0.4 / 1.5 s,
        /// L941). Tunable; the web build does not duck (a design addition the issue asks for).
        /// </summary>
        public const double MomentSfxDb = -6, MomentAmbienceDb = -9, MomentVoiceDb = 0, MomentMusicDb = 0;
        public const double DuckDownTau = 0.4, DuckUpTau = 1.5;

        public static MixSnapshot SnapshotFor(int region, LightZone zone)
        {
            switch (region)
            {
                case 1: return MixSnapshot.Depot;
                case 2: return zone == LightZone.Ration ? MixSnapshot.RationHall : MixSnapshot.Halls;
                case 3: return MixSnapshot.SortingFloor;
                case 4: return zone == LightZone.UpOnly ? MixSnapshot.UpOnly : MixSnapshot.Lower;
                case 5: return MixSnapshot.RingC;
                default: return MixSnapshot.School;
            }
        }

        /// <summary>The AudioMixer snapshot's name (the enum's, e.g. "RationHall").</summary>
        public static string Name(MixSnapshot s) => Names[(int)s];

        private static readonly string[] Names = { "Depot", "Halls", "RationHall", "SortingFloor", "Lower", "UpOnly", "RingC", "School" };

        /// <summary>A snapshot's trim on group <paramref name="g"/>, dB: 0 everywhere (parity with the web build).</summary>
        public static double TrimDb(MixSnapshot s, AudioGroup g) => 0;

        /// <summary>The duck on group <paramref name="g"/> under a moment, dB.</summary>
        public static double MomentDb(AudioGroup g)
        {
            switch (g)
            {
                case AudioGroup.Sfx: return MomentSfxDb;
                case AudioGroup.Ambience: return MomentAmbienceDb;
                case AudioGroup.Voice: return MomentVoiceDb;
                case AudioGroup.Music: return MomentMusicDb;
                default: return 0;
            }
        }
    }

    /// <summary>
    /// The mix now: the current snapshot (and whether it just changed, for <c>AudioMixerSnapshot.TransitionTo</c>), and each
    /// group's offset in dB (trim + the moment's duck, glided in the linear domain with the duck's τ), which the runtime adds
    /// to the options' level for that group (<see cref="AudioLevels.Decibels"/>). Allocation-free.
    /// </summary>
    public sealed class MixState
    {
        private readonly double[] _gain = new double[AudioLevels.All.Length];
        private bool _placed;

        public MixState()
        {
            for (int i = 0; i < _gain.Length; i++) _gain[i] = 1;
        }

        public MixSnapshot Snapshot { get; private set; }
        /// <summary>The snapshot changed at the last <see cref="Update"/>; <see cref="TransitionSeconds"/> is how long to blend.</summary>
        public bool SnapshotChanged { get; private set; }
        public double TransitionSeconds { get; private set; }
        /// <summary>A directed moment's shot is holding (the duck's target).</summary>
        public bool Ducked { get; private set; }

        /// <summary>A placement: the place's snapshot at once, no duck.</summary>
        public void Place(int region, LightZone zone)
        {
            Snapshot = MixRules.SnapshotFor(region, zone);
            SnapshotChanged = true;
            TransitionSeconds = 0;
            Ducked = false;
            _placed = true;
            for (int g = 0; g < _gain.Length; g++) _gain[g] = FromDb(MixRules.TrimDb(Snapshot, (AudioGroup)g));
        }

        /// <summary>One frame of <paramref name="dt"/> seconds.</summary>
        public void Update(int region, LightZone zone, bool moment, double dt)
        {
            MixSnapshot s = MixRules.SnapshotFor(region, zone);
            SnapshotChanged = s != Snapshot || _placed;
            if (s != Snapshot) TransitionSeconds = _placed ? 0 : MixRules.SnapshotTransition;
            else if (_placed) TransitionSeconds = 0;
            Snapshot = s;
            _placed = false;
            Ducked = moment;
            double tau = moment ? MixRules.DuckDownTau : MixRules.DuckUpTau;
            for (int g = 0; g < _gain.Length; g++)
            {
                var group = (AudioGroup)g;
                double target = FromDb(MixRules.TrimDb(s, group) + (moment ? MixRules.MomentDb(group) : 0));
                _gain[g] = OnePole.Step(_gain[g], target, tau, dt);
            }
        }

        /// <summary>The offset to add to group <paramref name="g"/>'s level, dB (0 = none).</summary>
        public double OffsetDb(AudioGroup g) => AudioLevels.LinearToDecibels(_gain[(int)g]);

        /// <summary>The options' level plus the mix's offset, floored at the mixer's −80 dB.</summary>
        public double Decibels(double optionsDb, AudioGroup g) => Math.Max(AudioLevels.SilentDb, optionsDb + OffsetDb(g));

        private static double FromDb(double db) => Math.Pow(10, db / 20);
    }
}
