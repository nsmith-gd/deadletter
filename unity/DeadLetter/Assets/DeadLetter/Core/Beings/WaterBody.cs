namespace DeadLetter.Core.Beings
{
    /// <summary>The White's part in a body of water (L7040–L7046).</summary>
    public enum WaterPart
    {
        /// <summary>It rolls once when something calls it; never touches him (DL-06's heap).</summary>
        Glimpse,
        /// <summary>It rears and slaps him back off the edge, unhurt (DL-07's shaft sump: the safe first meeting).</summary>
        Scare,
        /// <summary>It warns once (hiss, sink), then strikes and drags him under (DL-09/DL-11's flooded lane).</summary>
        Hunt,
    }

    /// <summary>
    /// One body of water the White lives in: the prototype's <c>WATERS</c> entries (L7047–L7048, L7238–L7239,
    /// L7326–L7330). In Unity these are filled from the <c>MECH_Water_*</c> empties (§4.15); the factories hold the
    /// prototype's values (x resolved from the OFF constants of L274, Unity z = −three z).
    /// </summary>
    public sealed class WaterBody
    {
        /// <summary>Stable name (<c>heap</c>, <c>sump7</c>, <c>lane9</c>): Show cues and saves refer to it.</summary>
        public string Id;
        /// <summary>The <c>game.region</c> it belongs to; it is only active while he is in that region.</summary>
        public int Region;
        public double X0, X1;
        /// <summary>Surface height.</summary>
        public double Y;
        /// <summary>Lane-relative depth of its centre, Unity sign (+ into the set).</summary>
        public double Z;
        public WaterPart Part;
        /// <summary>The White's scale here: its body is 2.5·scale long and stays inside the water (L7183–L7186).</summary>
        public double Scale = 1;
        /// <summary>How far onto an edge it strikes from its snout (<c>w.reach || 1.2</c>, L7148).</summary>
        public double Reach = 1.2;
        /// <summary>Ledge height above the surface its slap and lunge clips are placed for (<c>w.ledgeH ?? 0.25</c>, L7157).</summary>
        public double LedgeH = 0.25;
        /// <summary>Where he stands beside the water: pairs (x0, x1), flattened (L7108).</summary>
        public double[] Edges = new double[0];
        /// <summary>Active only while he is left of this x (<c>active()</c>); +∞ when unbounded.</summary>
        public double ActiveBelowX = double.PositiveInfinity;
        /// <summary>Active only while he is not on the upper level (<c>!game.upper</c>, the heap L7327).</summary>
        public bool LowerOnly;
        /// <summary>First sighting: where it surfaces (NaN: none).</summary>
        public double ShowX = double.NaN;
        /// <summary>First sighting triggered by his position: x &gt; this (lane L7271). NaN: a scene posts a Show cue.</summary>
        public double ShowWhenHeroPastX = double.NaN;
        /// <summary>The sighting's splash (0 for none; the heap's is silent, L4996).</summary>
        public double ShowSplash = 0.5;
        /// <summary>Whether the sighting forgets what it heard (the sump and lane do, the heap does not: L7272, L7372, L4996).</summary>
        public bool ShowClearsHeard = true;

        public double Centre => (X0 + X1) / 2;

        /// <summary>He is beside the water (on an edge) or in it, below its surface + 0.05 (<c>heroNearWater</c>, L7108).</summary>
        public bool HeroNear(double x, double y)
        {
            for (int i = 0; i + 1 < Edges.Length; i += 2) if (x > Edges[i] && x < Edges[i + 1]) return true;
            return x > X0 && x < X1 && y < Y + 0.05;
        }

        /// <summary>DL-06's heap pit: a glimpse, from the sorting floor only (L7327, OFF3 = 33). Shown on the first
        /// bucket weight (L4996) by a Show cue.</summary>
        public static WaterBody Heap() => new WaterBody
        {
            Id = "heap", Region = 3, X0 = 69.62, X1 = 71.93, Y = -0.75, Z = -0.85, Part = WaterPart.Glimpse, Scale = 0.5,   // L7327
            LowerOnly = true,                                                                                               // L7327
            ShowX = 70.8, ShowSplash = 0, ShowClearsHeard = false,                                                          // L4996
        };

        /// <summary>DL-07/08's shaft sump (SHAFT 85.8–88.3, L3011): the scare. Shown on the platform's first rise past
        /// 0.08 (L7372) by a Show cue.</summary>
        public static WaterBody Sump7() => new WaterBody
        {
            Id = "sump7", Region = 4, X0 = 85.8, X1 = 88.3, Y = -0.15, Z = -1.2, Part = WaterPart.Scare, Scale = 0.55,      // L7328
            Reach = 1.7, Edges = new[] { 85.8, 88.6 }, ActiveBelowX = 91.3,                                                 // L7328–L7329
            ShowX = 87.05,                                                                                                  // L7372
        };

        /// <summary>DL-11's flooded lane (OFF5 = 54): the hunt. It shows itself far off the first time he comes along it
        /// (x &gt; 145.3 → surfaces at 149.9, L7271–L7272).</summary>
        public static WaterBody Lane9() => new WaterBody
        {
            Id = "lane9", Region = 5, X0 = 145.95, X1 = 150.6, Y = -0.1, Z = 0.64, Part = WaterPart.Hunt, Scale = 0.8,     // L7238
            LedgeH = 0.1, Reach = 1.35, Edges = new[] { 145.7, 150.6 }, ActiveBelowX = 153.5,                               // L7238–L7239
            ShowX = 149.9, ShowWhenHeroPastX = 145.3,                                                                       // L7271–L7272
        };
    }

    /// <summary>
    /// DL-11's two cues on the lane (L7237, L7240–L7251), for the <c>dl11.bell</c> and <c>dl11.junction</c> mechanisms to
    /// post: the doorbell lures it to C-108's sunken step for 12 s; the junction drops the live cable in and it flees 20 s.
    /// </summary>
    public static class Lane9Cues
    {
        public const double BellX = 145.72, BellNose = 146.4, BellRing = 12;   // BELL9, L7237
        public const double JunctionX = 148.92, FleeFor = 20, ShortFor = 3.5;  // JUNCTION9 L7237, L7248–L7250
        public const int Region = 5;

        /// <summary><c>ringBell9</c>, L7241–L7245: a lure from the right (dir −1) at the nose point, then a loud ring.</summary>
        public static void RingBell(NoiseBus bus)
        {
            bus.Post(NoiseEvent.Lure(BellNose, BellRing, -1));
            bus.Post(NoiseEvent.Sound(BellNose, 1.5, Region));
        }

        /// <summary><c>throwJunction9</c>, L7246–L7251 (the White's part: <c>scareWhite(20)</c>).</summary>
        public static void ThrowJunction(NoiseBus bus) => bus.Post(NoiseEvent.Scare(FleeFor));
    }
}
