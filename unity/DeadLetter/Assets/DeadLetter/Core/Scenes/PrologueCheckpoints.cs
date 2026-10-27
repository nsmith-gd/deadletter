using System;
using System.Collections.Generic;
using DeadLetter.Core.Lane.Tables;

namespace DeadLetter.Core.Scenes
{
    /// <summary>
    /// The prologue's checkpoints, one table for the chapter (<c>CHECKPOINTS</c>, L7975–L7997; port_architecture §5): where
    /// each puts D-17 (lane x, feet y, facing, region) and the scene that owns it (<c>sceneName</c> at that spot, L8135–L8144).
    /// A scene's definition takes its own checkpoints from here (<see cref="Of"/>); a respawn or a continue places him at
    /// any of them (<see cref="TryGet"/>), including one that belongs to the scene before (DL-03 starts under DL-02's
    /// <c>room</c>, DL-05 under DL-04's <c>bay</c>). Names follow <see cref="Mechanisms.Checkpoint.PrototypeOrder"/>.
    /// <para><c>resetWorld</c> faces him +x at every checkpoint (L8019) and puts him at <c>c.y</c> where there is one (L4113).
    /// The region is <c>c.region || 1</c> (L8026).</para>
    /// </summary>
    public static class PrologueCheckpoints
    {
        /// <summary>The prototype's x offsets of the later sets (<c>OFF2</c>…<c>OFF5</c>, L274).</summary>
        public const double Off2 = 13, Off3 = 33, Off4 = 42, Off5 = 54;
        /// <summary><c>CG.top</c> (L3900) and <c>DECK</c> (L3007): the cage's top and the balcony deck.</summary>
        public const double CageTop = 3.4, Deck = 1.6;

        private static readonly CheckpointDef[] Table =
        {
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
            new CheckpointDef("forwarded", Off5 + 113.1, region: 5, scene: "DL-11"),
        };

        /// <summary>Every prologue checkpoint, in play order.</summary>
        public static IReadOnlyList<CheckpointDef> All => Table;

        /// <summary>The checkpoint called <paramref name="name"/>; false for a name outside the prologue (chapter 1's) or unknown.</summary>
        public static bool TryGet(string name, out CheckpointDef cp)
        {
            for (int i = 0; i < Table.Length; i++)
                if (string.Equals(Table[i].Name, name, StringComparison.Ordinal)) { cp = Table[i]; return true; }
            cp = default;
            return false;
        }

        /// <summary>The checkpoint called <paramref name="name"/>; throws for a name not in the table.</summary>
        public static CheckpointDef Get(string name)
            => TryGet(name, out var cp) ? cp : throw new ArgumentException("No prologue checkpoint '" + name + "'.", nameof(name));

        /// <summary>The scene that owns <paramref name="name"/> ("DL-03"), or null for a name not in the table.</summary>
        public static string SceneOf(string name) => TryGet(name, out var cp) ? cp.Scene : null;

        /// <summary>The checkpoints <paramref name="sceneId"/> owns, in play order (a new array: a definition may keep it).</summary>
        public static CheckpointDef[] Of(string sceneId)
        {
            var list = new List<CheckpointDef>();
            for (int i = 0; i < Table.Length; i++) if (string.Equals(Table[i].Scene, sceneId, StringComparison.Ordinal)) list.Add(Table[i]);
            return list.ToArray();
        }
    }
}
