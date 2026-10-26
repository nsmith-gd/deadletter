using System;
using System.Collections.Generic;
using DeadLetter.Core.Beings;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Save;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>U-14: the save format, migration, the atomic store, persist flags, settings and the checkpoint service (§4.28).</summary>
    public class SaveTests
    {
        /// <summary>
        /// A version 1 save (the prototype's <c>dl01-resume</c> record as a file), written by an independent encoder
        /// (Python, zlib's CRC-32): cp "hall", scene "DL-01 The Wake", at, found/curio/scale, found/secret/den,
        /// found/voice/card_wake, persist/warned, read/tube.
        /// </summary>
        private const string V1Fixture =
            "RExTVgEACAAAAAIAYXQBAA6fG5oBAAACAGNwBAQAAABoYWxsEQBmb3VuZC9jdXJpby9zY2FsZQMBEABmb3VuZC9zZWNyZXQvZGVuAwEVAGZvdW5kL3ZvaWNlL2NhcmRfd2FrZQMBDgBwZXJzaXN0L3dhcm5lZAMBCQByZWFkL3R1YmUDAQUAc2NlbmUEDgAAAERMLTAxIFRoZSBXYWtl9wYJRA==";

        private static SaveModel Sample()
        {
            var snap = new MemorySnapshot();
            snap.WriteLong("graph/tick", 1234);
            snap.WriteDouble("dl01.shutter/pos", 15.6);
            snap.WriteDouble("dl01.shutter/t", 1.0 / 3.0);
            snap.WriteBool("dl01.shutter/cued", true);
            snap.WriteLong("dl01.latch/state", -7);
            return new SaveModel
            {
                Checkpoint = "shutter",
                Scene = "DL-01 The Wake — Café",                    // non-ASCII survives
                PlayTime = 81.25,
                Flags = new List<string> { StoryFlags.Curio("scale"), StoryFlags.WhiteWarned },
                Mechanisms = snap,
                Settings = new Settings { AutoRun = false, Calm = true, Brightness = 1.35, Music = false, SubtitleSize = 2 },
            };
        }

        [Fact]
        public void Codec_RoundTrip_IsExact_AndTheBytesAreDeterministic()
        {
            var m = Sample();
            byte[] a = SaveCodec.Encode(m), b = SaveCodec.Encode(Sample());
            Assert.Equal(a, b);
            Assert.Equal(new byte[] { (byte)'D', (byte)'L', (byte)'S', (byte)'V', SaveModel.CurrentVersion, 0 }, a[..6]);
            Assert.True(SaveCodec.TryLoad(a, out var r, out string err), err);
            Assert.Equal("shutter", r.Checkpoint);
            Assert.Equal(m.Scene, r.Scene);
            Assert.Equal(81.25, r.PlayTime);
            Assert.Equal(new[] { "curio.scale", "persist.warned" }, r.Flags);
            Assert.Equal(m.Mechanisms.Dump(), r.Mechanisms.Dump());
            Assert.Equal(a, SaveCodec.Encode(r));                  // decode → encode: the same bytes
        }

        [Fact]
        public void Codec_InsertionOrderDoesNotChangeTheBytes()
        {
            var x = new SaveDocument(2); x.SetLong("b", 1); x.SetString("a", "z"); x.SetBool("c", true);
            var y = new SaveDocument(2); y.SetBool("c", true); y.SetLong("b", 1); y.SetString("a", "z");
            Assert.Equal(SaveCodec.Encode(x), SaveCodec.Encode(y));
        }

        [Fact]
        public void Codec_AnyFlippedBitOrTruncation_FailsTheChecksum()
        {
            var bytes = SaveCodec.Encode(Sample());
            for (int i = 0; i < bytes.Length; i += 7)
            {
                var bad = (byte[])bytes.Clone();
                bad[i] ^= 0x10;
                Assert.False(SaveCodec.TryLoad(bad, out _, out _));
            }
            Assert.False(SaveCodec.TryLoad(bytes[..^1], out _, out string e1));
            Assert.Equal("bad checksum", e1);
            Assert.False(SaveCodec.TryLoad(new byte[3], out _, out _));
            Assert.False(SaveCodec.TryLoad(null, out _, out _));
        }

        [Fact]
        public void Crc32_MatchesTheStandardCheckValue()
        {
            var data = System.Text.Encoding.ASCII.GetBytes("123456789");
            Assert.Equal(0xCBF43926u, Crc32.Compute(data, 0, data.Length));
        }

        [Fact]
        public void Migration_V1Fixture_BecomesTheCurrentModel()
        {
            var bytes = Convert.FromBase64String(V1Fixture);
            Assert.True(SaveCodec.TryDecode(bytes, out var doc, out string err), err);
            Assert.Equal(1, doc.Version);
            Assert.True(SaveCodec.TryLoad(bytes, out var m, out err), err);
            Assert.Equal("hall", m.Checkpoint);
            Assert.Equal("DL-01 The Wake", m.Scene);
            Assert.Equal(0, m.PlayTime);
            Assert.Null(m.Mechanisms);                                 // derived from the checkpoint alone
            Assert.Equal(new[] { "curio.scale", "letter.read.tube", "persist.warned", "secret.den", "voice.card_wake" }, m.Flags);
            Assert.Contains(StoryFlags.WhiteWarned, m.Flags);
            Assert.Contains(StoryFlags.LetterRead("tube"), m.Flags);
            Assert.True(m.Settings.AutoRun && m.Settings.Sound && !m.Settings.Calm);   // options: the defaults
            Assert.Equal(1.0, m.Settings.Brightness);
            Assert.True(SaveCodec.TryLoad(SaveCodec.Encode(m), out var again, out _));    // re-saved as v2
            Assert.Equal(m.Flags, again.Flags);
            Assert.Equal(SaveModel.CurrentVersion, SaveCodec.Encode(m)[4]);
        }

        [Fact]
        public void Migration_EveryOlderVersionHasAStep_AndANewerFileIsRefused()
        {
            Assert.Equal(SaveModel.CurrentVersion, SaveMigrations.Steps.Length);
            for (int v = 1; v < SaveModel.CurrentVersion; v++) Assert.NotNull(SaveMigrations.Steps[v]);
            var d = SaveModel.FromDocument(Sample().ToDocument()).ToDocument();
            d.Version = SaveModel.CurrentVersion + 1;
            Assert.False(SaveCodec.TryLoad(SaveCodec.Encode(d), out _, out string err));
            Assert.Contains("newer", err);
        }

        [Fact]
        public void Settings_RoundTrip_EveryOption()
        {
            var s = new Settings
            {
                AutoRun = false, Sound = false, Music = false, Prompts = false, StuckAssist = true, Calm = true,
                Telemetry = false, Brightness = 1.8, Subtitles = false, SubtitleSize = 0, SubtitleBackground = true, HoldToToggle = true,
            };
            Assert.True(SaveCodec.TryLoad(SaveCodec.Encode(new SaveModel { Settings = s }), out var m, out _));
            var r = m.Settings;
            Assert.Equal((s.AutoRun, s.Sound, s.Music, s.Prompts, s.StuckAssist, s.Calm, s.Telemetry),
                (r.AutoRun, r.Sound, r.Music, r.Prompts, r.StuckAssist, r.Calm, r.Telemetry));
            Assert.Equal((s.Brightness, s.Subtitles, s.SubtitleSize, s.SubtitleBackground, s.HoldToToggle),
                (r.Brightness, r.Subtitles, r.SubtitleSize, r.SubtitleBackground, r.HoldToToggle));
        }

        [Fact]
        public void Settings_PrototypeDefaults_AndBrightnessIsClamped_L8283_L8307()
        {
            var d = new Settings();
            Assert.True(d.Sound && d.Music && d.Prompts && !d.StuckAssist && !d.Calm && d.AutoRun && d.Telemetry);
            var doc = new SaveDocument(2);
            doc.SetDouble("opt/bright", 5);
            Assert.Equal(1.8, Settings.Read(doc).Brightness);
            doc.SetDouble("opt/bright", 0.1);
            Assert.Equal(0.8, Settings.Read(doc).Brightness);
        }

        [Fact]
        public void Settings_ApplyingThemSaves_AndSetsCalmOnTheGraph()
        {
            var g = Mech.Graph("start", new TestSource("t.a"));
            var store = new MemorySaveStore();
            var svc = new CheckpointService(g, Checkpoint.PrototypeOrder, store);
            svc.ApplySettings(new Settings { Calm = true, Brightness = 1.2 });
            Assert.True(g.Calm);
            Assert.True(store.TryLoad(0, out var m));
            Assert.True(m.Settings.Calm);
            Assert.Equal(1.2, m.Settings.Brightness);
        }

        [Fact]
        public void Reloaded_FiresOnNewGame_Respawn_AndContinue_NotOnReachingACheckpoint()
        {
            var g = Mech.Graph("start", new TestSource("t.a"));
            var store = new MemorySaveStore();
            var svc = new CheckpointService(g, Checkpoint.PrototypeOrder, store);
            var seen = new List<string>();
            svc.Reloaded += cp => seen.Add(cp.Name);

            svc.NewGame();
            string next = Checkpoint.PrototypeOrder[1];
            svc.Reach(next);
            svc.Reload();
            Assert.True(svc.TryContinue());

            Assert.Equal(new List<string> { Checkpoint.PrototypeOrder[0], next, next }, seen);
        }

        // ---- AtomicFileStore ----

        private static SaveModel At(string cp) { var m = Sample(); m.Checkpoint = cp; return m; }

        [Fact]
        public void Store_SaveLoad_KeepsOneBackup()
        {
            var fs = new MemoryFileSystem();
            var st = new AtomicFileStore(fs);
            Assert.False(st.TryLoad(0, out _));
            st.Save(0, At("shutter"));
            st.Save(0, At("hall"));
            Assert.True(st.TryLoad(0, out var m));
            Assert.Equal("hall", m.Checkpoint);
            Assert.False(st.LoadedBackup);
            Assert.Equal(new[] { "slot0.dls", "slot0.dls.bak" }, Sorted(fs.Files.Keys));
            st.Delete(0);
            Assert.Empty(fs.Files);
            Assert.False(st.TryLoad(0, out _));
        }

        [Fact]
        public void Store_BadChecksumOnTheCurrentFile_FallsBackToTheBackup()
        {
            var fs = new MemoryFileSystem();
            var st = new AtomicFileStore(fs);
            st.Save(0, At("shutter"));
            st.Save(0, At("hall"));
            fs.Files["slot0.dls"][20] ^= 0xFF;                         // bit rot
            Assert.True(st.TryLoad(0, out var m));
            Assert.True(st.LoadedBackup);
            Assert.Contains("bad checksum", st.LastError);
            Assert.Equal("shutter", m.Checkpoint);

            st.Save(0, At("door"));                                    // the damaged file must not replace the good backup
            Assert.True(st.TryLoad(0, out m));
            Assert.Equal("door", m.Checkpoint);
            fs.Files["slot0.dls"] = new byte[0];
            Assert.True(st.TryLoad(0, out m));
            Assert.Equal("shutter", m.Checkpoint);
        }

        [Fact]
        public void Store_TornWrite_LeavesTheLastSaveIntact()
        {
            var fs = new MemoryFileSystem();
            var st = new AtomicFileStore(fs);
            st.Save(0, At("shutter"));
            fs.TearNextWriteAt = 17;
            Assert.Throws<System.IO.IOException>(() => st.Save(0, At("hall")));
            Assert.Equal(17, fs.Files["slot0.dls.tmp"].Length);         // the torn temp file is never read
            Assert.True(st.TryLoad(0, out var m));
            Assert.False(st.LoadedBackup);
            Assert.Equal("shutter", m.Checkpoint);
            st.Save(0, At("hall"));                                    // the next save overwrites the temp file
            Assert.True(st.TryLoad(0, out m));
            Assert.Equal("hall", m.Checkpoint);
            Assert.False(fs.Files.ContainsKey("slot0.dls.tmp"));
        }

        [Fact]
        public void Store_CrashBetweenTheTwoRenames_LoadsTheBackup()
        {
            var fs = new MemoryFileSystem();
            var st = new AtomicFileStore(fs);
            st.Save(0, At("shutter"));
            st.Save(0, At("hall"));
            fs.CrashAtReplace = 1;                                     // current → backup done; temp → current never happens
            Assert.Throws<System.IO.IOException>(() => st.Save(0, At("door")));
            Assert.False(fs.Files.ContainsKey("slot0.dls"));
            Assert.True(st.TryLoad(0, out var m));
            Assert.True(st.LoadedBackup);
            Assert.Equal("hall", m.Checkpoint);
        }

        [Fact]
        public void Store_BothCopiesDamaged_LoadsNothing()
        {
            var fs = new MemoryFileSystem();
            var st = new AtomicFileStore(fs);
            st.Save(0, At("shutter"));
            st.Save(0, At("hall"));
            fs.Files["slot0.dls"][9] ^= 1;
            fs.Files["slot0.dls.bak"][9] ^= 1;
            Assert.False(st.TryLoad(0, out var m));
            Assert.Null(m);
            Assert.Contains("backup", st.LastError);
        }

        private static string[] Sorted(IEnumerable<string> keys) { var l = new List<string>(keys); l.Sort(StringComparer.Ordinal); return l.ToArray(); }

        // ---- PersistFlags and the service ----

        [Fact]
        public void PersistFlags_HandlesResolveOnce_SetNamesAreSorted()
        {
            var f = new PersistFlags();
            int h = f.Resolve("b");
            Assert.False(f.Get(h));
            f.Set("c"); f.Set("b"); f.Set("a"); f.Set("a", false);
            Assert.True(f.Get(h));
            Assert.Equal(new[] { "b", "c" }, f.SetNames());
            long v = f.Version;
            f.Set("b");
            Assert.Equal(v, f.Version);                                // no change, no bump
            f.Clear();
            Assert.False(f.Get(h));
            Assert.Empty(f.SetNames());
        }

        [Fact]
        public void Reach_OnlyALaterCheckpointCounts_AndEachOneSaves()
        {
            var g = Mech.Graph("start", new TestSource("t.a"));
            var store = new MemorySaveStore();
            var svc = new CheckpointService(g, Checkpoint.PrototypeOrder, store);
            Assert.True(svc.Reach("hall"));
            Assert.False(svc.Reach("shutter"));                        // !past(cp, X) guards (L4935)
            Assert.False(svc.Reach("hall"));
            Assert.True(svc.Reach("door"));
            Assert.Equal(2, store.Writes);
            Assert.True(store.TryLoad(0, out var m));
            Assert.Equal("door", m.Checkpoint);
            Assert.Throws<ArgumentException>(() => svc.Reach("nowhere"));
        }

        [Fact]
        public void Reach_RateLimited_HoldsTheWriteUntilUpdate_Switch2s()
        {
            var g = Mech.Graph("start", new TestSource("t.a"));
            var store = new MemorySaveStore();
            var svc = new CheckpointService(g, Checkpoint.PrototypeOrder, store) { MinSecondsBetweenWrites = 2 };
            svc.Reach("shutter");
            svc.Update(0.5, true);
            svc.Reach("hall");
            Assert.Equal(1, store.Writes);
            Assert.True(svc.Pending);
            svc.Update(1.0, true);
            Assert.Equal(1, store.Writes);
            svc.Update(0.6, false);
            Assert.Equal(2, store.Writes);
            Assert.True(store.TryLoad(0, out var m));
            Assert.Equal("hall", m.Checkpoint);
            Assert.Equal(1.5, m.PlayTime, 12);                         // paused time is not play time
            svc.Reach("door");
            svc.Flush();
            Assert.Equal(3, store.Writes);
        }

        [Fact]
        public void NewGame_ClearsEveryFlag_AndBoundState_L4133()
        {
            var senses = new BeingSenses { Region = 5 };
            var white = new WhiteBrain("dl11.white", WhiteParams.Dl11(), senses);
            var g = Mech.Graph("ringc", white);
            var store = new MemorySaveStore();
            var svc = new CheckpointService(g, Checkpoint.PrototypeOrder, store);
            svc.BindFlag(StoryFlags.WhiteWarned, () => white.Warned, v => white.Warned = v);
            svc.SetFlag(StoryFlags.Curio("mug"));
            white.Warned = true;
            svc.NewGame();
            Assert.False(white.Warned);
            Assert.False(svc.Flags.Has(StoryFlags.Curio("mug")));
            Assert.Equal("start", svc.Current.Name);
            Assert.True(store.TryLoad(0, out var m));
            Assert.Empty(m.Flags);
        }

        [Fact]
        public void TheWhitesWarning_SurvivesReload_AndQuitAndContinue_L7150()
        {
            var fs = new MemoryFileSystem();
            var senses = new BeingSenses { Region = 5 };
            var white = new WhiteBrain("dl11.white", WhiteParams.Dl11(), senses);
            var g = Mech.Graph("ringc", white);
            var svc = SaveKit.Service(g, fs, "DL-11");
            svc.BindFlag(StoryFlags.WhiteWarned, () => white.Warned, v => white.Warned = v);
            svc.Reach("ringc");                                        // the snapshot holds warned = false
            white.Warned = true;                                       // the hunt water warns him
            svc.Reload();                                              // he dies: respawn at ringc
            Assert.True(white.Warned);
            Assert.True(svc.RestoredSnapshot);
            Assert.True(new AtomicFileStore(fs).TryLoad(0, out var m));
            Assert.Contains(StoryFlags.WhiteWarned, m.Flags);          // saved on the respawn

            var white2 = new WhiteBrain("dl11.white", WhiteParams.Dl11(), new BeingSenses { Region = 5 });
            var g2 = Mech.Graph("start", white2);
            var svc2 = SaveKit.Service(g2, fs, "DL-11");
            svc2.BindFlag(StoryFlags.WhiteWarned, () => white2.Warned, v => white2.Warned = v);
            Assert.True(svc2.TryContinue());
            Assert.True(white2.Warned);
            Assert.Equal("ringc", svc2.Current.Name);
        }

        [Fact]
        public void Update_SavesABoundFlagThatChanged_WithoutACheckpoint()
        {
            var white = new WhiteBrain("dl11.white", WhiteParams.Dl11(), new BeingSenses { Region = 5 });
            var g = Mech.Graph("ringc", white);
            var store = new MemorySaveStore();
            var svc = new CheckpointService(g, Checkpoint.PrototypeOrder, store);
            svc.BindFlag(StoryFlags.WhiteWarned, () => white.Warned, v => white.Warned = v);
            svc.Reach("ringc");
            svc.Update(0.1, true);
            Assert.Equal(1, store.Writes);
            white.Warned = true;
            svc.Update(0.1, true);
            Assert.Equal(2, store.Writes);
            Assert.True(store.TryLoad(0, out var m));
            Assert.Contains(StoryFlags.WhiteWarned, m.Flags);
        }

        [Fact]
        public void Continue_ASnapshotFromAnotherScene_IsDropped_AndTheWorldIsDerived()
        {
            var store = new MemorySaveStore();
            var a = new TestSource("t.a") { Load = 3 };
            var g = Mech.Graph("start", a);
            new CheckpointService(g, Checkpoint.PrototypeOrder, store, 0, "DL-01").Reach("hall");
            var b = new TestSource("t.a");
            var g2 = Mech.Graph("start", b);
            var svc = new CheckpointService(g2, Checkpoint.PrototypeOrder, store, 0, "DL-02");
            Assert.True(svc.TryContinue());
            Assert.False(svc.RestoredSnapshot);
            Assert.Equal(0, b.Load);
            Assert.Equal("hall", svc.Current.Name);
        }

        [Fact]
        public void Continue_ASnapshotThatNoLongerFitsTheGraph_FallsBackToTheDerivedWorld()
        {
            var store = new MemorySaveStore();
            var g = Mech.Graph("start", new TestSource("t.a") { Load = 3 });
            new CheckpointService(g, Checkpoint.PrototypeOrder, store, 0, "S").Reach("hall");
            var other = new TestSource("t.renamed");
            var g2 = Mech.Graph("start", other);                       // a patch renamed the mechanism
            var svc = new CheckpointService(g2, Checkpoint.PrototypeOrder, store, 0, "S");
            Assert.True(svc.TryContinue());
            Assert.False(svc.RestoredSnapshot);
            Assert.Equal("hall", svc.Current.Name);
        }

        [Fact]
        public void Reload_KeepsTheGraphTickCountingUp()
        {
            var g = Mech.Graph("start", new TestSource("t.a"));
            var svc = new CheckpointService(g, Checkpoint.PrototypeOrder, new MemorySaveStore());
            Mech.Run(g, 10);
            svc.Reach("shutter");
            Mech.Run(g, 50);
            svc.Reload();
            Assert.Equal(60, g.Tick);
        }
    }
}
