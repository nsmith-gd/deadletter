using System;
using DeadLetter.Core.Maths;

namespace DeadLetter.Core.Camera
{
    /// <summary>How hard the rig pushes in (L7789–L7791). The value comes from <see cref="CameraConfig"/>.</summary>
    public enum CameraPush
    {
        None,
        /// <summary>Transit stage 0 (0.4).</summary>
        Transit,
        /// <summary>The <c>realise</c> act (0.55).</summary>
        Realise,
        /// <summary>Any act except latch/grab/scan/realise/refuse/quirk/check, once past its approach (0.8).</summary>
        Act,
        /// <summary>Mantling (1.0).</summary>
        Mantle,
    }

    /// <summary>
    /// An authored shot the camera leaves the side view for (one entry of <c>currentShot</c>, L3698–L3809).
    /// <see cref="Clock"/> is set for directed moments: the shot then follows the cue clock's delta, not the step's.
    /// </summary>
    public struct ShotRequest
    {
        public string Name;
        public Vec3 Position;
        public Vec3 Look;
        public double Focal;
        public double Ease;
        public double? Clock;

        public ShotRequest(string name, Vec3 position, Vec3 look, double focal, double ease, double? clock = null)
        { Name = name; Position = position; Look = look; Focal = focal; Ease = ease; Clock = clock; }
    }

    /// <summary>One step's inputs to the rig, read from Core state (player, acts, scene rules).</summary>
    public struct CameraRigInput
    {
        public double X, Y, Vx;
        public int Facing;
        /// <summary>No look-ahead: holding a trolley/desk/push/item, in a transit, or exiting (L7668).</summary>
        public bool NoLead;
        public CameraPush Push;
        /// <summary><c>paceSlow()</c> or DL-06's pit reveal: the camera slows with him (L7803).</summary>
        public bool SlowFollow;
        /// <summary>The ending's look up the well (region 5, exit phase past <c>out</c>): fog clears (L7799).</summary>
        public bool LookingUpWell;
        /// <summary>Viewport aspect (w/h). 0 = the config's reference aspect.</summary>
        public double Aspect;
        public IFramingSignals Signals;
        /// <summary>The authored shot wanted this step (from a shot selector or <see cref="MomentShots"/>), or null.</summary>
        public ShotRequest? Shot;
    }

    /// <summary>The rig's output for one step, in the prototype's axes (use <see cref="Vec3.ToUnity"/> at the edge).</summary>
    public struct CameraPose
    {
        public Vec3 Position;
        public Vec3 Look;
        /// <summary>Focal length in mm on a 36 mm film gauge.</summary>
        public double Focal;
        /// <summary>Exponential-squared fog density (three.js FogExp2 = Unity ExponentialSquared).</summary>
        public double Fog;
        /// <summary>The authored shot in play (null on the side view) and its smoothstepped weight.</summary>
        public string ShotName;
        public double ShotWeight;
    }

    /// <summary>
    /// The lane camera (index.html <c>cam</c>, <c>updateCamera</c> L7776–L7806, <c>applyShots</c> L3811–L3836): one
    /// continuous side-on camera that follows a <see cref="FramingTrack"/> with exponential lag, pushes in for acts, and
    /// blends to and from authored shots. Deterministic: same config, track and input sequence → same poses.
    /// <para>Deviation (port_architecture §3.1): every <c>min(1, dt·k)</c> easing is <see cref="Damp"/>, exact at 60 Hz and
    /// frame-rate independent (the prototype lags differently at 30 and 144 fps).</para>
    /// </summary>
    public sealed class CameraRig
    {
        private readonly CameraConfig _c;
        private readonly FramingTrack _track;

        // cam (L7647)
        private double _x, _dist, _y, _look, _push, _fogK;
        // shotCam (L3697)
        private bool _shotLive;
        private Vec3 _shotPos, _shotLook;
        private double _shotFocal, _shotW, _shake, _seed;
        private double? _shotClock;
        private Vec3 _lastPosition;
        private string _shotName;

        public CameraRig(CameraConfig config, FramingTrack track)
        {
            _c = config ?? throw new ArgumentNullException(nameof(config));
            _track = track ?? throw new ArgumentNullException(nameof(track));
            Reset();
        }

        public CameraConfig Config => _c;
        public FramingTrack Track => _track;
        public CameraPose Pose { get; private set; }
        public double X => _x;
        public double Distance => _dist;
        public double Height => _y;
        public double LookHeight => _look;
        public double PushAmount => _push;
        public double ShotWeightRaw => _shotW;
        public double ShakeAmount => _shake;

