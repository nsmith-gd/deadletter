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

        /// <summary>DL-13's three steps (<c>s13</c>, comma-separated).</summary>
        public double[] Steps13()
        {
            var parts = S13.Split(',');
            var v = new double[parts.Length];
            for (int i = 0; i < parts.Length; i++) v[i] = double.Parse(parts[i], System.Globalization.CultureInfo.InvariantCulture);
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
                default: return false;
            }
        }
    }
}
