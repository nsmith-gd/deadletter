using System;
using System.Collections.Generic;

namespace DeadLetter.Core.Motor
{
    /// <summary>One clip of d17.glb: its length in frames at 24 fps and, for loops, the loop length.</summary>
    public readonly struct ClipInfo
    {
        public readonly string Name;
        /// <summary>Length as exported (last key time × 24).</summary>
        public readonly double Frames;
        /// <summary>True for clips the prototype loops (<c>LOOP_FRAMES</c>, L315–L316).</summary>
        public readonly bool Loop;
        /// <summary>Loop length in frames (<c>LOOP_FRAMES</c> override), or <see cref="Frames"/> when not looping.</summary>
        public readonly double LoopFrames;

        public ClipInfo(string name, double frames, double loopFrames = 0)
        {
            Name = name;
            Frames = frames;
            Loop = loopFrames > 0;
            LoopFrames = loopFrames > 0 ? loopFrames : frames;
        }

        public double Seconds(double fps = 24) => Frames / fps;
    }

    /// <summary>A gameplay event at a clip frame. The frame thresholds are gameplay (port_architecture §3.3).</summary>
    public readonly struct ClipEvent
    {
        public readonly string Clip;
        public readonly string Name;
        public readonly double Frame;
        public readonly string Line;

        public ClipEvent(string clip, string name, double frame, string line)
        {
            Clip = clip; Name = name; Frame = frame; Line = line;
        }
    }

    /// <summary>Clip names used by Core. The Animator's state names must match (see Runtime D17AnimatorParams).</summary>
    public static class ClipNames
    {
        public const string Idle = "Idle", Walk = "Walk", Run = "Run", SadWalk = "SadWalk";
        public const string CrouchIdle = "CrouchIdle", CrouchWalk = "CrouchWalk";
        public const string JumpAir = "JumpAir", Fall = "Fall", Land = "Land", Mantle = "Mantle";
        public const string Lift = "Lift", SetDown = "SetDown", SetDownHigh = "SetDownHigh";
        public const string CarryIdle = "CarryIdle", CarryWalk = "CarryWalk";
        public const string Grab = "Grab", PushIdle = "PushIdle", PushWalk = "PushWalk", Nudge = "Nudge";
        public const string Present = "Present", Sit = "Sit", SitIdle = "SitIdle", SitUp = "SitUp";
        public const string Hop = "Hop", Ride = "Ride", Flinch = "Flinch", CheckLabel = "CheckLabel", Proud = "Proud", Startle = "Startle", PeekDown = "PeekDown";
        public const string Pull = "Pull", Tug = "Tug", Crank = "Crank", LeverPull = "LeverPull", LeverStuck = "LeverStuck";
        public const string DeathCrush = "DeathCrush", DeathShock = "DeathShock", DeathGrabbed = "DeathGrabbed", DeathFall = "DeathFall";
    }

    /// <summary>
    /// The clip table: lengths measured from <c>game/undelivered/assets/d17.glb</c> (76 clips, last changed in 53fd8be)
    /// with the <c>LOOP_FRAMES</c> overrides of L315–L316, and the frame-indexed act events the prototype's code reads
    /// (<c>actions.X.time * FPS</c>). U-12's ClipTableBuilder should regenerate <see cref="All"/> from the Unity import;
    /// the Core tests fail if an event frame falls outside its clip, so a re-export that shortens a clip is caught.
    /// </summary>
    public static class ClipTimings
    {
        // ---- Act event frames ---------------------------------------------------------------------------------------
        /// <summary>Lift: sound f13, attach f22 (blended over 4 frames), carrying at f39. L4418–L4420.</summary>
        public static class LiftEvents { public const double Sound = 13, Attach = 22, AttachBlend = 4, Carry = 39; }
        /// <summary>SetDown / SetDownHigh: release f14, done f35. L4425–L4426.</summary>
        public static class SetDownEvents { public const double Release = 14, Done = 35; }
        /// <summary>Grab: hold the pushable at f13. L4467.</summary>
        public static class GrabEvents { public const double Hold = 13; }
        /// <summary>Present: lamps f20/25/30, NOBODY f36, FORWARD + label stamp f50, out f63. L3622–L3625.</summary>
        public static class PresentEvents { public const double Lamp0 = 20, Lamp1 = 25, Lamp2 = 30, Nobody = 36, Forward = 50, Out = 63; }
        /// <summary>Mantle: <c>MANTLE_FRAMES</c> = 56 (2.33 s), L313.</summary>
        public static class MantleEvents { public const double End = 56; }
        // Verbs owned by U-10's acts (listed so the table test guards them too).
        /// <summary>Cord: click f19, done f43. L1865–L1869.</summary>
        public static class TugEvents { public const double Click = 19, Done = 43; }
        /// <summary>Latch: release f31, flinch f39. L1874–L1875.</summary>
        public static class PullEvents { public const double Release = 31, Flinch = 39; }
        /// <summary>Lever: throw f22, out f33; stuck: clunks to f45. L2899–L2937.</summary>
        public static class LeverEvents { public const double Throw = 22, Out = 33, StuckDone = 45; }
        /// <summary>Board / alight: take-off f8, land f18, done f23. L2884–L2894.</summary>
        public static class HopEvents { public const double TakeOff = 8, Land = 18, Done = 23; }
        /// <summary>Up button: press window f13–22, act f16, done f34. L4579–L4597.</summary>
        public static class PressButtonHighEvents { public const double WindowStart = 13, Act = 16, WindowEnd = 22, Done = 34; }
        /// <summary>Flinch after the latch: 1.6 s of the clip (f38.4), L1875–L1876; the trench's stuck act plays it from 0.2 s (L4520).</summary>
        public static class FlinchEvents { public const double End = 1.6 * 24; }
        /// <summary>CheckLabel: he perks up at f56 and is done at f83 (the scanner's check, L2811–L2812); a quirk ends 0.05 s
        /// before the clip's end (<c>act.time &gt;= dur − 0.05</c>, L3852) and CheckLabel then holds 0.8 s (L3853).</summary>
        public static class CheckLabelEvents { public const double Perk = 56, Done = 83; }
        /// <summary>Knock: taps f14, f20. L3634–L3668.</summary>
        public static class KnockEvents { public const double Tap0 = 14, Tap1 = 20; }

