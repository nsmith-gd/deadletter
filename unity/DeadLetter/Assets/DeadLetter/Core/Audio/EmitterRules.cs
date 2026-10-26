using System;

namespace DeadLetter.Core.Audio
{
    /// <summary>The emitter kinds of index.html's <c>Ambience</c> (L1145–L1211).</summary>
    public enum EmitterKind { Buzz, Hum, Lap, Wind, Machine, Static, Drip, Tick, Fan, MusicBox }

    /// <summary>Which deck an emitter sounds on (<c>upper</c>: undefined = either).</summary>
    public enum EmitterDeck { Any, Lower, Upper }

    /// <summary>One placed emitter (<c>EMITTERS</c>, L6577–L6598).</summary>
    public sealed class EmitterDef
    {
        public readonly int Region;
        public readonly double X;
        public readonly EmitterKind Kind;
        public readonly double Level, Reach;
        public readonly EmitterDeck Deck;
        /// <summary>A tick's interval (<c>e.period</c>, default 1 s).</summary>
        public readonly double Period;
        /// <summary>The <c>when</c> condition by name (null = always): <c>revealed</c>, <c>lessonRunning</c>.</summary>
        public readonly string Condition;
        public readonly string Note;

        public EmitterDef(int region, double x, EmitterKind kind, double level, double reach, EmitterDeck deck = EmitterDeck.Any,
            double period = 0, string condition = null, string note = null)
        {
            Region = region; X = x; Kind = kind; Level = level; Reach = reach; Deck = deck; Period = period;
            Condition = condition; Note = note;
        }

        /// <summary>Drip, tick and fan schedule blips (one-shots); the rest are one looping file.</summary>
        public bool IsEvent => EmitterRules.IsEvent(Kind);

        /// <summary>The SfxBank key of its loop, or of its blip takes.</summary>
        public string BankKey => EmitterRules.BankKey(Kind);
    }

    /// <summary>The prologue's and chapter one's emitters, <c>EMITTERS</c> L6577–L6598 (positions from the sets).</summary>
    public static class PrologueEmitters
    {
        public const string Revealed = "revealed", LessonRunning = "lessonRunning";

        // SCANNER_X = OFF3 + 28.9 (L2457); SHAFT = OFF3 + 52.8 .. OFF3 + 55.3 (L3011).
        public const double ScannerX = AmbienceRules.Off3 + 28.9;
        public const double ShaftMid = ((AmbienceRules.Off3 + 52.8) + (AmbienceRules.Off3 + 55.3)) / 2;

        public static readonly EmitterDef[] All =
        {
            new EmitterDef(1, 1.0, EmitterKind.Tick, 0.45, 3, period: 0.9, note: "the dispatch board's lit line"),
            new EmitterDef(1, 7.3, EmitterKind.Drip, 0.7, 4.5, note: "into the trench"),
            new EmitterDef(2, 19.8, EmitterKind.Fan, 0.6, 4.5, note: "the stopped fan's loose blade"),
            new EmitterDef(2, 23.4, EmitterKind.Buzz, 0.5, 4, note: "under the gantry"),
            new EmitterDef(2, 36.0, EmitterKind.Buzz, 0.35, 5, condition: Revealed, note: "a failing tube in the racks"),
            new EmitterDef(2, 56.2, EmitterKind.Drip, 0.55, 4, note: "the ration hall's tap"),
            new EmitterDef(3, ScannerX, EmitterKind.Hum, 0.5, 3.5, EmitterDeck.Lower, note: "the scanner's mains"),
            new EmitterDef(3, AmbienceRules.Off3 + 37.8, EmitterKind.Lap, 0.35, 4, EmitterDeck.Lower, note: "the heap's water"),
            new EmitterDef(4, ShaftMid, EmitterKind.Lap, 0.8, 4.5, note: "the sump"),
            new EmitterDef(4, 107.17, EmitterKind.MusicBox, 0.5, 3.2, note: "the den's music box, the cue to the vent"),
            new EmitterDef(4, 114.5, EmitterKind.Wind, 0.6, 6, note: "the balcony"),
            new EmitterDef(5, AmbienceRules.Off5 + 94.3, EmitterKind.Lap, 0.6, 5, note: "the flooded lane"),
            new EmitterDef(5, 150.0, EmitterKind.Lap, 0.45, 6, note: "the lane further on"),
            new EmitterDef(5, 170.85, EmitterKind.Hum, 0.45, 3, note: "the new splice box"),
            new EmitterDef(5, 174.5, EmitterKind.Wind, 0.7, 4.5, note: "the well"),
            new EmitterDef(6, 205.0, EmitterKind.Buzz, 0.3, 6, note: "school tubes"),
            new EmitterDef(6, 224.0, EmitterKind.Tick, 0.5, 7, period: 0.25, condition: LessonRunning, note: "the lesson's clockwork"),
            new EmitterDef(6, 224.0, EmitterKind.Machine, 0.35, 6, condition: LessonRunning, note: "the apparatus running"),
            new EmitterDef(6, 238.0, EmitterKind.Buzz, 0.25, 6, note: "school tubes"),
        };
    }

