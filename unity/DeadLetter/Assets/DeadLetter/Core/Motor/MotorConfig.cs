using System;

namespace DeadLetter.Core.Motor
{
    /// <summary>Jump launch speed: prototype parity (default) or the designed value. See <see cref="MotorConfig.JumpMode"/>.</summary>
    public enum JumpMode
    {
        /// <summary>Launch at <c>JUMP_V − g/(2·60)</c>: apex ≈ 0.377 m, as the playtested 60 Hz prototype jumps.</summary>
        Parity60Hz = 0,
        /// <summary>Launch at <c>JUMP_V = √(2·g·JUMP_APEX)</c>: apex = JUMP_APEX = 0.40 m.</summary>
        Designed = 1,
    }

    /// <summary>
    /// Every number the D-17 motor uses, with the prototype's exact values. Line numbers are
    /// <c>game/undelivered/index.html</c> at 7b3c123 (port_architecture §0.1, §4.7, §4.9–4.12).
    /// Plain fields so a Runtime ScriptableObject can wrap and tune a copy; <see cref="Prototype"/> is the reference.
    /// Units: metres, seconds, m/s, m/s², clip frames at 24 fps.
    /// </summary>
    public sealed class MotorConfig
    {
        // ---- Clock -------------------------------------------------------------------------------------------
        /// <summary>Clip frame rate. <c>FPS = 24</c>, L268.</summary>
        public double Fps = 24;

        // ---- Speeds (L304–L327) ----------------------------------------------------------------------------
        /// <summary><c>WALK</c>, L304.</summary>
        public double Walk = 0.9;
        /// <summary><c>RUN</c>, L304.</summary>
        public double Run = 1.6;
        /// <summary><c>CROUCH_WALK</c>, L304.</summary>
        public double CrouchWalk = 0.5;
        /// <summary><c>CARRY_WALK</c> (heavy items), L325.</summary>
        public double CarryWalk = 0.42;
        /// <summary><c>SLOW_WALK</c> (emotional beats, set by pace zones), L327.</summary>
        public double SlowWalk = 0.39;
        /// <summary>Approach to a stand point: <c>WALK·0.8</c> (or <c>CROUCH_WALK·0.8</c>), L1857, L4385.</summary>
        public double ApproachFactor = 0.8;
        /// <summary>Stepping along z into or out of the set, L1845, L3615.</summary>
        public double StepInSpeed = 0.45;

        // ---- Clip authored speeds (timeScale = speed / clip speed), L305, L326 ------------------------------
        public double ClipSpeedWalk = 0.79;
        public double ClipSpeedRun = 1.52;
        public double ClipSpeedCrouchWalk = 0.49;
        public double ClipSpeedCarryWalk = 0.295;
        public double ClipSpeedPushWalk = 0.45;
        public double ClipSpeedSadWalk = 0.387;

        // ---- Acceleration (L1981–L1984, L2332, L4690) ---------------------------------------------------------
        public double AccelGroundRun = 6.0;
        public double AccelGroundWalk = 4.5;
        public double AccelAir = 2.2;
        /// <summary>Release friction <c>vx *= 1 − 10·dt</c> (made frame-rate exact, see Smooth.DecayFactor), L1984.</summary>
        public double ReleaseFriction = 10.0;
        /// <summary>Stick scaling: <c>target = sign·top·min(1, |move|·1.15)</c>, L1981.</summary>
        public double StickGain = 1.15;
        /// <summary>Heavy carry acceleration, L2332.</summary>
        public double AccelCarry = 3.0;
        /// <summary>Chapter 1 pushables, L4690: the default of <c>IPushable.Accel</c> (the motor reads each pushable's own).</summary>
        public double AccelPush = 1.4;

        // ---- Input (L1266, L1927) --------------------------------------------------------------------------------
        /// <summary>Stick deadzone (not rescaled), L1266.</summary>
        public double StickDeadzone = 0.22;
        /// <summary>|axis| above which the stick runs (with auto-run), L1927.</summary>
        public double StickRunThreshold = 0.65;