        /// <summary>Every frame event above, for table tests and the Editor's clip validator.</summary>
        public static readonly ClipEvent[] Events =
        {
            new ClipEvent(ClipNames.Lift, "sound", LiftEvents.Sound, "L4418"),
            new ClipEvent(ClipNames.Lift, "attach", LiftEvents.Attach, "L4419"),
            new ClipEvent(ClipNames.Lift, "carry", LiftEvents.Carry, "L4420"),
            new ClipEvent(ClipNames.SetDown, "release", SetDownEvents.Release, "L4425"),
            new ClipEvent(ClipNames.SetDown, "done", SetDownEvents.Done, "L4426"),
            new ClipEvent(ClipNames.SetDownHigh, "release", SetDownEvents.Release, "L4425"),
            new ClipEvent(ClipNames.SetDownHigh, "done", SetDownEvents.Done, "L4426"),
            new ClipEvent(ClipNames.Grab, "hold", GrabEvents.Hold, "L4467"),
            new ClipEvent(ClipNames.Present, "lamp0", PresentEvents.Lamp0, "L3622"),
            new ClipEvent(ClipNames.Present, "lamp1", PresentEvents.Lamp1, "L3622"),
            new ClipEvent(ClipNames.Present, "lamp2", PresentEvents.Lamp2, "L3622"),
            new ClipEvent(ClipNames.Present, "nobody", PresentEvents.Nobody, "L3623"),
            new ClipEvent(ClipNames.Present, "forward", PresentEvents.Forward, "L3624"),
            new ClipEvent(ClipNames.Present, "out", PresentEvents.Out, "L3625"),
            new ClipEvent(ClipNames.Mantle, "end", MantleEvents.End, "L313"),
            new ClipEvent("Tug", "click", TugEvents.Click, "L1865"),
            new ClipEvent("Tug", "done", TugEvents.Done, "L1869"),
            new ClipEvent("Pull", "release", PullEvents.Release, "L1874"),
            new ClipEvent("Pull", "flinch", PullEvents.Flinch, "L1875"),
            new ClipEvent("LeverPull", "throw", LeverEvents.Throw, "L2899–L2937"),
            new ClipEvent("LeverPull", "out", LeverEvents.Out, "L2899–L2937"),
            new ClipEvent("LeverStuck", "done", LeverEvents.StuckDone, "L2899–L2937"),
            new ClipEvent("Hop", "takeoff", HopEvents.TakeOff, "L2884–L2894"),
            new ClipEvent("Hop", "land", HopEvents.Land, "L2884–L2894"),
            new ClipEvent("Hop", "done", HopEvents.Done, "L2884–L2894"),
            new ClipEvent("PressButtonHigh", "act", PressButtonHighEvents.Act, "L4579–L4597"),
            new ClipEvent("PressButtonHigh", "done", PressButtonHighEvents.Done, "L4579–L4597"),
            new ClipEvent("Flinch", "end", FlinchEvents.End, "L1876"),
            new ClipEvent("CheckLabel", "perk", CheckLabelEvents.Perk, "L2811"),
            new ClipEvent("CheckLabel", "done", CheckLabelEvents.Done, "L2812"),
            new ClipEvent("Knock", "tap0", KnockEvents.Tap0, "L3634–L3668"),
            new ClipEvent("Knock", "tap1", KnockEvents.Tap1, "L3634–L3668"),
        };