    /// <summary>What an emitter does this frame.</summary>
    public struct EmitterStep
    {
        /// <summary>The gain to glide to, and the glide's τ (<c>setTargetAtTime</c>).</summary>
        public double Target, Tau;
        /// <summary>An event kind fires a blip now (play a take at the current gain).</summary>
        public bool Blip;
        /// <summary>Out of reach for over 3 s: fade out and free the source after <see cref="EmitterRules.FreeAfter"/>.</summary>
        public bool Freed;
        /// <summary>k = max(0, 1 − |x − e.x| / reach) (0 when off).</summary>
        public double K;
    }

    /// <summary>
    /// <c>Ambience.update</c> (index.html L1196–L1209) for one emitter, ported exactly: in its region (and deck, and
    /// condition) it glides to <c>level·k²</c> with τ 0.25 s; out of reach it fades (τ 0.4), and after 3 s out it fades
    /// with τ 0.3 and is freed. Event kinds fire a blip when due and schedule the next with the kind's interval
    /// (L1179–L1181). The current gain is glided here too, so Runtime only copies <see cref="Gain"/> to the source.
    /// </summary>
    public sealed class EmitterState
    {
        public const double InTau = 0.25, OutTau = 0.4, FreeTau = 0.3, KeepAlive = 3, FreeAfter = 2;

        private readonly AudioRng _rng;
        private double _next, _offAt, _target, _tau = InTau;

        public EmitterState(uint seed) { _rng = new AudioRng(seed); }

        /// <summary>The emitter's graph exists (<c>live.has(e)</c>).</summary>
        public bool Live { get; private set; }
        /// <summary>The gain now (glided).</summary>
        public double Gain { get; private set; }
        /// <summary>When the last blip's next one is due.</summary>
        public double NextBlip => _next;

        public EmitterStep Update(EmitterDef e, double px, int region, bool upper, bool condition, double now, double dt)
        {
            var s = new EmitterStep();
            bool on = e.Region == region && (e.Deck == EmitterDeck.Any || (e.Deck == EmitterDeck.Upper) == upper) && condition;
            double k = on ? Math.Max(0, 1 - Math.Abs(px - e.X) / e.Reach) : 0;
            s.K = k;
            if (k <= 0)
            {
                if (Live && now > _offAt) { _target = 0; _tau = FreeTau; Live = false; s.Freed = true; }
                else if (Live) { _target = 0; _tau = OutTau; }
            }
            else
            {
                if (!Live) { Live = true; _next = 0; }   // make(e): n.next = 0, so a blip fires at once
                _offAt = now + KeepAlive;
                _target = e.Level * k * k;
                _tau = InTau;
                if (e.IsEvent && now >= _next)
                {
                    double at = Math.Max(now, _next);
                    _next = at + EmitterRules.Interval(e, _rng);
                    s.Blip = true;
                }
            }
            Gain = OnePole.Step(Gain, _target, _tau, dt);
            s.Target = _target;
            s.Tau = _tau;
            return s;
        }
    }

    public static class EmitterRules
    {
        public static bool IsEvent(EmitterKind k) => k == EmitterKind.Drip || k == EmitterKind.Tick || k == EmitterKind.Fan;

        /// <summary>
        /// The bank key (docs/unity/audio_inventory.md, Ambience). The music box is a blip sequence in the web build
        /// (L1182–L1191); its render is one turn of the tune as a loop, so in Unity it is a continuous kind.
        /// </summary>
        public static string BankKey(EmitterKind k)
        {
            switch (k)
            {
                case EmitterKind.Buzz: return "amb_buzz_loop";
                case EmitterKind.Hum: return "amb_hum_loop";
                case EmitterKind.Lap: return "amb_lap_loop";
                case EmitterKind.Wind: return "amb_wind_loop";
                case EmitterKind.Machine: return "amb_machine_loop";
                case EmitterKind.Static: return "amb_static_loop";
                case EmitterKind.MusicBox: return "amb_musicbox_loop";
                case EmitterKind.Drip: return "amb_drip";
                case EmitterKind.Tick: return "amb_tick";
                default: return "amb_fan";
            }
        }

        /// <summary>The delay to the next blip: drip 0.7–2.9 s (L1179), tick <c>period</c> or 1 s (L1180), fan 0.9–3.4 s (L1181).</summary>
        public static double Interval(EmitterDef e, AudioRng rng)
        {
            switch (e.Kind)
            {
                case EmitterKind.Drip: return 0.7 + rng.NextDouble() * 2.2;
                case EmitterKind.Tick: return e.Period > 0 ? e.Period : 1.0;
                case EmitterKind.Fan: return 0.9 + rng.NextDouble() * 2.5;
                default: return 1.0;
            }
        }

        /// <summary>Positional gain of an emitter: level·k², k = max(0, 1 − |dx| / reach) (L1203–L1208).</summary>
        public static double Gain(double level, double dx, double reach)
        {
            double k = Math.Max(0, 1 - Math.Abs(dx) / reach);
            return level * k * k;
        }
    }
}