        // ---- Jump (L306–L308) --------------------------------------------------------------------------------------
        /// <summary><c>GRAVITY</c>, L306.</summary>
        public double Gravity = 9.8;
        /// <summary><c>JUMP_APEX</c>, L306.</summary>
        public double JumpApex = 0.4;
        /// <summary><c>COYOTE</c>, L308.</summary>
        public double Coyote = 0.10;
        /// <summary><c>JUMP_BUFFER</c>, L308.</summary>
        public double JumpBuffer = 0.12;
        /// <summary>
        /// <b>Director's switch</b> for the jump launch speed. <see cref="Motor.JumpMode.Parity60Hz"/> (default) matches the
        /// playtested prototype, whose semi-implicit 60 Hz Euler step (<c>vy -= g·dt; y += vy·dt</c>, L1992–L1993,
        /// L2013–L2014) peaks at 0.377 m, not JUMP_APEX. <see cref="Motor.JumpMode.Designed"/> launches at the designed
        /// <c>JUMP_V</c> and peaks at exactly JUMP_APEX (0.40 m). Core integrates gravity exactly in both modes.
        /// </summary>
        public JumpMode JumpMode = JumpMode.Parity60Hz;
        /// <summary>The prototype's frame rate the parity launch speed reproduces (its rAF step, 60 Hz).</summary>
        public double JumpParityRate = 60;

        /// <summary><c>JUMP_V = √(2·GRAVITY·JUMP_APEX)</c> ≈ 2.80 m/s, L307 (the designed launch speed).</summary>
        public double JumpVelocityDesigned => Math.Sqrt(2 * Gravity * JumpApex);
        /// <summary>
        /// <c>JUMP_V − GRAVITY/(2·60)</c> ≈ 2.7183 m/s: with exact integration this peaks where the prototype's 60 Hz
        /// Euler step does (≈ 0.377 m), at any step length.
        /// </summary>
        public double JumpVelocityParity => JumpVelocityDesigned - Gravity / (2 * JumpParityRate);
        /// <summary>Launch speed the motor uses, per <see cref="JumpMode"/>.</summary>
        public double JumpVelocity => JumpMode == JumpMode.Designed ? JumpVelocityDesigned : JumpVelocityParity;

        // ---- Body (L309–L310) ------------------------------------------------------------------------------------
        /// <summary><c>STAND_H</c>, L309.</summary>
        public double StandHeight = 0.76;
        /// <summary><c>CROUCH_H</c>, L309.</summary>
        public double CrouchHeight = 0.58;
        /// <summary><c>ANTENNA_TOP</c> (antenna bend, Runtime), L309.</summary>
        public double AntennaTop = 1.12;
        /// <summary><c>HALF</c>: body half-width for the wall probe, L310.</summary>
        public double Half = 0.17;
        /// <summary><c>FOOT</c>: support probe offset, <c>supportAt</c> L1737.</summary>
        public double Foot = 0.08;
        /// <summary><c>STEP_UP</c>, L310.</summary>
        public double StepUp = 0.07;
        /// <summary>Step allowed on ramps, L2004.</summary>
        public double StepUpRamp = 0.45;
        /// <summary><c>FACE_D</c>: face distance from the body centre to a wall, L310.</summary>
        public double FaceDistance = 0.17;

        // ---- Crouch and ceilings (L1973–L1976, L2008) --------------------------------------------------------
        /// <summary>Ceiling clearance probe: from x − 0.12 to x + facing·0.22, L1973.</summary>
        public double ClearanceBack = 0.12;
        public double ClearanceAhead = 0.22;
        /// <summary>Crouch when clearance &lt; 0.8, L1975.</summary>
        public double CrouchBelow = 0.8;
        /// <summary>Stand when clearance &gt; 0.85, L1976.</summary>
        public double StandAbove = 0.85;
        /// <summary>Air/crouch ceiling block probe ±0.1, L2008.</summary>
        public double CeilingBlockProbe = 0.1;

        // ---- Mantle (L310–L313, L1989–L1990, L2021–L2022) ---------------------------------------------------------
        /// <summary><c>MANTLE_MIN</c> (exclusive: a ledge must be higher than this), L310.</summary>
        public double MantleMin = 0.24;
        /// <summary><c>MANTLE_MAX</c> (inclusive), L310.</summary>
        public double MantleMax = 0.62;
        /// <summary>Mid-air catch extends MANTLE_MAX by 0.1 (to 0.72), L2022.</summary>
        public double MantleAirExtra = 0.1;
        /// <summary>Mid-air catch only while <c>vy &lt; 1.2</c>, L2022.</summary>
        public double MantleAirMaxVy = 1.2;
        /// <summary>Standing mantle ledge scan range, L1989.</summary>
        public double MantleScanStanding = 0.5;
        /// <summary>Mid-air ledge scan range, L2021.</summary>
        public double MantleScanAir = 0.32;
        /// <summary>Standing mantle: ledge must be nearer than <c>FACE_D + 0.3</c>, L1990.</summary>
        public double MantleReachExtra = 0.3;
        /// <summary>Approach blend: <c>smooth(f / 10)</c>, L1943.</summary>
        public double MantleApproachFrames = 10;

