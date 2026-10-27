using System;
using System.Collections.Generic;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Scenes;

namespace DeadLetter.Core.Art
{
    /// <summary>A marker from a region's U-12 sidecar (<c>Assets/Art/DL-xx/DL-xx.art.json</c>, <c>markers[]</c>).</summary>
    public sealed class ArtMarker
    {
        /// <summary>The node name, e.g. <c>MECH_TippingBridge_dl01_cart</c> or <c>CHK_hall</c>.</summary>
        public string Name = "";
        /// <summary><c>MECH</c>, <c>CHK</c> (later <c>COL</c>, <c>LGT</c>, <c>CAM</c>).</summary>
        public string Prefix = "";
        /// <summary>Unity axes (port_architecture §0.2): x along the lane, y up.</summary>
        public double X, Y, Z;
        public readonly Dictionary<string, string> Props = new Dictionary<string, string>(StringComparer.Ordinal);

        public string Prop(string key) => Props.TryGetValue(key, out var v) ? v : null;
        /// <summary>A part of a mechanism's view (<c>MECH_…__Part</c>): the scene builder's concern, not the definition's.</summary>
        public bool IsPart => Name.IndexOf("__", StringComparison.Ordinal) >= 0;
    }

    /// <summary>
    /// Cross-checks a scene definition against its art (U-18/U-20, agreed on #16): the U-12 sidecar is the single source
    /// for where things are in the art, the <see cref="SceneDef"/> keeps its code factories, and this proves the two
    /// agree, so a position or a mechanism can't drift between Blender and Core unnoticed. JSON parsing stays outside
    /// Core (tests: System.Text.Json; Editor: <c>ArtSidecar</c>); callers hand in <see cref="ArtMarker"/>s.
    /// <para>Rules: mechanism ids unique and the graph builds (links resolve); every def mechanism has a root
    /// <c>MECH_</c> marker unless listed logic-only; every marker's <c>mech</c> id is in the def unless listed not yet
    /// ported; the marker's <c>type</c> is the class the factory builds, a base, or a contract it implements (<c>Carryable</c> → <c>ICarryable</c>), or an accepted alias; every part has its root;
    /// <c>CHK_</c> markers and the chapter table's rows for this scene have the same names, x and height to 1e-6,
    /// region, and the sidecar's <c>order</c> is the checkpoint's place in the save's order (<see cref="CheckpointTable.Order"/>).</para>
    /// </summary>
    public static class SceneArtCheck
    {
        public const double PositionTolerance = 1e-6;

