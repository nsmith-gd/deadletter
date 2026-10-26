using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.Json;
using DeadLetter.Core.Motor;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// Guards the D-17 asset the Unity project ships (<c>Assets/Art/D17/d17.glb</c>, copied from
    /// <c>game/undelivered/assets/d17.glb</c>) against <see cref="ClipTimings"/>: every clip Core times acts on must exist
    /// with the same frame count (last key time × 24), and the rig must be skinned with unique node names (glTFast binds
    /// Mecanim curves by transform path). Reads the GLB's JSON chunk only; no Unity needed.
    /// </summary>
    public class D17AssetTests
    {
        private const string GlbRelative = "DeadLetter/Assets/Art/D17/d17.glb";

        private static JsonDocument _doc;

        private static JsonElement Gltf
        {
            get
            {
                if (_doc == null) _doc = JsonDocument.Parse(ReadJsonChunk(FindGlb()));
                return _doc.RootElement;
            }
        }

        private static string FindGlb()
        {
            for (var dir = new DirectoryInfo(AppContext.BaseDirectory); dir != null; dir = dir.Parent)
            {
                var p = Path.Combine(dir.FullName, GlbRelative);
                if (File.Exists(p)) return p;
            }
            throw new FileNotFoundException("unity/" + GlbRelative + " not found above " + AppContext.BaseDirectory);
        }

        private static string ReadJsonChunk(string path)
        {
            byte[] b = File.ReadAllBytes(path);
            Assert.True(b.Length > 20, "GLB too short");
            Assert.Equal(0x46546C67u, BitConverter.ToUInt32(b, 0));   // "glTF"
            Assert.Equal(2u, BitConverter.ToUInt32(b, 4));
            Assert.Equal((uint)b.Length, BitConverter.ToUInt32(b, 8));
            int len = (int)BitConverter.ToUInt32(b, 12);
            Assert.Equal(0x4E4F534Au, BitConverter.ToUInt32(b, 16));  // "JSON"
            return Encoding.UTF8.GetString(b, 20, len);
        }

        /// <summary>Clip name → frames (max sampler input time × 24), as ClipTimings measured them.</summary>
        private static Dictionary<string, double> GlbClipFrames()
        {
            var accessors = Gltf.GetProperty("accessors");
            var result = new Dictionary<string, double>(StringComparer.Ordinal);
            foreach (var anim in Gltf.GetProperty("animations").EnumerateArray())
            {
                double maxT = 0;
                foreach (var s in anim.GetProperty("samplers").EnumerateArray())
                {
                    var input = accessors[s.GetProperty("input").GetInt32()];
                    maxT = Math.Max(maxT, input.GetProperty("max")[0].GetDouble());
                }
                string name = anim.GetProperty("name").GetString();
                Assert.True(!result.ContainsKey(name), "duplicate clip " + name);
                result[name] = maxT * 24.0;
            }
            return result;
        }

        [Fact]
        public void Glb_HasEveryClipTimingsClip_WithTheSameFrameCount()
        {
            var frames = GlbClipFrames();
            var problems = new List<string>();
            foreach (var c in ClipTimings.All)
            {
                if (!frames.TryGetValue(c.Name, out double f)) problems.Add("missing " + c.Name);
                else if (Math.Abs(f - c.Frames) > 1e-3) problems.Add($"{c.Name}: glb {f:0.###} vs table {c.Frames}");
            }
            Assert.True(problems.Count == 0, string.Join("; ", problems));
        }

        [Fact]
        public void Glb_HasNoClipsOutsideTheTable()
        {
            var frames = GlbClipFrames();
            Assert.Equal(ClipTimings.All.Length, frames.Count);
            foreach (var name in frames.Keys) Assert.True(ClipTimings.TryGet(name, out _), "clip not in ClipTimings: " + name);
        }

        [Fact]
        public void Glb_IsSkinned_WithUniqueNodeNames_AndAnimatesOnlyRigNodes()
        {
            var skins = Gltf.GetProperty("skins");
            Assert.Equal(1, skins.GetArrayLength());
            Assert.Equal(26, skins[0].GetProperty("joints").GetArrayLength());

            var nodes = Gltf.GetProperty("nodes");
            var names = new HashSet<string>(StringComparer.Ordinal);
            foreach (var n in nodes.EnumerateArray())
                Assert.True(names.Add(n.GetProperty("name").GetString()), "duplicate node name " + n.GetProperty("name"));
            foreach (var bone in new[] { "root", "body", "head", "antenna_1", "ik_foot.L", "ik_foot.R", "ik_hand.L", "ik_hand.R" })
                Assert.Contains(bone, names);

            var joints = new HashSet<int>();
            foreach (var j in skins[0].GetProperty("joints").EnumerateArray()) joints.Add(j.GetInt32());
            foreach (var anim in Gltf.GetProperty("animations").EnumerateArray())
                foreach (var ch in anim.GetProperty("channels").EnumerateArray())
                {
                    var target = ch.GetProperty("target");
                    Assert.NotEqual("weights", target.GetProperty("path").GetString());
                    int node = target.GetProperty("node").GetInt32();
                    Assert.True(joints.Contains(node), anim.GetProperty("name") + " animates non-joint node " + nodes[node].GetProperty("name"));
                }
        }

        [Fact]
        public void Glb_RequiresNoExtensions()
        {
            Assert.False(Gltf.TryGetProperty("extensionsRequired", out var req) && req.GetArrayLength() > 0,
                "glTFast must not need an extension to load D-17");
        }
    }
}