        /// <summary>Back to <c>cam</c>'s initial values (L7647), no shot, no shake.</summary>
        public void Reset()
        {
            _x = _c.StartX; _dist = _c.StartDistance; _y = _c.StartHeight; _look = _c.StartLook;
            _push = 0; _fogK = 0;
            _shotLive = false; _shotW = 0; _shake = 0; _seed = 0; _shotClock = null; _shotName = null;
            _shotFocal = _c.BaseFocal;
            _lastPosition = new Vec3(_x, _y, _dist);
            _shotPos = _lastPosition; _shotLook = new Vec3(_x, _look, 0);
            Pose = new CameraPose { Position = _lastPosition, Look = _shotLook, Focal = _c.BaseFocal };
        }

        /// <summary>The look-ahead, L7668.</summary>
        public double Lead(in CameraRigInput i) =>
            i.NoLead ? 0 : i.Facing * (_c.LeadBase + _c.LeadPerSpeed * Math.Abs(i.Vx));

        public double PushWanted(CameraPush p)
        {
            switch (p)
            {
                case CameraPush.Mantle: return _c.PushMantle;
                case CameraPush.Act: return _c.PushAct;
                case CameraPush.Realise: return _c.PushRealise;
                case CameraPush.Transit: return _c.PushTransit;
                default: return 0;
            }
        }

        public Frame FrameFor(in CameraRigInput i) => _track.Evaluate(i.X, i.Y, Lead(i), i.Signals, _c, AspectOf(i));

        /// <summary>Checkpoint start / respawn (L8115): the rig jumps to the frame, no lag.</summary>
        public void SnapToFrame(in CameraRigInput i)
        {
            Frame f = FrameFor(i);
            _x = f.Cx; _dist = f.Volume.Distance; _y = f.Volume.Height; _look = f.Volume.Look;
            _lastPosition = new Vec3(_x, _y, _dist);
        }

        /// <summary>After the opening (L8113–L8114): the side view starts where the opening's camera is.</summary>
        public void ContinueFrom(Vec3 position, Vec3 look)
        {
            Vec3 fwd = look - position;
            double len = fwd.Length;
            double t = 0;
            if (len > 0) { fwd = fwd * (1 / len); t = fwd.Z < -1e-3 ? -position.Z / fwd.Z : 0; }
            _x = position.X; _y = position.Y; _dist = position.Z; _look = position.Y + fwd.Y * t;
            _lastPosition = position;
        }

        /// <summary>A short damped tremor (L3810); calm mode disables it.</summary>
        public void Shake(double amount, bool calm)
        {
            if (!calm) _shake = Math.Max(_shake, amount);
        }

        /// <summary>One step of <c>updateCamera</c> outside the opening.</summary>
        public CameraPose Step(in CameraRigInput i, double dt)
        {
            double aspect = AspectOf(i);
            Frame frame = _track.Evaluate(i.X, i.Y, Lead(i), i.Signals, _c, aspect);
            FramingVolume v = frame.Volume;

            _push = Damp.Toward(_push, PushWanted(i.Push), _c.PushRate, dt);
            double k = Damp.Factor(_c.FollowRate, dt);
            double rise = Math.Max(0, i.Y - _c.HeightFollowFrom);
            double distWant = Math.Max(v.Distance, _c.WidthFit(_c.BaseFocal, v.Distance * _c.MinFitFraction, aspect)) * (1 - _c.PushDistance * _push);
            _dist += (distWant - _dist) * k;
            _y += (v.Height - _c.PushHeight * _push + rise * _c.HeightFollow - _y) * k;
            _look += (v.Look - _c.PushLook * _push + rise * _c.LookFollow - _look) * k;

            double fog = frame.Fog;
            if (i.LookingUpWell)
            {
                _fogK = Math.Min(1, _fogK + dt / _c.EndingFogSeconds);
                fog = fog + (_c.EndingFog - fog) * Smooth.Step(_fogK);
            }
            else _fogK = 0;

            double ease = i.SlowFollow ? _c.FollowRateXSlow : _c.FollowRateX;
            _x = Damp.Toward(_x, frame.Cx, ease, dt);

            CameraPose pose = ApplyShots(i.Shot, dt, new Vec3(_x, _y, _dist), new Vec3(_x, _look, 0), _c.BaseFocal);
            pose.Fog = fog;
            Pose = pose;
            return pose;
        }