        // ---- Landing, falling, slopes (L2019–L2031) ----------------------------------------------------------
        public double HardLandingDrop = 0.25;     // land timer 0.30 vs 0.18, and White noise, L2026–L2028
        public double LandTimerHard = 0.30;
        public double LandTimerSoft = 0.18;
        public double ShakeDrop = 0.3;            // shake(0.25) when fall > 0.3, L2027
        public double ShakeAmount = 0.25;
        public double NoiseAmount = 1.1;          // makeNoise(x, 1.1), L2028
        public double SlopeSnap = 0.09;           // stay grounded if 0 < y − support < 0.09, L2031
        public double FallClipVy = -1.4;          // JumpAir → Fall when vy < −1.4 ...
        public double FallClipDrop = 0.25;        // ... and peakY − y > 0.25, L2019

        // ---- Animation selection (L2053–L2063, L4701) -------------------------------------------------------
        public double MovingSpeed = 0.03;
        public double RunClipSpeed = 1.15;        // speed > 1.15 → Run, L2060
        public double WalkMinTimeScale = 0.4;     // L2061
        public double CarryMinTimeScale = 0.5;    // L2058
        public double PushMinTimeScale = 0.4;     // L4701

        // ---- Facing (L7579–L7583) ---------------------------------------------------------------------------------
        /// <summary>Yaw turn rate toward ±π/2 or an override, L7581.</summary>
        public double YawRate = 8.0;
        /// <summary>A turn is finished within 0.05 rad of the target, L1879, L3606.</summary>
        public double TurnTolerance = 0.05;

        // ---- Interaction reach (L320, L4219–L4255, L1812–L1814) -------------------------------------------------
        /// <summary><c>GRIP_FWD</c>: stand this far from an item to lift it, L320.</summary>
        public double GripForward = 0.29;
        /// <summary>Item reach around its stand point, L4221.</summary>
        public double ItemReach = 0.4;
        /// <summary>Item must be at his feet level within 0.05, L4219.</summary>
        public double ItemLevelTolerance = 0.05;
        /// <summary>Default push grip reach (front and back), L4254.</summary>
        public double PushReach = 0.34;
        /// <summary>Stand point reached when |dx| &lt; 0.012 and |dz| &lt; 0.004, L1846, L4384.</summary>
        public double ArriveX = 0.012;
        public double ArriveZ = 0.004;

        // ---- Push hold (L4683–L4724) --------------------------------------------------------------------------------
        public double PushLipTolerance = 0.005;   // L4686
        public double ShoveTime = 0.45;           // held into the lip, L4710
        public double ShoveActTime = 0.8;         // 'shove' act length, L4518
        public double DetentMove = 0.02;          // L4718

        // ---- Sit (L5673–L5684) ------------------------------------------------------------------------------------
        public double SitSeatedAfter = 0.4;
        public double SitIdleAfter = 0.66;
        public double SitCanStandAfter = 1.0;
        public double SitUpTime = 0.6;

        // ---- Hop: board, alight, a station's chained hop (hopTo, L2884–L2894) -----------------------------------
        /// <summary>The hop's arc height, metres (<c>0.38·sin(π·k)</c>, L2888).</summary>
        public double HopArc = 0.38;

        // ---- Hide (DL-14b, L6111–L6125) ---------------------------------------------------------------------------
        /// <summary>Backing into the recess, m/s (<c>z − 0.6·dt</c>, L6115), and stepping out (<c>z + 0.7·dt</c>, L6122).</summary>
        public double HideInSpeed = 0.6, HideOutSpeed = 0.7;
        /// <summary>The Walk clip's speed while backing in / out (±0.5 / CLIP_SPEED.Walk, L6115, L6122).</summary>
        public double HideWalkSpeed = 0.5;
        /// <summary>Any input after this long hidden brings him out (L6120).</summary>
        public double HideLeaveAfter = 0.3;

        // ---- Escorted (DL-14b, L6126–L6134) ---------------------------------------------------------------------
        /// <summary>His z eases back to the lane at rate 4 (<c>z += (0 − z)·min(1, dt·4)</c>, L6129).</summary>
        public double EscortZRate = 4;

