using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using DeadLetter.Core.Art;
using DeadLetter.Core.Scenes;
using Xunit;
using Xunit.Abstractions;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// Each ported scene's <see cref="SceneDef"/> against its U-12 sidecar (<see cref="SceneArtCheck"/>, agreed on #16).
    /// A new scene is one row in <see cref="Rows"/>; its exceptions are named there, so none is silent.
    /// </summary>
    public class SceneArtCheckTests
    {
        private readonly ITestOutputHelper _out;
        public SceneArtCheckTests(ITestOutputHelper output) { _out = output; }

        private sealed class Row
        {
            public Func<SceneDef> Def;
            public string Art;
            public string[] LogicOnly = Array.Empty<string>(), NotPorted = Array.Empty<string>(), SharedWith = Array.Empty<string>();
        }

        /// <summary>
        /// U-12's marker types (docs/unity/name_map.csv, the <c>MECH_&lt;Type&gt;</c> table) where Core's class has another
        /// name. Every entry is a naming drift to settle in one place or the other; the check names the pair.
        /// </summary>
        private static readonly Dictionary<string, string> Aliases = new Dictionary<string, string>
        {
            ["Press"] = "PeriodicCrusher",       // Core/Hazards (DL-02's franking press)
            ["Draggable"] = "Pushable",          // Core/Push drags too (DL-05's body: StopAt/MinRoom)
            ["Scanner"] = "Dl06Scanner",         // DL-06's scanner is a scene mechanism of its own
        };

        private static readonly Dictionary<string, Row> Rows = new Dictionary<string, Row>
        {
            ["DL-01"] = new Row { Def = DeadLetter.Core.Scenes.Dl01.Dl01Scene.Def, Art = "DL-01", NotPorted = new[] { "dl01.scale" } },   // the scale curiosity
            ["DL-02"] = new Row { Def = DeadLetter.Core.Scenes.Dl02.Dl02Scene.Def, Art = "DL-02", LogicOnly = new[] { "dl02.tubeLetter" } },
            ["DL-03"] = new Row { Def = DeadLetter.Core.Scenes.Dl03.Dl03Scene.Def, Art = "DL-03" },
            ["DL-04"] = new Row { Def = () => DeadLetter.Core.Scenes.Dl04.Dl04Scene.Def(), Art = "DL-04" },
            ["DL-05"] = new Row { Def = DeadLetter.Core.Scenes.Dl05.Dl05Scene.Def, Art = "DL-05" },
            // DL-06 shares DL-07's sidecar (the floor): DL-07's gate and collapse are not ported yet (#17), its checkpoints are
            // DL-07's; the hatch is the scanner's, with no art of its own.
            ["DL-06"] = new Row
            {
                Def = DeadLetter.Core.Scenes.Dl06.Dl06Scene.Def, Art = "DL-06_07", LogicOnly = new[] { "dl06.hatch" },
                NotPorted = new[] { "dl07.gate", "dl07.collapse" }, SharedWith = new[] { "DL-07" },
            },
        };

        private static CheckpointTable Table => ChapterDefs.PrologueCheckpoints;

        public static IEnumerable<object[]> SceneIds()
        {
            foreach (var k in Rows.Keys) yield return new object[] { k };
        }

        internal static List<ArtMarker> LoadMarkers(string region)
        {
            string path = Path.Combine(ArtDir(), region, region + ".art.json");
            using var doc = JsonDocument.Parse(File.ReadAllText(path));
            var list = new List<ArtMarker>();
            foreach (var m in doc.RootElement.GetProperty("markers").EnumerateArray())
            {
                var p = m.GetProperty("position");
                var mk = new ArtMarker
                {
                    Name = m.GetProperty("name").GetString(), Prefix = m.GetProperty("prefix").GetString(),
                    X = p[0].GetDouble(), Y = p[1].GetDouble(), Z = p[2].GetDouble(),
                };
                foreach (var kv in m.GetProperty("props").EnumerateArray()) mk.Props[kv.GetProperty("key").GetString()] = kv.GetProperty("value").GetString();
                list.Add(mk);
            }
            return list;
        }

        private static string ArtDir()
        {
            var d = new DirectoryInfo(AppContext.BaseDirectory);
            while (d != null && !Directory.Exists(Path.Combine(d.FullName, "unity", "DeadLetter", "Assets", "Art"))) d = d.Parent;
            if (d == null) throw new DirectoryNotFoundException("unity/DeadLetter/Assets/Art not found above " + AppContext.BaseDirectory);
            return Path.Combine(d.FullName, "unity", "DeadLetter", "Assets", "Art");
        }

        [Theory]
        [MemberData(nameof(SceneIds))]
        public void TheSceneDefinition_AgreesWithItsArt(string scene)
        {
            var row = Rows[scene];
            var problems = SceneArtCheck.Check(row.Def(), Table, LoadMarkers(row.Art), row.LogicOnly, row.NotPorted, Aliases, row.SharedWith);
            foreach (var p in problems) _out.WriteLine(p);
            Assert.Empty(problems);
        }

        // ---- the check itself, on a small definition ---------------------------------------------------------------
        private static ArtMarker Mech(string type, string id, string part = null) => new ArtMarker
        {
            Name = "MECH_" + type + "_" + id.Replace('.', '_') + (part != null ? "__" + part : ""), Prefix = "MECH",
            Props = { ["mech"] = id, ["type"] = type },
        };

        private static ArtMarker Chk(string name, double x, int order, int region = 1) => new ArtMarker
        {
            Name = "CHK_" + name, Prefix = "CHK", X = x,
            Props = { ["game_region"] = region.ToString(), ["order"] = order.ToString(), ["height"] = "0.0" },
        };

        private static List<ArtMarker> Dl01Art() => new List<ArtMarker>
        {
            Mech("PulseSequencer", "dl01.relay"), Mech("Latch", "dl01.latch"), Mech("Door", "dl01.shutter"), Mech("Door", "dl01.shutter", "Rail"),
            Mech("CrankActuator", "dl01.crank"), Mech("Door", "dl01.door"), Mech("TippingBridge", "dl01.cart"),
            Chk("start", 1.0, 1), Chk("shutter", 2.9, 2), Chk("hall", 8.35, 3), Chk("door", 9.62, 4),
        };

        [Fact]
        public void ACleanDefinition_HasNoProblems()
        {
            Assert.Empty(SceneArtCheck.Check(DeadLetter.Core.Scenes.Dl01.Dl01Scene.Def(), Table, Dl01Art()));
        }

        [Fact]
        public void EachKindOfDrift_IsNamed()
        {
            var art = Dl01Art();
            art.RemoveAll(m => m.Name == "MECH_CrankActuator_dl01_crank");              // a def mechanism without art
            art.Add(Mech("LoadPlate", "dl01.scale"));                                       // art the def doesn't have
            art.Add(Mech("Door", "dl01.nothing", "Lamp"));                                  // a part without a root
            art.Find(m => m.Name == "MECH_TippingBridge_dl01_cart").Props["type"] = "Latch";      // type drift
            art.Find(m => m.Name == "CHK_hall").X = 8.4;                                    // a moved checkpoint
            art.Find(m => m.Name == "CHK_door").Props["order"] = "7";                       // order drift
            art.RemoveAll(m => m.Name == "CHK_start");                                      // a checkpoint without a marker
            var p = SceneArtCheck.Check(DeadLetter.Core.Scenes.Dl01.Dl01Scene.Def(), Table, art);
            foreach (var line in p) _out.WriteLine(line);
            Assert.Contains(p, s => s.Contains("dl01.crank has no MECH_ marker"));
            Assert.Contains(p, s => s.Contains("(dl01.scale) is not in the def"));
            Assert.Contains(p, s => s.Contains("has no root marker for dl01.nothing"));
            Assert.Contains(p, s => s.Contains("dl01.cart is a TippingBridge in Core but a Latch"));
            Assert.Contains(p, s => s.Contains("checkpoint hall is at x 8.35 in Core but 8.4"));
            Assert.Contains(p, s => s.Contains("checkpoint door is #4 in the save's order but order 7"));
            Assert.Contains(p, s => s.Contains("checkpoint start has no CHK_ marker"));
            Assert.Equal(7, p.Count);

            var listed = SceneArtCheck.Check(DeadLetter.Core.Scenes.Dl01.Dl01Scene.Def(), Table, Dl01Art(), logicOnly: new[] { "dl01.cart" }, notPorted: new[] { "dl01.latch" });
            Assert.Contains(listed, s => s.Contains("dl01.cart is listed logic-only but has art"));
            Assert.Contains(listed, s => s.Contains("dl01.latch is listed not-yet-ported but the def has it"));
        }

        [Fact]
        public void DuplicateIds_AndBrokenFactories_AreNamed()
        {
            var def = DeadLetter.Core.Scenes.Dl01.Dl01Scene.Def();
            var ms = new List<MechanismDef>(def.Mechanisms) { def.Mechanisms[0], new MechanismDef("dl01.bad", () => null) };
            def.Mechanisms = ms.ToArray();
            var p = SceneArtCheck.Check(def, Table, Dl01Art());
            Assert.Contains(p, s => s.Contains("mechanism id dl01.relay is used twice"));
            Assert.Contains(p, s => s.Contains("dl01.bad's factory returned null"));
        }
    }
}
