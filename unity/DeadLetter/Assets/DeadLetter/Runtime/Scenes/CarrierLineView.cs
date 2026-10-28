using DeadLetter.Core.Presentation;
using UnityEngine;

namespace DeadLetter.Runtime.Scenes
{
    /// <summary>
    /// DL-06's carriers (port_architecture §4.13h; <c>spawnCarrier</c>, L2660–L2681): one pooled instance of
    /// <see cref="carrierPrefab"/> per Core view slot (<see cref="CarrierViews"/>, sized to the line's capacity), placed
    /// each frame from Core's poses between the last two steps. A slot keeps its carrier from the hatch to the return lift;
    /// an empty slot's instance is hidden. Lives in the DL-06 view scene; <see cref="GameHost"/> binds it when the scene
    /// loads (<see cref="Bind"/>) and drives it from LateUpdate.
    /// <para>The prefab: its root is the carrier's rail point (lane x, y; z = the rail's), turned by the rail's angle about
    /// lane z; a child named <see cref="pivotName"/> tips the tub; children named <see cref="parcelPrefix"/>0..2 are its
    /// parcels (shown by count) and <see cref="loadPrefix"/>0..1 the weights a tub carries in DL-07.</para>
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class CarrierLineView : MonoBehaviour
    {
        [Tooltip("One carrier (MECH_CarrierLine's tub): root at the rail point, a tip pivot, parcels.")]
        [SerializeField] private GameObject carrierPrefab;
        [Tooltip("The rail's Unity z (CarrierLineParams.RailZ: RAIL_Z −0.55 negated).")]
        [SerializeField] private float railZ = 0.55f;
        [SerializeField] private string pivotName = "Pivot";
        [SerializeField] private string parcelPrefix = "Parcel";
        [SerializeField] private string loadPrefix = "Load";

        private const int Parcels = 3, Loads = 2;

        private CarrierViews _views;
        private GameObject[] _roots;
        private Transform[] _pivots;
        private GameObject[,] _parcels, _loads;

        /// <summary>The scene's view (the last enabled), for GameHost to bind.</summary>
        public static CarrierLineView Current { get; private set; }

        public bool Bound => _views != null;

        /// <summary>Builds the pool for <paramref name="views"/> (null: hide everything).</summary>
        public void Bind(CarrierViews views)
        {
            _views = views;
            if (views == null || carrierPrefab == null) { Hide(); return; }
            if (_roots != null && _roots.Length == views.Capacity) return;
            Clear();
            int n = views.Capacity;
            _roots = new GameObject[n];
            _pivots = new Transform[n];
            _parcels = new GameObject[n, Parcels];
            _loads = new GameObject[n, Loads];
            for (int s = 0; s < n; s++)
            {
                GameObject go = Instantiate(carrierPrefab, transform);
                go.name = "Carrier " + s;
                go.SetActive(false);
                _roots[s] = go;
                Transform pivot = go.transform.Find(pivotName);
                _pivots[s] = pivot != null ? pivot : go.transform;
                for (int k = 0; k < Parcels; k++) _parcels[s, k] = FindChild(go.transform, parcelPrefix + k);
                for (int k = 0; k < Loads; k++) _loads[s, k] = FindChild(go.transform, loadPrefix + k);
            }
        }

        /// <summary>Places every slot's instance at Core's pose, <paramref name="alpha"/> of the way from the step before.</summary>
        public void Apply(float alpha)
        {
            if (_views == null || _roots == null) return;
            for (int s = 0; s < _roots.Length; s++)
            {
                GameObject go = _roots[s];
                bool on = _views.Active(s);
                if (go.activeSelf != on) go.SetActive(on);
                if (!on) continue;
                CarrierPose p = _views.Pose(s, alpha);
                go.transform.localPosition = new Vector3((float)p.X, (float)p.Y, railZ);
                go.transform.localRotation = Quaternion.AngleAxis((float)(p.Angle * Mathf.Rad2Deg), Vector3.forward);   // three.js rotation.z (§0.2)
                if (_pivots[s] != go.transform)
                    _pivots[s].localRotation = Quaternion.AngleAxis((float)(p.Tip * Mathf.Rad2Deg), Vector3.forward);
                int parcels = _views.Parcels(s);
                for (int k = 0; k < Parcels; k++) SetActive(_parcels[s, k], k < parcels);
                SetActive(_loads[s, 0], _views.Load1(s) != 0);
                SetActive(_loads[s, 1], _views.Load2(s) != 0);
            }
        }

        private static void SetActive(GameObject go, bool on)
        {
            if (go != null && go.activeSelf != on) go.SetActive(on);
        }

        private static GameObject FindChild(Transform root, string name)
        {
            Transform t = root.Find(name);
            return t != null ? t.gameObject : null;
        }

        private void Hide()
        {
            if (_roots == null) return;
            for (int s = 0; s < _roots.Length; s++) if (_roots[s] != null) _roots[s].SetActive(false);
        }

        private void Clear()
        {
            if (_roots == null) return;
            for (int s = 0; s < _roots.Length; s++) if (_roots[s] != null) Destroy(_roots[s]);
            _roots = null;
        }

        private void OnEnable()
        {
            Current = this;
            if (GameHost.Instance != null) GameHost.Instance.OnCarrierViewLoaded(this);
        }

        private void OnDisable()
        {
            if (Current == this) Current = null;
        }
    }
}
