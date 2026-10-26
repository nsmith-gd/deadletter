using System;
using DeadLetter.Core.Maths;

namespace DeadLetter.Core.Camera
{
    /// <summary>
    /// Every number the lane camera rig uses, with the prototype's values. Line numbers are
    /// <c>game/undelivered/index.html</c> at 7b3c123 (port_architecture §0.1, §4.17, §4.18). Plain fields so a Runtime
    /// ScriptableObject can wrap and tune a copy; <see cref="Prototype"/> is the reference.
    /// Positions are in the prototype's axes (camera at +z, see <see cref="Vec3"/>). Rates are the prototype's per-second
    /// <c>k</c> in <c>min(1, dt·k)</c>; Core applies them with <see cref="Damp"/> (exact at 60 Hz, frame-rate independent).
    /// </summary>
    public sealed class CameraConfig
    {
        // ---- Lens (L352–L353, L7658–L7666) ---------------------------------------------------------------------
        /// <summary><c>camera.filmGauge = 36</c> (horizontal film width, mm), L353.</summary>
        public double FilmGauge = 36;
        /// <summary>Side-on framing focal length (mm): <c>applyShots(…, 35)</c>, L7805; <c>widthFit(35, …)</c>, L7666.</summary>
        public double BaseFocal = 35;
        /// <summary>Near / far clip planes, L352 (DL-09–11 raise far to 400 m for the atrium, port_architecture §5).</summary>
        public double Near = 0.05, Far = 60;
        /// <summary>Reference aspect, L352.</summary>
        public double Aspect = 16.0 / 9.0;

        // ---- Rig start (L7647–L7648) ---------------------------------------------------------------------------
        public double StartX = 1.9, StartDistance = 5.2, StartHeight = 1.0, StartLook = 0.8;

        // ---- Lead / look-ahead (L7668) -----------------------------------------------------------------------
        /// <summary><c>lead = facing·(0.6 + 0.35·|vx|)</c>; 0 while holding a trolley/desk/push/item, in transit or exiting.</summary>
        public double LeadBase = 0.6, LeadPerSpeed = 0.35;

        // ---- Follow rates (L7792–L7804) ------------------------------------------------------------------------
        /// <summary>Distance / height / look follow, <c>min(1, dt·1.4)</c>, L7793.</summary>
        public double FollowRate = 1.4;
        /// <summary>Lane x follow, <c>dt·1.6</c>; <see cref="FollowRateXSlow"/> while pace is slow or over the pit, L7803.</summary>
        public double FollowRateX = 1.6, FollowRateXSlow = 0.6;
        /// <summary>Push-in follow, <c>dt·1.5</c>, L7792.</summary>
        public double PushRate = 1.5;

        // ---- Push-in (L7789–L7796) -----------------------------------------------------------------------------
        /// <summary>Push wanted: mantle 1.0, an act (not latch/grab/scan/realise/refuse/quirk/check, not approaching) 0.8,
        /// realise 0.55, transit stage 0 0.4, L7790–L7791.</summary>
        public double PushMantle = 1.0, PushAct = 0.8, PushRealise = 0.55, PushTransit = 0.4;
        /// <summary><c>dist × (1 − 0.22·push)</c>, <c>height − 0.25·push</c>, <c>look − 0.2·push</c>, L7794–L7796.</summary>
        public double PushDistance = 0.22, PushHeight = 0.25, PushLook = 0.2;
        /// <summary>Minimum distance <c>widthFit(35, vd·0.85)</c>, L7794 (only bites in portrait).</summary>
        public double MinFitFraction = 0.85;

        // ---- Height follow (L7795–L7796) ----------------------------------------------------------------------
        /// <summary><c>+0.6·max(0, y − 0.2)</c> on height, <c>+0.5·…</c> on look.</summary>
        public double HeightFollowFrom = 0.2, HeightFollow = 0.6, LookFollow = 0.5;

        // ---- Ending fog (L7799–L7802) --------------------------------------------------------------------------
        /// <summary>Fog → 0.012 over 2.5 s (smoothstepped) while he looks up the well.</summary>
        public double EndingFog = 0.012, EndingFogSeconds = 2.5;

