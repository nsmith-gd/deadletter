using System;
using DeadLetter.Core.Save;
using UnityEngine;

namespace DeadLetter.Runtime.Save
{
    /// <summary>
    /// A checkpoint volume (§5's checkpoint column; the importer's <c>CHK_</c> objects): when D-17 enters it, tells
    /// Core's <see cref="CheckpointService"/> that <see cref="checkpoint"/> was reached. The service decides everything
    /// (only a later checkpoint counts, what is saved, when it is written). Checkpoints set by a state rather than a
    /// place (the shutter's release, the crank's last stroke) call <see cref="CheckpointService.Reach"/> from Core.
    /// <see cref="Service"/> is set by whoever builds the scene's simulation.
    /// </summary>
    [RequireComponent(typeof(Collider))]
    public sealed class CheckpointTrigger : MonoBehaviour
    {
        private static CheckpointService _service;

        /// <summary>The running game's service (one per loaded scene graph).</summary>
        public static CheckpointService Service
        {
            get => _service;
            set
            {
                if (_service == value) return;
                _service = value;
                ServiceChanged?.Invoke(value);
            }
        }

        /// <summary>
        /// The service was set or replaced (a scene's simulation was built). Listeners outside the graph that must reset
        /// with the world (<c>DirectedMomentPlayer</c>) rebind their <see cref="CheckpointService.Reloaded"/> here, so the
        /// order in which the scene's objects are enabled does not matter.
        /// </summary>
        public static event Action<CheckpointService> ServiceChanged;

        [Tooltip("A name in the checkpoint order (Checkpoint.GameOrder), e.g. \"hall\" or \"terrace\".")]
        [SerializeField] private string checkpoint;

        public string Checkpoint => checkpoint;

        private void Reset() => GetComponent<Collider>().isTrigger = true;

        private void OnTriggerEnter(Collider other)
        {
            if (Service == null || string.IsNullOrEmpty(checkpoint)) return;
            if (other.GetComponentInParent<D17Controller>() == null) return;
            Service.Reach(checkpoint);
        }
    }
}
