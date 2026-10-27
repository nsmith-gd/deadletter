using System;

namespace DeadLetter.Core.Audio
{
    /// <summary>The voice treatments of index.html's <c>Voice</c> (<c>TREAT</c>, L973–L985).</summary>
    public enum VoiceTreatment { Tannoy, Dispatch, Card, CardWorn, Child, Elder, Machine, Radio }

    /// <summary>
    /// One treatment's settings (port_architecture §4.25). Unity plays placeholders until recordings exist and does no
    /// voice DSP yet (decision on #20): when recordings arrive, the chain is baked offline with tools/audio_render, so
    /// Unity only plays files. Kept here so that bake, and the voice timing below, read one table.
    /// </summary>
    public sealed class TreatmentDef
    {
        public readonly VoiceTreatment Id;
        public readonly double Rate, Pitch, Lo, Hi, Drive, Crackle, Wow, Room, Ring, Echo;
        /// <summary>The room's return; NaN = min(0.6, 0.18 + 0.12·room) (L1034).</summary>
        public readonly double Wet;
        public readonly bool Chime, Machine, Tremble, StaticSwell;

        public TreatmentDef(VoiceTreatment id, double rate, double pitch, double lo, double hi, double drive, double crackle,
            double wow, double room, double wet = double.NaN, double ring = 0, double echo = 0, bool chime = false,
            bool machine = false, bool tremble = false, bool staticSwell = false)
        {
            Id = id; Rate = rate; Pitch = pitch; Lo = lo; Hi = hi; Drive = drive; Crackle = crackle; Wow = wow; Room = room;
            Wet = wet; Ring = ring; Echo = echo; Chime = chime; Machine = machine; Tremble = tremble; StaticSwell = staticSwell;
        }

        /// <summary><c>playbackRate = rate × 2^(pitch/12)</c> (L1062): speed and pitch together, like tape.</summary>
        public double PlaybackRate => Rate * Math.Pow(2, Pitch / 12.0);

        public double RoomWet => double.IsNaN(Wet) ? Math.Min(0.6, 0.18 + 0.12 * Room) : Wet;

        /// <summary>The rendered crackle bed under every voice of this treatment (a 3 s loop at its gain).</summary>
        public string CrackleKey => "voice_crackle_" + VoiceCatalog.Name(Id);
    }

    /// <summary>One subtitle line and its length in seconds (<c>[text, sec, who?]</c>).</summary>
    public sealed class VoiceLine
    {
        public readonly string Text;
        public readonly double Seconds;
        /// <summary>A speaker other than the voice's own <see cref="VoiceDef.Who"/>, or null.</summary>
        public readonly string Who;

        public VoiceLine(string text, double seconds, string who = null) { Text = text; Seconds = seconds; Who = who; }
    }

    /// <summary>One voice id of <c>VOICE_LINES</c> (L6522–L6554).</summary>
    public sealed class VoiceDef
    {
        public readonly string Id, Who;
        public readonly VoiceTreatment Treat;
        /// <summary>Recording files played in turn (<c>card_den</c>'s three children); null = <c>[id]</c>.</summary>
        public readonly string[] Files;
        public readonly VoiceLine[] Lines;

        public VoiceDef(string id, string who, VoiceTreatment treat, string[] files, params VoiceLine[] lines)
        {
            Id = id; Who = who; Treat = treat; Files = files ?? new[] { id }; Lines = lines;
        }

        /// <summary>The placeholder's length: the sum of the subtitle lines (L1095).</summary>
        public double Length
        {
            get
            {
                double s = 0;
                for (int i = 0; i < Lines.Length; i++) s += Lines[i].Seconds;
                return s;
            }
        }
    }

    public enum VoicePlacementKind { Tannoy, Card }

    /// <summary>A voice placed in the world (<c>VOICES</c>, L6556–L6573): a tannoy that plays as he passes, or a card he winds.</summary>
    public sealed class VoicePlacement
    {
        public readonly string Id;
        public readonly VoicePlacementKind Kind;
        public readonly int Region;
        public readonly double X;
        /// <summary>A tannoy's trigger point if not its own x (<c>at</c>); NaN = x.</summary>
        public readonly double At;
        /// <summary><c>trigger</c>: how near he must be (default 2.5).</summary>
        public readonly double Trigger;
        /// <summary><c>reach</c>: earshot; 0 = the default (9 tannoys, 6 cards).</summary>
        public readonly double Reach;
        public readonly EmitterDeck Deck;
        /// <summary>A card: where he stands to wind it, and whether it is loose (he reads it himself).</summary>
        public readonly double StandX;
        public readonly bool Loose;
        /// <summary>The <c>when</c> condition by name (null = always).</summary>
        public readonly string Condition;

