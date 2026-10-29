using System;
using DeadLetter.Core.Maths;

namespace DeadLetter.Core.Camera
{
    /// <summary>A framing volume <c>[distance, camera height, look height]</c> (index.html <c>VOL</c>, L7662–L7664).</summary>
    public readonly struct FramingVolume
    {
        public readonly double Distance, Height, Look;
        public FramingVolume(double distance, double height, double look) { Distance = distance; Height = height; Look = look; }

        /// <summary><c>lerp3(a, b, k)</c>, L7665.</summary>
        public static FramingVolume Lerp(FramingVolume a, FramingVolume b, double k) => new FramingVolume(
            a.Distance + (b.Distance - a.Distance) * k, a.Height + (b.Height - a.Height) * k, a.Look + (b.Look - a.Look) * k);

        public override string ToString() => "[" + Distance.ToString("R") + ", " + Height.ToString("R") + ", " + Look.ToString("R") + "]";
    }

    /// <summary>
    /// What <c>frameFor(x)</c> returns (L7773): the target lane centre, the volume and the fog density; and the focal length
    /// (#53; the prototype frames at a fixed <see cref="CameraConfig.BaseFocal"/>).
    /// </summary>
    public struct Frame
    {
        public double Cx;
        public FramingVolume Volume;
        public double Fog;
        /// <summary>Focal length in mm (36 mm gauge): <see cref="CameraConfig.BaseFocal"/> unless a zone sets one.</summary>
        public double Focal;
    }

    /// <summary>
    /// Scalar signals (usually 0..1) that scene rules in Core publish for framing: puzzle state, region gates and timed pans
    /// (e.g. <c>dl02</c>, <c>dl02.reveal</c>, <c>dl02.realised</c>). An unknown name reads 0.
    /// </summary>
    public interface IFramingSignals
    {
        double Get(string name);
    }

    /// <summary>A simple mutable <see cref="IFramingSignals"/>: scene rules <see cref="Set"/> values each step.</summary>
    public sealed class FramingSignalTable : IFramingSignals
    {
        private readonly System.Collections.Generic.Dictionary<string, double> _values =
            new System.Collections.Generic.Dictionary<string, double>(StringComparer.Ordinal);

        public double Get(string name) => name != null && _values.TryGetValue(name, out double v) ? v : 0;
        public FramingSignalTable Set(string name, double value) { _values[name] = value; return this; }
        public void Clear() => _values.Clear();
    }

    /// <summary>
    /// One framing zone (port_architecture §4.17 <c>FramingZone</c>): a region of the lane that overrides the frame, blended
    /// in by a weight. Evaluated exactly as the prototype's cascades in <c>frameFor</c> (L7667–L7774):
    /// <code>
    ///   cx  += (target − cx) · w · CxWeightScale        target = clamp(Pivot + Offset + Gain·(x − Pivot) + LeadK·lead, CxMin, CxMax)
    ///   vol  = lerp3(vol, fit(Volume, FitWidth), w)
    ///   fog += (Fog − fog) · w
    ///   focal += (Focal − focal) · w         (#53: chapter 2's per-zone lenses; the prototype's zones keep 35 mm)
    /// </code>
    /// where <c>w</c> is the product of the optional terms <c>smooth((x − XIn)/XInBlend)</c>,
    /// <c>1 − smooth((x − XOut)/XOutBlend)</c>, <c>smooth((y − YIn)/YInBlend)</c> and <c>signals[Signal]</c>, and is 0 if
    /// <see cref="Gate"/> names a signal that is not &gt; 0. A zone with <see cref="Children"/> first builds its own target
    /// (its cx/volume/fog, or the parent's where it has none), cascades the children over that, and then blends the
    /// result into the parent by its weight: the prototype's nested blocks (<c>tx</c>, <c>v3</c>, <c>v4</c>, <c>v5</c>).
    /// This is data: scene definitions build it from Blender <c>CAM_</c> empties (port_architecture §6).
    /// </summary>
    public sealed class FramingZone
    {
        public string Name;

