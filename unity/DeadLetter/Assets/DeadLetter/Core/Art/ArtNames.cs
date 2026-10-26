using System;
using System.Text;

namespace DeadLetter.Core.Art
{
    /// <summary>What a node's name prefix says it is (docs/unity/asset_conventions.md).</summary>
    public enum ArtPrefix
    {
        /// <summary>Ordinary set dressing: rendered, no marker data.</summary>
        None,
        /// <summary><c>COL_&lt;name&gt;</c>: a collision box. Not rendered.</summary>
        Collider,
        /// <summary><c>LGT_&lt;zone&gt;_&lt;name&gt;</c>: a light marker (an empty; the light pool makes the real light).</summary>
        Light,
        /// <summary><c>MECH_&lt;Type&gt;_&lt;scene&gt;_&lt;name&gt;[__&lt;part&gt;]</c>: a mechanism anchor or one of its parts.</summary>
        Mechanism,
        /// <summary><c>CAM_&lt;zone&gt;</c>: a camera framing volume marker.</summary>
        Camera,
        /// <summary><c>CHK_&lt;name&gt;</c>: a checkpoint (D-17's respawn point on the lane).</summary>
        Checkpoint,
    }

    /// <summary>A parsed node name. <see cref="Id"/> and <see cref="Type"/> depend on the prefix (see <see cref="ArtNames"/>).</summary>
    public struct ArtName
    {
        public ArtPrefix Prefix;
        /// <summary>The name as found, minus any duplicate suffix (<c>.001</c>, <c> (1)</c>).</summary>
        public string Name;
        /// <summary>MECH: the mechanism type (<c>Shutter</c>). LGT: the light zone (<c>r1</c>). Otherwise null.</summary>
        public string Type;
        /// <summary>MECH: the mechanism ID (<c>dl01.shutter</c>). LGT/COL/CHK: the name after the prefix. CAM: the zone.</summary>
        public string Id;
        /// <summary>MECH: the part after <c>__</c> (<c>ShutterRail</c>), or null for the mechanism's root.</summary>
        public string Part;

        public bool IsMarker => Prefix != ArtPrefix.None;
        /// <summary>The mechanism's root object (a MECH name with no part).</summary>
        public bool IsMechanismRoot => Prefix == ArtPrefix.Mechanism && Part == null;
    }

    /// <summary>
    /// The naming conventions the Blender export writes and the Unity scene builder reads (U-12, port_architecture §6.1):
    /// <list type="bullet">
    /// <item><c>COL_&lt;name&gt;</c> collider boxes, <c>CHK_&lt;name&gt;</c> checkpoints, <c>CAM_&lt;zone&gt;</c> framing volumes.</item>
    /// <item><c>LGT_&lt;zone&gt;_&lt;name&gt;</c> light markers.</item>
    /// <item><c>MECH_&lt;Type&gt;_&lt;scene&gt;_&lt;name&gt;[__&lt;part&gt;]</c>: <c>Type</c> is PascalCase with no underscore, the
    /// mechanism ID is <c>&lt;scene&gt;.&lt;name&gt;</c> (the §5 IDs, e.g. <c>dl01.shutter</c>; Blender/glTF names avoid the dot
    /// because three.js strips it). A part keeps its source object's name, e.g.
    /// <c>MECH_Door_dl01_shutter__ShutterRail</c>.</item>
    /// </list>
    /// Prefixes are case-sensitive. Pure string code: no UnityEngine.
    /// </summary>
    public static class ArtNames
    {
        public const string ColliderPrefix = "COL_";
        public const string LightPrefix = "LGT_";
        public const string MechanismPrefix = "MECH_";
        public const string CameraPrefix = "CAM_";
        public const string CheckpointPrefix = "CHK_";
        public const string PartSeparator = "__";

        public static string PrefixOf(ArtPrefix p)
        {
            switch (p)
            {
                case ArtPrefix.Collider: return ColliderPrefix;
                case ArtPrefix.Light: return LightPrefix;
                case ArtPrefix.Mechanism: return MechanismPrefix;
                case ArtPrefix.Camera: return CameraPrefix;
                case ArtPrefix.Checkpoint: return CheckpointPrefix;
                default: return "";
            }
        }

        /// <summary>
        /// Removes a duplicate suffix: Blender's <c>.001</c> (a dot and exactly three digits) and Unity's <c> (1)</c>.
        /// </summary>
        public static string StripDuplicateSuffix(string name)
        {
            if (string.IsNullOrEmpty(name)) return name;
            string n = name;
            if (n.EndsWith(")", StringComparison.Ordinal))
            {
                int open = n.LastIndexOf(" (", StringComparison.Ordinal);
                if (open > 0 && AllDigits(n, open + 2, n.Length - 1)) n = n.Substring(0, open);
            }
            if (n.Length > 4 && n[n.Length - 4] == '.' && AllDigits(n, n.Length - 3, n.Length)) n = n.Substring(0, n.Length - 4);
            return n;
        }

