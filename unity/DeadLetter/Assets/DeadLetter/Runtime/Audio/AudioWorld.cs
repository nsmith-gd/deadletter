using System.Collections.Generic;
using DeadLetter.Core.Audio;
using UnityEngine;

namespace DeadLetter.Runtime.Audio
{
    /// <summary>
    /// What the audio reads from the game each frame: D-17's lane x, his region and deck, and the named conditions the
    /// emitters and tannoys wait on (<c>revealed</c>, <c>released</c>, <c>lessonRunning</c>…). Scene rules (U-20–U-22) set
    /// them; until then <see cref="listener"/>'s x is used and every condition is false unless set.
    /// Also holds the one pan setting (±<see cref="edgePan"/> at the frame edges) every positional sound uses.
    /// </summary>
    [DisallowMultipleComponent]
    [DefaultExecutionOrder(-50)]
    public sealed class AudioWorld : MonoBehaviour
    {
        [Tooltip("D-17's root. Its world x is the prototype's lane x (Vec3.ToUnity keeps x).")]
        [SerializeField] private Transform listener;
        [Tooltip("The camera the pan is measured in (empty = Camera.main).")]
        [SerializeField] private UnityEngine.Camera panCamera;
        [Tooltip("Pan at the left/right frame edges (decision on #20: 0.4). One value for the whole game.")]
        [Range(0f, 1f)]
        [SerializeField] private float edgePan = (float)PanLaw.DefaultEdgePan;

        [Tooltip("game.region: 1 DL-01, 2 DL-02–05, 3 DL-06–07, 4 DL-08–10, 5 DL-11, 6 chapter one.")]
        public int region = 1;
        [Tooltip("game.upper: on the upper deck.")]
        public bool upper;

        private readonly HashSet<string> _conditions = new HashSet<string>();

        /// <summary>The scene's AudioWorld (the last one enabled).</summary>
        public static AudioWorld Current { get; private set; }

        public float EdgePan
        {
            get => edgePan;
            set => edgePan = Mathf.Clamp01(value);
        }

        /// <summary>D-17's lane x.</summary>
        public double ListenerX => listener != null ? listener.position.x : 0.0;

        public void SetCondition(string name, bool on)
        {
            if (string.IsNullOrEmpty(name)) return;
            if (on) _conditions.Add(name); else _conditions.Remove(name);
        }

        /// <summary>True for a null/empty condition (none), else whether it is set.</summary>
        public bool Condition(string name) => string.IsNullOrEmpty(name) || _conditions.Contains(name);

        /// <summary>The stereo pan for a sound at <paramref name="worldPosition"/> (0 behind the camera or with no camera).</summary>
        public float PanFor(Vector3 worldPosition)
        {
            UnityEngine.Camera cam = panCamera != null ? panCamera : UnityEngine.Camera.main;
            if (cam == null) return 0f;
            Vector3 vp = cam.WorldToViewportPoint(worldPosition);
            if (vp.z <= 0f) return 0f;
            return (float)PanLaw.FromViewportX(vp.x, edgePan);
        }

        /// <summary>The pan for a lane x at the listener's height (sounds placed only by x, as the prototype's are).</summary>
        public float PanForX(double x)
        {
            Vector3 p = listener != null ? listener.position : Vector3.zero;
            p.x = (float)x;
            return PanFor(p);
        }

        private void OnEnable() => Current = this;

        private void OnDisable()
        {
            if (Current == this) Current = null;
        }
    }
}