        // ---- Weight (all optional; NaN / null = term absent) -----------------------------------------------
        public double XIn = double.NaN, XInBlend;
        public double XOut = double.NaN, XOutBlend;
        public double YIn = double.NaN, YInBlend;
        /// <summary>Multiplies the weight by this signal.</summary>
        public string Signal;
        /// <summary>The zone only applies while this signal is &gt; 0 (the prototype's <c>if (k &gt; 0)</c> blocks).</summary>
        public string Gate;

        // ---- Lane centre target --------------------------------------------------------------------------
        public bool HasCx;
        public double CxMin = double.NegativeInfinity, CxMax = double.PositiveInfinity;
        public double LeadK = 1, Pivot, Gain = 1, Offset;
        /// <summary>Extra factor on the weight for cx only (DL-04's among-the-couriers frame uses 0.6, L7689).</summary>
        public double CxWeightScale = 1;
        /// <summary>
        /// Moves <see cref="CxMax"/> by <see cref="CxMaxGain"/> × this signal (null: fixed). DL-17's workshop frame reaches
        /// 2.2 m further right as the stair door opens, <c>clamp(…, 328.2, 336.8 + 2.2·open17)</c>, L5877.
        /// </summary>
        public string CxMaxSignal;
        public double CxMaxGain;

        // ---- Volume and fog --------------------------------------------------------------------------------
        public bool HasVolume;
        public FramingVolume Volume;
        /// <summary><c>fit(vol, width)</c> width in metres; 0 = no fit (DL-01's raw volumes).</summary>
        public double FitWidth;
        /// <summary>Fog density target; NaN = keep.</summary>
        public double Fog = double.NaN;
        /// <summary>
        /// Focal length target in mm, blended like <see cref="Fog"/>; NaN = keep (the base zone: <see cref="CameraConfig.BaseFocal"/>).
        /// <see cref="FitWidth"/> fits the width at this zone's focal length. Not in the prototype: chapter 2's scene docs give
        /// a lens per framing (#53).
        /// </summary>
        public double Focal = double.NaN;

        public FramingZone[] Children;

        /// <summary>
        /// Softens the look-ahead every cx target uses by <c>(1 − LeadSoften·w)</c> (top-level zones only): DL-01's hall
        /// takes 60% of the lead away inside the clamp, <c>clamp(x + lead·(1 − 0.6·inHall), …)</c>, L7672.
        /// </summary>
        public double LeadSoften;

        // ---- Builders (keep scene data short) ----------------------------------------------------------------
        public FramingZone WithCx(double min, double max, double leadK = 1, double offset = 0)
        { HasCx = true; CxMin = min; CxMax = max; LeadK = leadK; Offset = offset; return this; }

        public FramingZone WithVolume(double d, double h, double look, double fitWidth = 0)
        { HasVolume = true; Volume = new FramingVolume(d, h, look); FitWidth = fitWidth; return this; }

        public FramingZone WithCxMaxSignal(string signal, double gain) { CxMaxSignal = signal; CxMaxGain = gain; return this; }

        public FramingZone WithFog(double fog) { Fog = fog; return this; }
        public FramingZone WithFocal(double focal) { Focal = focal; return this; }
        public FramingZone In(double x, double blend) { XIn = x; XInBlend = blend; return this; }
        public FramingZone Out(double x, double blend) { XOut = x; XOutBlend = blend; return this; }
        public FramingZone InY(double y, double blend) { YIn = y; YInBlend = blend; return this; }
        public FramingZone When(string gate) { Gate = gate; return this; }
        public FramingZone Times(string signal) { Signal = signal; return this; }
        public FramingZone With(params FramingZone[] children) { Children = children; return this; }

        public static FramingZone Named(string name) => new FramingZone { Name = name };

        /// <summary>This zone's weight at (x, y). 0..1.</summary>
        public double Weight(double x, double y, IFramingSignals signals)
        {
            if (Gate != null && !(Read(signals, Gate) > 0)) return 0;
            double w = 1;
            if (!double.IsNaN(XIn)) w *= Ramp(x - XIn, XInBlend);
            if (!double.IsNaN(XOut)) w *= 1 - Ramp(x - XOut, XOutBlend);
            if (!double.IsNaN(YIn)) w *= Ramp(y - YIn, YInBlend);
            if (Signal != null) w *= Read(signals, Signal);
            return w;
        }