        public VoicePlacement(string id, VoicePlacementKind kind, int region, double x, double at = double.NaN, double trigger = 0,
            double reach = 0, EmitterDeck deck = EmitterDeck.Any, double standX = double.NaN, bool loose = false, string condition = null)
        {
            Id = id; Kind = kind; Region = region; X = x; At = at; Trigger = trigger; Reach = reach; Deck = deck; StandX = standX;
            Loose = loose; Condition = condition;
        }

        public double TriggerX => double.IsNaN(At) ? X : At;
        public double TriggerDistance => Trigger > 0 ? Trigger : VoiceRules.DefaultTrigger;
        public double EffectiveReach => Reach > 0 ? Reach : Kind == VoicePlacementKind.Tannoy ? VoiceRules.TannoyReach : VoiceRules.CardReach;
    }

    public static class VoiceCatalog
    {
        public const string Released = "released", Revealed = "revealed", RestDoorShut = "restDoorShut", Dismissed = "dismissed";

        /// <summary><c>TREAT</c>, L976–L984.</summary>
        public static readonly TreatmentDef[] Treatments =
        {
            new TreatmentDef(VoiceTreatment.Tannoy, 1, 0, 380, 3400, 1.6, 0.005, 2, 1.4, wet: 0.2, echo: 0.23, chime: true),
            new TreatmentDef(VoiceTreatment.Dispatch, 1, 0, 330, 3600, 1.3, 0.003, 0, 1.2, wet: 0.18, ring: 47, echo: 0.23, machine: true),
            new TreatmentDef(VoiceTreatment.Card, 1, 0, 250, 3500, 1.6, 0.02, 9, 0.5),
            new TreatmentDef(VoiceTreatment.CardWorn, 0.97, 0, 300, 3000, 2.2, 0.045, 18, 0.5),
            new TreatmentDef(VoiceTreatment.Child, 1.06, 4, 250, 3800, 1.6, 0.02, 9, 0.6),
            new TreatmentDef(VoiceTreatment.Elder, 0.95, -1.5, 250, 3300, 1.6, 0.025, 12, 0.5, tremble: true),
            new TreatmentDef(VoiceTreatment.Machine, 1, 0, 600, 2600, 3, 0.006, 0, 0.9, ring: 31, machine: true),
            new TreatmentDef(VoiceTreatment.Radio, 1, 0, 500, 2800, 3, 0.08, 6, 0.2, staticSwell: true),
        };

        public static TreatmentDef Treatment(VoiceTreatment t) => Treatments[(int)t];

        /// <summary>The prototype's treatment name (<c>card_worn</c>…).</summary>
        public static string Name(VoiceTreatment t) => t == VoiceTreatment.CardWorn ? "card_worn" : t.ToString().ToLowerInvariant();

        /// <summary><c>VOICES</c>, L6556–L6573 (pass 7/8 placements; cards with no x are triggered by their secret rooms).</summary>
        public static readonly VoicePlacement[] Placements =
        {
            new VoicePlacement("tan_depot_1", VoicePlacementKind.Tannoy, 1, 1.69, at: 8.6, trigger: 0.6, reach: 14, condition: Released),
            new VoicePlacement("tan_racks", VoicePlacementKind.Tannoy, 2, 38.2, trigger: 3.0, condition: Revealed),
            new VoicePlacement("tan_rations", VoicePlacementKind.Tannoy, 2, 56.6, trigger: 2.6),
            new VoicePlacement("tan_bridge", VoicePlacementKind.Tannoy, 4, 116.1, trigger: 2.4, reach: 7),
            new VoicePlacement("tan_relocation", VoicePlacementKind.Tannoy, 4, 120.45, trigger: 2.2),
            new VoicePlacement("card_sorter", VoicePlacementKind.Card, 2, 16.6, standX: 16.45),
            new VoicePlacement("card_queue", VoicePlacementKind.Card, 2, 51.55, standX: 51.55, loose: true),
            new VoicePlacement("card_heap", VoicePlacementKind.Card, 3, 68.0, deck: EmitterDeck.Lower, standX: 68.0),
            new VoicePlacement("card_lastcar", VoicePlacementKind.Card, 4, 121.74, standX: 122.25, loose: true),
            new VoicePlacement("att_rest", VoicePlacementKind.Tannoy, 6, 250.6, trigger: 2.0, reach: 12, condition: RestDoorShut),
            new VoicePlacement("att_bell", VoicePlacementKind.Tannoy, 6, 295.4, trigger: 1.2, reach: 12, condition: Dismissed),
            new VoicePlacement("att_volunteer", VoicePlacementKind.Card, 6, 332.0, standX: 332.0),
            new VoicePlacement("card_mara_parent", VoicePlacementKind.Card, 5, 158.07, standX: 158.07),
        };

