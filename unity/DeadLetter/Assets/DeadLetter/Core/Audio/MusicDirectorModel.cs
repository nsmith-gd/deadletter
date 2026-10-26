using System;
using System.Collections.Generic;
using DeadLetter.Core.Cues;

namespace DeadLetter.Core.Audio
{
    public enum MusicLayerKind { Cue, Ambience }

    /// <summary>
    /// One clip playing (or fading) on the music bus: what Runtime binds to an <c>AudioSource</c>. Times are on the music
    /// clock (<see cref="IMusicClock.Now"/>). The source starts at <see cref="StartAt"/> from the clip's top (Unity's clips
    /// are preloaded, so there is no decode offset; loops are trimmed to their loop region at import), its
    /// volume each frame is <see cref="Gain"/> at now × the bus level, and it stops once the layer leaves
    /// <see cref="MusicDirectorModel.Layers"/>.
    /// </summary>
    public sealed class MusicLayer
    {
        public readonly int Id;
        public readonly MusicLayerKind Kind;
        public readonly string Key;
        public readonly MusicTrack Track;
        /// <summary>0 or 1: which of the kind's two AudioSources (cue A/B, ambience A/B) plays it.</summary>
        public readonly int Slot;
        public readonly double StartAt;
        public readonly bool Loop;
        public readonly bool Moment;
        public readonly GainEnvelope Gain = new GainEnvelope(0);

        internal MusicLayer(int id, MusicLayerKind kind, MusicTrack track, int slot, double startAt, double length, bool moment)
        {
            Id = id; Kind = kind; Track = track; Key = track.Key; Slot = slot; StartAt = startAt; Moment = moment;
            Loop = track.IsLoop;
            EndsAt = Loop ? double.PositiveInfinity : startAt + length;
            HandAt = track.HasHandover ? startAt + track.HandoverAt : double.NaN;
        }

        /// <summary>When the clip runs out by itself (∞ for loops).</summary>
        public double EndsAt { get; }
        /// <summary>When the fade-out finishes and the source is stopped (∞ while it is wanted).</summary>
        public double StopAt { get; internal set; } = double.PositiveInfinity;
        /// <summary>The level it was asked for (an ambience's level × scale).</summary>
        public double Level { get; internal set; }
        /// <summary>The cue's handover time on the music clock (NaN = none).</summary>
        public double HandAt { get; }
        /// <summary>The cue has passed its handover bar (<c>c.handed</c>).</summary>
        public bool Handed { get; internal set; }
        /// <summary>A cue queued to follow this one (<c>c.next</c>).</summary>
        public string Next { get; internal set; }
    }

    /// <summary>
    /// The decisions of index.html's <c>Music</c> (L780–L943), with no audio: which cue plays, what is queued, when each
    /// handover falls on the music clock, which ambience loop is wanted and how everything fades. Runtime's
    /// <c>MusicDirector</c> plays <see cref="Layers"/> on two AudioSource pairs with <c>PlayScheduled</c>.
    /// <list type="bullet">
    /// <item><b>Cues.</b> One at a time. A new cue fades the old one out over 1.5 s (1 s for a moment) and fades in
    /// linearly over its fade-in (1.2 s by default) to its <c>LEVEL</c> (L861–L867). A directed moment starts at full
    /// level 0.1 s ahead, and that start is its cue clock's zero (L876).</item>
    /// <item><b>Handovers.</b> At <c>HAND[cue][0]</c> s the scene's loop comes in from its loop start under the cue's
    /// tail (fade-in 1.5 s), or the queued cue starts (L877–L882).</item>
    /// <item><b>Ambience.</b> Hidden while a cue that has not handed over plays (out over 1.5 s, or 4 s / 2 s by the cue's
    /// intro bars, 1 s for a moment); changes crossfade (4 s in, τ = out/4) (L832–L847).</item>
    /// <item><b>Bus.</b> enabled × (paused ? 0.45 : 1) × duck (0.4 under a voice), τ 0.3 / 0.4 down / 1.5 up (L818,
    /// L931–L941).</item>
    /// </list>
    /// Deterministic: the same calls at the same clock times give the same layers.
    /// </summary>
    public sealed class MusicDirectorModel
    {
        public const double DefaultFadeIn = 1.2;          // L861
        public const double StopFade = 1.5;               // L886
        public const double MomentFade = 1.0;             // L863, L841
        public const double HandoverFadeIn = 1.5;         // L880
        public const double AmbienceCrossfade = 4.0;      // L807
        public const double AmbienceLevelTau = 1.0;       // L837
        public const double IntroBarsFade = 4.0, NoIntroFade = 2.0;   // L841
        public const double BedFadeIn = 6.0, BedFadeOut = 3.0;        // L930
        public const double MinFade = 0.05;               // L846, L867
        public const double StopTail = 0.2, AmbienceTail = 0.3;       // L890, L842 (source freed after the fade)
        public const double PausedLevel = 0.45, DuckLevel = 0.4;      // L818, L941
        public const double BusTau = 0.3, DuckDownTau = 0.4, DuckUpTau = 1.5;   // L931–L941
        public const double Floor = 0.0001;               // L846, L867

