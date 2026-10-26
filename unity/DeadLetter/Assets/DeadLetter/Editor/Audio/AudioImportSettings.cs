using DeadLetter.Core.Audio;
using UnityEditor;
using UnityEngine;

namespace DeadLetter.Editor.Audio
{
    /// <summary>
    /// Import settings for everything under <c>Assets/Audio/</c>, re-applied on every import so nobody has to set them
    /// by hand (issue #13: Vorbis for music and loops, ADPCM for short SFX, per platform):
    /// <list type="bullet">
    /// <item><b>Music</b> (cues and trimmed loops): Vorbis, compressed in memory (not streamed, so
    /// <c>PlayScheduled</c> starts on the sample for the directed moments). Switch: lower quality.</item>
    /// <item><b>SFX loops</b> (<c>loop_*</c>, <c>amb_*_loop</c>, <c>voice_crackle_*</c>) and <b>voice recordings</b>: Vorbis,
    /// compressed in memory.</item>
    /// <item><b>Short SFX</b>: ADPCM, decompressed on load (cheap to trigger, small).</item>
    /// <item><c>Music/Source/</c>: the importer's temporary copy of a padded loop, PCM and decompressed so
    /// <c>AudioClip.GetData</c> can read it for trimming.</item>
    /// </list>
    /// Switch overrides go through the platform-name string <see cref="SwitchPlatform"/>, so this compiles and runs without
    /// the Switch build module (the override is simply ignored where the platform is unknown).
    /// </summary>
    public sealed class AudioImportSettings : AssetPostprocessor
    {
        public const string Root = "Assets/Audio/";
        public const string SwitchPlatform = "Switch";

        public const float MusicQuality = 0.7f, LoopQuality = 0.6f, VoiceQuality = 0.6f;
        public const float SwitchMusicQuality = 0.5f, SwitchLoopQuality = 0.45f;

        private static bool _warned;

        public override uint GetVersion() => 1;

        private void OnPreprocessAudio()
        {
            if (!assetPath.StartsWith(Root)) return;
            var importer = assetImporter as global::UnityEditor.AudioImporter;
            if (importer == null) return;
            string rel = assetPath.Substring(Root.Length);

            importer.forceToMono = false;
            importer.loadInBackground = false;
            AudioImporterSampleSettings s = importer.defaultSampleSettings;
            s.sampleRateSetting = AudioSampleRateSetting.PreserveSampleRate;

            if (rel.StartsWith("Music/Source/"))
            {
                s.loadType = AudioClipLoadType.DecompressOnLoad;
                s.compressionFormat = AudioCompressionFormat.PCM;
                importer.defaultSampleSettings = s;
                importer.ClearSampleSettingOverride(SwitchPlatform);
                return;
            }

            string stem = System.IO.Path.GetFileNameWithoutExtension(rel);
            SfxNaming.TryParse(stem, out string key, out _, out _);
            bool music = rel.StartsWith("Music/");
            bool voice = rel.StartsWith("Voice/");
            bool loop = !music && !voice && SfxNaming.IsLoop(key);

            AudioImporterSampleSettings sw = s;
            if (music || loop || voice)
            {
                s.loadType = AudioClipLoadType.CompressedInMemory;
                s.compressionFormat = AudioCompressionFormat.Vorbis;
                s.quality = music ? MusicQuality : voice ? VoiceQuality : LoopQuality;
                sw = s;
                sw.quality = music ? SwitchMusicQuality : SwitchLoopQuality;
            }
            else
            {
                s.loadType = AudioClipLoadType.DecompressOnLoad;
                s.compressionFormat = AudioCompressionFormat.ADPCM;
                sw = s;
            }
            importer.defaultSampleSettings = s;
            if (!importer.SetOverrideSampleSettings(SwitchPlatform, sw) && !_warned)
            {
                _warned = true;
                Debug.Log("[Audio] The '" + SwitchPlatform + "' audio overrides were not set (platform not known to this editor).");
            }
        }
    }
}
