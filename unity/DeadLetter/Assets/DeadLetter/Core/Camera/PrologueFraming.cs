using DeadLetter.Core.Maths;

namespace DeadLetter.Core.Camera
{
    /// <summary>
    /// The prototype's framing for DL-01 to DL-07 (the floor and gallery) as <see cref="FramingZone"/> data, transcribed
    /// from <c>frameFor</c> (index.html L7667–L7726) with OFF2/OFF3 resolved (L274). It is the reference the scene
    /// definitions' <c>CAM_</c> data is checked against, and the parity fixture for the tests. Not yet transcribed (they
    /// arrive with their scene ports, U-20/21/22): DL-07's <c>watchLoad</c> wide frame (its centre and width follow x,
    /// L7713–L7720), DL-08–DL-10 (<c>k4</c>, L7728–L7753) and DL-11 (<c>k5</c>, L7755–L7772). Chapter 1's
    /// (<c>frameAtt</c>, <c>frameAtt2</c>) is <see cref="AttendanceFraming"/>; <see cref="ChapterFraming"/> picks the track.
    /// </summary>
    public static class PrologueFraming
    {
        /// <summary>Signal: DL-02–DL-05's frames are live (region 2, or the passage out of DL-01), L7673.</summary>
        public const string Dl02 = "dl02";
        /// <summary>Signal: DL-03's solution widens to the racks for a few seconds, L7685.</summary>
        public const string Dl02Reveal = "dl02.reveal";
        /// <summary>Signal: 1 once he has realised (region 2), L7688.</summary>
        public const string Dl02Realised = "dl02.realised";
        /// <summary>Signal: DL-06's pit after the refusal, L7724.</summary>
        public const string Dl06Pit = "dl06.pit";

        /// <summary>
        /// <c>k</c>, L7673: 1 in region 2; on the DL-01 → DL-02 passage (transit stage ≥ 1) <c>smooth((x − 10.4)/2.8)</c>.
        /// Pass <paramref name="transitStage"/> −1 when not in transit.
        /// </summary>
        public static double Dl02Signal(int region, int transitStage, double x) =>
            region == 2 ? 1 : transitStage >= 1 ? Smooth.Step((x - 10.4) / 2.8) : 0;

        /// <summary><c>kr</c>, L7685: a slow pan to the racks, <paramref name="secondsSinceReveal"/> after the reveal.</summary>
        public static double RevealSignal(double secondsSinceReveal) =>
            Smooth.Step(secondsSinceReveal / 3.6) * (1 - Smooth.Step((secondsSinceReveal - 9.5) / 3.0));

        /// <summary><c>kp</c>, L7724 (SCAN.REVEAL 4.0, SCAN.CHECK 17.2, L2465); <paramref name="scanT"/> in phase reveal/check.</summary>
        public static double PitSignal(bool revealOrCheck, double scanT) =>
            revealOrCheck ? Smooth.Step((scanT - 4.0) / 3.0) * (1 - Smooth.Step((scanT - 17.2 - 0.8) / 2.5)) : 0;

        public static FramingTrack Build()
        {
            // DL-01: alcove → hall (6.9) → bulkhead (8.9); in the hall (inHall) the lead is softened by 0.6 (L7670–L7672).
            FramingZone alcove = FramingZone.Named("dl01.alcove").WithCx(1.2, 10.6).WithVolume(5.2, 1.0, 0.8).WithFog(0.075);
            FramingZone hallLead = FramingZone.Named("dl01.hallLead").In(6.9, 0.9).Out(8.9, 0.8);
            hallLead.LeadSoften = 0.6;
            FramingZone hall = FramingZone.Named("dl01.hall").In(6.9, 0.9).WithVolume(9.2, 2.35, 1.95).WithFog(0.043);
            FramingZone bulk = FramingZone.Named("dl01.bulk").In(8.9, 0.8).WithVolume(6.0, 1.15, 0.9).WithFog(0.075);

            // DL-02 to DL-05 (L7674–L7702), in the prototype's order; every zone is inside its `if (k > 0)`.
            FramingZone room = FramingZone.Named("dl03.room").When(Dl02).Times(Dl02).WithVolume(5.9, 1.2, 0.85, 6.2).WithFog(0.06);
            room.HasCx = true; room.Pivot = 28.0; room.Offset = 0.05; room.Gain = 0.2; room.LeadK = 0; room.CxMin = 28.0; room.CxMax = 28.35;
            FramingZone racks = FramingZone.Named("dl04.racks").When(Dl02).Times(Dl02).In(30.3, 1.4).WithCx(32.0, 37.4).WithVolume(7.4, 1.6, 1.1, 6.4).WithFog(0.045);
            FramingZone reveal = FramingZone.Named("dl04.reveal").When(Dl02).Times(Dl02Reveal).WithCx(33.7, 33.7, 0).WithVolume(10.8, 2.7, 1.45, 9.5).WithFog(0.03);
            FramingZone couriers = FramingZone.Named("dl04.couriers").When(Dl02).Times(Dl02Realised).In(30.7, 0.5).Out(35.6, 1.2)
                .WithCx(32.2, 37.0, 0, 0.4).WithVolume(6.2, 0.95, 0.72, 6.0);
            couriers.CxWeightScale = 0.6;
            FramingZone bay = FramingZone.Named("dl04.bay").When(Dl02).In(38.4, 1.4).WithCx(41.6, 44.9, 0.5).WithVolume(6.2, 1.15, 0.8, 7.0).WithFog(0.05);
            FramingZone ration = FramingZone.Named("dl05.shrine").When(Dl02).In(47.1, 1.2).WithCx(49.6, 51.6, 0.6).WithVolume(6.4, 1.25, 0.8, 6.8).WithFog(0.045)
                .With(FramingZone.Named("dl05.counter").In(51.6, 1.4).WithCx(53.8, 57.2, 0.3));
            FramingZone sortingHall = FramingZone.Named("dl02.hall").When(Dl02).Out(24.4, 1.2).WithCx(15.2, 20.9, 0.6).WithVolume(6.6, 1.55, 0.95, 8.4).WithFog(0.05);

            // DL-06/07: scanner corridor → sorting floor (62.6) → up the ramp to the gallery (by y), L7704–L7721.
            FramingZone floor = FramingZone.Named("dl06.corridor").In(58.4, 1.6).WithCx(60.6, 62.6, 0.6).WithVolume(5.4, 1.15, 0.85, 5.0).WithFog(0.05)
                .With(
                    FramingZone.Named("dl06.floor").In(62.6, 1.0).WithCx(64.8, 67.2, 0.5).WithVolume(6.6, 1.35, 0.85, 6.6),
                    FramingZone.Named("dl07.gallery").InY(0.2, 1.2).WithCx(73.2, 78.4).WithVolume(7.0, 1.4, 0.9, 7.0).WithFog(0.038));
            // The pit after the refusal (inside `if (k3 > 0)`: a hard step at 58.4), L7722–L7725.
            FramingZone pit = FramingZone.Named("dl06.pit").In(58.4, 0).Times(Dl06Pit).WithCx(70.9, 70.9, 0).WithVolume(11.5, 2.5, -0.7, 12.2).WithFog(0.028);

            return new FramingTrack(alcove, hallLead, hall, bulk, room, racks, reveal, couriers, bay, ration, sortingHall, floor, pit);
        }
    }
}