        // ---- Authored shots (L3811–L3836) --------------------------------------------------------------------
        /// <summary>Shot follow <c>min(1, dt·ease·1.6)</c>, L3819.</summary>
        public double ShotFollowScale = 1.6;
        /// <summary>Shot weight in at 1.4, out at 0.8 (smoothstepped), L3822–L3823.</summary>
        public double ShotBlendIn = 1.4, ShotBlendOut = 0.8;
        /// <summary>A moment shot's dt is the cue clock's delta, clamped to [0, 0.5] s, L3815.</summary>
        public double ShotClockMaxDt = 0.5;
        /// <summary>Moment shots' ease (lag &lt; 0.2 s), L3708, L3720, L3751, L3792; directed_moments.md "Keyframes".</summary>
        public double MomentEase = 4;

        // ---- Shake (L3810, L3826–L3832) ----------------------------------------------------------------------
        public double ShakeSeedRate = 37;
        public double ShakeX = 0.035, ShakeXFreq = 1.7;
        public double ShakeY = 0.03, ShakeYFreq = 2.3, ShakeYPhase = 1;
        public double ShakeLookY = 0.02, ShakeLookFreq = 1.1, ShakeLookPhase = 2;
        /// <summary>Shake decays as <c>e^(−5·dt)</c> (already frame-rate exact), L3832.</summary>
        public double ShakeDecay = 5;
        public double ShakeEpsilon = 0.001;

        // ---- Opening (L7649–L7657, L7777–L7786) -------------------------------------------------------------
        /// <summary>The camera starts 1.05 m from the chest at 45° (+0.12 up), drifting to 0.95 m (+0.11) over 120 f.</summary>
        public double OpeningStartDistance = 1.05, OpeningStartRise = 0.12;
        public double OpeningDriftDistance = 0.95, OpeningDriftRise = 0.11;
        public double OpeningDriftFrames = 120, OpeningPullFrames = 180;
        /// <summary>Pull-back end <c>(1.9, 1.0, max(5.2, widthFit(35, 4.6)))</c> looking at (1.9, 0.8, 0), L7648, L7781.</summary>
        public Vec3 OpeningEnd = new Vec3(1.9, 1.0, 5.2);
        public Vec3 OpeningEndTarget = new Vec3(1.9, 0.8, 0);
        public double OpeningFitWidth = 4.6;
        /// <summary>Arc height <c>0.35·sin(π·k)</c>, focal 50 → 35, L7782, L7785.</summary>
        public double OpeningArc = 0.35, OpeningFocalStart = 50, OpeningFocalEnd = 35;
        /// <summary>The opening lasts 480 frames (L8503–L8507).</summary>
        public int OpeningFrames = 480;

        /// <summary>The prototype's values.</summary>
        public static CameraConfig Prototype => new CameraConfig();

        // ---- Lens maths --------------------------------------------------------------------------------------

        /// <summary>
        /// <c>widthFit(focal, width)</c>, L7658–L7661: the distance at which <paramref name="width"/> metres fill the frame.
        /// The prototype scales the horizontal angle (not its tangent) by the aspect in portrait; kept as is.
        /// </summary>
        public double WidthFit(double focal, double width, double aspect)
        {
            double hfov = 2 * Math.Atan(FilmGauge * 0.5 / focal) * (aspect < 1 ? aspect : 1);
            return width / (2 * Math.Tan(hfov / 2));
        }

        /// <summary>
        /// three.js <c>setFocalLength</c> with <c>filmGauge</c>: the <b>vertical</b> field of view in degrees (what Unity's
        /// <c>Camera.fieldOfView</c> and Cinemachine's <c>Lens.FieldOfView</c> take). Film height = gauge / max(aspect, 1).
        /// </summary>
        public double VerticalFovDegrees(double focal, double aspect)
        {
            double filmHeight = FilmGauge / Math.Max(aspect, 1);
            return 2 * Math.Atan(0.5 * filmHeight / focal) * 180.0 / Math.PI;
        }
    }
}
