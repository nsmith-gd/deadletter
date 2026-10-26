using System;
using DeadLetter.Core.Maths;

namespace DeadLetter.Core.Camera
{
    /// <summary>A camera keyframe <c>{ t, pos, look, focal }</c> (index.html <c>keyShot</c>, L959–L964).</summary>
    public readonly struct ShotKey
    {
        public readonly double T;
        public readonly Vec3 Position, Look;
        public readonly double Focal;
        public ShotKey(double t, Vec3 position, Vec3 look, double focal) { T = t; Position = position; Look = look; Focal = focal; }
    }

    /// <summary>
    /// The four directed moments' camera beats on their cue clocks (port_architecture §4.18; docs/directed_moments.md), in
    /// the prototype's axes. Each returns the <see cref="ShotRequest"/> for <see cref="CameraRig"/> at moment time
    /// <c>t</c>, with <c>Clock = t</c> so the rig follows the cue clock's delta. The game decides whether a moment shot is
    /// live (<c>MomentDirector.ShotTime</c> plus the act checks of <c>currentShot</c>, L3702–L3721, L3744, L3787).
    /// </summary>
    public static class MomentShots
    {
        public const double Ease = 4;

        // Scene constants (index.html), OFF4 = 42, OFF5 = 54 (L274).
        /// <summary><c>ATRIUM4</c>, L3019: where the city's wide view looks.</summary>
        public static readonly Vec3 Atrium = new Vec3(42 + 92, 22, -150);
        /// <summary>The vista's first look, <c>(OFF4 + 95, 12, −160)</c>, L3791.</summary>
        public static readonly Vec3 VistaLook0 = new Vec3(42 + 95, 12, -160);
        /// <summary><c>UO.car.mid</c>, L3459; <c>DECK</c>, L3007.</summary>
        public const double CarMid = 54 + 70.95, Deck = 1.6;
        /// <summary><c>END5.cam</c>, <c>END5.win</c>, L3465–L3466.</summary>
        public static readonly Vec3 EndCam = new Vec3(172.4, 0.6, 0.8);
        public static readonly Vec3 EndWindow = new Vec3(173.6, 24.0, -10.3);
        /// <summary>The ring C cold light (<c>RINGC_LIGHT</c>, L4610): up from 9.5, full at 12, off at 20 (or when he is
        /// freed), intensity 2.6 (L4620).</summary>
        public const double RingCLightFrom = 9.5, RingCLightFull = 12.0, RingCLightOff = 20, RingCLightMax = 2.6, RingCLightFade = 1.5;

        /// <summary><c>keyShot(keys, t)</c>: smoothstep between neighbouring keys; a hold is two equal keys.</summary>
        public static ShotKey Evaluate(ShotKey[] keys, double t)
        {
            if (keys == null || keys.Length < 2) throw new ArgumentException("Need at least two keys.", nameof(keys));
            int i = 0;
            while (i < keys.Length - 2 && t >= keys[i + 1].T) i++;
            ShotKey a = keys[i], b = keys[i + 1];
            double k = Smooth.Step((t - a.T) / Math.Max(1e-3, b.T - a.T));
            return new ShotKey(t, Vec3.Lerp(a.Position, b.Position, k), Vec3.Lerp(a.Look, b.Look, k), a.Focal + (b.Focal - a.Focal) * k);
        }

        /// <summary><c>REALISE_KEYS(X)</c>, L3689–L3692: over the shoulder; round to his face 3.7–5.3; held close to 9; the
        /// pull back and up to the wide at 15 (the peak); held to 21.</summary>
        public static ShotKey[] KinKeys(double x) => new[]
        {
            new ShotKey(0, new Vec3(x + 1.7, 0.42, 1.0), new Vec3(x - 0.1, 0.6, -1.4), 30),
            new ShotKey(3.7, new Vec3(x + 1.7, 0.42, 1.0), new Vec3(x - 0.1, 0.6, -1.4), 30),
            new ShotKey(5.3, new Vec3(x + 0.9, 0.62, 1.3), new Vec3(x, 0.5, 0), 50),
            new ShotKey(9.0, new Vec3(x + 0.85, 0.64, 1.36), new Vec3(x, 0.5, 0), 50),
            new ShotKey(15, new Vec3(x - 0.7, 3.6, 4.6), new Vec3(x + 3.2, 0.0, -1.4), 22),
            new ShotKey(21, new Vec3(x - 0.75, 3.62, 4.65), new Vec3(x + 3.2, 0.0, -1.4), 22),
        };

