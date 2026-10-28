using System.IO;
using System.Text.RegularExpressions;
using DeadLetter.Core.Art;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>PrototypeMaterials against index.html's WORN / PLAIN / GLASSY / EMIT tables (L393–L490) and materialFor's suffix rule.</summary>
    public class PrototypeMaterialsTests
    {
        [Theory]
        [InlineData("CreamLimb.003", PrototypeSurface.Worn, 0.62, 0.72, 0.0)]
        [InlineData("DarkMetal", PrototypeSurface.Worn, 0.017, 0.72, 0.25)]
        [InlineData("EyeDark.003", PrototypeSurface.Plain, 0.003, 0.3, 0.0)]
        [InlineData("Window.003", PrototypeSurface.Glassy, 0.8, 0.06, 0.1)]
        [InlineData("Glow.003", PrototypeSurface.Emissive, 1.0, 0.4, 0.0)]
        public void Names_resolve_as_materialFor_does(string name, PrototypeSurface surface, double r, double rough, double metal)
        {
            Assert.True(PrototypeMaterials.Lookup(name, out PrototypeMaterial m));
            Assert.Equal(surface, m.Surface);
            Assert.Equal(r, m.R, 6);
            Assert.Equal(rough, m.Roughness, 6);
            Assert.Equal(metal, m.Metalness, 6);
        }

        [Theory]
        [InlineData("CreamLimb.003", "CreamLimb")]
        [InlineData("RelayA", "RelayA")]
        [InlineData("Lamp.v2", "Lamp.v2")]
        [InlineData("Odd.", "Odd.")]
        public void BaseName_strips_numeric_suffixes_only(string name, string expected) => Assert.Equal(expected, PrototypeMaterials.BaseName(name));

        [Fact]
        public void Every_table_name_in_index_html_is_ported()
        {
            string[] lines = File.ReadAllLines(RepoFiles.Find("game/undelivered/index.html"));
            int ported = 0;
            foreach (string table in new[] { "WORN", "PLAIN", "GLASSY", "EMIT" })
            {
                int i = System.Array.FindIndex(lines, l => l.StartsWith("const " + table + " = {"));
                Assert.True(i >= 0, table);
                for (int j = i; ; j++)
                {
                    string code = Regex.Replace(lines[j], "//.*$", "");
                    if (j == i) code = code.Substring(code.IndexOf('{') + 1);
                    foreach (Match k in Regex.Matches(code, @"\b([A-Z][A-Za-z0-9]*):\s*[\[{]"))
                    {
                        Assert.True(PrototypeMaterials.Lookup(k.Groups[1].Value, out _), table + "." + k.Groups[1].Value);
                        ported++;
                    }
                    if (code.TrimEnd().EndsWith("};")) break;
                }
            }
            Assert.Equal(PrototypeMaterials.All.Length, ported);
        }
    }
}
