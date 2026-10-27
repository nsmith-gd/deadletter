using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using DeadLetter.Core.Art;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// Guards the committed Unity export of the sets (<c>unity/DeadLetter/Assets/Art/</c>, written by
    /// <c>tools/unity_export/export_regions.py</c>): every prologue region of <c>set.glb</c> and every chapter 1 region is
    /// there, the textures fit the §8.2 budget, the markers follow the naming conventions and sit in their region, and
    /// chapter 1's mechanism markers name the Core mechanisms that drive them. Reads JSON only.
    /// </summary>
    public class ArtExportTests
    {
        private const string Art = "unity/DeadLetter/Assets/Art/";

        /// <summary>The regions set.glb splits into (tools/unity_export/conventions.py PROLOGUE + the backdrop).</summary>
        private static readonly string[] PrologueRegions =
            { "DL-01", "DL-02", "DL-03", "DL-04", "DL-05", "DL-06_07", "DL-08", "DL-09", "DL-10", "DL-11", "DL-09_Atrium" };

        /// <summary>Chapter 1's regions (conventions.py CHAPTER1, <c>--chapter1</c>).</summary>
        private static readonly string[] Chapter1Regions =
            { "DL-12", "DL-13", "DL-14", "DL-14a", "DL-14b", "DL-15", "DL-16", "DL-16a", "DL-17" };

        private static JsonElement Load(string relative) => JsonDocument.Parse(File.ReadAllText(RepoFiles.Find(relative))).RootElement;

        private static IEnumerable<JsonElement> Regions =>
            Load(Art + "regions.json").GetProperty("regions").EnumerateArray().Where(r => r.GetProperty("kind").GetString() == "set");

        private static JsonElement Sidecar(JsonElement r) =>
            Load(Art + r.GetProperty("folder").GetString() + "/" + r.GetProperty("sidecar").GetString());

        [Fact]
        public void Every_region_is_exported_with_its_files()
        {
            var names = Regions.Select(r => r.GetProperty("name").GetString()).ToList();
            foreach (string region in PrologueRegions.Concat(Chapter1Regions))
            {
                Assert.Contains(region, names);
                string folder = Art + region + "/";
                string gltf = RepoFiles.Find(folder + region + ".gltf");
                var doc = JsonDocument.Parse(File.ReadAllText(gltf)).RootElement;
                foreach (JsonElement b in doc.GetProperty("buffers").EnumerateArray())
                    Assert.True(File.Exists(Path.Combine(Path.GetDirectoryName(gltf), b.GetProperty("uri").GetString())), region + " buffer");
                foreach (JsonElement im in doc.TryGetProperty("images", out JsonElement ims) ? ims.EnumerateArray() : Enumerable.Empty<JsonElement>())
                {
                    string uri = im.GetProperty("uri").GetString();
                    Assert.StartsWith("../Textures/", uri);
                    Assert.True(File.Exists(Path.Combine(Path.GetDirectoryName(gltf), uri)), region + " image " + uri);
                }
            }
            foreach (string c in new[] { "D17/d17.glb", "White/white.glb", "Couriers/couriers.glb" })
                RepoFiles.Find(Art + c);
        }

        [Fact]
        public void Textures_fit_the_budget()
        {
            var textures = Load(Art + "Textures/textures.json").GetProperty("textures").EnumerateArray().ToList();
            Assert.NotEmpty(textures);
            long pc = 0, sw = 0;
            foreach (JsonElement t in textures)
            {
                int w = t.GetProperty("width").GetInt32(), h = t.GetProperty("height").GetInt32();
                Assert.True(w > 0 && h > 0, t.GetProperty("file").GetString());
                TextureUse use = TextureBudget.Classify(w, h);
                Assert.True(Math.Max(w, h) <= TextureBudget.MaxSize(ArtPlatform.PC, use), "source larger than any PC cap: " + t.GetProperty("file").GetString());
                pc += TextureBudget.EstimateBytes(w, h, ArtPlatform.PC, use);
                sw += TextureBudget.EstimateBytes(w, h, ArtPlatform.Switch, use);
            }
            // Every exported texture resident at once still fits one streaming window's budget.
            Assert.True(pc <= TextureBudget.ResidentBudget(ArtPlatform.PC), "PC " + pc);
            Assert.True(sw <= TextureBudget.ResidentBudget(ArtPlatform.Switch), "Switch " + sw);
        }

        [Fact]
        public void Markers_follow_the_conventions_and_sit_in_their_region()
        {
            var checkpoints = new List<string>();
            var roots = new Dictionary<string, int>();
            foreach (JsonElement r in Regions)
            {
                JsonElement sc = Sidecar(r);
                string region = sc.GetProperty("region").GetString();
                var scenes = sc.GetProperty("scenes").EnumerateArray().Select(s => s.GetString()).ToList();
                double x0 = sc.GetProperty("laneRange")[0].GetDouble(), x1 = sc.GetProperty("laneRange")[1].GetDouble();
                foreach (JsonElement m in sc.GetProperty("markers").EnumerateArray())
                {
                    string name = m.GetProperty("name").GetString();
                    ArtName n = ArtNames.Parse(name);
                    Assert.True(n.IsMarker, name);
                    Assert.Equal(m.GetProperty("prefix").GetString(), ArtNames.PrefixOf(n.Prefix).TrimEnd('_'));
                    if (n.Prefix == ArtPrefix.Checkpoint)
                    {
                        double x = m.GetProperty("position")[0].GetDouble();
                        Assert.True(x >= x0 && x < x1, name + " at x " + x + " outside " + region);
                        checkpoints.Add(n.Id);
                    }
                    if (n.Prefix == ArtPrefix.Mechanism)
                    {
                        string scene = n.Id.Substring(0, n.Id.IndexOf('.'));
                        Assert.Contains("DL-" + scene.Substring(2), scenes);
                        if (n.IsMechanismRoot) roots[n.Id] = roots.TryGetValue(n.Id, out int k) ? k + 1 : 1;
                    }
                }
            }
            // index.html's checkpoints, once each: 22 in the prologue (L7975–L7997), 15 in chapter 1 (L7999–L8013).
            Assert.Equal(37, checkpoints.Count);
            Assert.Equal(checkpoints.Count, checkpoints.Distinct().Count());
            Assert.Contains("start", checkpoints);
            Assert.Contains("forwarded", checkpoints);
            Assert.Contains("school", checkpoints);
            Assert.Contains("workshop", checkpoints);
            // Every mechanism has exactly one root (its main object or an anchor empty).
            Assert.NotEmpty(roots);
            Assert.All(roots, kv => Assert.Equal(1, kv.Value));
        }

        [Fact]
        public void Chapter1_mechanism_markers_name_their_Core_mechanisms()
        {
            // Each mechanism of the Attendance chapter, by ID, with the class Core builds for it.
            var types = new Dictionary<string, string>();
            foreach (var scene in Scenes.ChapterDefs.Attendance().Scenes)
                foreach (var def in scene.Mechanisms)
                    types[def.Id.ToString()] = def.Create().GetType().Name;
            var seen = new HashSet<string>();
            foreach (string region in Chapter1Regions)
            {
                JsonElement sc = Load(Art + region + "/" + region + ".art.json");
                int mechs = 0;
                foreach (JsonElement m in sc.GetProperty("markers").EnumerateArray())
                {
                    ArtName n = ArtNames.Parse(m.GetProperty("name").GetString());
                    if (n.Prefix != ArtPrefix.Mechanism) continue;
                    mechs++;
                    Assert.True(types.TryGetValue(n.Id, out string type), region + ": " + n.Id + " is not an Attendance mechanism");
                    Assert.Equal(type, n.Type);
                    seen.Add(n.Id);
                }
                Assert.True(mechs > 0, region + " has no mechanism markers");
            }
            // conventions.py maps 41 of the chapter's mechanisms to art (the rest have no object of their own).
            Assert.Equal(41, seen.Count);
        }
    }
}
