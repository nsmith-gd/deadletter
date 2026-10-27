using System;
using System.Collections.Generic;
using System.Globalization;

namespace DeadLetter.Core.Audio
{
    /// <summary>
    /// index.html's <c>Sound.*</c> calls (L606–L774) → SfxBank keys (docs/unity/audio_inventory.md, "Output" column).
    /// Scene rules call <c>SfxPlayer.Play(SfxKeys.X)</c> where the prototype called <c>Sound.x()</c>, with the same
    /// per-call volume (the inventory's Gain column).
    /// </summary>
    public static class SfxKeys
    {
        /// <summary>Calls with no argument that picks the file (a volume argument such as <c>crackle(v)</c> is the AudioSource volume).</summary>
        public static readonly IReadOnlyDictionary<string, string> Simple = new Dictionary<string, string>(StringComparer.Ordinal)
        {
            { "tick", "mech_tick" }, { "spark", "mech_spark" }, { "relayPulse", "mech_relay_pulse" }, { "click", "mech_click" },
            { "grit", "mech_grit" }, { "chirp", "d17_chirp" }, { "worried", "d17_worried" }, { "tap", "d17_tap" },
            { "step", "d17_step" }, { "jump", "d17_jump" }, { "land", "d17_land" }, { "lampClick", "mech_lamp_click" },
            { "buzzShort", "elec_buzz_short" }, { "ratchet", "mech_ratchet" }, { "doorRumble", "mech_door_rumble" },
            { "doorOpen", "mech_door_open" }, { "strain", "d17_strain" }, { "drip", "env_drip" }, { "crackle", "elec_crackle" },
            { "groan", "env_groan" }, { "scrape", "mech_scrape" }, { "bonk", "d17_bonk" }, { "clank", "mech_clank" },
            { "thud", "mech_thud" }, { "distant", "env_distant" }, { "plate", "mech_plate" }, { "gateTick", "mech_gate_tick" },
            { "gateSlam", "mech_gate_slam" }, { "lift", "d17_lift" }, { "squeak", "mech_squeak" }, { "knock", "d17_knock" },
            { "scanSweep", "mech_scan_sweep" }, { "reject", "mech_reject" }, { "hatchLift", "mech_hatch_lift" }, { "bell", "mech_bell" },
            { "klaxon", "mech_klaxon" }, { "beltStop", "mech_belt_stop" }, { "clunk", "mech_clunk" }, { "clack", "mech_clack" },
            { "tumble", "mech_tumble" }, { "pawlClick", "mech_pawl_click" }, { "pawlClatter", "mech_pawl_clatter" },
            { "lurch", "mech_lurch" }, { "alarmBell", "mech_alarm_bell" }, { "crateLand", "mech_crate_land" }, { "found", "curio_found" },
            { "radio", "curio_radio" }, { "splash", "env_splash" }, { "zap", "elec_zap" },
        };

        /// <summary>The rendered lengths (ms) of <c>creak(dur)</c> (L640) and <c>chain(dur)</c> (L642), and <c>rattle(dur)</c> (L616).</summary>
        public static readonly int[] CreakMs = { 300, 400, 500, 600, 700, 800 };
        public static readonly int[] ChainMs = { 300, 500, 550, 600, 1000, 1200, 1500, 2000, 2200, 2500, 3000 };
        public static readonly int[] RattleMs = { 500, 900 };

        /// <summary><c>servo(dur, f0, f1)</c> argument sets the game uses (L610), as <c>ms_f0_f1</c>.</summary>
        public static readonly string[] ServoArgs =
        {
            "120_900_1300", "400_400_1600", "220_300_520", "220_320_560", "240_340_620", "2000_180_420", "120_500_900", "200_500_900",
            "150_400_700", "350_900_1500", "500_260_520", "600_300_700", "250_500_820", "300_300_500", "200_400_520", "200_120_160",
            "300_300_420", "220_700_1250",
        };

        public static readonly string[] CurioKinds = { "scale", "paper", "stamp", "mug", "mugDown", "sit", "wind", "coin", "radio", "switch" };
        public static readonly string[] DeathKinds = { "crush", "shock", "grabbed", "fall" };