        private readonly Dictionary<string, double> _lengths = new Dictionary<string, double>();
        private readonly List<MusicLayer> _layers = new List<MusicLayer>();
        private readonly List<KeyValuePair<double, string>> _log = new List<KeyValuePair<double, string>>();
        private readonly List<Pending> _pending = new List<Pending>();
        private readonly GainEnvelope _bus = new GainEnvelope(1);
        private int _nextId = 1;
        private MusicLayer _cue, _amb;
        private string _want;
        private double _scale = 1, _fadeIn = AmbienceCrossfade, _fadeOut = AmbienceCrossfade;
        private bool _enabled = true, _paused, _ducked;

        private struct Pending
        {
            public double At, FadeIn;
            public string Name;
        }

        public IReadOnlyList<MusicLayer> Layers => _layers;

        /// <summary><c>Music.playing()</c>: the cue playing, or null.</summary>
        public string Playing => _cue?.Key;
        public MusicLayer CurrentCue => _cue;
        public MusicLayer CurrentAmbience => _amb;
        /// <summary><c>Music.ambienceName()</c>.</summary>
        public string AmbienceName => _amb?.Key;
        /// <summary><c>Music.ambienceWant()</c>.</summary>
        public string AmbienceWant => _want;
        public double AmbienceScale => _scale;
        public bool Paused => _paused;
        public bool InMoment => _cue != null && _cue.Moment;
        /// <summary>Layers dropped because both of their kind's sources were busy (a third overlapping fade).</summary>
        public int Evicted { get; private set; }

        /// <summary>
        /// The <c>note()</c> log (L830): (time, "cue|ambience") each time either changes. For replay tests.
        /// </summary>
        public IReadOnlyList<KeyValuePair<double, string>> Log => _log;

        /// <summary>Use the real clip's length for <paramref name="key"/> (Runtime passes <c>AudioClip.length</c>).</summary>
        public void SetLength(string key, double seconds)
        {
            if (key != null && seconds > 0) _lengths[key] = seconds;
        }

        /// <summary>The bus gain at <paramref name="now"/> (multiply every music source's volume by it).</summary>
        public double BusLevel(double now) => _bus.ValueAt(now);

        /// <summary>Seconds into the playing cue as scheduled (no latency), or null.</summary>
        public double? CueTime(double now) => _cue == null ? (double?)null : Math.Max(0, now - _cue.StartAt);

        // ---- Cues ----------------------------------------------------------------------------------------------------

        /// <summary><c>Music.play(name, fadeIn)</c>, L861–L884.</summary>
        public void Play(string name, double now, double fadeIn = DefaultFadeIn) => PlayCue(name, now, fadeIn, false);

        /// <summary>
        /// <c>Music.moment(name)</c>, L906–L911: drops any queue, takes the cue and the ambience out over 1 s and starts the
        /// moment's cue from its top <see cref="CueClock.ScheduleLeadIn"/> ahead at full level. Returns that start on the
        /// music clock, for <see cref="CueClock.Scheduled"/>.
        /// </summary>
        public double Moment(string name, double now)
        {
            if (_cue != null) _cue.Next = null;
            return PlayCue(name, now, 0, true).StartAt;
        }

        /// <summary>
        /// The cue could not start (no clip): <c>if (cue === c) { cue = null; updateBed(); }</c>, L871. For a moment, call
        /// <see cref="CueClock.MusicFailed"/> too.
        /// </summary>
        public void CueFailed(string name, double now)
        {
            if (_cue == null || _cue.Key != name) return;
            _layers.Remove(_cue);
            _cue = null;
            UpdateBed(now, _fadeIn);
        }

        /// <summary><c>Music.stop(sec)</c>, L885–L891.</summary>
        public void Stop(double now, double seconds = StopFade) => StopCue(now, seconds, false);

