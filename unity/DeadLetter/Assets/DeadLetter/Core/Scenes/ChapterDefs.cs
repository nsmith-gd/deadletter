using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Scenes.Dl01;
using DeadLetter.Core.Scenes.Dl02;
using DeadLetter.Core.Scenes.Dl03;
using DeadLetter.Core.Scenes.Dl04;
using DeadLetter.Core.Scenes.Dl05;
using DeadLetter.Core.Scenes.Dl06;
using DeadLetter.Core.Scenes.Dl12;
using DeadLetter.Core.Scenes.Dl13;
using DeadLetter.Core.Scenes.Dl14;
using DeadLetter.Core.Scenes.Dl14a;
using DeadLetter.Core.Scenes.Dl14b;
using DeadLetter.Core.Scenes.Dl15;
using DeadLetter.Core.Scenes.Dl16;
using DeadLetter.Core.Scenes.Dl16a;

namespace DeadLetter.Core.Scenes
{
    /// <summary>The chapters, as Core builds them. A scene joins one by being listed here in lane order.</summary>
    public static class ChapterDefs
    {
        /// <summary>The prologue's ID (the save's scene key).</summary>
        public const string PrologueId = "prologue";

        /// <summary>The prototype's x offsets of the later sets (<c>OFF2</c>…<c>OFF5</c>, L274).</summary>
        public const double Off2 = 13, Off3 = 33, Off4 = 42, Off5 = 54;
        /// <summary><c>CG.top</c> (L3900) and <c>DECK</c> (L3007): the cage's top and the balcony deck.</summary>
        public const double CageTop = 3.4, Deck = 1.6;

        /// <summary>
        /// The prologue's checkpoints (<c>CHECKPOINTS</c>, L7975–L7997; port_architecture §5) in the save's order
        /// (<see cref="Checkpoint.PrototypeOrder"/>, which runs on into chapter 1): where each puts D-17 (lane x, feet y,
        /// facing, region) and the scene that owns it (<c>sceneName</c> at that spot, L8135–L8144). <c>resetWorld</c>
        /// faces him +x at every checkpoint (L8019) and puts him at <c>c.y</c> where there is one (L4113); the region is
        /// <c>c.region || 1</c> (L8026). The later scenes' rows are here already, so a save made there names a place.
        /// </summary>
        public static CheckpointTable PrologueCheckpoints { get; } = new CheckpointTable(Checkpoint.PrototypeOrder,
            new CheckpointDef("start", 1.0, region: 1, scene: "DL-01"),                                     // START_X, L302
            new CheckpointDef("shutter", 2.9, region: 1, scene: "DL-01"),
            new CheckpointDef("hall", 8.35, region: 1, scene: "DL-01"),
            new CheckpointDef("door", 9.62, region: 1, scene: "DL-01"),
            new CheckpointDef("room", 13.2, region: 2, scene: "DL-02"),                                      // EMERGE_X, L319
            new CheckpointDef("weighroom", Off2 + 12.9, region: 2, scene: "DL-03"),
            new CheckpointDef("solved", Off2 + 16.95, region: 2, scene: "DL-03"),
            new CheckpointDef("bay", Dl04Lane.DoorX1 + 0.4, region: 2, scene: "DL-04"),                    // RK.door.x1 + 0.4
            new CheckpointDef("ration", Dl05Lane.HallX0 + 0.7, region: 2, scene: "DL-05"),                 // RATION5.x0 + 0.7
            new CheckpointDef("hatch", Dl05Lane.CrawlX1 + 0.35, region: 2, scene: "DL-05"),                // RH5.crawl[1] + 0.35
            new CheckpointDef("scanned", Off3 + 30.3, region: 3, scene: "DL-06"),
            new CheckpointDef("landing", Off3 + 40.0, region: 3, scene: "DL-07"),                           // past landing is DL-07's
            new CheckpointDef("gallery", Off3 + 42.3, region: 3, scene: "DL-07"),
            new CheckpointDef("goods", Off3 + 48.9, region: 4, scene: "DL-08"),
            new CheckpointDef("latched", Off3 + 56.2, region: 4, scene: "DL-08"),
            new CheckpointDef("cage", Off3 + 67.8, CageTop, region: 4, scene: "DL-09"),                     // x ≥ CG.x0
            new CheckpointDef("landing8", Off3 + 70.3, Deck, region: 4, scene: "DL-09"),                    // CG.landing = DECK
            new CheckpointDef("tunnel", Off4 + 65.7, region: 4, scene: "DL-09"),
            new CheckpointDef("uponly", Off4 + 76.8 + 0.6, Deck, region: 4, scene: "DL-10"),                // UPONLY.x0 + 0.6
            new CheckpointDef("ringc", Off5 + 81.25, region: 5, scene: "DL-11"),
            new CheckpointDef("bedroom", Off5 + 110.1, region: 5, scene: "DL-11"),
            new CheckpointDef("forwarded", Off5 + 113.1, region: 5, scene: "DL-11"));

