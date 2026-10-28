using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using DeadLetter.Core.Simulation.Replay;
using DeadLetter.Core.Simulation.Replay.Scripts;
using DeadLetter.Runtime;
using DeadLetter.Core.Platform;
using DeadLetter.Runtime.Platform;
using DeadLetter.Runtime.Scenes;
using UnityEngine;
using UnityEngine.Rendering;

namespace DeadLetter.Runtime.Dev
{
    /// <summary>
    /// A test-only playthrough with screenshots (the Unity side of the prototype comparison, tools/capture/): Core's bot
    /// (<see cref="PrologueScript"/>, bot.js's port) plays the prologue through <see cref="D17Controller.InputSource"/> while
    /// <see cref="GameHost"/> runs the game as usual, one Core step per rendered frame (<see cref="Time.captureFramerate"/>
    /// 60), and the camera's view is saved as PNG:
    /// <list type="bullet">
    /// <item>at each of <see cref="times"/>, in seconds after the bot's <c>play</c> mark (control comes to him), and</item>
    /// <item>at each new bot mark (<c>cp &lt;checkpoint&gt;</c>, <c>DL-02</c>, …) when <see cref="captureMarks"/> is set,</item>
    /// </list>
    /// the clock both sides share, so the prototype's capture (tools/capture/capture_prototype.mjs, the same seed and marks)
    /// lines up frame for frame. <c>capture.json</c> lists every shot with his position and scene, then the bot's result.
    /// The fade (<see cref="ScreenFade"/>, drawn with IMGUI) is composited into the shot. Added by the editor's
    /// <c>Dead Letter → Capture</c> (PlayCapture), never by a generated scene.
    /// </summary>
    [DefaultExecutionOrder(10000)]   // after GameHost, D-17 and the mechanism views have posed the frame
    public sealed class PlaythroughCapture : MonoBehaviour
    {
        public string outDir = "Captures";
        public uint seed = 1;
        public bool mechanical = true;
        [Tooltip("Seconds after the bot's play mark.")]
        public double[] times = { 0.1, 1, 3, 6, 10 };
        public bool captureMarks = true;
        [Tooltip("Stop this many seconds after the play mark, or when the bot is done.")]
        public double maxPlaySeconds = 600;
        public int width = 1280, height = 720;

        /// <summary>Raised once, when the run ends (the bot is done, stuck, or out of time).</summary>
        public event Action Finished;

        private GameHost _host;
        private D17Controller _player;
        private UnityEngine.Camera _cam;
        private ScreenFade _fade;
        private ChapterSimTarget _target;
        private PrologueScript _bot;
        private RenderTexture _rt;
        private Texture2D _read;
        private int _calls, _nextTime, _marksSeen, _shots;
        private bool _finished;
        private readonly StringBuilder _json = new StringBuilder();

        private void Awake()
        {
            Time.captureFramerate = 60;
        }

        private void Start()
        {
            _host = GameHost.Instance;
            _player = FindFirstObjectByType<D17Controller>();
            _fade = FindFirstObjectByType<ScreenFade>();
            _cam = UnityEngine.Camera.main;
            if (_host == null || _host.Sim == null || _player == null || _cam == null)
            {
                Debug.LogError("[Capture] Needs DL_Persistent's GameHost, D-17 and the main camera.");
                Finish();
                return;
            }
            PauseGate gate = PlatformServicesHost.Instance != null ? PlatformServicesHost.Instance.Pause : null;
            if (gate != null)
            {
                gate.PauseOnFocusLoss = false;   // a headless editor never has focus
                gate.OnFocus(true, true);
            }
            Directory.CreateDirectory(outDir);
            _target = new ChapterSimTarget(_host.Sim);
            _bot = new PrologueScript(new PlayerModel(seed, mechanical));
            _bot.Begin(_target);
            _player.InputSource = () =>
            {
                if (_calls++ > 0) _target.HostStepped();
                return _bot.Tick();
            };
            _rt = new RenderTexture(width, height, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB) { name = "Capture" };
            _read = new Texture2D(width, height, TextureFormat.RGB24, false, false);
            _cam.targetTexture = _rt;   // Core's framing reads the camera's aspect: the shot's, not the editor window's
            _json.Append("{\n \"seed\": ").Append(seed).Append(", \"mechanical\": ").Append(mechanical ? "true" : "false")
                 .Append(", \"width\": ").Append(width).Append(", \"height\": ").Append(height).Append(",\n \"shots\": [");
            Debug.Log("[Capture] Seed " + seed + (mechanical ? " (mechanical)" : "") + " → " + Path.GetFullPath(outDir));
        }