        /// <summary><c>Music.queue(name)</c>, L903: after the cue playing (at its handover, or its end), or now.</summary>
        public void Queue(string name, double now)
        {
            if (_cue != null) _cue.Next = name;
            else Play(name, now);
        }

        /// <summary>A play after a delay (<c>setTimeout(() =&gt; Music.play(…), ms)</c>, as finish() does, L8188).</summary>
        public void PlayAfter(string name, double now, double delay, double fadeIn = DefaultFadeIn)
        {
            _pending.Add(new Pending { At = now + Math.Max(0, delay), Name = name, FadeIn = fadeIn });
        }

        // ---- Ambience ------------------------------------------------------------------------------------------------

        /// <summary><c>Music.ambience(name, {fadeIn, fadeOut, scale})</c>, L898–L899. Null = no loop.</summary>
        public void Ambience(string name, double now, double fadeIn = AmbienceCrossfade, double fadeOut = AmbienceCrossfade, double scale = 1)
        {
            if (name == _want && scale == _scale) return;
            _want = name; _scale = scale; _fadeIn = fadeIn; _fadeOut = fadeOut;
            UpdateBed(now, _fadeIn);
        }

        /// <summary><c>Music.bed(on)</c>, L930: chapter one's old bed, 6 s in, 3 s out.</summary>
        public void Bed(bool on, double now) => Ambience(on ? "bed" : null, now, BedFadeIn, BedFadeOut);

        // ---- Bus -----------------------------------------------------------------------------------------------------

        /// <summary><c>Music.setEnabled</c>, L931.</summary>
        public void SetEnabled(bool on, double now) { _enabled = on; _bus.TargetAt(now, BusTarget, BusTau); }

        /// <summary>
        /// <c>Music.setPaused</c>, L932–L936: the music steps down to 0.45. In a moment, Runtime also pauses the sources and
        /// the music clock (the score stops where it is, so the shot and the music pick up together).
        /// </summary>
        public void SetPaused(bool on, double now) { _paused = on; _bus.TargetAt(now, BusTarget, BusTau); }

        /// <summary><c>Music.duck</c>, L941: 0.4 under a voice, τ 0.4 down and 1.5 back.</summary>
        public void Duck(bool on, double now)
        {
            _ducked = on;
            _bus.TargetAt(now, BusTarget, on ? DuckDownTau : DuckUpTau);
        }

        private double BusTarget => _enabled ? (_paused ? PausedLevel : 1.0) * (_ducked ? DuckLevel : 1.0) : 0.0;

        // ---- Clock ---------------------------------------------------------------------------------------------------

        /// <summary>
        /// Runs the timers (handovers, cue ends, delayed plays) due by <paramref name="horizon"/> (≥ now; Runtime looks a
        /// little ahead so a handover or a queued cue can be scheduled sample-accurately), in time order, then drops the
        /// layers that have stopped by <paramref name="now"/>.
        /// </summary>
        public void Update(double now, double horizon = double.NaN)
        {
            if (double.IsNaN(horizon) || horizon < now) horizon = now;
            for (int guard = 0; guard < 64; guard++)
            {
                double best = double.PositiveInfinity;
                int which = 0, pendingIndex = -1;
                if (_cue != null)
                {
                    if (!_cue.Handed && !double.IsNaN(_cue.HandAt) && _cue.HandAt < best) { best = _cue.HandAt; which = 1; }
                    if (_cue.EndsAt < best) { best = _cue.EndsAt; which = 2; }
                }
                for (int i = 0; i < _pending.Count; i++)
                    if (_pending[i].At < best) { best = _pending[i].At; which = 3; pendingIndex = i; }
                if (which == 0 || best > horizon) break;

                if (which == 1)
                {
                    // L877–L882: the handover bar.
                    MusicLayer c = _cue;
                    c.Handed = true;
                    if (c.Next != null) { string n = c.Next; c.Next = null; PlayCue(n, best, DefaultFadeIn, false); }
                    else UpdateBed(best, HandoverFadeIn);
                    Note(best);
                }
                else if (which == 2)
                {
                    // L883: onended. A queued cue follows with no ambience between.
                    MusicLayer c = _cue;
                    _cue = null;
                    c.StopAt = Math.Min(c.StopAt, c.EndsAt);
                    if (c.Next != null) PlayCue(c.Next, best, DefaultFadeIn, false);
                    else UpdateBed(best, _fadeIn);
                }
                else
                {
                    Pending p = _pending[pendingIndex];
                    _pending.RemoveAt(pendingIndex);
                    PlayCue(p.Name, p.At, p.FadeIn, false);
                }
            }
            for (int i = _layers.Count - 1; i >= 0; i--)
            {
                MusicLayer l = _layers[i];
                if (l == _cue || l == _amb) continue;
                if (l.StopAt <= now || l.EndsAt <= now) _layers.RemoveAt(i);
            }
        }

