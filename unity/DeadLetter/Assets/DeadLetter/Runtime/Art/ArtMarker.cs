using System;
using System.Collections.Generic;
using UnityEngine;

namespace DeadLetter.Runtime.Art
{
    /// <summary>
    /// What the Blender export said about one convention-named node (<c>COL_</c>, <c>LGT_</c>, <c>MECH_</c>, <c>CAM_</c>,
    /// <c>CHK_</c>; docs/unity/asset_conventions.md). Added by the Editor's region prefab builder from the region's
    /// <c>.art.json</c> sidecar so the scene builder (U-20) can read markers from the prefab without parsing JSON.
    /// Data only: no behaviour, no per-frame cost.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class ArtMarker : MonoBehaviour
    {
        [Serializable]
        public struct Prop
        {
            public string key;
            public string value;
        }

        [Tooltip("COL, LGT, MECH, CAM or CHK.")]
        public string prefix;
        [Tooltip("MECH: mechanism type (Shutter). LGT: light zone.")]
        public string type;
        [Tooltip("MECH: mechanism ID (dl01.shutter). CHK/COL/LGT: the name after the prefix. CAM: the zone.")]
        public string id;
        [Tooltip("MECH: the part (its source object's name), empty for the mechanism's root or anchor.")]
        public string part;
        [Tooltip("The object's name in the Blender generators / the web build, if the export renamed it.")]
        public string sourceName;
        public List<Prop> props = new List<Prop>();

        public bool TryGet(string key, out string value)
        {
            for (int i = 0; i < props.Count; i++)
                if (props[i].key == key) { value = props[i].value; return true; }
            value = null;
            return false;
        }
    }
}
