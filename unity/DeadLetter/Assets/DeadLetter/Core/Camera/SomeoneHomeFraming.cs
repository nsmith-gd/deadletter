using DeadLetter.Core.Lane.Tables;

namespace DeadLetter.Core.Camera
{
    /// <summary>
    /// Chapter 2 Someone Home's framing (region 7, DL-18 and DL-19; #53) as <see cref="FramingZone"/> data. Chapter 2 has no
    /// prototype: the source is each scene doc's §7 (Camera), which gives the x ranges, what each frame holds and the lens
    /// (DL-18: 32 and 40 mm; DL-19: 38 and 30 mm), and no volumes. In chapter 2's lane coordinates, ring A's datum (y 0 at
    /// the stair top); <see cref="CameraRig.UseTrack"/> places them at <c>ChapterSeams.Origin</c> (#53's comment).
    /// <para>Where §7 gives no number, chapter 1's nearest is taken (<see cref="AttendanceFraming"/>), as noted on each
    /// zone: the gallery's and the terrace landing's volumes are DL-15's and DL-16a's, the leads are DL-14's to DL-16a's
    /// (0.4–0.5), the fog is chapter 1's last (0.03), and zones with no lens keep the prototype's 35 mm. The volumes of the zones §7 does describe are sized so that what it
    /// says the frame holds is in frame at rest on 16:9 (<c>SomeoneHomeFramingTests</c>). Heights are lane heights, before
    /// the rig's height follow (<c>+0.6·(y − 0.2)</c> on the camera, <c>+0.5·…</c> on the look); the raised floors set
    /// theirs lower so that, with it, he sits as low in frame as on chapter 1's.</para>
    /// <para>Each blend starts at §7's boundary (<see cref="FramingZone.In"/>), so a frame holds over its whole range and
    /// the rig's lag eases into the next. No signals and no authored shots (DL-18 §7: none; DL-19's <c>witness</c> is a
    /// directed moment, not framing).</para>
    /// </summary>
    public static class SomeoneHomeFraming
    {
        /// <summary>DL-18 §7: the arrival and box room lenses; the gallery is "normal framing" (35 mm).</summary>
        public const double ArrivalFocal = 32, BoxRoomFocal = 40;
        /// <summary>DL-19 §7: the repair and upper terrace lenses.</summary>
        public const double RepairFocal = 38, UpperTerraceFocal = 30;

        /// <summary>DL-18 §7, the box room's frame: the box room door to the landing doorway's far side, floor to the frame's top (1.5).</summary>
        public const double BoxRoomHoldX0 = Dl18Lane.RoomDoorX, BoxRoomHoldX1 = Dl18Lane.LandingX0, BoxRoomHoldTop = 1.5;
        /// <summary>DL-19 §7, the repair's frame: the jack bay (362.5) to the top of the upper flight, floor (1.2) to the drip tube's top (2.5).</summary>
        public const double RepairHoldX0 = 362.5, RepairHoldX1 = Dl19Lane.FlightX1, RepairHoldBottom = Dl19Lane.FloorY, RepairHoldTop = 2.5;

        public static FramingTrack Build()
        {
            // DL-18 §7 "Arrival", 347.0 to 349.5: wider and lifted (32 mm), the sealed door (347.4–348.6) left, the gallery
            // ahead and the window high across the shaft in one frame while he walks. cx held near the gallery's middle so the
            // door stays in; fog: chapter 1's last (0.03, DL-14 to DL-17).
            FramingZone arrival = FramingZone.Named("dl18.arrival").WithCx(349.4, 350.0, 0.4).WithVolume(8.4, 2.6, 1.8, 10.0)
                .WithFog(0.03).WithFocal(ArrivalFocal);
            // §7 "Gallery", 349.5 to 351.4: normal framing (35 mm), the window drifting out of the top. §7 gives no volume:
            // DL-15's classroom (7.0, 1.7, 1.2, fit 9.6) and its lead (0.5), chapter 1's plain room frame.
            FramingZone gallery = FramingZone.Named("dl18.gallery").In(349.5, 1.0).WithCx(350.0, 351.4, 0.5).WithVolume(7.0, 1.7, 1.2, 9.6)
                .WithFocal(35);
            // §7 "Box room", 351.6 to 355.0: closer and lower (40 mm), door to landing doorway, floor to frame top, the
            // whole puzzle in one still frame while he thinks: cx fixed on the room's middle, no lead.
            double room = (BoxRoomHoldX0 + BoxRoomHoldX1) / 2;
            FramingZone boxRoom = FramingZone.Named("dl18.boxroom").In(Dl18Lane.RoomDoorX - 0.4, 0.8).WithCx(room, room, 0)
                .WithVolume(5.4, 1.5, 1.2, 5.2).WithFocal(BoxRoomFocal);
            // §7 "Terrace landing", 355.0 on: eases wider with the shaft behind the rail, handing to DL-19. §7 gives no lens or
            // volume: 35 mm, and DL-16a's servery (7.8 back, fit 11.5; lead 0.4) with its heights lowered by the landing's
            // height follow (floor 1.2: +0.6 camera, +0.5 look).
            FramingZone landing = FramingZone.Named("dl18.landing").In(Dl18Lane.LandingX0, 1.2).WithCx(356.4, 359.6, 0.4)
                .WithVolume(7.8, 1.9, 1.2, 11.5).WithFocal(35);

            // DL-19 §7 "The repair", 361.5 to 366.5: lower and a little closer (38 mm), the jack bay, tracks, pocket,
            // bracket, the whole half landing and the top of the upper flight, floor to Barnaby, held while he thinks: cx held
            // on the middle of that (lead: DL-14's room, 0.4). Heights lowered for the floor's height follow, as the landing's.
            double repair = (RepairHoldX0 + RepairHoldX1) / 2;
            FramingZone repairZone = FramingZone.Named("dl19.repair").In(361.0, 1.0).WithCx(repair - 0.1, repair + 0.1, 0.4)
                .WithVolume(6.6, 1.5, 1.4, 6.8).WithFocal(RepairFocal);
            // §7 "Upper terrace", 367.4 to 377.0: eases wider and higher (30 mm), the shaft beside him, the window across it
            // and the gallery below. §7 gives no volume: DL-16a's back (7.8; fit 11.5) and its lead (0.4), following him on
            // from 370.4 (the lane beyond is DL-20's), heights lowered for the terrace's height follow (2.3: +1.26, +1.05),
            // still "higher" than the repair's.
            FramingZone upper = FramingZone.Named("dl19.upper").In(366.5, 1.4).WithCx(370.4, double.PositiveInfinity, 0.4)
                .WithVolume(7.8, 2.1, 1.3, 11.5).WithFocal(UpperTerraceFocal);

            return new FramingTrack(arrival, gallery, boxRoom, landing, repairZone, upper);
        }
    }
}