        /// <summary>DL-04 <c>realise</c>, L3707–L3708.</summary>
        public static ShotRequest Kin(double x, double t)
        {
            ShotKey k = Evaluate(KinKeys(x), t);
            return new ShotRequest("realise", k.Position, k.Look, k.Focal, Ease, t);
        }

        /// <summary>DL-09 <c>vista</c>, L3789–L3792: on his shoulder 0–2, the crane up and back 2–10 onto the widest frame.</summary>
        public static ShotRequest Refuge(double x, double y, double t)
        {
            double k = Smooth.Step((t - 2.0) / 8.0);
            Vec3 pos = Vec3.Lerp(new Vec3(x + 0.45, y + 0.95, 1.35), new Vec3(x + 3.2, y + 7.9, 8.5), k);
            Vec3 look = Vec3.Lerp(VistaLook0, Atrium, k);
            return new ShotRequest("vista", pos, look, 32 - 8 * k, Ease, t);
        }

        /// <summary>DL-10 <c>car10</c> → <c>ringc10</c>, L3717–L3720: up at the car leaving (0–5.5), the rise over his shoulder
        /// down ring C's lane (6–9), held. <paramref name="carRise"/> is the car's travel <c>uo.d</c>.</summary>
        public static ShotRequest RingC(double x, double y, double t, double carRise)
        {
            double k = Smooth.Step((t - 6.0) / 3.0);
            Vec3 carPos = new Vec3(x + 0.9, y + 0.35, 1.5), carLook = new Vec3(CarMid, Deck + 1.3 + carRise, -0.9);
            Vec3 lanePos = new Vec3(x - 0.2, 3.3, 3.6), laneLook = new Vec3(x + 7.5, 0.2, -1.4);
            return new ShotRequest(k > 0.5 ? "ringc10" : "car10", Vec3.Lerp(carPos, lanePos, k), Vec3.Lerp(carLook, laneLook, k), 24 + (22 - 24) * k, Ease, t);
        }

        /// <summary>The ending's look up the well, L3749–L3751: still 0–1.5, the rise 1.5–6.5 onto the lit window (peak), held
        /// to 11.5, back down by 13.5. <paramref name="clock"/> is the cue time (null when the ending runs on its own timer).</summary>
        public static ShotRequest Window(double x, double y, double t, double? clock)
        {
            double up = Smooth.Step((t - 1.5) / 5.0) * (1 - Smooth.Step((t - 11.5) / 2.0));
            Vec3 look = Vec3.Lerp(new Vec3(x + 0.3, y + 0.7, -0.4), EndWindow, up);
            return new ShotRequest("ending", EndCam + new Vec3(0, 1.6 * up, 0), look, 28 + 10 * up, Ease, clock);
        }

        /// <summary>The ring C cold light's intensity at cue time <paramref name="t"/> (L4619–L4620); <paramref name="freedAt"/>
        /// is when control came back (it switches off then, if before 20).</summary>
        public static double RingCLight(double? t, double? freedAt)
        {
            if (t == null) return 0;
            double off = Math.Min(freedAt ?? RingCLightOff, RingCLightOff);
            return RingCLightMax * Smooth.Step((t.Value - RingCLightFrom) / (RingCLightFull - RingCLightFrom)) * (1 - Smooth.Step((t.Value - off) / RingCLightFade));
        }
    }
}