        /// <param name="logicOnly">Def mechanisms with no art (e.g. a letter that is a prop of another view).</param>
        /// <param name="notPorted">Marker ids the def does not have yet (e.g. a curiosity's scale).</param>
        /// <param name="typeAliases">Marker type → Core class name, where U-12's name map and Core differ.</param>
        /// <param name="checkpoints">The chapter's checkpoint table: the rows this scene owns (<see cref="CheckpointDef.Scene"/>) are checked against its <c>CHK_</c> markers.</param>
        /// <param name="sharedWith">Scenes that share this sidecar (DL-06 and DL-07: <c>Art/DL-06_07</c>): their <c>CHK_</c> markers are theirs to check, not this scene's.</param>
        /// <returns>Problems, one line each; empty when the definition and the art agree.</returns>
        public static List<string> Check(SceneDef def, CheckpointTable checkpoints, IEnumerable<ArtMarker> markers, IEnumerable<string> logicOnly = null,
            IEnumerable<string> notPorted = null, IDictionary<string, string> typeAliases = null, IEnumerable<string> sharedWith = null)
        {
            if (def == null) throw new ArgumentNullException(nameof(def));
            if (markers == null) throw new ArgumentNullException(nameof(markers));
            var problems = new List<string>();
            var logic = new HashSet<string>(logicOnly ?? Array.Empty<string>(), StringComparer.Ordinal);
            var later = new HashSet<string>(notPorted ?? Array.Empty<string>(), StringComparer.Ordinal);
            if (checkpoints == null) throw new ArgumentNullException(nameof(checkpoints));
            var shared = new HashSet<string>(sharedWith ?? Array.Empty<string>(), StringComparer.Ordinal);

            // ---- the definition on its own ----------------------------------------------------------------------------
            var built = new Dictionary<string, Type>(StringComparer.Ordinal);         // id → class
            var graph = new MechanismGraph();
            foreach (var md in def.Mechanisms)
            {
                string id = md.Id.ToString();
                if (built.ContainsKey(id)) { problems.Add(def.Id + ": mechanism id " + id + " is used twice"); continue; }
                IMechanism m;
                try { m = md.Create(); }
                catch (Exception e) { problems.Add(def.Id + ": " + id + "'s factory threw " + e.GetType().Name + ": " + e.Message); continue; }
                if (m == null) { problems.Add(def.Id + ": " + id + "'s factory returned null"); continue; }
                if (!m.Id.Equals(md.Id)) problems.Add(def.Id + ": " + id + "'s factory built " + m.Id);
                built[id] = m.GetType();
                graph.Add(m);
            }
            try { graph.Build(); }
            catch (Exception e) { problems.Add(def.Id + ": the graph does not build (a link does not resolve?): " + e.Message); }

            // ---- mechanisms against MECH_ markers ---------------------------------------------------------------------
            var roots = new Dictionary<string, ArtMarker>(StringComparer.Ordinal);
            var parts = new List<ArtMarker>();
            var chkMarkers = new List<ArtMarker>();
            foreach (var mk in markers)
            {
                if (mk.Prefix == "CHK") { chkMarkers.Add(mk); continue; }
                if (mk.Prefix != "MECH") continue;
                string id = mk.Prop("mech");
                if (string.IsNullOrEmpty(id)) { problems.Add(def.Id + ": marker " + mk.Name + " has no 'mech' property"); continue; }
                if (mk.IsPart) { parts.Add(mk); continue; }
                if (roots.ContainsKey(id)) { problems.Add(def.Id + ": two root markers for " + id + " (" + roots[id].Name + ", " + mk.Name + ")"); continue; }
                roots[id] = mk;
            }
            foreach (var kv in built)
            {
                if (roots.TryGetValue(kv.Key, out var mk))
                {
                    if (logic.Contains(kv.Key)) problems.Add(def.Id + ": " + kv.Key + " is listed logic-only but has art (" + mk.Name + ")");
                    string type = mk.Prop("type") ?? "";
                    string want = typeAliases != null && typeAliases.TryGetValue(type, out var alias) ? alias : type;
                    if (!IsA(kv.Value, want)) problems.Add(def.Id + ": " + kv.Key + " is a " + kv.Value.Name + " in Core but a " + type + " in the art (" + mk.Name + ")");
                }
                else if (!logic.Contains(kv.Key)) problems.Add(def.Id + ": " + kv.Key + " has no MECH_ marker in the art (or list it logic-only)");
            }
            foreach (var kv in roots)
            {
                if (built.ContainsKey(kv.Key)) { if (later.Contains(kv.Key)) problems.Add(def.Id + ": " + kv.Key + " is listed not-yet-ported but the def has it"); }
                else if (!later.Contains(kv.Key)) problems.Add(def.Id + ": the art's " + kv.Value.Name + " (" + kv.Key + ") is not in the def (or list it not-yet-ported)");
            }
            foreach (var p in parts)
                if (!roots.ContainsKey(p.Prop("mech"))) problems.Add(def.Id + ": part " + p.Name + " has no root marker for " + p.Prop("mech"));

            // ---- checkpoints against CHK_ markers ---------------------------------------------------------------------
            var seen = new HashSet<string>(StringComparer.Ordinal);
            foreach (var mk in chkMarkers)
            {
                string name = mk.Name.StartsWith("CHK_", StringComparison.Ordinal) ? mk.Name.Substring(4) : mk.Name;
                seen.Add(name);
                if (checkpoints.TryGet(name, out var other) && other.Scene != def.Id && shared.Contains(other.Scene)) continue;   // a sharing scene's
                if (!checkpoints.TryGet(name, out var cp) || cp.Scene != def.Id) { problems.Add(def.Id + ": the art's " + mk.Name + " is not one of this scene's checkpoints in the chapter table"); continue; }
                if (Math.Abs(cp.X - mk.X) > PositionTolerance)
                    problems.Add(def.Id + ": checkpoint " + name + " is at x " + cp.X.ToString("R", System.Globalization.CultureInfo.InvariantCulture)
                        + " in Core but " + mk.X.ToString("R", System.Globalization.CultureInfo.InvariantCulture) + " in the art");
                if (double.TryParse(mk.Prop("height"), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double h)
                    && Math.Abs(cp.Y - h) > PositionTolerance)
                    problems.Add(def.Id + ": checkpoint " + name + " is at height " + cp.Y + " in Core but " + h + " in the art");
                if (int.TryParse(mk.Prop("game_region"), out int region))
                {
                    int coreRegion = cp.Region != 0 ? cp.Region : def.Region;
                    if (coreRegion != region) problems.Add(def.Id + ": checkpoint " + name + " is in region " + coreRegion + " in Core but " + region + " in the art");
                }
                if (int.TryParse(mk.Prop("order"), out int order))
                {
                    int idx = IndexOf(checkpoints.Order, name);
                    if (idx != order - 1) problems.Add(def.Id + ": checkpoint " + name + " is #" + (idx + 1) + " in the save's order but order " + order + " in the art");
                }
            }
            foreach (var cp in checkpoints.Of(def.Id))
                if (!seen.Contains(cp.Name)) problems.Add(def.Id + ": checkpoint " + cp.Name + " has no CHK_ marker in the art");
            return problems;
        }

        /// <summary>
        /// The class or one of its bases is called <paramref name="name"/>, or it implements the contract
        /// <c>I&lt;name&gt;</c>: U-12 names some markers by role (<c>Carryable</c>), which Core's contracts carry
        /// (<c>ICarryable</c>: <c>CarriedItem</c>, DL-03's own <c>Dl03Weight</c>).
        /// </summary>
        private static bool IsA(Type t, string name)
        {
            foreach (var i in t.GetInterfaces())
                if (i.Name == "I" + name) return true;
            for (; t != null && t != typeof(object); t = t.BaseType)
                if (t.Name == name) return true;
            return false;
        }

        private static int IndexOf(IReadOnlyList<string> list, string name)
        {
            for (int i = 0; i < list.Count; i++) if (string.Equals(list[i], name, StringComparison.Ordinal)) return i;
            return -1;
        }
    }
}
