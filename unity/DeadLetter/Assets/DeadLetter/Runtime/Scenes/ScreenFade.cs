using UnityEngine;

namespace DeadLetter.Runtime.Scenes
{
    /// <summary>
    /// A full-screen black fade the GameHost holds while it loads the scenes a continue or a respawn needs (port_architecture
    /// §7: "behind the existing fade (1.3 s) or death cut (0.6 s)"). Drawn with IMGUI over everything, so it needs no canvas,
    /// no UI package reference and no camera; it draws nothing at all while clear. Starts opaque, so the first frames before
    /// the boot load are black. Runs on unscaled time (it fades in and out under a pause too).
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class ScreenFade : MonoBehaviour
    {
        [Tooltip("Seconds from clear to black.")]
        [SerializeField] private float fadeOutSeconds = 0.6f;
        [Tooltip("Seconds from black to clear (the prototype's checkpoint fade, 1.3 s).")]
        [SerializeField] private float fadeInSeconds = 1.3f;

        private float _alpha = 1f, _target = 1f;

        /// <summary>0 clear … 1 black.</summary>
        public float Alpha => _alpha;
        /// <summary>The screen is fully black (a load may swap what is behind it).</summary>
        public bool IsBlack => _alpha >= 1f;
        public bool IsClear => _alpha <= 0f;

        /// <summary>Fade to black (<paramref name="instant"/>: now).</summary>
        public void FadeOut(bool instant = false)
        {
            _target = 1f;
            if (instant) _alpha = 1f;
        }

        /// <summary>Fade back to the game.</summary>
        public void FadeIn() => _target = 0f;

        private void Update()
        {
            if (_alpha == _target) return;
            float seconds = _target > _alpha ? fadeOutSeconds : fadeInSeconds;
            _alpha = seconds <= 0f ? _target : Mathf.MoveTowards(_alpha, _target, Time.unscaledDeltaTime / seconds);
        }

        private void OnGUI()
        {
            if (_alpha <= 0f || Event.current.type != EventType.Repaint) return;
            GUI.depth = -1000;
            Color c = GUI.color;
            GUI.color = new Color(0f, 0f, 0f, _alpha);
            GUI.DrawTexture(new Rect(0f, 0f, Screen.width, Screen.height), Texture2D.whiteTexture);
            GUI.color = c;
        }
    }
}
