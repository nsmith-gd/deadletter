using System;

namespace DeadLetter.Core.Presentation
{
    /// <summary>
    /// One one-shot the runtime plays: the SfxBank key (<see cref="Audio.SfxKeys"/>), the AudioSource volume (the
    /// prototype's per-call gain, audio_inventory.md "Gain") and where it is on the lane, which the runtime pans by
    /// (<see cref="Audio.PanLaw"/> through <c>AudioWorld.PanForX</c>; NaN = at D-17).
    /// </summary>
    public readonly struct SfxRequest
    {
        public readonly string Key;
        public readonly double Volume;
        /// <summary>Lane x of the source (NaN: D-17's x).</summary>
        public readonly double X;

        public SfxRequest(string key, double volume, double x) { Key = key; Volume = volume; X = x; }

        public override string ToString() => Key + (Volume != 1 ? "@" + Volume.ToString("0.##", System.Globalization.CultureInfo.InvariantCulture) : "");
    }

    /// <summary>
    /// The one-shots of one Core step, plus the prototype's <c>setTimeout</c>s (a thud 560 ms after the release, a tap
    /// 200 ms after the tube's cough …) held on the game clock until due. Preallocated: queueing allocates nothing;
    /// past the capacity a sound is dropped and counted (<see cref="Dropped"/>).
    /// </summary>
    public sealed class SfxQueue
    {
        private readonly SfxRequest[] _now;
        private readonly SfxRequest[] _later;
        private readonly double[] _due;
        private int _count, _laterCount;

        public SfxQueue(int capacity = 48, int delayedCapacity = 32)
        {
            _now = new SfxRequest[Math.Max(1, capacity)];
            _later = new SfxRequest[Math.Max(1, delayedCapacity)];
            _due = new double[_later.Length];
        }

        /// <summary>Sounds to play now (this step's).</summary>
        public int Count => _count;
        public SfxRequest this[int i] => _now[i];
        /// <summary>Sounds waiting on the clock.</summary>
        public int Pending => _laterCount;
        /// <summary>Sounds lost to a full queue since construction.</summary>
        public int Dropped { get; private set; }

        /// <summary>Starts a step: this step's list empties (delayed sounds stay).</summary>
        public void Clear() => _count = 0;

        /// <summary>Forgets the delayed sounds too (a new world: nothing scheduled in the old one plays into it).</summary>
        public void Reset()
        {
            _count = 0;
            _laterCount = 0;
        }

        public void Play(string key, double volume = 1, double x = double.NaN)
        {
            if (key == null || !(volume > 0)) return;
            if (_count == _now.Length) { Dropped++; return; }
            _now[_count++] = new SfxRequest(key, volume, x);
        }

        /// <summary><c>setTimeout(() =&gt; Sound.x(), delay · 1000)</c>: plays at clock <paramref name="now"/> + <paramref name="delay"/>.</summary>
        public void PlayAfter(double now, double delay, string key, double volume = 1, double x = double.NaN)
        {
            if (key == null || !(volume > 0)) return;
            if (!(delay > 0)) { Play(key, volume, x); return; }
            if (_laterCount == _later.Length) { Dropped++; return; }
            _later[_laterCount] = new SfxRequest(key, volume, x);
            _due[_laterCount] = now + delay;
            _laterCount++;
        }

        /// <summary>Moves every delayed sound due by <paramref name="now"/> into this step's list, in the order queued.</summary>
        public void Release(double now)
        {
            int keep = 0;
            for (int i = 0; i < _laterCount; i++)
            {
                if (_due[i] <= now + 1e-9) { Play(_later[i].Key, _later[i].Volume, _later[i].X); continue; }
                _later[keep] = _later[i];
                _due[keep] = _due[i];
                keep++;
            }
            _laterCount = keep;
        }
    }
}
