using DeadLetter.Core.Art;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>The prototype's material tables and <c>materialFor</c>'s rules (index.html L393–L554, port_architecture §4.3).</summary>
    public class PrototypeMaterialsTests
    {
        [Fact]
        public void Tables_have_the_prototypes_counts()
        {
            Assert.Equal(64, PrototypeMaterials.Worn.Count);
            Assert.Equal(33, PrototypeMaterials.Plain.Count);
            Assert.Equal(2, PrototypeMaterials.Glassy.Count);
            Assert.Equal(107, PrototypeMaterials.Emit.Count);
        }

        [Theory]
        [InlineData("Concrete", "Concrete")]
        [InlineData("CreamPaint.001", "CreamPaint")]
        [InlineData("CreamPaint.012", "CreamPaint")]
        [InlineData("Glass.Pane", "Glass.Pane")]
        [InlineData("Lamp.", "Lamp.")]
        [InlineData("", "")]
        public void Base_name_strips_a_numbered_suffix(string name, string expected) =>
            Assert.Equal(expected, PrototypeMaterials.BaseName(name));

        [Fact]
        public void Worn_entry_is_verbatim_with_defaults()
        {
            MaterialSpec s = PrototypeMaterials.For("Concrete");   // L400
            Assert.Equal(MaterialKind.Worn, s.Kind);
            Assert.Equal(0.075, s.Worn.Base.R);
            Assert.Equal(0.11, s.Worn.Dust.R);
            Assert.Equal(1.3, s.Worn.Grime);
            Assert.Equal(0.5, s.Worn.Streak);
            Assert.Equal(0.92, s.Roughness);

            WornSpec limb = PrototypeMaterials.For("CreamLimb.001").Worn;   // L396: no dust, no dustAmt
            Assert.Equal(limb.Base.R, limb.Dust.R);
            Assert.Equal(0, limb.DustAmt);
            Assert.Equal(0.6, limb.Streak);
            Assert.Equal(0.4, PrototypeMaterials.Worn["BareMetal"].Streak);   // L397: no streak → 0.4
        }

        [Fact]
        public void Water_is_see_through()
        {
            MaterialSpec s = PrototypeMaterials.For("Water");   // L535
            Assert.Equal(MaterialKind.Plain, s.Kind);
            Assert.True(s.Transparent);
            Assert.False(s.DepthWrite);
            Assert.Equal(0.66, s.Opacity);
            Assert.Equal(0.24, s.Roughness);
            Assert.Equal(0.05, s.Color.G);
        }

        [Fact]
        public void Emitters_are_black_with_their_glow()
        {
            MaterialSpec s = PrototypeMaterials.For("ParcelLamp");   // L470
            Assert.Equal(MaterialKind.Emit, s.Kind);
            Assert.Equal(0, s.Color.R);
            Assert.Equal(0.4, s.Roughness);
            Assert.Equal(0.55, s.Emissive.G);
            Assert.Equal(6, s.EmissiveIntensity);
        }

        [Fact]
        public void Glassy_and_mist()
        {
            MaterialSpec w = PrototypeMaterials.For("Window");
            Assert.Equal(MaterialKind.Glassy, w.Kind);
            Assert.Equal(0.16, w.Opacity);
            Assert.Equal(0.06, w.Roughness);
            Assert.Equal(MaterialKind.Additive, PrototypeMaterials.For("AtriumMist").Kind);
        }

        [Theory]
        [InlineData("DispatchBoardMat", false, false)]
        [InlineData("ChalkTally", false, true)]
        [InlineData("RingLetterC", false, true)]
        [InlineData("NoticeMat", true, true)]
        public void Images_keep_their_map_and_decals_blend(string name, bool sourceTransparent, bool decal)
        {
            MaterialSpec s = PrototypeMaterials.For(name, hasImage: true, sourceTransparent: sourceTransparent);
            Assert.Equal(MaterialKind.Image, s.Kind);
            Assert.Equal(0.75, s.Roughness);
            Assert.Equal(decal, s.Decal);
            Assert.Equal(decal ? 0.02 : 0, s.AlphaTest);
        }

        [Fact]
        public void A_listed_name_wins_over_its_image_and_unknowns_stay()
        {
            Assert.Equal(MaterialKind.Worn, PrototypeMaterials.For("CastIron", hasImage: true).Kind);
            Assert.Equal(MaterialKind.Source, PrototypeMaterials.For("SomethingNew").Kind);
        }
    }
}
