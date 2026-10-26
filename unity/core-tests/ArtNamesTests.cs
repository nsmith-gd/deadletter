using System;
using DeadLetter.Core.Art;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>The node naming conventions (docs/unity/asset_conventions.md) and the texture budget (§8.2).</summary>
    public class ArtNamesTests
    {
        [Theory]
        [InlineData("MECH_Shutter_dl01_shutter", "Shutter", "dl01.shutter", null)]
        [InlineData("MECH_Shutter_dl01_shutter__ShutterRail", "Shutter", "dl01.shutter", "ShutterRail")]
        [InlineData("MECH_CounterweightLift_dl08_platform__GoodsPlatformFrame", "CounterweightLift", "dl08.platform", "GoodsPlatformFrame")]
        [InlineData("MECH_Door_dl11_c114Door", "Door", "dl11.c114Door", null)]
        [InlineData("MECH_Relay_dl14a_relay.001", "Relay", "dl14a.relay", null)]
        [InlineData("MECH_Letter_dl06_heap", "Letter", "dl06.heap", null)]
        public void Mechanism_names_parse(string name, string type, string id, string part)
        {
            ArtName n = ArtNames.Parse(name);
            Assert.Equal(ArtPrefix.Mechanism, n.Prefix);
            Assert.Equal(type, n.Type);
            Assert.Equal(id, n.Id);
            Assert.Equal(part, n.Part);
            Assert.Equal(part == null, n.IsMechanismRoot);
        }

        [Theory]
        [InlineData("Shutter", "dl01.shutter", null, "MECH_Shutter_dl01_shutter")]
        [InlineData("Pawl", "dl08.pawl", "PawlLever", "MECH_Pawl_dl08_pawl__PawlLever")]
        public void Mechanism_names_round_trip(string type, string id, string part, string expected)
        {
            string name = ArtNames.Mechanism(type, id, part);
            Assert.Equal(expected, name);
            ArtName n = ArtNames.Parse(name);
            Assert.Equal((type, id, part), (n.Type, n.Id, n.Part));
        }

        [Theory]
        [InlineData("Bad_Type", "dl01.x")]
        [InlineData("", "dl01.x")]
        [InlineData("Door", "dl01")]
        [InlineData("Door", "dl_01.x")]
        [InlineData("Door", "dl01.a.b")]
        [InlineData("Door", ".x")]
        public void Mechanism_builder_rejects_bad_parts(string type, string id)
        {
            Assert.Throws<ArgumentException>(() => ArtNames.Mechanism(type, id));
        }

        [Theory]
        [InlineData("CHK_start", ArtPrefix.Checkpoint, null, "start")]
        [InlineData("CHK_landing8", ArtPrefix.Checkpoint, null, "landing8")]
        [InlineData("COL_floor_dl01", ArtPrefix.Collider, null, "floor_dl01")]
        [InlineData("CAM_dl01.hall", ArtPrefix.Camera, null, "dl01.hall")]
        [InlineData("LGT_r1_workLamp", ArtPrefix.Light, "r1", "workLamp")]
        [InlineData("LGT_ration_strip_02", ArtPrefix.Light, "ration", "strip_02")]
        [InlineData("COL_box (2)", ArtPrefix.Collider, null, "box")]
        public void Marker_names_parse(string name, ArtPrefix prefix, string type, string id)
        {
            ArtName n = ArtNames.Parse(name);
            Assert.Equal(prefix, n.Prefix);
            Assert.Equal(type, n.Type);
            Assert.Equal(id, n.Id);
            Assert.True(n.IsMarker);
        }

        [Theory]
        [InlineData("Shutter")]
        [InlineData("")]
        [InlineData(null)]
        [InlineData("CHK_")]
        [InlineData("COL_")]
        [InlineData("LGT_r1")]
        [InlineData("LGT_r1_")]
        [InlineData("MECH_Door")]
        [InlineData("MECH_Door_dl01")]
        [InlineData("MECH_Door_dl01_")]
        [InlineData("MECH__dl01_door")]
        [InlineData("MECH_Door_dl01_door__")]
        [InlineData("mech_Door_dl01_door")]
        [InlineData("RelayLamp0")]
        public void Other_names_are_not_markers(string name)
        {
            Assert.Equal(ArtPrefix.None, ArtNames.Parse(name).Prefix);
            Assert.False(ArtNames.IsMarker(name));
        }

        [Theory]
        [InlineData("Wall.001", "Wall")]
        [InlineData("Wall.1", "Wall.1")]
        [InlineData("CourierSlot.A.0", "CourierSlot.A.0")]
        [InlineData("D5FrontRowA.5", "D5FrontRowA.5")]
        [InlineData("Wall (3)", "Wall")]
        [InlineData("Wall (x)", "Wall (x)")]
        [InlineData("Wall.002 (1)", "Wall")]
        public void Duplicate_suffixes_strip(string name, string expected)
        {
            Assert.Equal(expected, ArtNames.StripDuplicateSuffix(name));
        }

        [Fact]
        public void Web_names_drop_dots_like_threejs()
        {
            Assert.Equal("CourierSlotA0", ArtNames.WebName("CourierSlot.A.0"));
            Assert.Equal("Shutter", ArtNames.WebName("Shutter"));
        }

        // ---- Texture budget ---------------------------------------------------------------------------------------------

        [Theory]
        [InlineData(ArtPlatform.PC, TextureUse.Default, 2048)]
        [InlineData(ArtPlatform.PC, TextureUse.Mural, 4096)]
        [InlineData(ArtPlatform.PC, TextureUse.UI, 2048)]
        [InlineData(ArtPlatform.Switch, TextureUse.Default, 1024)]
        [InlineData(ArtPlatform.Switch, TextureUse.Mural, 1024)]
        [InlineData(ArtPlatform.Switch, TextureUse.UI, 2048)]
        public void Max_sizes_follow_section_8_2(ArtPlatform p, TextureUse use, int max)
        {
            Assert.Equal(max, TextureBudget.MaxSize(p, use));
        }

        [Fact]
        public void Classify_and_fit()
        {
            Assert.Equal(TextureUse.Default, TextureBudget.Classify(2048, 2048));
            Assert.Equal(TextureUse.Mural, TextureBudget.Classify(4096, 1024));
            TextureBudget.Fit(4096, 1024, 1024, out int w, out int h);
            Assert.Equal((1024, 256), (w, h));
            TextureBudget.Fit(1621, 192, 1024, out w, out h);
            Assert.Equal((810, 96), (w, h));
            TextureBudget.Fit(512, 256, 1024, out w, out h);
            Assert.Equal((512, 256), (w, h));
        }

        [Fact]
        public void Estimates_match_block_sizes()
        {
            // 1024² BC7 = 1 MiB for the top level; the full chain is 4/3 of it plus the 4×4-block floor of the small levels.
            Assert.Equal(1L << 20, TextureBudget.LevelBytes(1024, 1024, ArtPlatform.PC));
            Assert.Equal(16L * 171 * 171, TextureBudget.LevelBytes(1024, 1024, ArtPlatform.Switch));
            long chain = TextureBudget.EstimateBytes(1024, 1024, ArtPlatform.PC, TextureUse.Default);
            Assert.InRange(chain, (1L << 20) * 4 / 3, (1L << 20) * 4 / 3 + 1024);
            Assert.Equal(TextureBudget.LevelBytes(1024, 1024, ArtPlatform.PC), TextureBudget.EstimateBytes(1024, 1024, ArtPlatform.PC, TextureUse.Default, mips: false));
            // A 2048² source costs a 1024² on Switch.
            Assert.Equal(TextureBudget.EstimateBytes(1024, 1024, ArtPlatform.Switch, TextureUse.Default),
                         TextureBudget.EstimateBytes(2048, 2048, ArtPlatform.Switch, TextureUse.Default));
        }
    }
}
