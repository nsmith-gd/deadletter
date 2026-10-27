using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using DeadLetter.Core.Audio;
using DeadLetter.Runtime.Audio;
using UnityEditor;
using UnityEngine;

namespace DeadLetter.Editor.Audio
{
    /// <summary>
    /// <c>Dead Letter → Audio → Import Audio</c> (issue #13). Git holds one copy of every sound: the renders in
    /// <c>art/sfx/out/</c> and the score in <c>game/undelivered/assets/music/</c>. This copies them into
    /// <c>Assets/Audio/</c> (gitignored), writes each copy's <c>.meta</c> first with a stable GUID (MD5 of the asset
    /// path, <see cref="StableGuid"/>) so references survive a re-import on any machine, lets
    /// <see cref="AudioImportSettings"/> set the per-platform import settings, and builds <c>Assets/Audio/SfxBank.asset</c>.
    /// <list type="bullet">
    /// <item><b>SFX:</b> every top-level <c>art/sfx/out/*.wav</c> (the <c>ir/</c> impulses stay sources: the reverb is baked).</item>
    /// <item><b>Music:</b> only the 19 files the game plays (<see cref="MusicCatalog"/>); the 10 unreferenced ones stay out.
    /// Cues are copied as MP3. Loops are trimmed to their loop region (the 2 s padding at each end goes) and written as
    /// <c>&lt;file&gt;_loop.wav</c>, because an AudioSource cannot loop a sub-range.</item>
    /// <item><b>Voice recordings:</b> <c>game/undelivered/assets/voice/*</c> if that folder exists (key <c>voice_&lt;file&gt;</c>).</item>
    /// </list>
    /// Re-running is cheap: unchanged files are skipped, and the bank is rebuilt in place (its GUID is kept).
    /// </summary>
    public static class AudioImporter
    {
        public const string AudioRoot = "Assets/Audio";
        public const string SfxFolder = AudioRoot + "/Sfx";
        public const string MusicFolder = AudioRoot + "/Music";
        public const string LoopSourceFolder = MusicFolder + "/Source";
        public const string VoiceFolder = AudioRoot + "/Voice";
        public const string BankPath = AudioRoot + "/SfxBank.asset";

        private static readonly string[] VoiceExtensions = { ".wav", ".mp3", ".ogg" };

        /// <summary>The repository root: <c>Assets/</c> is <c>unity/DeadLetter/Assets</c>.</summary>
        public static string RepoRoot => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
        private static string ProjectRoot => Path.GetFullPath(Path.Combine(Application.dataPath, ".."));

        [MenuItem("Dead Letter/Audio/Import Audio")]
        public static void ImportAudio()
        {
            string sfxSrc = Path.Combine(RepoRoot, "art", "sfx", "out");
            string musicSrc = Path.Combine(RepoRoot, "game", "undelivered", "assets", "music");
            string voiceSrc = Path.Combine(RepoRoot, "game", "undelivered", "assets", "voice");
            if (!Directory.Exists(sfxSrc) || !Directory.Exists(musicSrc))
            {
                Debug.LogError("[Audio] Sources not found: " + sfxSrc + " and " + musicSrc + ". Is the project at unity/DeadLetter in the repo?");
                return;
            }

            int copied = 0, skipped = 0;
            try
            {
                EnsureFolder(SfxFolder);
                EnsureFolder(MusicFolder);

                // 1. SFX.
                foreach (string src in Directory.GetFiles(sfxSrc, "*.wav", SearchOption.TopDirectoryOnly))
                    if (CopyWithMeta(src, SfxFolder + "/" + Path.GetFileName(src))) copied++; else skipped++;

                // 2. Music cues as they are; loop sources into a temporary folder for trimming.
                var loopsToTrim = new List<MusicTrack>();
                foreach (MusicTrack t in MusicCatalog.All)
                {
                    string src = Path.Combine(musicSrc, t.File + ".mp3");
                    if (!File.Exists(src)) { Debug.LogError("[Audio] Missing music file " + src); continue; }
                    if (!t.IsLoop)
                    {
                        if (CopyWithMeta(src, MusicFolder + "/" + t.File + ".mp3")) copied++; else skipped++;
                        continue;
                    }
                    string trimmed = MusicFolder + "/" + t.AssetName + ".wav";
                    if (File.Exists(Abs(trimmed)) && File.GetLastWriteTimeUtc(Abs(trimmed)) >= File.GetLastWriteTimeUtc(src))
                    {
                        WriteMetaIfNeeded(trimmed);
                        skipped++;
                        continue;
                    }
                    EnsureFolder(LoopSourceFolder);
                    CopyWithMeta(src, LoopSourceFolder + "/" + t.File + ".mp3");
                    loopsToTrim.Add(t);
                }

                // 3. Voice recordings, once they exist.
                if (Directory.Exists(voiceSrc))
                {
                    EnsureFolder(VoiceFolder);
                    foreach (string src in Directory.GetFiles(voiceSrc))
                        if (Array.IndexOf(VoiceExtensions, Path.GetExtension(src).ToLowerInvariant()) >= 0)
                            if (CopyWithMeta(src, VoiceFolder + "/" + Path.GetFileName(src))) copied++; else skipped++;
                }

                AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);

                // 4. Trim the loops: read the PCM copy, write the loop region, drop the copy.
                foreach (MusicTrack t in loopsToTrim)
                    if (TrimLoop(t)) copied++;
                if (AssetDatabase.IsValidFolder(LoopSourceFolder)) AssetDatabase.DeleteAsset(LoopSourceFolder);
                AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);