        /// <summary><c>relay(i)</c>, i = 0..2 (L607).</summary>
        public static string Relay(int i) => "mech_relay_" + Check(i, 2);
        /// <summary><c>answer(i)</c>, i = 0..2 (L609).</summary>
        public static string Answer(int i) => "mech_answer_" + Check(i, 2);
        /// <summary><c>rowOn(i)</c>, i = 0..5 (L670).</summary>
        public static string RowOn(int i) => "mech_row_on_" + Check(i, 5);
        /// <summary><c>creak(dur)</c>, default 0.5 s (L640); the nearest rendered length.</summary>
        public static string Creak(double seconds = 0.5) => "mech_creak_" + Nearest(CreakMs, seconds);
        /// <summary><c>chain(dur)</c> (L642); the nearest rendered length.</summary>
        public static string Chain(double seconds) => "mech_chain_" + Nearest(ChainMs, seconds);
        /// <summary><c>rattle(dur)</c> (L616); the nearest rendered length.</summary>
        public static string Rattle(double seconds) => "mech_rattle_" + Nearest(RattleMs, seconds);
        /// <summary><c>setDown(onDeck)</c> (L650).</summary>
        public static string SetDown(bool onDeck) => onDeck ? "d17_setdown_deck" : "d17_setdown_floor";

        /// <summary>
        /// <c>liftCrash(v)</c> (L712): the cage dip's v 0.4 has its own render; any other v plays the full crash at volume v
        /// (<see cref="LiftCrashVolume"/>).
        /// </summary>
        public static string LiftCrash(double v) => Math.Abs(v - 0.4) < 0.005 ? "mech_lift_crash_v040" : "mech_lift_crash";
        public static double LiftCrashVolume(double v) => Math.Abs(v - 0.4) < 0.005 ? 1.0 : v;

        /// <summary><c>servo(dur, f0, f1, peak)</c> (L610): one render per argument set the game uses, or null.</summary>
        public static string Servo(double seconds, double f0, double f1)
        {
            string args = ((int)Math.Round(seconds * 1000)).ToString(CultureInfo.InvariantCulture) + "_" +
                          ((int)Math.Round(f0)).ToString(CultureInfo.InvariantCulture) + "_" +
                          ((int)Math.Round(f1)).ToString(CultureInfo.InvariantCulture);
            return Array.IndexOf(ServoArgs, args) >= 0 ? "mech_servo_" + args : null;
        }

        /// <summary><c>curio(kind)</c> (L743–L754).</summary>
        public static string Curio(string kind)
        {
            if (Array.IndexOf(CurioKinds, kind) < 0) throw new ArgumentException("Unknown curio sound " + kind, nameof(kind));
            return kind == "mugDown" ? "curio_mug_down" : "curio_" + kind;
        }

        /// <summary><c>death(how)</c> (L765–L771).</summary>
        public static string Death(string how)
        {
            if (Array.IndexOf(DeathKinds, how) < 0) throw new ArgumentException("Unknown death sound " + how, nameof(how));
            return "death_" + how;
        }

        /// <summary>Every key a call can produce (for checking a bank).</summary>
        public static IEnumerable<string> AllKeys()
        {
            foreach (string k in Simple.Values) yield return k;
            for (int i = 0; i <= 2; i++) { yield return Relay(i); yield return Answer(i); }
            for (int i = 0; i <= 5; i++) yield return RowOn(i);
            foreach (int ms in CreakMs) yield return "mech_creak_" + ms;
            foreach (int ms in ChainMs) yield return "mech_chain_" + ms;
            foreach (int ms in RattleMs) yield return "mech_rattle_" + ms;
            foreach (string a in ServoArgs) yield return "mech_servo_" + a;
            yield return SetDown(true); yield return SetDown(false);
            yield return "mech_lift_crash"; yield return "mech_lift_crash_v040";
            foreach (string c in CurioKinds) yield return Curio(c);
            foreach (string d in DeathKinds) yield return Death(d);
        }

        private static int Check(int i, int max)
        {
            if (i < 0 || i > max) throw new ArgumentOutOfRangeException(nameof(i));
            return i;
        }

        private static int Nearest(int[] ms, double seconds)
        {
            double want = seconds * 1000;
            int best = ms[0];
            for (int i = 1; i < ms.Length; i++) if (Math.Abs(ms[i] - want) < Math.Abs(best - want)) best = ms[i];
            return best;
        }
    }
}