        // ---- Stuck, death, quirks (L4519–L4521, L7421–L7453, L3841–L3856) ---------------------------------------
        /// <summary>The stuck act flinches after 0.2 s and calls <c>respawn()</c> after 2.0 s (L4520–L4521).</summary>
        public double StuckFlinchAfter = 0.2, StuckRespawnAfter = 2.0;
        /// <summary><c>respawn()</c>: the fade, then the reload 1.3 s later (L2998).</summary>
        public double RespawnFade = 1.3;
        /// <summary>The death cut: black, the reload 0.6 s later (L7451).</summary>
        public double DeathCut = 0.6;
        /// <summary>Death holds before the cut: crush 0.7, shock 1.0, grabbed 1.15, fall 0.9 s (<c>DEATH</c>, L7421–L7424).</summary>
        public double DeathHoldCrush = 0.7, DeathHoldShock = 1.0, DeathHoldGrabbed = 1.15, DeathHoldFall = 0.9;
        /// <summary>The death shake: crush 0.9, fall 0.7, else 0.45 (L7441).</summary>
        public double DeathShakeCrush = 0.9, DeathShakeFall = 0.7, DeathShakeOther = 0.45;
        /// <summary>A quirk is cancelled by a move only once its clip is past 0.3 s (L3851); it ends 0.05 s before the clip's end (L3852).</summary>
        public double QuirkCancelAfter = 0.3, QuirkEndEarly = 0.05;
        /// <summary>CheckLabel holds this long after its clip, so the label can be read (<c>a.holdFor ?? 0.8</c>, L3853).</summary>
        public double CheckLabelHold = 0.8;

        /// <summary>The death act's hold for <paramref name="how"/>.</summary>
        public double DeathHold(DeathKind how) => how == DeathKind.Crush ? DeathHoldCrush : how == DeathKind.Shock ? DeathHoldShock
            : how == DeathKind.Grabbed ? DeathHoldGrabbed : DeathHoldFall;

        /// <summary>The death act's camera shake for <paramref name="how"/>.</summary>
        public double DeathShake(DeathKind how) => how == DeathKind.Crush ? DeathShakeCrush : how == DeathKind.Fall ? DeathShakeFall : DeathShakeOther;

        // ---- Set-down search (L4342–L4353) ---------------------------------------------------------------------
        /// <summary>Offsets from GRIP_FWD tried in front, then behind: +0, +0.08, +0.16, −0.05, L4344.</summary>
        public double[] PlaceOffsets = { 0.0, 0.08, 0.16, -0.05 };
        /// <summary>Flatness tolerance across the item's radius, L4342.</summary>
        public double PlaceFlatTolerance = 0.02;

        /// <summary>A fresh copy holding the prototype's values.</summary>
        public static MotorConfig Prototype() => new MotorConfig();

        // ---- MANTLE_KEYS (frame, forward, up-fraction), L311–L312; MANTLE_FRAMES L313 ----------------------------
        /// <summary>Root path of the authored mantle: (frame, forward m, fraction of the climb). build_dl01.py matches.</summary>
        public static readonly double[,] MantleKeys =
        {
            { 0, 0, 0 }, { 6, 0, 0 }, { 10, 0.03, 0.12 }, { 14, 0.03, 0.18 }, { 20, 0.05, 0.45 },
            { 24, 0.05, 0.38 }, { 32, 0.10, 0.78 }, { 38, 0.20, 0.95 }, { 44, 0.33, 1.0 }, { 56, 0.38, 1.0 },
        };

        /// <summary><c>mantleAt(f)</c>, L1913–L1919: forward offset and up-fraction at clip frame f.</summary>
        public static void MantleAt(double f, out double forward, out double fraction)
        {
            int n = MantleKeys.GetLength(0);
            for (int i = 0; i < n - 1; i++)
            {
                double f0 = MantleKeys[i, 0], w0 = MantleKeys[i, 1], u0 = MantleKeys[i, 2];
                double f1 = MantleKeys[i + 1, 0], w1 = MantleKeys[i + 1, 1], u1 = MantleKeys[i + 1, 2];
                if (f <= f1)
                {
                    double k = f1 > f0 ? Maths.Smooth.Step((f - f0) / (f1 - f0)) : 1;
                    forward = w0 + (w1 - w0) * k;
                    fraction = u0 + (u1 - u0) * k;
                    return;
                }
            }
            forward = MantleKeys[n - 1, 1];
            fraction = MantleKeys[n - 1, 2];
        }
    }
}
