namespace DeadLetter.Core.Presentation
{
    /// <summary>The two sub-region light zones (<c>game.lightZone</c>, L2622–L2629): the Ration Hall in region 2, Up Only in region 4.</summary>
    public enum LightZone { None, Ration, UpOnly }

    /// <summary>
    /// The region lists of <c>setRegionLights</c> (L2631–L2657), one per <c>refs.*Lights</c> array (or single light) the
    /// prototype switches, plus <see cref="Always"/> for the lights no list holds (the hemisphere, the rim, the kick).
    /// Where a list switches its members one by one (<c>secretLights</c>, <c>spillLights</c>, <c>voiceLights</c>) each is its own group.
    /// </summary>
    public enum LightGroup
    {
        Always,
        Relay, Work, Spark, Cord, Pool,           // r1
        Cable, Door, Back, Search,                // r ≤ 2, not in the Ration Hall
        Crank,                                    // r1
        Dl02, Scanner,                            // dl02Lights (the scanner's also in r3)
        Dl03,                                     // r3
        Dl04Hall, Dl04Mid, UpOnly, Dl04Far, Dl05,
        SortingHall, Ration, Bay, Cage, RingC,
        Secret0, Secret1, End, RingCLook, Spill0, Spill1, Cot, Attendance,
        Voice0, Voice1, Voice2,
    }

    /// <summary>Which proxies a region and zone show (<c>setRegionLights</c>), and the zone's hysteresis (<c>lightZoneFor</c>).</summary>
    public static class LightRegions
    {
        // RATION5.x0 (L3447), UPONLY.x0 (L3455), OFF3/OFF5 (L274).
        public const double RationX0 = 47.9, UpOnlyX0 = 118.8, Off3 = 33, Off5 = 54;
        /// <summary><c>lightZoneFor</c>: the zone starts this far before its x, more once inside (hysteresis).</summary>
        public const double RationLead = 0.5, RationHold = 1.0, UpOnlyLead = 1.0, UpOnlyHold = 1.4;

        /// <summary><c>lightZoneFor(r)</c> (L2625–L2629): the zone for light region <paramref name="lightRegion"/>, his x and the zone he had.</summary>
        public static LightZone ZoneFor(int lightRegion, int gameRegion, double x, LightZone was)
        {
            if (lightRegion == 2 && x > RationX0 - (was == LightZone.Ration ? RationHold : RationLead)) return LightZone.Ration;
            if (lightRegion == 4 && gameRegion >= 4 && x > UpOnlyX0 - (was == LightZone.UpOnly ? UpOnlyHold : UpOnlyLead)) return LightZone.UpOnly;
            return LightZone.None;
        }

        /// <summary><c>setRegionLights(r, zone)</c>: whether group <paramref name="g"/> is shown (<paramref name="upper"/> = <c>game.upper</c>).</summary>
        public static bool Visible(LightGroup g, int r, LightZone zone, bool upper)
        {
            bool ration = zone == LightZone.Ration && r == 2, uo = zone == LightZone.UpOnly && r == 4;
            switch (g)
            {
                case LightGroup.Always: return true;
                case LightGroup.Relay: case LightGroup.Work: case LightGroup.Spark: case LightGroup.Cord: case LightGroup.Pool:
                case LightGroup.Crank: case LightGroup.Cot:
                    return r == 1;
                case LightGroup.Cable: case LightGroup.Door: case LightGroup.Back: case LightGroup.Search: return r <= 2 && !ration;
                case LightGroup.Dl02: return r == 2;
                case LightGroup.Scanner: return r == 2 || r == 3;
                case LightGroup.Dl03: return r == 3;
                case LightGroup.Dl04Hall: return (r == 4 && !uo) || (r == 3 && upper);
                case LightGroup.Dl04Mid: return r == 4 && !uo;
                case LightGroup.UpOnly: return uo || r == 5;
                case LightGroup.Dl04Far: return r == 4;
                case LightGroup.Dl05: return r == 5 || uo;
                case LightGroup.SortingHall: return r == 2 && !ration;
                case LightGroup.Ration: return ration;
                case LightGroup.Bay: return r == 2;
                case LightGroup.Cage: return r == 4 && !uo;
                case LightGroup.RingC: return r == 5 || uo;
                case LightGroup.Secret0: return r == 3;
                case LightGroup.Secret1: return r == 4 && !uo;
                case LightGroup.End: return r == 5;
                case LightGroup.RingCLook: return r == 5 || uo;
                case LightGroup.Spill0: return r == 3 && !upper;
                case LightGroup.Spill1: return r == 4 && !uo;
                case LightGroup.Attendance: return r == 6;
                case LightGroup.Voice0: return r == 2 && !ration;
                case LightGroup.Voice1: return r == 3 && !upper;
                case LightGroup.Voice2: return r == 5;
                default: return false;
            }
        }
    }

    /// <summary>
    /// <c>game.lightRegion</c> and <c>game.lightZone</c>: the light region lags the game region where the prototype switches
    /// lights early or late (§4.20's table): DL-01's passage turns region 2's on at the transit's first leg (L2149), DL-06's
    /// floor stays on region 2's lights until the scan starts (L2781; on a reset, region 3 not yet scanned is lit as 2,
    /// L8055), the shaft and ring C switch on the camera's x (L3237–L3238, L3560–L3561). The zone follows every frame (L4924–L4925).
    /// </summary>
    public sealed class LightRegionTracker
    {
        public int Region { get; private set; } = 1;
        public LightZone Zone { get; private set; }
        /// <summary>The lists changed at the last <see cref="Place"/> or <see cref="Update"/>.</summary>
        public bool Changed { get; private set; }

        /// <summary>A reset (<c>resetWorld</c>, L8055): region 3 before the scan is lit as region 2.</summary>
        public void Place(int gameRegion, bool scanned, double x, bool upper = false)
        {
            Region = gameRegion == 3 && !scanned ? 2 : gameRegion;
            Zone = LightRegions.ZoneFor(Region, gameRegion, x, LightZone.None);
            Changed = true;
        }

        /// <summary>
        /// One frame: <paramref name="transitLeg"/> ≥ 1 in DL-01's passage, <paramref name="scanning"/> once DL-06's scan has
        /// started (or is done), <paramref name="cameraX"/> for the shaft's and ring C's switches.
        /// </summary>
        public void Update(int gameRegion, double x, double cameraX, int transitLeg, bool scanning)
        {
            int was = Region;
            LightZone wasZone = Zone;
            int r = Region;
            if (gameRegion == 1) r = transitLeg >= 1 ? 2 : 1;                                             // L2149
            else if (gameRegion == 2) r = 2;
            else if (gameRegion == 3 && r < 3 && scanning) r = 3;                                       // L2781
            else if (gameRegion == 3 && r > 3) r = 3;
            if (gameRegion == 4 && r == 3 && cameraX > LightRegions.Off3 + 54) r = 4;                     // L3237
            else if (r == 4 && (gameRegion == 3 || (gameRegion == 4 && cameraX < LightRegions.Off3 + 53))) r = 3;   // L3238
            if (gameRegion == 5 && r == 4 && x > LightRegions.Off5 + 79.6) r = 5;                        // L3560
            else if (r == 5 && (gameRegion != 5 || x < LightRegions.Off5 + 79.2)) r = 4;                 // L3561
            if (gameRegion == 6) r = 6;
            Region = r;
            Zone = LightRegions.ZoneFor(r, gameRegion, x, Zone);
            Changed = was != Region || wasZone != Zone;
        }
    }
}
