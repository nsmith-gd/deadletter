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
        /// <summary>The running game's service (one per loaded scene graph).</summary>
        public static CheckpointService Service { get; set; }

        [Tooltip("A name in the checkpoint order (Checkpoint.PrototypeOrder), e.g. \"hall\".")]
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