        // ---- Internals -----------------------------------------------------------------------------------------------

        private MusicLayer PlayCue(string name, double now, double fadeIn, bool moment)
        {
            MusicTrack track = MusicCatalog.Find(name);
            if (track == null || track.IsLoop) throw new ArgumentException("Not a music cue: " + name, nameof(name));
            StopCue(now, moment ? MomentFade : StopFade, true);   // the ambience stays hidden: a cue follows at once
            double startAt = moment ? now + CueClock.ScheduleLeadIn : now;
            MusicLayer c = NewLayer(MusicLayerKind.Cue, track, startAt, LengthOf(track), moment);
            c.Level = track.Level;
            if (moment) c.Gain.Set(now, track.Level);
            else c.Gain.Ramp(now, Floor, track.Level, Math.Max(MinFade, fadeIn));
            _cue = c;
            UpdateBed(now, _fadeIn);
            return c;
        }

        private void StopCue(double now, double seconds, bool quiet)
        {
            if (_cue == null) return;
            MusicLayer c = _cue;
            _cue = null;
            c.Gain.TargetAt(now, 0, seconds / 4);
            c.StopAt = Math.Min(c.EndsAt, now + seconds + StopTail);
            if (!quiet) UpdateBed(now, _fadeIn);
        }

        /// <summary><c>updateBed(fadeIn)</c>, L832–L847.</summary>
        private void UpdateBed(double now, double fadeIn)
        {
            string name = _cue != null && !_cue.Handed ? null : _want;
            MusicLayer cur = _amb;
            if (cur != null && cur.Key == name)
            {
                double lv = cur.Track.Level * _scale;
                if (Math.Abs(cur.Level - lv) > 1e-3) { cur.Level = lv; cur.Gain.TargetAt(now, lv, AmbienceLevelTau); }
                Note(now);
                return;
            }
            if (cur != null)
            {
                double outSec = _cue != null && !_cue.Handed
                    ? (_cue.Moment ? MomentFade : _cue.Track.HasHandover ? (_cue.Track.IntroBars ? IntroBarsFade : NoIntroFade) : StopFade)
                    : _fadeOut;
                cur.Gain.TargetAt(now, 0, outSec / 4);
                cur.StopAt = now + outSec + AmbienceTail;
                _amb = null;
            }
            if (name != null)
            {
                MusicTrack track = MusicCatalog.Find(name);
                if (track == null || !track.IsLoop) throw new ArgumentException("Not a music loop: " + name);
                MusicLayer a = NewLayer(MusicLayerKind.Ambience, track, now, double.PositiveInfinity, false);
                a.Level = track.Level * _scale;
                a.Gain.Ramp(now, Floor, a.Level, Math.Max(MinFade, fadeIn));
                _amb = a;
            }
            Note(now);
        }

        private MusicLayer NewLayer(MusicLayerKind kind, MusicTrack track, double startAt, double length, bool moment)
        {
            bool used0 = false, used1 = false;
            MusicLayer oldest = null;
            for (int i = 0; i < _layers.Count; i++)
            {
                MusicLayer l = _layers[i];
                if (l.Kind != kind) continue;
                if (l.Slot == 0) used0 = true; else used1 = true;
                if (oldest == null || l.StopAt < oldest.StopAt || (l.StopAt == oldest.StopAt && l.Id < oldest.Id)) oldest = l;
            }
            int slot;
            if (!used0) slot = 0;
            else if (!used1) slot = 1;
            else
            {
                // Both sources still sound (a third overlapping fade): cut the one that would stop first.
                _layers.Remove(oldest);
                Evicted++;
                slot = oldest.Slot;
            }
            var layer = new MusicLayer(_nextId++, kind, track, slot, startAt, length, moment);
            _layers.Add(layer);
            return layer;
        }

        private double LengthOf(MusicTrack t) => _lengths.TryGetValue(t.Key, out double s) ? s : t.ClipLength;

        private void Note(double now)
        {
            string k = (_cue != null ? _cue.Key : "-") + "|" + (_amb != null ? _amb.Key : "-");
            if (_log.Count > 0 && _log[_log.Count - 1].Value == k) return;
            _log.Add(new KeyValuePair<double, string>(Math.Round(now, 3), k));
            if (_log.Count > 400) _log.RemoveAt(0);
        }
    }
}