        private void LateUpdate()
        {
            if (_finished || _bot == null) return;
            if (Time.frameCount % 600 == 0)
                Debug.Log("[Capture] frame " + Time.frameCount + ", " + _calls + " steps, in play " + _host.InPlay + ", x " +
                          _target.X.ToString("0.00", CultureInfo.InvariantCulture) + ", fade " + (_fade != null ? _fade.Alpha : 0f));
            SimResult o = _bot.Out;
            bool played = o.TryGetMark("play", out double play);
            double rel = played ? _target.Clock - play : double.NaN;

            if (captureMarks)
                while (_marksSeen < o.Marks.Count)
                {
                    string key = o.Marks[_marksSeen].Key;
                    _marksSeen++;
                    Shoot("m" + _marksSeen.ToString("00") + "_" + Safe(key), rel);
                }
            while (played && _nextTime < times.Length && rel >= times[_nextTime] - 1e-9)
            {
                Shoot("t" + times[_nextTime].ToString("0000.0", CultureInfo.InvariantCulture), rel);
                _nextTime++;
            }

            if (o.Done || (played && rel > maxPlaySeconds) || (!played && _calls > 60 * 300))
                Finish();
            else if (Time.frameCount > (maxPlaySeconds + 300) * 60)
            {
                Debug.LogError("[Capture] Stalled: " + _calls + " Core steps in " + Time.frameCount + " frames.");
                Finish();
            }
        }

        private void Shoot(string name, double rel)
        {
            Render();
            RenderTexture prev = RenderTexture.active;
            RenderTexture.active = _rt;
            _read.ReadPixels(new Rect(0, 0, width, height), 0, 0, false);
            RenderTexture.active = prev;
            float fade = _fade != null ? _fade.Alpha : 0f;
            if (fade > 0f)
            {
                Color32[] px = _read.GetPixels32();
                float k = 1f - fade;
                for (int i = 0; i < px.Length; i++)
                    px[i] = new Color32((byte)(px[i].r * k), (byte)(px[i].g * k), (byte)(px[i].b * k), 255);
                _read.SetPixels32(px);
            }
            _read.Apply(false);
            File.WriteAllBytes(Path.Combine(outDir, name + ".png"), _read.EncodeToPNG());

            var inv = CultureInfo.InvariantCulture;
            _json.Append(_shots++ == 0 ? "\n" : ",\n").Append("  {\"name\": \"").Append(name)
                 .Append("\", \"steps\": ").Append(_calls)
                 .Append(", \"clock\": ").Append(_target.Clock.ToString("0.000", inv))
                 .Append(", \"rel\": ").Append(double.IsNaN(rel) ? "null" : rel.ToString("0.000", inv))
                 .Append(", \"x\": ").Append(_target.X.ToString("0.000", inv))
                 .Append(", \"y\": ").Append(_target.Y.ToString("0.000", inv))
                 .Append(", \"scene\": \"").Append(_target.SceneName).Append("\", \"checkpoint\": \"").Append(_target.Checkpoint)
                 .Append("\", \"act\": \"").Append(_target.Act).Append("\", \"fade\": ").Append(fade.ToString("0.00", inv)).Append('}');
        }

        /// <summary>One render of the main camera into the shot's texture (a headless editor has no game view to draw).</summary>
        private void Render()
        {
            var request = new RenderPipeline.StandardRequest { destination = _rt };
            if (RenderPipeline.SupportsRenderRequest(_cam, request)) RenderPipeline.SubmitRenderRequest(_cam, request);
            else _cam.Render();
        }

        private void Finish()
        {
            if (_finished) return;
            _finished = true;
            if (_player != null) _player.InputSource = null;
            if (_bot != null)
            {
                SimResult o = _bot.Out;
                _json.Append("\n ],\n \"result\": ").Append(o.ToJson()).Append("\n}\n");
                File.WriteAllText(Path.Combine(outDir, "capture.json"), _json.ToString());
                Debug.Log("[Capture] " + _shots + " shots; " + (o.Error ?? (o.Done ? "done" : "stopped")) + " at x=" +
                          _target.X.ToString("0.00", CultureInfo.InvariantCulture) + ", clock " + _target.Clock.ToString("0.0", CultureInfo.InvariantCulture));
            }
            if (_cam != null) _cam.targetTexture = null;
            Time.captureFramerate = 0;
            Finished?.Invoke();
        }

        private void OnDestroy()
        {
            if (_rt != null) Destroy(_rt);
            if (_read != null) Destroy(_read);
        }

        private static string Safe(string s)
        {
            var sb = new StringBuilder(s.Length);
            foreach (char c in s) sb.Append(char.IsLetterOrDigit(c) || c == '-' ? c : '_');
            return sb.ToString();
        }
    }
}
