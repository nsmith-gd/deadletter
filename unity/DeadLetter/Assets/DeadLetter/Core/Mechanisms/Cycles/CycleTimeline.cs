using System;

namespace DeadLetter.Core.Mechanisms.Cycles
{
    /// <summary>A named moment on the timeline (a chime, a bowl set, a lamp).</summary>
    public sealed class CycleCue
    {
        public readonly string Name;
        public readonly double At;
        public CycleCue(string name, double at) { Name = name; At = at; }
    }

    /// <summary>
    /// One output of a cycle (a step, a table, a sun) as keys of (time, value), linear between keys. Repeat a time to
    /// make a jump: the later key holds from that time on (keys (1, 0), (1, 1), (5.6, 1), (5.6, 0) are 1 on [1, 5.6),
    /// as <c>t &gt;= t0 &amp;&amp; t &lt; t1</c>, L5422).
    /// </summary>
    public sealed class CycleTrack
    {
        public readonly string Name;
        public readonly double[] Times, Values;
        /// <summary>0: the value is the timeline's value. &gt; 0: it moves toward it at most this fast (units/s).</summary>
        public double Slew;
        /// <summary>Its value while the cycle is off.</summary>
        public double Rest;
        /// <summary>How fast it goes home when the cycle stops (units/s); 0 = at once.</summary>
        public double ReturnRate;
        /// <summary>Threshold for <see cref="CycleClockEvent.TrackUp"/>/<see cref="CycleClockEvent.TrackDown"/>; NaN = none.</summary>
        public double Threshold = double.NaN;
        /// <summary><see cref="CycleClock.IsOut"/> when the value is at least this (DL-13: a step is solid from 0.95, L5243).</summary>
        public double OutAt = double.NaN;

        public CycleTrack(string name, double[] times, double[] values)
        {
            if (times == null || values == null || times.Length == 0 || times.Length != values.Length)
                throw new ArgumentException("A track needs as many values as times.");
            for (int i = 1; i < times.Length; i++)
                if (times[i] < times[i - 1]) throw new ArgumentException("Track '" + name + "': times must not decrease.");
            Name = name; Times = times; Values = values;
        }

        /// <summary>Keys as alternating time, value.</summary>
        public static CycleTrack Keys(string name, params double[] timeValue)
        {
            int n = timeValue.Length / 2;
            var t = new double[n];
            var v = new double[n];
            for (int i = 0; i < n; i++) { t[i] = timeValue[2 * i]; v[i] = timeValue[2 * i + 1]; }
            return new CycleTrack(name, t, v);
        }

        /// <summary>1 on [from, to), 0 elsewhere.</summary>
        public static CycleTrack Window(string name, double from, double to)
            => new CycleTrack(name, new[] { from, from, to, to }, new[] { 0.0, 1, 1, 0 });

        /// <summary>The timeline's value at phase <paramref name="t"/>.</summary>
        public double At(double t)
        {
            if (t < Times[0]) return Values[0];
            for (int i = 0; i < Times.Length - 1; i++)
            {
                double t1 = Times[i + 1];
                if (t < t1)
                {
                    double t0 = Times[i], v0 = Values[i];
                    return v0 + (Values[i + 1] - v0) * (t - t0) / (t1 - t0);
                }
            }
            return Values[Values.Length - 1];
        }
    }
}