        /// <summary>
        /// The prologue as far as it is ported: DL-01 to DL-06 (regions 1–3), one world from the wake to the belt running
        /// to the exit, where DL-07 begins.
        /// </summary>
        public static ChapterDef Prologue() => new ChapterDef(PrologueId, PrologueCheckpoints,
            Dl01Scene.Def(), Dl02Scene.Def(), Dl03Scene.Def(), Dl04Scene.Def(), Dl05Scene.Def(), Dl06Scene.Def());

        // ---- Chapter 1 Attendance (#18) --------------------------------------------------------------------------------
        /// <summary>Chapter 1's ID (the save's scene key).</summary>
        public const string AttendanceId = "attendance";

        /// <summary>
        /// Chapter 1's checkpoints (<c>CHECKPOINTS</c>, L7999–L8013), all in region 6, in the save's order: where each puts
        /// D-17 (x, feet y, facing +1) and the scene that owns it (<c>sceneName</c> at its spot, L8136). <c>hatch14</c> is
        /// reached going into the duct, but its row is the window's spot, as the prototype has it.
        /// </summary>
        public static CheckpointTable AttendanceCheckpoints { get; } = new CheckpointTable(Checkpoint.PrototypeOrder,
            new CheckpointDef("school", 200.8, region: 6, scene: "DL-12"),
            new CheckpointDef("register", 210.0, region: 6, scene: "DL-12"),
            new CheckpointDef("lesson", 216.8, region: 6, scene: "DL-13"),
            new CheckpointDef("gallery13", 228.4, 2.05, region: 6, scene: "DL-13"),
            new CheckpointDef("window", 234.8, region: 6, scene: "DL-14"),
            new CheckpointDef("hatch14", 234.8, region: 6, scene: "DL-14"),
            new CheckpointDef("dorm", 249.4, 1.15, region: 6, scene: "DL-14a"),
            new CheckpointDef("corridor", 263.6, region: 6, scene: "DL-14b"),
            new CheckpointDef("sickbay", 279.0, 1.6, region: 6, scene: "DL-15"),
            new CheckpointDef("class6", 282.7, region: 6, scene: "DL-15"),
            new CheckpointDef("dismissed", 292.6, region: 6, scene: "DL-15"),
            new CheckpointDef("crossing", 294.6, region: 6, scene: "DL-16"),
            new CheckpointDef("store", 300.6, region: 6, scene: "DL-16"),
            new CheckpointDef("kitchen", 310.6, region: 6, scene: "DL-16a"),
            new CheckpointDef("workshop", 325.0, region: 6, scene: "DL-17"));

        /// <summary>
        /// Chapter 1 Attendance as far as it is ported (region 6, the school): one world from the arrival door at
        /// <c>school</c> on. Its continue and respawn take only rows whose scene it has.
        /// </summary>
        public static ChapterDef Attendance() => new ChapterDef(AttendanceId, AttendanceCheckpoints,
            Dl12Scene.Def(), Dl13Scene.Def(), Dl14Scene.Def(), Dl14aScene.Def(), Dl14bScene.Def(),
            Dl15Scene.Def(), Dl16Scene.Def(), Dl16aScene.Def());
    }
}