                // 5. The bank.
                SfxBank bank = BuildBank(out int sounds, out int music);
                Debug.Log("[Audio] Import done: " + copied + " written, " + skipped + " unchanged; bank " + BankPath + " has " +
                          sounds + " sounds and " + music + " music clips.", bank);
            }
            finally
            {
                EditorUtility.ClearProgressBar();
            }
        }

        // ---- Copy and metas --------------------------------------------------------------------------------------------

        /// <summary>Copies <paramref name="src"/> to the project path if it is new or changed; writes its .meta first.</summary>
        private static bool CopyWithMeta(string src, string assetPath)
        {
            WriteMetaIfNeeded(assetPath);
            string dst = Abs(assetPath);
            var si = new FileInfo(src);
            var di = new FileInfo(dst);
            if (di.Exists && di.Length == si.Length && di.LastWriteTimeUtc >= si.LastWriteTimeUtc) return false;
            Directory.CreateDirectory(Path.GetDirectoryName(dst));
            File.Copy(src, dst, true);
            return true;
        }

        /// <summary>Writes the deterministic .meta unless one with the right GUID is there (Unity then fills in the rest).</summary>
        private static void WriteMetaIfNeeded(string assetPath, bool folder = false)
        {
            string meta = Abs(assetPath) + ".meta";
            string want = StableGuid.ForPath(assetPath);
            if (File.Exists(meta) && StableGuid.ReadGuid(File.ReadAllText(meta)) == want) return;
            if (File.Exists(meta))
                Debug.LogWarning("[Audio] Replacing the GUID of " + assetPath + " with its stable one; re-link anything that used the old one.");
            Directory.CreateDirectory(Path.GetDirectoryName(meta));
            File.WriteAllText(meta, folder ? StableGuid.FolderMeta(assetPath) : StableGuid.FileMeta(assetPath), new UTF8Encoding(false));
        }

        private static void EnsureFolder(string assetPath)
        {
            WriteMetaIfNeeded(assetPath, true);
            Directory.CreateDirectory(Abs(assetPath));
        }

        private static string Abs(string assetPath) => Path.Combine(ProjectRoot, assetPath.Replace('/', Path.DirectorySeparatorChar));

        // ---- Loops -----------------------------------------------------------------------------------------------------

        private static bool TrimLoop(MusicTrack t)
        {
            string srcPath = LoopSourceFolder + "/" + t.File + ".mp3";
            string dstPath = MusicFolder + "/" + t.AssetName + ".wav";
            var clip = AssetDatabase.LoadAssetAtPath<AudioClip>(srcPath);
            if (clip == null) { Debug.LogError("[Audio] Could not load " + srcPath + " to trim it."); return false; }
            if (clip.loadState != AudioDataLoadState.Loaded) clip.LoadAudioData();
            int rate = clip.frequency, ch = clip.channels;
            int start = (int)Math.Round(t.LoopStart * rate), frames = (int)Math.Round((t.LoopEnd - t.LoopStart) * rate);
            if (start + frames > clip.samples)
            {
                Debug.LogError("[Audio] " + srcPath + " is shorter (" + clip.length + " s) than its loop end " + t.LoopEnd + " s.");
                return false;
            }
            var data = new float[frames * ch];
            if (!clip.GetData(data, start))
            {
                Debug.LogError("[Audio] AudioClip.GetData failed for " + srcPath + " (it must import as Decompress On Load). " +
                               "The loop " + t.Key + " was not written.");
                return false;
            }
            WriteMetaIfNeeded(dstPath);
            WriteWav(Abs(dstPath), data, ch, rate);
            return true;
        }

        /// <summary>16-bit PCM WAV.</summary>
        private static void WriteWav(string path, float[] interleaved, int channels, int rate)
        {
            using (var fs = new FileStream(path, FileMode.Create, FileAccess.Write))
            using (var w = new BinaryWriter(fs))
            {
                int dataBytes = interleaved.Length * 2;
                w.Write(Encoding.ASCII.GetBytes("RIFF"));
                w.Write(36 + dataBytes);
                w.Write(Encoding.ASCII.GetBytes("WAVE"));
                w.Write(Encoding.ASCII.GetBytes("fmt "));
                w.Write(16);
                w.Write((short)1);
                w.Write((short)channels);
                w.Write(rate);
                w.Write(rate * channels * 2);
                w.Write((short)(channels * 2));
                w.Write((short)16);
                w.Write(Encoding.ASCII.GetBytes("data"));
                w.Write(dataBytes);
                for (int i = 0; i < interleaved.Length; i++)
                {
                    float v = Mathf.Clamp(interleaved[i], -1f, 1f);
                    w.Write((short)Mathf.RoundToInt(v * 32767f));
                }
            }
        }

        // ---- The bank --------------------------------------------------------------------------------------------------

        private static SfxBank BuildBank(out int soundCount, out int musicCount)
        {
            var files = new List<string>();
            foreach (string f in Directory.GetFiles(Abs(SfxFolder), "*.wav")) files.Add(Path.GetFileName(f));
            SfxCatalog catalog = SfxCatalog.FromFiles(files, WetPolicy.PreferWet);

            var sounds = new List<SfxBank.Sound>();
            foreach (SfxEntry e in catalog.Entries)
            {
                var takes = new List<AudioClip>();
                foreach (string stem in e.Files)
                {
                    var c = AssetDatabase.LoadAssetAtPath<AudioClip>(SfxFolder + "/" + stem + ".wav");
                    if (c != null) takes.Add(c); else Debug.LogWarning("[Audio] Not imported: " + stem);
                }
                if (takes.Count > 0) sounds.Add(new SfxBank.Sound { key = e.Key, loop = e.Loop, takes = takes.ToArray() });
            }
            if (AssetDatabase.IsValidFolder(VoiceFolder))
                foreach (string f in Directory.GetFiles(Abs(VoiceFolder)))
                {
                    if (Array.IndexOf(VoiceExtensions, Path.GetExtension(f).ToLowerInvariant()) < 0) continue;
                    var c = AssetDatabase.LoadAssetAtPath<AudioClip>(VoiceFolder + "/" + Path.GetFileName(f));
                    if (c != null) sounds.Add(new SfxBank.Sound { key = "voice_" + Path.GetFileNameWithoutExtension(f), takes = new[] { c } });
                }

            var music = new List<SfxBank.Music>();
            foreach (MusicTrack t in MusicCatalog.All)
            {
                string path = MusicFolder + "/" + t.AssetName + (t.IsLoop ? ".wav" : ".mp3");
                var c = AssetDatabase.LoadAssetAtPath<AudioClip>(path);
                if (c != null) music.Add(new SfxBank.Music { key = t.Key, clip = c });
                else Debug.LogWarning("[Audio] No clip for music key " + t.Key + " at " + path);
            }

            var bank = AssetDatabase.LoadAssetAtPath<SfxBank>(BankPath);
            if (bank == null)
            {
                bank = ScriptableObject.CreateInstance<SfxBank>();
                AssetDatabase.CreateAsset(bank, BankPath);
            }
            bank.SetContents(sounds, music);
            EditorUtility.SetDirty(bank);
            AssetDatabase.SaveAssets();
            soundCount = sounds.Count;
            musicCount = music.Count;
            return bank;
        }
    }
}