        public static VoiceDef Find(string id)
        {
            if (id == null) return null;
            for (int i = 0; i < Lines.Length; i++) if (Lines[i].Id == id) return Lines[i];
            return null;
        }

        public static VoicePlacement FindPlacement(string id)
        {
            for (int i = 0; i < Placements.Length; i++) if (Placements[i].Id == id) return Placements[i];
            return null;
        }

        /// <summary>
        /// <c>VOICE_LINES</c>, generated from index.html L6522–L6554 (the subtitles and the placeholders' timing; the text is
        /// docs/voice_script.md's). Regenerate rather than edit by hand.
        /// </summary>
        public static readonly VoiceDef[] Lines =
        {
            new VoiceDef("dispatch_wake", "Dispatch", VoiceTreatment.Dispatch, null,
                    new VoiceLine("Supply restored.", 2.2),
                    new VoiceLine("Resuming dispatch.", 2.4)),
            new VoiceDef("dispatch_item", "Dispatch", VoiceTreatment.Dispatch, null,
                    new VoiceLine("Courier D-17. One item outstanding.", 3.0),
                    new VoiceLine("Deliver to: Mara. C-114, ring C.", 3.4)),
            new VoiceDef("tan_depot_1", "Tannoy", VoiceTreatment.Tannoy, null,
                    new VoiceLine("Night shift, to your stations.", 2.6),
                    new VoiceLine("Night shift, to your stations.", 2.6),
                    new VoiceLine("Sorting will run until oh-six-hundred. Couriers, report to dispatch.", 4.6),
                    new VoiceLine("Thank you for your work. The refuge depends on it.", 4.0),
                    new VoiceLine("Order above all.", 2.0)),
            new VoiceDef("card_sorter", "Voice card", VoiceTreatment.Card, null,
                    new VoiceLine("Hello, little bird. It’s Mum.", 3.0),
                    new VoiceLine("I’m on nights again, so you’ll be asleep when this comes. Gran will play it for you at breakfast.", 6.0),
                    new VoiceLine("It’s warm in here tonight. Stuffy. They’ve turned the fans down to save power, so we’re all yawning over the letters.", 7.0),
                    new VoiceLine("Ruth fell asleep on the franking machine.", 3.0),
                    new VoiceLine("Be good for Gran. I’ll be home when the shift’s done.", 4.0),
                    new VoiceLine("Love you. Bye-bye. Bye.", 3.0)),
            new VoiceDef("tan_racks", "Tannoy", VoiceTreatment.Tannoy, null,
                    new VoiceLine("Couriers to dispatch.", 2.2),
                    new VoiceLine("D-12.", 1.4),
                    new VoiceLine("D-13.", 1.4),
                    new VoiceLine("D-14.", 1.4),
                    new VoiceLine("D-15.", 1.4),
                    new VoiceLine("D-16.", 3.2)),
            new VoiceDef("tan_rations", "Tannoy", VoiceTreatment.Tannoy, null,
                    new VoiceLine("Attention, grade four. Rations are suspended until further notice.", 5.0),
                    new VoiceLine("Distribution will resume at oh-eight-hundred.", 3.6),
                    new VoiceLine("Please remain in the hall. Please keep the aisles clear for the weigh-in.", 5.0),
                    new VoiceLine("Order above all.", 2.0)),
            new VoiceDef("card_queue", "Voice card", VoiceTreatment.CardWorn, null,
                    new VoiceLine("If someone finds this.", 2.6),
                    new VoiceLine("We waited for them to open the hatch. They said eight o’clock.", 4.6),
                    new VoiceLine("That was the eleventh. I’ve lost count since.", 3.6),
                    new VoiceLine("There are a lot of us here. We’re keeping our places.", 4.2),
                    new VoiceLine("If you’re from upstairs… there are children here. Please.", 5.0)),
            new VoiceDef("tan_scanner", "Scanner", VoiceTreatment.Machine, null,
                    new VoiceLine("Return to sender. Return to sender.", 3.0)),
            new VoiceDef("card_reader", "Voice card", VoiceTreatment.Elder, null,
                    new VoiceLine("Number two thousand and eleven.", 3.0),
                    new VoiceLine("“Dear Tomas. The rain on ring A is only the pipes, they say, but it sounds like rain, and I stand under it some evenings.", 8.0),
                    new VoiceLine("I hope you are eating. Your sister sends her love…”", 4.5),
                    new VoiceLine("I read them all, in the end. Somebody ought to.", 4.5),
                    new VoiceLine("Tomas, if you’re out there, she sent her love.", 4.5),
                    new VoiceLine("Number two thousand and twelve.", 3.0)),
            new VoiceDef("card_heap", "Voice card", VoiceTreatment.Card, null,
                    new VoiceLine("Hello, love, it’s your dad. We’re fine. Your mother’s fine.", 5.0),
                    new VoiceLine("The ration’s short this month, but we’re fine. Don’t send any of yours, I mean it.", 5.5),
                    new VoiceLine("The lift’s still not running to your level, but they say soon.", 4.0),
                    new VoiceLine("Write when you can. We play your last one every night.", 4.0),
                    new VoiceLine("We’re fine.", 2.5)),
            new VoiceDef("card_den", "Voice card", VoiceTreatment.Child, new[] { "card_den_1", "card_den_2", "card_den_3" },
                    new VoiceLine("Is it on? Is it going?", 2.2),
                    new VoiceLine("It’s going! Say it!", 1.8),
                    new VoiceLine("Okay. This is the Den. If you found this, you are in the club.", 4.0),
                    new VoiceLine("You have to say the password.", 2.0),
                    new VoiceLine("The password is crooked tree.", 2.5),
                    new VoiceLine("That’s Mara’s. She drew it.", 2.2),
                    new VoiceLine("Mara, say something!", 2.0),
                    new VoiceLine("She won’t, she’s shy. Okay. Club rules: no grown-ups. No telling.", 5.0),
                    new VoiceLine("And whoever finds this has to come back.", 3.5)),
            new VoiceDef("tan_bridge", "Tannoy", VoiceTreatment.Tannoy, null,
                    new VoiceLine("Grades one and two only beyond this point. Grades one and two only.", 5.0),
                    new VoiceLine("All other residents, return to your rings. Thank you for your patience.", 5.5),
                    new VoiceLine("Order above all.", 2.0)),
            new VoiceDef("tan_relocation", "Tannoy", VoiceTreatment.Tannoy, null,
                    new VoiceLine("Relocation. This car is for grades one and two. Please have your papers ready.", 5.5),
                    new VoiceLine("One case per person. Do not push.", 3.4),
                    new VoiceLine("This is the last scheduled car. This is the last scheduled car.", 5.0),
                    new VoiceLine("Order above all.", 2.0)),
            new VoiceDef("card_lastcar", "Voice card", VoiceTreatment.Card, null,
                    new VoiceLine("Sweetheart. You did so well getting on.", 3.6),
                    new VoiceLine("I’m sorry I let go of your hand so fast. They were shouting, and I wanted you on before the gate.", 6.0),
                    new VoiceLine("You go with Aunt Ila now. Do what she tells you.", 3.6),
                    new VoiceLine("We’ll be on the next one. We’ll be on the next one, and I’ll find you.", 5.5),
                    new VoiceLine("Keep your coat on. It’s cold up there, they say.", 3.8)),
            new VoiceDef("radio_above", "Radio", VoiceTreatment.Radio, null,
                    new VoiceLine("…feed to C, test four.", 2.4),
                    new VoiceLine("Load’s holding.", 1.8),
                    new VoiceLine("Well. Not that there’s anyone down there to…", 4.2),
                    new VoiceLine("…logging it anyway.", 2.4)),
            new VoiceDef("card_mara_parent", "Voice card", VoiceTreatment.Card, null,
                    new VoiceLine("Happy birthday, my Mara. Nine!", 3.6),
                    new VoiceLine("I’m sorry I can’t be there. They need the couriers’ parents on the works this month, and the lift’s slow.", 6.4),
                    new VoiceLine("So I’ve sent you something with the post. Don’t open it till the day. I mean it.", 5.2),
                    new VoiceLine("It’s for outside. One day there’ll be an outside, and you’ll need them.", 5.4),
                    new VoiceLine("Keep drawing your trees. Don’t let them tell you they have to be straight.", 5.0),
                    new VoiceLine("I love you. I’ll see you soon. Happy birthday.", 4.4)),
            new VoiceDef("att_gate_1", "Register", VoiceTreatment.Tannoy, null,
                    new VoiceLine("Good morning. Please hang your coat on your peg.", 3.2)),
            new VoiceDef("att_gate_2", "Register", VoiceTreatment.Tannoy, null,
                    new VoiceLine("Coat seven, please.", 2.0)),
            new VoiceDef("att_gate_3", "Register", VoiceTreatment.Tannoy, null,
                    new VoiceLine("Thank you. You are present.", 2.4)),
            new VoiceDef("att_caretaker", "Voice card", VoiceTreatment.Elder, null,
                    new VoiceLine("Lost property, week forty.", 2.6),
                    new VoiceLine("One mitten, red. One shoe, small, left foot. A lunch tin, M.D. on the lid.", 6.0),
                    new VoiceLine("I keep it all. Somebody’ll come back for it.", 4.0),
                    new VoiceLine("Register’s down to one this week. Just the little one with the drawings. Sits at the front, never says a word.", 7.0),
                    new VoiceLine("Good kid.", 2.0)),
            new VoiceDef("att_lesson", "Lesson", VoiceTreatment.Card, null,
                    new VoiceLine("Good morning, class. Today we will learn how a tree grows.", 4.0),
                    new VoiceLine("First, the root. Then, the trunk.", 3.2),
                    new VoiceLine("Then the branches reach for the light. And then, the leaves.", 4.4),
                    new VoiceLine("A tree always grows straight, and tall, toward the sun.", 4.0),
                    new VoiceLine("Let us watch it again.", 2.4)),
            new VoiceDef("att_escort", "Voice card", VoiceTreatment.CardWorn, null,
                    new VoiceLine("Escort log. Fourteen hundred.", 2.6),
                    new VoiceLine("Pupil M.D. not in sick bay at the check. Not in class. Not in the cloakroom.", 5.4),
                    new VoiceLine("Found under the sick bay balcony. Again. Third time this week.", 4.6),
                    new VoiceLine("She says she was listening to the pipes.", 3.4),
                    new VoiceLine("Recommend…", 1.6),
                    new VoiceLine("No recommendation. Let her listen.", 3.4)),
            new VoiceDef("att_rest", "Tannoy", VoiceTreatment.Tannoy, null,
                    new VoiceLine("Rest hour.", 1.6),
                    new VoiceLine("Lights out, please. Blinds down.", 2.8),
                    new VoiceLine("Pupils will remain in their own beds.", 3.0)),
            new VoiceDef("att_trolley", "Escort", VoiceTreatment.Machine, null,
                    new VoiceLine("Pupil found. Returning you to the dormitory.", 3.0)),
            new VoiceDef("att_bell", "Tannoy", VoiceTreatment.Tannoy, null,
                    new VoiceLine("End of lessons.", 2.0),
                    new VoiceLine("Pupils will walk, not run, to the playground.", 3.6),
                    new VoiceLine("Escorts to the gate, please.", 2.6),
                    new VoiceLine("Order above all.", 2.0)),
            new VoiceDef("att_volunteer", "Voice card", VoiceTreatment.Elder, null,
                    new VoiceLine("Mara. Lisle here. The bench.", 3.0),
                    new VoiceLine("You asked me about the Works again, so I asked them for you.", 4.4),
                    new VoiceLine("Your drawing’s good. Better than mine.", 3.2),
                    new VoiceLine("Water’s patient, love. Give it a slope and it’ll go round anything.", 5.0),
                    new VoiceLine("They said yes. Ring A, water and the growing beds. After your birthday.", 5.2),
                    new VoiceLine("They’ll grumble you’re young. Let them.", 3.4),
                    new VoiceLine("Your tree can be crooked. The channels can’t. Mind the levels.", 4.6)),
            new VoiceDef("att_teacher", "Voice card", VoiceTreatment.Card, null,
                    new VoiceLine("To the family of Mara D., class four.", 3.4),
                    new VoiceLine("She’s doing well. She doesn’t speak much in class, but she listens to everything.", 5.6),
                    new VoiceLine("She asked me today why the windows don’t open. I told her the truth. I hope that was right.", 6.4),
                    new VoiceLine("The protocol says she isn’t to be left alone, so I eat my lunch with her. I don’t mind.", 5.0),
                    new VoiceLine("She’s drawn on the wall behind the window panel. A tree. I haven’t had it cleaned.", 5.6),
                    new VoiceLine("I’ll keep recording these until someone writes back. Take care of yourselves.", 5.0)),
        };
    }
}