        /// <summary><c>smooth(d / blend)</c>; a zero blend is a hard step at d &gt; 0.</summary>
        private static double Ramp(double d, double blend) => blend > 0 ? Smooth.Step(d / blend) : (d > 0 ? 1 : 0);

        internal static double Read(IFramingSignals s, string name) => s == null ? 0 : s.Get(name);
    }

    /// <summary>
    /// A framing track: a base frame plus an ordered list of zones, evaluated like <c>frameFor</c>. Pure, no state.
    /// </summary>
    public sealed class FramingTrack
    {
        /// <summary>The frame at the start of the cascade (its zone must have cx, volume and fog).</summary>
        public FramingZone Base;
        public FramingZone[] Zones;

        public FramingTrack(FramingZone baseZone, params FramingZone[] zones)
        {
            if (baseZone == null || !baseZone.HasCx || !baseZone.HasVolume || double.IsNaN(baseZone.Fog))
                throw new ArgumentException("The base zone needs cx, a volume and fog.", nameof(baseZone));
            Base = baseZone;
            Zones = zones ?? new FramingZone[0];
        }

        /// <summary><c>frameFor(x)</c>: the target frame for the player at (x, y) with look-ahead <paramref name="lead"/>.</summary>
        public Frame Evaluate(double x, double y, double lead, IFramingSignals signals, CameraConfig config, double aspect)
        {
            for (int i = 0; i < Zones.Length; i++)
                if (Zones[i].LeadSoften != 0) lead *= 1 - Zones[i].LeadSoften * Zones[i].Weight(x, y, signals);
            double focal = double.IsNaN(Base.Focal) ? config.BaseFocal : Base.Focal;
            var f = new Frame
            {
                Cx = CxTarget(Base, x, lead, signals),
                Volume = Fit(Base, config, aspect, focal),
                Fog = Base.Fog,
                Focal = focal,
            };
            f = Cascade(f, Base.Children, x, y, lead, signals, config, aspect);
            return Cascade(f, Zones, x, y, lead, signals, config, aspect);
        }

        private static Frame Cascade(Frame f, FramingZone[] zones, double x, double y, double lead, IFramingSignals s, CameraConfig c, double aspect)
        {
            if (zones == null) return f;
            for (int i = 0; i < zones.Length; i++)
            {
                FramingZone z = zones[i];
                double w = z.Weight(x, y, s);
                if (!(w > 0)) continue;
                double focal = double.IsNaN(z.Focal) ? f.Focal : z.Focal;
                var t = new Frame
                {
                    Cx = z.HasCx ? CxTarget(z, x, lead, s) : f.Cx,
                    Volume = z.HasVolume ? Fit(z, c, aspect, focal) : f.Volume,
                    Fog = double.IsNaN(z.Fog) ? f.Fog : z.Fog,
                    Focal = focal,
                };
                t = Cascade(t, z.Children, x, y, lead, s, c, aspect);
                f.Cx += (t.Cx - f.Cx) * w * z.CxWeightScale;
                f.Volume = FramingVolume.Lerp(f.Volume, t.Volume, w);
                f.Fog += (t.Fog - f.Fog) * w;
                f.Focal += (t.Focal - f.Focal) * w;
            }
            return f;
        }

        private static double CxTarget(FramingZone z, double x, double lead, IFramingSignals s) =>
            Smooth.Clamp(z.Pivot + z.Offset + z.Gain * (x - z.Pivot) + z.LeadK * lead, z.CxMin,
                z.CxMaxSignal == null ? z.CxMax : z.CxMax + z.CxMaxGain * FramingZone.Read(s, z.CxMaxSignal));

        /// <summary>
        /// <c>fit(vol, width)</c>, L7666: widen the distance so <c>width</c> metres fit the frame at <paramref name="focal"/>
        /// (the prototype's 35 mm unless the zone sets a lens).
        /// </summary>
        private static FramingVolume Fit(FramingZone z, CameraConfig c, double aspect, double focal)
        {
            if (!(z.FitWidth > 0)) return z.Volume;
            return new FramingVolume(Math.Max(z.Volume.Distance, c.WidthFit(focal, z.FitWidth, aspect)), z.Volume.Height, z.Volume.Look);
        }
    }
}