        /// <summary><c>applyShots</c>, L3811–L3836.</summary>
        private CameraPose ApplyShots(ShotRequest? shot, double dt, Vec3 basePos, Vec3 baseLook, double baseFocal)
        {
            double? clock = shot.HasValue ? shot.Value.Clock : null;
            if (clock.HasValue && _shotClock.HasValue) dt = Math.Min(_c.ShotClockMaxDt, Math.Max(0, clock.Value - _shotClock.Value));
            _shotClock = clock;

            if (shot.HasValue)
            {
                ShotRequest s = shot.Value;
                if (!_shotLive) { _shotPos = _lastPosition; _shotLook = baseLook; _shotFocal = baseFocal; _shotLive = true; }
                double k = Damp.Factor(s.Ease * _c.ShotFollowScale, dt);
                _shotPos = Vec3.Lerp(_shotPos, s.Position, k);
                _shotLook = Vec3.Lerp(_shotLook, s.Look, k);
                _shotFocal += (s.Focal - _shotFocal) * k;
                _shotName = s.Name;
            }
            else _shotLive = false;

            _shotW = Damp.Toward(_shotW, shot.HasValue ? 1 : 0, shot.HasValue ? _c.ShotBlendIn : _c.ShotBlendOut, dt);
            double w = Smooth.Step(_shotW);
            Vec3 pos = Vec3.Lerp(basePos, _shotPos, w);
            Vec3 look = Vec3.Lerp(baseLook, _shotLook, w);

            _seed += dt * _c.ShakeSeedRate;
            double a = _shake;
            if (a > _c.ShakeEpsilon)
            {
                pos = new Vec3(pos.X + a * _c.ShakeX * Math.Sin(_seed * _c.ShakeXFreq),
                               pos.Y + a * _c.ShakeY * Math.Sin(_seed * _c.ShakeYFreq + _c.ShakeYPhase), pos.Z);
                look = new Vec3(look.X, look.Y + a * _c.ShakeLookY * Math.Sin(_seed * _c.ShakeLookFreq + _c.ShakeLookPhase), look.Z);
            }
            _shake *= Math.Exp(-dt * _c.ShakeDecay);

            _lastPosition = pos;
            if (w <= 0) _shotName = null;
            return new CameraPose
            {
                Position = pos,
                Look = look,
                Focal = baseFocal + (_shotFocal - baseFocal) * w,
                ShotName = w > 0 ? _shotName : null,
                ShotWeight = w,
            };
        }

        /// <summary>
        /// The opening move (L7777–L7786, <c>captureChest</c> L7649–L7657) at clip frame <paramref name="frame"/> (0–480):
        /// from the chest at 45° drifting in over 120 f, then the arcing pull-back f120–300 with focal 50 → 35.
        /// <paramref name="chest"/> is the label's centre on frame 0 of the Opening clip.
        /// </summary>
        public CameraPose StepOpening(double frame, Vec3 chest, double aspect)
        {
            CameraPose p = OpeningPose(_c, frame, chest, aspect <= 0 ? _c.Aspect : aspect);
            _lastPosition = p.Position;
            Pose = p;
            return p;
        }

        public static CameraPose OpeningPose(CameraConfig c, double frame, Vec3 chest, double aspect)
        {
            double s = Math.Sin(Math.PI / 4), co = Math.Cos(Math.PI / 4);
            var facing = new Vec3(s, 0, co);
            Vec3 start = chest + facing * c.OpeningStartDistance + new Vec3(0, c.OpeningStartRise, 0);
            Vec3 drift = chest + facing * c.OpeningDriftDistance + new Vec3(0, c.OpeningDriftRise, 0);
            double k0 = frame > c.OpeningDriftFrames ? Smooth.Step((frame - c.OpeningDriftFrames) / c.OpeningPullFrames) : 0;
            double k = k0 * k0 * (3 - 2 * k0);
            Vec3 near = Vec3.Lerp(start, drift, Math.Min(1, frame / c.OpeningDriftFrames));
            Vec3 end = new Vec3(c.OpeningEnd.X, c.OpeningEnd.Y, Math.Max(c.OpeningEnd.Z, c.WidthFit(c.BaseFocal, c.OpeningFitWidth, aspect)));
            Vec3 pos = Vec3.Lerp(near, end, k);
            pos = new Vec3(pos.X, pos.Y + c.OpeningArc * Math.Sin(Math.PI * k), pos.Z);
            return new CameraPose
            {
                Position = pos,
                Look = Vec3.Lerp(chest, c.OpeningEndTarget, k),
                Focal = c.OpeningFocalStart - (c.OpeningFocalStart - c.OpeningFocalEnd) * k,
                Fog = double.NaN,
                ShotName = "opening",
                ShotWeight = 1,
            };
        }

        private double AspectOf(in CameraRigInput i) => i.Aspect > 0 ? i.Aspect : _c.Aspect;
    }
}
