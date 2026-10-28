using System;
using System.Collections.Generic;
using DeadLetter.Core.Beings;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Routes;
using DeadLetter.Core.Save;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>U-14: the save format, migration, the atomic store, persist flags, settings and the checkpoint service (§4.28).</summary>
    public class SaveTests
    {
        /// <summary>
        /// A version 1 save (the synthetic pre-release v1 fixture format, keyed after the prototype's <c>dl01-resume</c> fields; that localStorage record is never imported), written by an independent encoder
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
                Settings = new Settings { AutoRun = false, Calm = true, Brightness = 1.35, Music = false, SubtitleSize = TextSize.Large },
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
            Assert.True(SaveCodec.TryLoad(SaveCodec.Encode(m), out var again, out _));    // re-saved as the current version
            Assert.Equal(m.Flags, again.Flags);
            Assert.Equal(SaveModel.CurrentVersion, SaveCodec.Encode(m)[4]);
        }

        [Fact]
        public void Migration_V2SeenFlags_BecomeTheSeenSet_V3_OtherFlagsStay()
        {
            // A version 2 slot kept seen moments as persist flags named seen.<moment> (StoryFlags.Seen, now gone).
            var v2 = new SaveDocument(2);
            v2.SetString("cp", "bay"); v2.SetString("scene", "DL-04"); v2.SetDouble("playTime", 12.5);
            v2.SetBool("flag/seen.realise", true);
            v2.SetBool("flag/seen.labelWake", true);
            v2.SetBool("flag/seen.awe", false);
            v2.SetBool("flag/curio.scale", true);
            v2.SetDouble("mech/dl04.cradle/t", 0.25);
            byte[] bytes = SaveCodec.Encode(v2);
            Assert.Equal(2, bytes[4]);
            Assert.True(SaveCodec.TryLoad(bytes, out var m, out string err), err);
            Assert.Equal(new[] { "labelWake", "realise" }, m.Seen);
            Assert.Equal(new[] { "curio.scale" }, m.Flags);
            Assert.Equal("bay", m.Checkpoint);
            Assert.Equal(12.5, m.PlayTime);
            Assert.Equal(0.25, m.Mechanisms.ReadDouble("dl04.cradle/t"));
            byte[] again = SaveCodec.Encode(m);
            Assert.Equal(SaveModel.CurrentVersion, again[4]);
            Assert.True(SaveCodec.TryLoad(again, out var m3, out _));
            Assert.Equal(m.Seen, m3.Seen);
            Assert.Equal(again, SaveCodec.Encode(m3));

            // The v1 fixture goes through both steps.
            Assert.True(SaveCodec.TryLoad(Convert.FromBase64String(V1Fixture), out var m1, out _));
            Assert.Empty(m1.Seen);
        }

        /// <summary>
        /// A v2 slot saved mid-act: the station snapshot lacks the fields v3 added (<c>act.part</c>, <c>act.lastPart</c>,
        /// the latch's <c>pullF</c>, a lever's <c>clipStuck</c>). The migration fills them as a v2 station implies, so the
        /// snapshot restores (no fallback to the derived world) exactly as v3 would have saved it, and the act plays on.
        /// </summary>
        [Fact]
        public void Migration_V2MidActStationSnapshot_RestoresWithoutFallingBack()
        {
            MechanismGraph Build() => Mech.Graph("start", new Latch("dl01.latch", LatchParams.Dl01Latch()),
                new Pawl("dl08.pawl", PawlParams.Dl08Pawl()), new TestSource("dl08.platform") { Position = 0.5 });
            var played = Build();
            var latch = played.Get<Latch>("dl01.latch");
            var pawl = played.Get<Pawl>("dl08.pawl");
            Assert.Equal(-1, Mech.PlayAct(played, pawl, max: 40));           // a LeverStuck cut short (below the landing)
            Assert.Equal(-1, Mech.PlayAct(played, latch, max: 50));          // mid-Pull, f20
            var snap = Mech.Snapshot(played);

            var v2 = new SaveDocument(2);
            v2.SetString("cp", "start"); v2.SetString("scene", "S"); v2.SetDouble("playTime", 3);
            var keep = new HashSet<string> { "act.part", "act.lastPart", "pullF", "clipStuck" };
            foreach (var k in snap.Keys)
                if (!keep.Contains(k.Substring(k.IndexOf('/') + 1))) Copy(snap, k, v2);   // the v3-only fields are left out
            Assert.False(v2.Contains("mech/dl01.latch/pullF"));
            Assert.True(v2.Contains("mech/dl01.latch/act.fed"));

            var store = new MemorySaveStore();
            store.Slots[0] = SaveCodec.Encode(v2);
            var fresh = Build();
            var svc = new CheckpointService(fresh, Checkpoint.PrototypeOrder, store, 0, "S");
            Assert.True(svc.TryContinue());
            Assert.True(svc.RestoredSnapshot);                                // not the derived-world fallback
            Assert.NotNull(svc.CheckpointSnapshot);
            Assert.Equal(WithoutTick(snap.Dump()), WithoutTick(SaveKit.Dump(fresh)));   // as v3 would have saved it

            // The act plays on from the restored frames: the latch releases at f31, the pawl rattles and never bites.
            var l2 = fresh.Get<Latch>("dl01.latch");
            Assert.Equal(LatchState.Locked, l2.State);
            Assert.True(Mech.PlayAct(fresh, l2, startStep: 51) > 0);
            Assert.Equal(LatchState.Released, l2.State);
            Assert.Equal(72, l2.LeverDeg, 9);
        }

        private static void Copy(MemorySnapshot from, string key, SaveDocument to)
        {
            try { to.SetDouble("mech/" + key, from.ReadDouble(key)); return; } catch (InvalidOperationException) { }
            try { to.SetLong("mech/" + key, from.ReadLong(key)); return; } catch (InvalidOperationException) { }
            to.SetBool("mech/" + key, from.ReadBool(key));
        }

        private static string WithoutTick(string dump)
            => string.Join("\n", Array.FindAll(dump.Split('\n'), l => !l.StartsWith("graph/tick=", StringComparison.Ordinal)));

        [Fact]
        public void Seen_IsSavedWithTheSlot_SurvivesARespawn_AndStartOverClearsIt_L1309_L4133()
        {
            var fs = new MemoryFileSystem();
            var g = Mech.Graph("start", new TestSource("t.src"));
            var svc = SaveKit.Service(g, fs, "DL-01");
            svc.NewGame();
            int writes = svc.Writes;
            svc.MarkSeen("labelWake");
            Assert.True(svc.HasSeen("labelWake"));
            Assert.Equal(writes + 1, svc.Writes);                                    // saved when it played
            svc.MarkSeen("labelWake");
            Assert.Equal(writes + 1, svc.Writes);                                    // no change, no write
            svc.Reach("shutter");
            svc.Reload();
            Assert.True(svc.HasSeen("labelWake"));                                   // a respawn never replays it
            Assert.True(new AtomicFileStore(fs).TryLoad(0, out var saved));
            Assert.Equal(new[] { "labelWake" }, saved.Seen);

            var g2 = Mech.Graph("start", new TestSource("t.src"));
            var svc2 = SaveKit.Service(g2, fs, "DL-01");
            Assert.True(svc2.TryContinue());
            Assert.True(svc2.HasSeen("labelWake"));
            svc2.NewGame();
            Assert.False(svc2.HasSeen("labelWake"));                                 // Start over
            Assert.True(new AtomicFileStore(fs).TryLoad(0, out var fresh));
            Assert.Empty(fresh.Seen);
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
                Telemetry = true, Brightness = 1.8, Subtitles = false, SubtitleSize = TextSize.Small, SubtitleBackground = true, HoldToToggle = true,
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
            Assert.True(d.Sound && d.Music && d.Prompts && !d.StuckAssist && !d.Calm && d.AutoRun);
            Assert.False(d.Telemetry);   // §4.30: the shipped uploader is opt-in (the prototype defaulted it on)
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
        public void Settings_AppliedFromReloaded_StayPendingThroughLoad_WhenWritesAreRateLimited()
        {
            // The options store (U-17) applies settings edited before the slot was loaded from inside Reloaded.
            var g = Mech.Graph("start", new TestSource("t.a"));
            var store = new MemorySaveStore();
            var svc = new CheckpointService(g, Checkpoint.PrototypeOrder, store) { MinSecondsBetweenWrites = 2 };
            svc.ApplySettings(new Settings());                 // a write now, so the next one falls inside the window
            var slot = svc.ToModel();
            bool applied = false;
            svc.Reloaded += _ => { if (!applied) { applied = true; svc.ApplySettings(new Settings { Calm = true }); } };
            svc.Load(slot);
            Assert.True(svc.Pending);
            svc.Flush();
            Assert.True(store.TryLoad(0, out var m));
            Assert.True(m.Settings.Calm);
        }

        /// <summary>A slot with progress (checkpoint hall, a flag, play time, a snapshot) and non-default options.</summary>
        private static MemorySaveStore SlotWithProgress(out SaveModel saved)
        {
            var store = new MemorySaveStore();
            saved = Sample();
            saved.Checkpoint = "hall";
            saved.Settings = new Settings { Calm = true, MusicVolume = 0.25, SfxVolume = 0.5, BindingOverrides = "{\"bindings\":[]}" };
            store.Save(0, saved);
            return store;
        }

        [Fact]
        public void Settings_SavedOptionsHoldFromConstruction_WithoutContinue()
        {
            var store = SlotWithProgress(out _);
            var g = Mech.Graph("start", new TestSource("t.a"));
            var svc = new CheckpointService(g, Checkpoint.PrototypeOrder, store, 0, "S");
            Assert.True(svc.Settings.Calm);                            // photosensitivity: calm from the title screen on
            Assert.True(g.Calm);
            Assert.Equal(0.25, svc.Settings.MusicVolume);
            Assert.Equal(0.5, svc.Settings.SfxVolume);
            Assert.Equal("{\"bindings\":[]}", svc.Settings.BindingOverrides);
            Assert.False(svc.Started);
            Assert.Equal("start", svc.Current.Name);                   // the world is not loaded
            Assert.Equal(1, store.Writes);                             // and nothing was written
        }

        [Fact]
        public void Settings_EmptyStore_GivesDefaults()
        {
            var store = new MemorySaveStore();
            var g = Mech.Graph("start", new TestSource("t.a"));
            var svc = new CheckpointService(g, Checkpoint.PrototypeOrder, store);
            Assert.False(svc.TryLoadSettings());
            var d = new Settings();
            Assert.Equal(d.Calm, svc.Settings.Calm);
            Assert.Equal(d.MusicVolume, svc.Settings.MusicVolume);
            Assert.Equal(d.Brightness, svc.Settings.Brightness);
            Assert.Equal(d.BindingOverrides, svc.Settings.BindingOverrides);
            Assert.False(g.Calm);
            Assert.Equal(0, store.Writes);
        }

        [Fact]
        public void NewGame_KeepsThePlayersOptions()
        {
            var store = SlotWithProgress(out _);
            var g = Mech.Graph("start", new TestSource("t.a"));
            var svc = new CheckpointService(g, Checkpoint.PrototypeOrder, store);
            svc.NewGame();
            Assert.True(store.TryLoad(0, out var m));
            Assert.Equal("start", m.Checkpoint);                       // progress cleared
            Assert.Empty(m.Flags);
            Assert.True(m.Settings.Calm);                              // options kept
            Assert.Equal(0.25, m.Settings.MusicVolume);
            Assert.True(g.Calm);
        }

        [Fact]
        public void Settings_AppliedOnTheTitleScreen_KeepTheSlotsProgress_AndContinueUsesThem()
        {
            var store = SlotWithProgress(out var saved);
            var g = Mech.Graph("start", new TestSource("t.a"));
            var svc = new CheckpointService(g, Checkpoint.PrototypeOrder, store, 0, saved.Scene);
            var edited = svc.Settings.Clone();
            edited.Calm = false;
            edited.Brightness = 1.5;
            svc.ApplySettings(edited);                                 // before Continue or New Game

            Assert.True(store.TryLoad(0, out var m));
            Assert.Equal("hall", m.Checkpoint);
            Assert.Equal(saved.Scene, m.Scene);
            Assert.Equal(saved.PlayTime, m.PlayTime);
            Assert.Equal(saved.Flags, m.Flags);
            Assert.Equal(saved.Mechanisms.Dump(), m.Mechanisms.Dump());
            Assert.False(m.Settings.Calm);
            Assert.Equal(1.5, m.Settings.Brightness);
            Assert.Equal(0.25, m.Settings.MusicVolume);                // untouched options carried over

            // A fresh boot sees them, and Continue keeps them.
            var svc2 = new CheckpointService(Mech.Graph("start", new TestSource("t.a")), Checkpoint.PrototypeOrder, store, 0, saved.Scene);
            Assert.Equal(1.5, svc2.Settings.Brightness);
            Assert.True(svc2.TryContinue());
            Assert.Equal("hall", svc2.Current.Name);
            Assert.Equal(1.5, svc2.Settings.Brightness);
            Assert.False(svc2.Settings.Calm);
        }

        [Fact]
        public void Settings_AppliedOnTheTitleScreen_RateLimited_KeepProgress_AndSurviveContinue()
        {
            var store = SlotWithProgress(out var saved);
            var g = Mech.Graph("start", new TestSource("t.a"));
            var svc = new CheckpointService(g, Checkpoint.PrototypeOrder, store, 0, saved.Scene) { MinSecondsBetweenWrites = 2 };
            svc.ApplySettings(new Settings { Brightness = 1.2 });      // written now (options only)
            svc.ApplySettings(new Settings { Brightness = 1.6 });      // held by the rate limit
            Assert.True(svc.Pending);
            Assert.False(svc.TryLoadSettings());                       // the held options are newer than the slot's
            Assert.Equal(1.6, svc.Settings.Brightness);
            Assert.True(svc.TryContinue());                            // continue before the held write
            Assert.Equal("hall", svc.Current.Name);
            Assert.Equal(1.6, svc.Settings.Brightness);                // not the slot's older 1.2
            Assert.True(svc.Pending);
            svc.Flush();
            Assert.True(store.TryLoad(0, out var m));
            Assert.Equal("hall", m.Checkpoint);
            Assert.Equal(saved.Flags, m.Flags);
            Assert.Equal(1.6, m.Settings.Brightness);
        }

        [Fact]
        public void Update_BeforeAGameStarts_NeverOverwritesTheSlotsProgress()
        {
            var store = SlotWithProgress(out var saved);
            var white = new WhiteBrain("dl11.white", WhiteParams.Dl11(), new BeingSenses { Region = 5 });
            var g = Mech.Graph("start", white);
            var svc = new CheckpointService(g, Checkpoint.PrototypeOrder, store, 0, saved.Scene);
            svc.BindFlag(StoryFlags.Curio("other"), () => true, _ => { });  // a bound flag that differs from the slot's
            svc.Update(0.1, false);
            svc.SetFlag(StoryFlags.Curio("mug"));
            Assert.True(store.TryLoad(0, out var m));
            Assert.Equal("hall", m.Checkpoint);
            Assert.Equal(saved.Flags, m.Flags);
            Assert.Equal(saved.Mechanisms.Dump(), m.Mechanisms.Dump());
        }

        [Fact]
        public void Settings_AppliedBeforeAnySlot_WriteAFreshSlot_WithTheDefaultsElsewhere()
        {
            var store = new MemorySaveStore();
            var svc = new CheckpointService(Mech.Graph("start", new TestSource("t.a")), Checkpoint.PrototypeOrder, store);
            svc.ApplySettings(new Settings { Calm = true });
            Assert.True(store.TryLoad(0, out var m));
            Assert.True(m.Settings.Calm);
            Assert.Equal(Checkpoint.PrototypeOrder[0], m.Checkpoint);
            Assert.Empty(m.Flags);
            Assert.Equal(0, m.PlayTime);
            Assert.True(m.OptionsOnly);
            // Nothing to continue: a fresh install that only changed options never offers Continue.
            var svc2 = new CheckpointService(Mech.Graph("start", new TestSource("t.a")), Checkpoint.PrototypeOrder, store);
            Assert.True(svc2.Settings.Calm);
            Assert.False(svc2.TryContinue());
            svc2.NewGame();                                          // the first real save is a normal slot
            Assert.True(store.TryLoad(0, out var m2));
            Assert.False(m2.OptionsOnly);
            Assert.True(m2.Settings.Calm);
            Assert.True(new CheckpointService(Mech.Graph("start", new TestSource("t.a")), Checkpoint.PrototypeOrder, store).TryContinue());
        }

        [Fact]
        public void SceneStart_AdoptThenRestart_SavesProgress_NotOnlyOptions()
        {
            // #26's Begin/Handover path (TryAdoptSlot/Adopt, then Restart): a moment seen before the next checkpoint must
            // reach the slot (nathaniel3's probe on #24).
            var store = new MemorySaveStore();
            var first = new CheckpointService(Mech.Graph("start", new TestSource("t.a")), Checkpoint.PrototypeOrder, store);
            first.NewGame();
            var svc = new CheckpointService(Mech.Graph("start", new TestSource("t.a")), Checkpoint.PrototypeOrder, store);
            Assert.True(svc.TryAdoptSlot());
            svc.Restart(Checkpoint.PrototypeOrder[0]);
            svc.MarkSeen("kin");
            svc.Flush();
            Assert.True(store.TryLoad(0, out var m));
            Assert.Contains("kin", m.Seen);
            Assert.False(m.OptionsOnly);
        }

        [Fact]
        public void Adopt_KeepsOptionsAppliedBeforeTheGameStarted_StillWaitingToBeWritten()
        {
            var store = new MemorySaveStore();
            var first = new CheckpointService(Mech.Graph("start", new TestSource("t.a")), Checkpoint.PrototypeOrder, store);
            first.NewGame();                                    // the slot holds default options
            var svc = new CheckpointService(Mech.Graph("start", new TestSource("t.a")), Checkpoint.PrototypeOrder, store) { MinSecondsBetweenWrites = 2 };
            svc.ApplySettings(new Settings());                  // a write now, so the next one is held
            svc.ApplySettings(new Settings { Calm = true });
            Assert.True(svc.Pending);
            Assert.True(svc.TryAdoptSlot());
            Assert.True(svc.Settings.Calm);
        }

        [Fact]
        public void Boot_WritesNothingUntilSomethingChanges()
        {
            var store = new MemorySaveStore();
            var svc = new CheckpointService(Mech.Graph("start", new TestSource("t.a")), Checkpoint.PrototypeOrder, store);
            svc.Update(10, false);
            Assert.Equal(0, store.Writes);
            Assert.False(store.TryLoad(0, out _));
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
        public void Store_CrashBetweenTheTwoRenames_LoadsTheNewerTemp_AndPromotesIt()
        {
            var fs = new MemoryFileSystem();
            var st = new AtomicFileStore(fs);
            st.Save(0, At("shutter"));
            st.Save(0, At("hall"));
            fs.CrashAtReplace = 1;                                     // current → backup done; temp → current never happens
            Assert.Throws<System.IO.IOException>(() => st.Save(0, At("door")));
            Assert.False(fs.Files.ContainsKey("slot0.dls"));
            Assert.True(st.TryLoad(0, out var m));
            Assert.True(st.LoadedTemp);
            Assert.False(st.LoadedBackup);
            Assert.Equal("door", m.Checkpoint);                         // the newest save, not the backup's "hall"
            Assert.True(fs.Files.ContainsKey("slot0.dls"));            // promoted
            Assert.False(fs.Files.ContainsKey("slot0.dls.tmp"));
            Assert.True(st.TryLoad(0, out m));
            Assert.False(st.LoadedTemp);
            Assert.Equal("door", m.Checkpoint);
        }

        [Fact]
        public void Store_CrashBetweenTheTwoRenames_WithATornOrInvalidTemp_StillLoadsTheBackup()
        {
            var fs = new MemoryFileSystem();
            var st = new AtomicFileStore(fs);
            st.Save(0, At("shutter"));
            st.Save(0, At("hall"));
            fs.CrashAtReplace = 1;
            Assert.Throws<System.IO.IOException>(() => st.Save(0, At("door")));
            var good = fs.Files["slot0.dls.tmp"];
            fs.Files["slot0.dls.tmp"] = good[..(good.Length / 2)];     // torn
            Assert.True(st.TryLoad(0, out var m));
            Assert.True(st.LoadedBackup);
            Assert.False(st.LoadedTemp);
            Assert.Equal("hall", m.Checkpoint);
            Assert.Contains("temp", st.LastError);
            var flipped = (byte[])good.Clone();
            flipped[9] ^= 1;                                            // bad checksum
            fs.Files["slot0.dls.tmp"] = flipped;
            Assert.True(st.TryLoad(0, out m));
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
        public void Recapture_TakesTheCheckpointsSnapshotAgain_SoAReloadAndTheSlotFindTheWorldAsItWasThen()
        {
            var src = new TestSource("t.a");
            var g = Mech.Graph("start", src);
            var store = new MemorySaveStore();
            var svc = new CheckpointService(g, Checkpoint.PrototypeOrder, store);
            svc.Recapture();                                           // no game yet: nothing taken, nothing written
            Assert.Equal(0, store.Writes);
            Assert.True(svc.Reach("hall"));
            src.Position = 0.5;
            svc.Recapture();                                           // DL-19 §9: progress that persists at its checkpoint
            src.Position = 0.9;
            svc.Reload();
            Assert.Equal(0.5, src.Position);
            Assert.Equal("hall", svc.Current.Name);
            svc.Flush();
            Assert.True(store.TryLoad(0, out var m));
            Assert.Equal("hall", m.Checkpoint);
            var g2 = Mech.Graph("start", new TestSource("t.a"));
            var svc2 = new CheckpointService(g2, Checkpoint.PrototypeOrder, store);
            Assert.True(svc2.TryContinue());
            Assert.Equal(0.5, g2.Get<TestSource>("t.a").Position);
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

        // ---- Stale snapshots: a later build under the same scene name ----

        /// <summary>
        /// Saves <paramref name="played"/>'s snapshot at <paramref name="cp"/> (edited by <paramref name="edit"/>), then
        /// continues into <paramref name="fresh"/>: it must not throw, must not restore, and must equal a derived reset.
        /// </summary>
        private static void ContinuesIntoTheDerivedWorld(MechanismGraph played, MechanismGraph fresh, MechanismGraph derived, string cp,
            Action<MemorySnapshot> edit = null)
        {
            var snap = new MemorySnapshot();
            played.Snapshot(snap);
            edit?.Invoke(snap);
            var store = new MemorySaveStore();
            store.Save(0, new SaveModel { Checkpoint = cp, Scene = "S", Mechanisms = snap });
            var svc = new CheckpointService(fresh, Checkpoint.PrototypeOrder, store, 0, "S");
            Assert.True(svc.TryContinue());
            Assert.False(svc.RestoredSnapshot);
            Assert.Null(svc.CheckpointSnapshot);
            Assert.Equal(cp, svc.Current.Name);
            Assert.Equal(SaveKit.Dump(derived), SaveKit.Dump(fresh));  // wholly derived, never half-restored
            svc.Reload();                                              // and a respawn stays derived
            Assert.False(svc.RestoredSnapshot);
        }

        private static MechanismGraph Line(int capacity = -1)
        {
            var p = CarrierLineParams.Dl06Line();
            if (capacity > 0) p.Capacity = capacity;
            return Mech.Graph("scanned", new TestSource("dl06.stopLever") { Engaged = true }, new TestSource("dl06.points"), new CarrierLine("dl06.line", p));
        }

        private static MechanismGraph Belt(int capacity = -1)
        {
            var p = ReturnsBeltParams.Dl08Belt();
            if (capacity > 0) p.Capacity = capacity;
            return Mech.Graph("cage", new TestSource("dl08.pawl") { Engaged = true }, new ReturnsBelt("dl08.belt", p));
        }

        private static int Count(MechanismGraph g, string id)
            => g.TryGet<CarrierLine>(id, out var l) ? l.Count : g.Get<ReturnsBelt>(id).Count;

        [Fact]
        public void Continue_CarrierLineSnapshot_WithMoreCarriersThanThisBuildHolds_ContinuesDerived()
        {
            var played = Line();
            Assert.True(Mech.RunUntil(played, () => Count(played, "dl06.line") >= 2, 20000) > 0);
            ContinuesIntoTheDerivedWorld(played, Line(capacity: 1), Line(capacity: 1), "scanned");
        }

        [Fact]
        public void Continue_CarrierLineSnapshot_WithANegativeOrHugeCount_ContinuesDerived()
        {
            ContinuesIntoTheDerivedWorld(Line(), Line(), Line(), "scanned", s => s.WriteLong("dl06.line/n", 1L << 40));
            ContinuesIntoTheDerivedWorld(Line(), Line(), Line(), "scanned", s => s.WriteLong("dl06.line/n", -1));
        }

        [Fact]
        public void Continue_ReturnsBeltSnapshot_WithMoreCratesThanThisBuildHolds_ContinuesDerived()
        {
            var played = Belt();
            Assert.True(Mech.RunUntil(played, () => Count(played, "dl08.belt") >= 2, 5000, new PlayerPose(89.5, 1.6)) > 0);
            ContinuesIntoTheDerivedWorld(played, Belt(capacity: 1), Belt(capacity: 1), "cage");
        }

        [Fact]
        public void Continue_ReturnsBeltSnapshot_WithACrateTypeThisBuildLacks_ContinuesDerived()
        {
            var played = Belt();
            Assert.True(Mech.RunUntil(played, () => Count(played, "dl08.belt") >= 1, 5000, new PlayerPose(89.5, 1.6)) > 0);
            ContinuesIntoTheDerivedWorld(played, Belt(), Belt(), "cage", s => s.WriteLong("dl08.belt/c0.type", 7));
            ContinuesIntoTheDerivedWorld(played, Belt(), Belt(), "cage", s => s.WriteLong("dl08.belt/c0.type", -1));
        }

        [Fact]
        public void Continue_WhiteSnapshot_InAWaterThisBuildLacks_ContinuesDerived()
        {
            static MechanismGraph White(WhiteParams p) => Mech.Graph("ringc", new WhiteBrain("dl11.white", p, new BeingSenses { Region = 5 }));
            var played = White(WhiteParams.Chapter1());                // three waters
            ContinuesIntoTheDerivedWorld(played, White(WhiteParams.Dl11()), White(WhiteParams.Dl11()), "ringc",
                s => s.WriteLong("dl11.white/water", 2));               // a later build has one
        }

        [Fact]
        public void Codec_ACrcValidFileWithABareMechKey_IsUnreadable_NotAThrow()
        {
            var d = Sample().ToDocument();
            d.SetLong("mech/", 1);                                     // maps to an empty snapshot key
            byte[] bytes = SaveCodec.Encode(d);
            Assert.True(SaveCodec.TryDecode(bytes, out _, out _));     // the CRC and framing are fine
            Assert.False(SaveCodec.TryLoad(bytes, out var m, out string err));
            Assert.Null(m);
            Assert.False(string.IsNullOrEmpty(err));

            var store = new MemorySaveStore();
            store.Slots[0] = bytes;
            var svc = new CheckpointService(Mech.Graph("start", new TestSource("t.a")), Checkpoint.PrototypeOrder, store, 0, "S");
            Assert.False(svc.TryContinue());

            var fs = new MemoryFileSystem();
            var st = new AtomicFileStore(fs);
            st.Save(0, At("hall"));
            st.Save(0, At("door"));
            fs.Files["slot0.dls"] = bytes;                             // the current file is malformed: the backup loads
            Assert.True(st.TryLoad(0, out m));
            Assert.True(st.LoadedBackup);
            Assert.Equal("hall", m.Checkpoint);
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
