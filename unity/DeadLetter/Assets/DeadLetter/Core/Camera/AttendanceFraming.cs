using System;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Maths;

namespace DeadLetter.Core.Camera
{
    /// <summary>
    /// The prototype's framing for chapter 1 Attendance (region 6, DL-12 to DL-17) as <see cref="FramingZone"/> data,
    /// transcribed from <c>frameAtt</c> (index.html L6470–L6489: DL-12 to DL-14) and <c>frameAtt2</c> (L5855–L5879:
    /// DL-14a to DL-17), which <c>frameFor</c> hands region 6 to (L7669). Every zone is <c>fit(vol, width)</c>.
    /// <para>As written in the prototype, not as its comments say: DL-17's volume line is inside the comment that follows
    /// its cx line (L5877), so DL-17's frame moves cx only and keeps DL-16a's volume.</para>
    /// <para>The signals are published by <see cref="DeadLetter.Core.Streaming.ChapterPresenter"/>; the two eased ones
    /// (<c>k13</c>, <c>k15</c>) are the prototype's own camera state in <c>game.att</c>, kept by
    /// <see cref="AttendanceFramingState"/>.</para>
    /// <para>Past the prototype: the stair walk to ring A (<see cref="Stair"/>, #54/#56). The prototype cut to its end card
    /// 0.9 s up the stair, so it has no frame there; DL-17's caps cx at 339.0 and would lose him on the way to 347.0.</para>
    /// </summary>
    public static class AttendanceFraming
    {
        /// <summary>Signal: 1 while the duct act runs (<c>game.act.kind === 'att' &amp;&amp; what === 'duct'</c>, L5857).</summary>
        public const string Duct = "att.duct";
        /// <summary>Signal: <c>smooth(a.k13)</c>, the lesson's wide frame eased in time (L6481).</summary>
        public const string Lesson = "att.k13";
        /// <summary>Signal: DL-13's gallery frame, 1 when he is above 1.5 m, else 0.3 (<c>game.y &gt; 1.5 ? 1 : 0.3</c>, L6483).</summary>
        public const string Gallery = "att.gallery";
        /// <summary>Signal: <c>smooth(a.k15 ?? 1)</c>, DL-15's balcony frame over the classroom's (L5865).</summary>
        public const string Balcony = "att.k15";
        /// <summary>Signal: <c>smooth(a.f17.door17)</c>, DL-17's stair door, widening the workshop frame (L5876).</summary>
        public const string Door17 = "att.door17";

        /// <summary>
        /// Signal: the stair walk to ring A (<c>Dl17StairAct</c>), eased in over its first <see cref="StairEaseSeconds"/>; 1 at
        /// the stair head until the seam hands him to chapter 2 (the act ends on the step the seam falls due). 0 everywhere
        /// else, so no step of chapter 1 before the stair (all of the prototype's trace) changes.
        /// </summary>
        public const string Stair = "att.stair";
        public const double StairEaseSeconds = 0.5;

        /// <summary><see cref="Gallery"/> from his height (L6483).</summary>
        public static double GallerySignal(double y) => y > 1.5 ? 1 : 0.3;

        /// <summary><see cref="Stair"/>: <c>smooth(t / 0.5)</c> while he climbs (<paramref name="t"/>: the act's time), 1 at the head.</summary>
        public static double StairSignal(bool climbing, double t, bool atHead) =>
            climbing ? Smooth.Step(Math.Min(1, t / StairEaseSeconds)) : atHead ? 1 : 0;

