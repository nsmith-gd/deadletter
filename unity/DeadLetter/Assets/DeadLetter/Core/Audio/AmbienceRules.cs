namespace DeadLetter.Core.Audio
{
    /// <summary>What <c>sceneAmbience()</c> reads from the game (index.html L8147–L8162). Scene rules fill it each frame.</summary>
    public struct AmbienceContext
    {
        /// <summary><c>game.region</c>: 1 DL-01; 2 DL-02–05; 3 DL-06–07; 4 DL-08–10; 5 DL-11; 6 chapter one.</summary>
        public int Region;
        public double X;
        /// <summary><c>game.revealed</c>: the DL-04 racks reveal has happened.</summary>
        public bool Revealed;
        /// <summary><c>past(checkpoint, 'scanned')</c>.</summary>
        public bool PastScanned;
        /// <summary><c>game.dl4.awed</c>: the city's awe stop has played.</summary>
        public bool Awed;
        /// <summary><c>game.ch1.cage.phase === 'caught'</c>.</summary>
        public bool CageCaught;
        /// <summary><c>past(checkpoint, 'landing8')</c>.</summary>
        public bool PastLanding8;
        /// <summary><c>persist.cageDanger</c>: from the slip, through every retry.</summary>
        public bool CageDanger;
        /// <summary><c>game.ch1.uo.riding</c>: riding the Up Only car.</summary>
        public bool RidingUpOnly;
        /// <summary><c>past(checkpoint, 'bedroom')</c>.</summary>
        public bool PastBedroom;
    }

    /// <summary>The ambience a scene wants: a loop key (null = silence) and its options for <see cref="MusicDirectorModel.Ambience"/>.</summary>
    public struct AmbienceChoice
    {
        public string Name;
        public double Scale, FadeIn, FadeOut;

        public static AmbienceChoice Of(string name, double scale = 1, double fadeIn = MusicDirectorModel.AmbienceCrossfade) =>
            new AmbienceChoice { Name = name, Scale = scale, FadeIn = fadeIn, FadeOut = MusicDirectorModel.AmbienceCrossfade };
    }

    /// <summary>
    /// The prologue's ambience map (index.html <c>sceneAmbience</c> L8147–L8162, <c>updateAmbience</c> L8163–L8168;
    /// docs/prologue_music.md's beat map). Cues hide the ambience on their own; chapter one (region 6) uses the bed.
    /// </summary>
    public static class AmbienceRules
    {
        // index.html constants: OFF2..OFF5 (L274), GATE_X (L323), RATION5 (L3447), CG (L3899), UPONLY (L3455), AWE_X (L3018).
        public const double Off2 = 13, Off3 = 33, Off4 = 42, Off5 = 54;
        public const double GateX = Off2 + 17.6;
        public const double Ration5X0 = Off2 + 34.9;
        public const double CgX0 = Off3 + 64.6;
        public const double UpOnlyX0 = Off4 + 76.8;
        public const double AweX = Off4 + 71.3;
        /// <summary>The cage-danger loop fades in over 1 s (L8157); leaving it fades out over 2 s (L8166).</summary>
        public const double FailureFadeIn = 1, FailureFadeOut = 2;
        public const double RingCScale = 0.6;

        /// <summary><c>sceneAmbience()</c>, L8147–L8162.</summary>
        public static AmbienceChoice SceneAmbience(in AmbienceContext c)
        {
            double x = c.X;
            switch (c.Region)
            {
                case 1:
                    return AmbienceChoice.Of("lower_works");
                case 2:   // the racks, then the ration hall (L8150)
                    return AmbienceChoice.Of(x < GateX || !c.Revealed ? "lower_works" : x < Ration5X0 ? "heaps" : "order");
                case 3:   // the scanner's corridor is the Order's (L8151)
                    return AmbienceChoice.Of(c.PastScanned ? "lower_works" : "order");
                case 4:
                    if (x < CgX0) return AmbienceChoice.Of("lower_works");
                    if (x > UpOnlyX0) return c.RidingUpOnly ? AmbienceChoice.Of("heaps", RingCScale) : AmbienceChoice.Of("order");   // L8154
                    if (c.Awed && x > AweX - 0.1) return AmbienceChoice.Of("order");          // the city's cue hands to the march (L8155)
                    if (c.CageCaught || c.PastLanding8) return AmbienceChoice.Of(null);        // silence into the tunnel (L8156)
                    if (c.CageDanger) return AmbienceChoice.Of("failure", 1, FailureFadeIn); // from the slip, through every retry (L8157)
                    return AmbienceChoice.Of("lower_works");
                case 5:   // ring C, low; the bedroom is quiet (L8160)
                    return AmbienceChoice.Of(c.PastBedroom ? null : "heaps", RingCScale);
                default:
                    return AmbienceChoice.Of(null);
            }
        }

        /// <summary><c>updateAmbience()</c>, L8163–L8168: every frame in play, except in chapter one.</summary>
        public static void Apply(MusicDirectorModel music, in AmbienceContext c, double now)
        {
            if (c.Region == 6) return;
            AmbienceChoice a = SceneAmbience(c);
            if (music.AmbienceWant == "failure" && a.Name != "failure") a.FadeOut = FailureFadeOut;
            music.Ambience(a.Name, now, a.FadeIn, a.FadeOut, a.Scale);
        }
    }
}