        /// <summary>Parses a node name. Never throws; a name with no known prefix (or a malformed one) is <see cref="ArtPrefix.None"/>.</summary>
        public static ArtName Parse(string name)
        {
            var r = new ArtName { Prefix = ArtPrefix.None, Name = StripDuplicateSuffix(name ?? "") };
            string n = r.Name;
            if (Starts(n, MechanismPrefix)) return ParseMechanism(n, r);
            if (Starts(n, LightPrefix))
            {
                string body = n.Substring(LightPrefix.Length);
                int us = body.IndexOf('_');
                if (us <= 0 || us == body.Length - 1) return r;
                r.Prefix = ArtPrefix.Light;
                r.Type = body.Substring(0, us);
                r.Id = body.Substring(us + 1);
                return r;
            }
            if (Starts(n, ColliderPrefix)) return Simple(r, ArtPrefix.Collider, ColliderPrefix);
            if (Starts(n, CameraPrefix)) return Simple(r, ArtPrefix.Camera, CameraPrefix);
            if (Starts(n, CheckpointPrefix)) return Simple(r, ArtPrefix.Checkpoint, CheckpointPrefix);
            return r;
        }

        /// <summary>True for a well-formed convention name (any prefix but <see cref="ArtPrefix.None"/>).</summary>
        public static bool IsMarker(string name) => Parse(name).IsMarker;

        /// <summary>
        /// <c>MECH_Door_dl01_shutter</c> from ("Door", "dl01.shutter"), with <c>__part</c> when a part is given.
        /// The ID must be <c>scene.name</c> with neither half empty, no underscore in the scene, and no second dot.
        /// </summary>
        public static string Mechanism(string type, string id, string part = null)
        {
            if (string.IsNullOrEmpty(type) || type.IndexOf('_') >= 0) throw new ArgumentException("type must be non-empty with no '_'", nameof(type));
            int dot = id == null ? -1 : id.IndexOf('.');
            if (dot <= 0 || dot == id.Length - 1 || id.IndexOf('.', dot + 1) >= 0 || id.Substring(0, dot).IndexOf('_') >= 0)
                throw new ArgumentException("id must be 'scene.name'", nameof(id));
            var sb = new StringBuilder(MechanismPrefix).Append(type).Append('_').Append(id.Substring(0, dot)).Append('_').Append(id.Substring(dot + 1));
            if (!string.IsNullOrEmpty(part)) sb.Append(PartSeparator).Append(part);
            return sb.ToString();
        }

        /// <summary>
        /// The name three.js sees: it removes every <c>.</c> from node names (port_architecture §9 #13: <c>CourierSlot.A.0</c>
        /// is looked up as <c>CourierSlotA0</c>). glTFast keeps raw names, so code ported from index.html compares through this.
        /// </summary>
        public static string WebName(string name) => name == null ? null : name.Replace(".", "");

        // ---- helpers ------------------------------------------------------------------------------------------------

        private static ArtName ParseMechanism(string n, ArtName r)
        {
            string body = n.Substring(MechanismPrefix.Length);
            string part = null;
            int sep = body.IndexOf(PartSeparator, StringComparison.Ordinal);
            if (sep >= 0)
            {
                part = body.Substring(sep + PartSeparator.Length);
                body = body.Substring(0, sep);
                if (part.Length == 0) return r;
            }
            int a = body.IndexOf('_');
            if (a <= 0) return r;
            int b = body.IndexOf('_', a + 1);
            if (b <= a + 1 || b == body.Length - 1) return r;
            r.Prefix = ArtPrefix.Mechanism;
            r.Type = body.Substring(0, a);
            r.Id = body.Substring(a + 1, b - a - 1) + "." + body.Substring(b + 1);
            r.Part = part;
            return r;
        }

        private static ArtName Simple(ArtName r, ArtPrefix p, string prefix)
        {
            if (r.Name.Length == prefix.Length) return r;
            r.Prefix = p;
            r.Id = r.Name.Substring(prefix.Length);
            return r;
        }

        private static bool Starts(string s, string prefix) => s.StartsWith(prefix, StringComparison.Ordinal);

        private static bool AllDigits(string s, int from, int to)
        {
            if (to <= from) return false;
            for (int i = from; i < to; i++) if (s[i] < '0' || s[i] > '9') return false;
            return true;
        }
    }
}