        public static FramingTrack Build()
        {
            // DL-12: the bin, the bench and peg, the figure, the strip and the gate in one frame; then the corridor (L6472–L6475).
            FramingZone register = FramingZone.Named("dl12.register").WithCx(203.6, 207.0, 0.5).WithVolume(6.4, 1.45, 0.9, 8.8).WithFog(0.035);
            FramingZone corridor = FramingZone.Named("dl12.corridor").In(209.6, 1.2).WithCx(211.0, 214.5).WithVolume(5.8, 1.35, 0.85, 6.4);
            // DL-13: the figure, the seat and the brake; then, eased in time, the wide frame with the dial and the steps (L6479–L6482).
            FramingZone lesson = FramingZone.Named("dl13.seat").In(215.3, 1.8).WithCx(218.9, 219.8, 0.4).WithVolume(6.6, 1.6, 1.0, 7.6).WithFog(0.03);
            FramingZone wide = FramingZone.Named("dl13.wide").In(215.3, 1.8).Times(Lesson).WithCx(223.4, 224.6, 0.4).WithVolume(7.4, 2.0, 1.35, 11.0);
            // DL-13's gallery: full weight above 1.5 m, 0.3 below (L6483–L6484).
            FramingZone gallery = FramingZone.Named("dl13.gallery").In(227.4, 1.0).Times(Gallery).WithCx(229.0, 231.2).WithVolume(6.0, 2.6, 2.2, 6.4);
            // DL-14: the pole, the desk, both blinds and ledges, the hatch and the crank (L6486–L6487).
            FramingZone window = FramingZone.Named("dl14.room").In(232.4, 1.4).WithCx(237.6, 239.0, 0.4).WithVolume(7.0, 1.7, 1.25, 10.0).WithFog(0.03);

            // frameAtt2. DL-14a: the bunks, W1's blind, the crank, the eye and the door; DL-14b: the corridor and the trolley's round (L5860–L5863).
            FramingZone dorm = FramingZone.Named("dl14a.dorm").In(248.2, 0.6).WithCx(252.2, 259.4, 0.4).WithVolume(7.6, 2.1, 1.5, 11.2);
            FramingZone round = FramingZone.Named("dl14b.corridor").In(262.6, 1.2).WithCx(268.2, 273.4, 0.5).WithVolume(7.6, 1.9, 1.3, 13.0);
            // DL-15: the classroom, and over it the balcony by `high` (c15/v15 = room + (balc − room)·high), L5864–L5869.
            FramingZone classroom = FramingZone.Named("dl15.room").In(278.0, 0.8).WithCx(284.4, 289.0, 0.5).WithVolume(7.0, 1.7, 1.2, 9.6)
                .With(FramingZone.Named("dl15.balcony").Times(Balcony).WithCx(280.2, 281.3, 0.4).WithVolume(6.2, 2.5, 2.0, 7.2));
            FramingZone store = FramingZone.Named("dl16.store").In(293.4, 1.4).WithCx(297.4, 305.0, 0.5).WithVolume(7.2, 1.8, 1.2, 10.0);
            // DL-16a: the servery and the car, the gate, the passage over it and the stair down (L5873–L5874).
            FramingZone servery = FramingZone.Named("dl16a.servery").In(309.6, 1.2).WithCx(314.6, 319.4, 0.4).WithVolume(7.8, 2.5, 1.7, 11.5);
            // DL-17: cx only (see the class note), reaching 2.2 m further as the stair door opens (L5875–L5877).
            FramingZone workshop = FramingZone.Named("dl17.workshop").In(323.4, 1.4).WithCx(328.2, 336.8, 0.4).WithCxMaxSignal(Door17, 2.2);
            // The stair walk (not in the prototype, see the class note). cx follows him past DL-17's cap with no lead (he is
            // exited, L7668), and over the flight's height the frame eases into chapter 2's arrival frame as it will stand in
            // the world once he is handed over: the same cx and lens, and heights raised by the stair's top (chapter 2's origin)
            // less the rig's height follow at the top (+0.6·(3.24 − 0.2) on the camera, +0.5·… on the look; chapter 2's
            // datum is 0 there). So the seam changes the target frame by nothing.
            CameraConfig c = CameraConfig.Prototype;
            double follow = Dl17Lane.StairTop - c.HeightFollowFrom;
            FramingZone stair = FramingZone.Named("dl17.stair").Times(Stair).WithCx(339.0, double.PositiveInfinity, 0)
                .With(FramingZone.Named("dl17.stairhead").InY(0, Dl17Lane.StairTop)
                    .WithCx(SomeoneHomeFraming.ArrivalCxMin, SomeoneHomeFraming.ArrivalCxMax, SomeoneHomeFraming.ArrivalLead)
                    .WithVolume(SomeoneHomeFraming.ArrivalDistance,
                        SomeoneHomeFraming.ArrivalHeight + Dl17Lane.StairTop - c.HeightFollow * follow,
                        SomeoneHomeFraming.ArrivalLook + Dl17Lane.StairTop - c.LookFollow * follow, SomeoneHomeFraming.ArrivalFit)
                    .WithFog(SomeoneHomeFraming.ArrivalFog).WithFocal(SomeoneHomeFraming.ArrivalFocal));
            // The duct (L5857): the whole frame is the duct's, cx on him with no lead. frameAtt2 returns it outright; as the
            // last zone at weight 1 it replaces everything before it.
            FramingZone duct = FramingZone.Named("dl14.duct").Times(Duct).WithCx(double.NegativeInfinity, double.PositiveInfinity, 0)
                .WithVolume(7.0, 2.4, 1.6, 9.0).WithFog(0.03);

            return new FramingTrack(register, corridor, lesson, wide, gallery, window, dorm, round, classroom, store, servery, workshop, stair, duct);
        }
    }

    /// <summary>
    /// The prototype's eased camera state in <c>game.att</c>: <c>k13</c> (L5416) and <c>k15</c> (L5772), each
    /// <c>k += (want − k)·min(1, dt·0.9)</c> once a step in <c>updateAtt</c>, before <c>updateCamera</c>. <c>resetAtt</c>
    /// (every checkpoint start and respawn, L8018) clears them: k13 to 0, k15 to 1 (<c>?? 1</c>).
    /// </summary>
    public sealed class AttendanceFramingState
    {
        /// <summary>The ease rate, <c>dt · 0.9</c>.</summary>
        public const double Rate = 0.9;
        /// <summary>DL-13: past the steps (x &gt; 221.6) or up them (y &gt; 0.3) holds the wide frame (L5416).</summary>
        public const double LessonPastX = 221.6, LessonAboveY = 0.3;
        /// <summary>DL-15: the balcony frame above 1.0 m while x &lt; <c>ATT2.lift.x1 + 0.3</c> (L5772, L5521).</summary>
        public const double BalconyAboveY = 1.0, BalconyBeforeX = Dl15Lane.LiftX1 + 0.3;

        public double K13 { get; private set; }
        public double K15 { get; private set; } = 1;

        public void Reset() { K13 = 0; K15 = 1; }

        /// <summary>One step: <paramref name="lessonOn"/> is DL-13's lesson running (<c>L.on</c>).</summary>
        public void Step(bool lessonOn, double x, double y, double dt)
        {
            K13 = Damp.Toward(K13, lessonOn || x > LessonPastX || y > LessonAboveY ? 1 : 0, Rate, dt);
            K15 = Damp.Toward(K15, y > BalconyAboveY && x < BalconyBeforeX ? 1 : 0, Rate, dt);
        }

        /// <summary>The framing signals from this state (<see cref="AttendanceFraming.Lesson"/>, <see cref="AttendanceFraming.Balcony"/>).</summary>
        public void Publish(FramingSignalTable signals)
        {
            signals.Set(AttendanceFraming.Lesson, Smooth.Step(K13));
            signals.Set(AttendanceFraming.Balcony, Smooth.Step(K15));
        }
    }
}