        // ---- The clip table ---------------------------------------------------------------------------------------------
        /// <summary>All 76 clips of d17.glb. Second number = LOOP_FRAMES override (L315–L316) for looping clips.</summary>
        public static readonly ClipInfo[] All =
        {
            new ClipInfo("Opening", 480), new ClipInfo("Idle", 168, 168), new ClipInfo("Walk", 12, 11),
            new ClipInfo("Run", 11, 10), new ClipInfo("CrouchWalk", 14, 13), new ClipInfo("CrouchIdle", 49, 48),
            new ClipInfo("JumpStart", 6), new ClipInfo("JumpAir", 9, 8), new ClipInfo("Fall", 17, 16),
            new ClipInfo("Land", 10), new ClipInfo("Sit", 16), new ClipInfo("SitIdle", 49, 48),
            new ClipInfo("SitUp", 14), new ClipInfo("AfterYou", 36), new ClipInfo("Mantle", 56),
            new ClipInfo("Pull", 40), new ClipInfo("Flinch", 40), new ClipInfo("Tug", 44),
            new ClipInfo("Crank", 25, 24), new ClipInfo("Lift", 40), new ClipInfo("SetDown", 36),
            new ClipInfo("SetDownHigh", 36), new ClipInfo("CarryIdle", 49, 48), new ClipInfo("CarryWalk", 15, 14),
            new ClipInfo("Grab", 14), new ClipInfo("PushIdle", 49, 48), new ClipInfo("PushWalk", 13, 12),
            new ClipInfo("Nudge", 84), new ClipInfo("Attention", 108), new ClipInfo("Proud", 40),
            new ClipInfo("PeekDown", 72), new ClipInfo("BrushOff", 60), new ClipInfo("Startle", 30),
            new ClipInfo("CheckLabel", 84), new ClipInfo("LeverPull", 34), new ClipInfo("LeverStuck", 46),
            new ClipInfo("Hop", 24), new ClipInfo("Ride", 49, 48), new ClipInfo("Refuse", 40),
            new ClipInfo("Realise", 156), new ClipInfo("Slide", 25), new ClipInfo("SadWalk", 17, 16),
            new ClipInfo("Teeter", 38), new ClipInfo("Pat", 48), new ClipInfo("Hopscotch", 70),
            new ClipInfo("HopscotchLong", 288), new ClipInfo("LookBack", 84), new ClipInfo("Awe", 160),
            new ClipInfo("Knock", 48), new ClipInfo("Present", 64), new ClipInfo("Straighten", 52),
            new ClipInfo("WaterFlinch", 30), new ClipInfo("PickUpLetter", 30), new ClipInfo("PostLetter", 40),
            new ClipInfo("TouchHead", 52), new ClipInfo("CageBrace", 49), new ClipInfo("CageRideLever", 49, 48),
            new ClipInfo("CagePullPawl", 18), new ClipInfo("DeathCrush", 20), new ClipInfo("DeathShock", 30),
            new ClipInfo("DeathGrabbed", 24), new ClipInfo("DeathFall", 24), new ClipInfo("Knockback", 40),
            new ClipInfo("Startled", 18), new ClipInfo("WeighSelf", 86), new ClipInfo("ReadRoute", 84),
            new ClipInfo("FrankHand", 80), new ClipInfo("HoldMug", 102), new ClipInfo("SitRack", 150),
            new ClipInfo("WindClock", 88), new ClipInfo("SitChair", 128), new ClipInfo("LookViewer", 170),
            new ClipInfo("TuneRadio", 112), new ClipInfo("FlickSwitch", 52), new ClipInfo("PressButtonHigh", 36),
            new ClipInfo("RideCounterweight", 96),
        };

        private static Dictionary<string, ClipInfo> _byName;

        /// <summary>Looks a clip up by name (ordinal).</summary>
        public static bool TryGet(string name, out ClipInfo info)
        {
            if (_byName == null)
            {
                var d = new Dictionary<string, ClipInfo>(All.Length, StringComparer.Ordinal);
                foreach (var c in All) d[c.Name] = c;
                _byName = d;
            }
            return _byName.TryGetValue(name ?? string.Empty, out info);
        }

        /// <summary>Loop length in frames for footstep phase, or 0 when unknown.</summary>
        public static double LoopFramesOf(string name) => TryGet(name, out var c) ? c.LoopFrames : 0;
    }
}
