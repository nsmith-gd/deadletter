using System.Text.Json;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// Chapter 1's trace fields (<c>CHAPTER=att</c>, tools/sim/README.md "Chapter 1"): only while he is in region 6, named
    /// with the scene's number; null before. Kept here so the prologue's fields (TraceKit.cs) and these never collide.
    /// </summary>
    internal sealed partial class TraceStep
    {
        // The whole chapter: what an 'att' act is about (game.act.what: coat, hang, pawl, crank, duct, ...; null outside one).
        public string Aw;
        // DL-12: the coat (x, base, state: bin, carried, peg, floor), the stand-in figure (x, v), the gate (y, fall speed),
        // someone on the strip and how many times (game.att, L5228–L5243, L5381–L5408).
        public double? C12x, C12b, F12x, F12v, G12y, G12v;
        public string C12s;
        public bool? P12;
        public int? Pc12;
        // DL-13: the second figure (x, v), the lesson (on, its clock, braked, the three steps, the tree) (L5409–L5436).
        public double? F13x, F13v, T13, Tr13;
        public bool? L13, K13;
        public string S13;
        // DL-14: the blinds and their targets, the winds, the jam, the pole (x, base, state), the peel, the rattle, the duct (L5437–L5511).
        public double? Ba14, Bb14, Px14, Pb14, Pe14;
        public int? Ta14, Tb14, W14;
        public bool? J14, Pd14, Rt14, Du14;
        public string Ps14;

        // DL-14a: the night-light (clock, braked), W1/W2 and their targets, the winds, the door, the gown and the bag (L6217–L6228).
        public double? Nt14a, W1a, W2a, Do14a, Gx14a, Gb14a, Bx14a, Bb14a;
        public int? T1a, T2a, Wn14a;
        public bool? Nk14a, Op14a;
        public string Gs14a, Bs14a;
        // DL-14b: the escort trolley (x, dir, mode, its clock), the figure in the bay (x, state, out, kept), hiding (L6352–L6434).
        public double? Tx14b, Tt14b, Fx14b, Fo14b, Hd14b;
        public int? Td14b;
        public string Tm14b, Fs14b;
        public bool? Fk14b;
        // DL-15: the two figures (x, base, state, lean), the pupil lift (height, speed), the seat lamps, seated, dismissed, the class door (L5709–L5736).
        public double? Ax15, Ab15, Al15, Bx15, Bb15, Bl15, Li15, Lv15, Do15;
        public string As15, Bs15, Lm15;
        public bool? Se15, Di15;
        // DL-16: the bridge, latched, the lever held, stored, the rack's counterweight (L5737–L5770).
        public double? Br16, Cw16;
        public bool? La16, He16;
        public int? Sn16;
        // DL-16a: the stool (x, state), the car (height, mode, clock), the tins and books ("x,base,state") (L6136–L6192).
        public double? Sx16a, H16a, Mt16a;
        public string Ss16a, M16a, Tin1_16a, Tin2_16a, Bk16a;
        // DL-17: the tray ("x,base,state"), drawer, read, key, the sluices, the tank and run, the beds, the latch, the stair door, the end (L5773–L5794, L6247–L6259).
        public string Ty17, Sl17, Be17;
        public double? Dr17, Tk17, Ru17, Lt17, Do17;
        public bool? Rd17, Ky17, Ld17, En17;

        /// <summary>DL-13's three steps (<c>s13</c>, comma-separated).</summary>
        public double[] Steps13() => Numbers(S13);

        /// <summary>A comma-separated list of numbers (<c>s13</c>, <c>be17</c>, the items' "x,base,state" without the state).</summary>
        public static double[] Numbers(string list)
        {
            var parts = list.Split(',');
            int n = 0;
            var v = new double[parts.Length];
            foreach (var t in parts)
                if (double.TryParse(t, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double d)) v[n++] = d;
            System.Array.Resize(ref v, n);
            return v;
        }

        /// <summary>Applies a chapter 1 field; false for a name that is not one.</summary>
        internal bool ApplyChapter1(string k, JsonElement v)
        {
            switch (k)
            {
                case "aw": Aw = Trace.S(v); return true;
                case "c12x": C12x = Trace.N(v); return true;
                case "c12b": C12b = Trace.N(v); return true;
                case "c12s": C12s = Trace.S(v); return true;
                case "f12x": F12x = Trace.N(v); return true;
                case "f12v": F12v = Trace.N(v); return true;
                case "g12y": G12y = Trace.N(v); return true;
                case "g12v": G12v = Trace.N(v); return true;
                case "p12": P12 = Trace.B(v); return true;
                case "pc12": Pc12 = v.GetInt32(); return true;
                case "f13x": F13x = Trace.N(v); return true;
                case "f13v": F13v = Trace.N(v); return true;
                case "l13": L13 = Trace.B(v); return true;
                case "t13": T13 = Trace.N(v); return true;
                case "k13": K13 = Trace.B(v); return true;
                case "s13": S13 = Trace.S(v); return true;
                case "tr13": Tr13 = Trace.N(v); return true;
                case "ba14": Ba14 = Trace.N(v); return true;
                case "bb14": Bb14 = Trace.N(v); return true;
                case "ta14": Ta14 = v.GetInt32(); return true;
                case "tb14": Tb14 = v.GetInt32(); return true;
                case "w14": W14 = v.GetInt32(); return true;
                case "j14": J14 = Trace.B(v); return true;
                case "px14": Px14 = Trace.N(v); return true;
                case "pb14": Pb14 = Trace.N(v); return true;
                case "ps14": Ps14 = Trace.S(v); return true;
                case "pe14": Pe14 = Trace.N(v); return true;
                case "pd14": Pd14 = Trace.B(v); return true;
                case "rt14": Rt14 = Trace.B(v); return true;
                case "du14": Du14 = Trace.B(v); return true;
                case "nt14a": Nt14a = Trace.N(v); return true;
                case "nk14a": Nk14a = Trace.B(v); return true;
                case "w1a": W1a = Trace.N(v); return true;
                case "w2a": W2a = Trace.N(v); return true;
                case "t1a": T1a = v.GetInt32(); return true;
                case "t2a": T2a = v.GetInt32(); return true;
                case "wn14a": Wn14a = v.GetInt32(); return true;
                case "do14a": Do14a = Trace.N(v); return true;
                case "op14a": Op14a = Trace.B(v); return true;
                case "gx14a": Gx14a = Trace.N(v); return true;
                case "gb14a": Gb14a = Trace.N(v); return true;
                case "gs14a": Gs14a = Trace.S(v); return true;
                case "bx14a": Bx14a = Trace.N(v); return true;
                case "bb14a": Bb14a = Trace.N(v); return true;
                case "bs14a": Bs14a = Trace.S(v); return true;
                case "tx14b": Tx14b = Trace.N(v); return true;
                case "td14b": Td14b = v.GetInt32(); return true;
                case "tm14b": Tm14b = Trace.S(v); return true;
                case "tt14b": Tt14b = Trace.N(v); return true;
                case "fx14b": Fx14b = Trace.N(v); return true;
                case "fs14b": Fs14b = Trace.S(v); return true;
                case "fo14b": Fo14b = Trace.N(v); return true;
                case "fk14b": Fk14b = Trace.B(v); return true;
                case "hd14b": Hd14b = Trace.N(v); return true;
                case "ax15": Ax15 = Trace.N(v); return true;
                case "ab15": Ab15 = Trace.N(v); return true;
                case "as15": As15 = Trace.S(v); return true;
                case "al15": Al15 = Trace.N(v); return true;
                case "bx15": Bx15 = Trace.N(v); return true;
                case "bb15": Bb15 = Trace.N(v); return true;
                case "bs15": Bs15 = Trace.S(v); return true;
                case "bl15": Bl15 = Trace.N(v); return true;
                case "li15": Li15 = Trace.N(v); return true;
                case "lv15": Lv15 = Trace.N(v); return true;
                case "lm15": Lm15 = Trace.S(v); return true;
                case "se15": Se15 = Trace.B(v); return true;
                case "di15": Di15 = Trace.B(v); return true;
                case "do15": Do15 = Trace.N(v); return true;
                case "br16": Br16 = Trace.N(v); return true;
                case "la16": La16 = Trace.B(v); return true;
                case "he16": He16 = Trace.B(v); return true;
                case "sn16": Sn16 = v.GetInt32(); return true;
                case "cw16": Cw16 = Trace.N(v); return true;
                case "sx16a": Sx16a = Trace.N(v); return true;
                case "ss16a": Ss16a = Trace.S(v); return true;
                case "h16a": H16a = Trace.N(v); return true;
                case "m16a": M16a = Trace.S(v); return true;
                case "mt16a": Mt16a = Trace.N(v); return true;
                case "t1_16a": Tin1_16a = Trace.S(v); return true;
                case "t2_16a": Tin2_16a = Trace.S(v); return true;
                case "bk16a": Bk16a = Trace.S(v); return true;
                case "ty17": Ty17 = Trace.S(v); return true;
                case "dr17": Dr17 = Trace.N(v); return true;
                case "rd17": Rd17 = Trace.B(v); return true;
                case "ky17": Ky17 = Trace.B(v); return true;
                case "sl17": Sl17 = Trace.S(v); return true;
                case "tk17": Tk17 = Trace.N(v); return true;
                case "ru17": Ru17 = Trace.N(v); return true;
                case "be17": Be17 = Trace.S(v); return true;
                case "lt17": Lt17 = Trace.N(v); return true;
                case "ld17": Ld17 = Trace.B(v); return true;
                case "do17": Do17 = Trace.N(v); return true;
                case "en17": En17 = Trace.B(v); return true;
                default: return false;
            }
        }
    }
}
