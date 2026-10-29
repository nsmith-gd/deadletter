using System;
using System.Collections.Generic;
using DeadLetter.Core.Platform;
using DeadLetter.Core.Scenes;

namespace DeadLetter.Core.Streaming
{
    /// <summary>
    /// How near a seam he must be before the scene past it streams in (port_architecture §7; metres of lane x, measured by
    /// <see cref="ChapterSim.DistanceToSeam"/>). Larger on Switch: its storage is slower and its CPU decodes meshes for longer,
    /// so a scene must start loading earlier to be resident before he reaches the seam at run speed (1.6 m/s).
    /// </summary>
    public static class StreamingRadii
    {
        /// <summary>PC (Steam, Itch, the editor): ~5.6 s at run speed, ample for an SSD load and a time-sliced activation.</summary>
        public const double Desktop = 9.0;
        /// <summary>Switch: ~8.8 s at run speed (game-card reads, single-threaded activation on the main core).</summary>
        public const double Switch = 14.0;

        public static double For(PlatformKind kind) => kind == PlatformKind.Switch ? Switch : Desktop;
    }

    /// <summary>
    /// Which scene views of a chapter should be resident (port_architecture §7: one Unity scene per <see cref="SceneDef"/>,
    /// loaded additively, never owning sim state). Pure: it reads where he is (<see cref="ChapterSim.Current"/> and
    /// <see cref="ChapterSim.DistanceToSeam"/>) and what is resident, and says what to load and unload.
    /// <list type="bullet">
    /// <item>Scenes are grouped into <b>slots</b>: one stretch of lane. Scenes that share a stretch (DL-07 on DL-06's floor,
    /// <see cref="ChapterDef"/>) are one slot and always stream together.</item>
    /// <item><b>Load:</b> his slot always; the next slot on a side once he is within <see cref="Radius"/> of that seam.</item>
    /// <item><b>Unload:</b> only a slot two or more away from his (he is a full scene away from it), so turning back at a
    /// seam never unloads what he just left (hysteresis).</item>
    /// <item><b>Placement</b> (continue, respawn, begin): the checkpoint's slot and both neighbours, loaded before he is put
    /// there (behind a fade).</item>
    /// <item><b>Across a seam</b> (#51): built over the chapters a seam joins (<see cref="ChapterSeams.Span"/>), their scenes
    /// in play order, the next chapter's first slot is the neighbour of this one's last: within <see cref="Radius"/> of DL-17's
    /// end DL-18 streams in, and after the handover DL-17 stays until he is two slots on.</item>
    /// </list>
    /// Allocation-free per call when the caller reuses its lists.
    /// </summary>
    public sealed class StreamingPlanner
    {
        private readonly SceneDef[] _scenes;
        private readonly int[] _slot;
        private readonly string[] _chapter;

        public StreamingPlanner(IReadOnlyList<SceneDef> scenes, double radius)
        {
            if (scenes == null || scenes.Count == 0) throw new ArgumentException("No scenes to stream.", nameof(scenes));
            _scenes = new SceneDef[scenes.Count];
            _slot = new int[scenes.Count];
            int slot = -1;
            for (int i = 0; i < scenes.Count; i++)
            {
                var s = scenes[i] ?? throw new ArgumentException("Scene " + i + " is null.", nameof(scenes));
                _scenes[i] = s;
                bool shares = i > 0 && SameStretch(_scenes[i - 1], s);
                if (!shares) slot++;
                _slot[i] = slot;
            }
            SlotCount = slot + 1;
            Radius = radius;
        }

        public StreamingPlanner(ChapterDef chapter, double radius) : this(new[] { chapter ?? throw new ArgumentNullException(nameof(chapter)) }, radius) { }

        /// <summary>
        /// Every scene of <paramref name="chapters"/> (in play order: a seam's span, <see cref="ChapterSeams.Span"/>), streamed as
        /// one lane. Scene IDs must be unique across them (<see cref="IndexOf(string)"/> finds a scene of either sim by its ID).
        /// </summary>
        public StreamingPlanner(IReadOnlyList<ChapterDef> chapters, double radius) : this(ScenesOf(chapters), radius)
        {
            _chapter = new string[_scenes.Length];
            for (int c = 0, i = 0; c < chapters.Count; c++)
                for (int k = 0; k < chapters[c].Scenes.Count; k++) _chapter[i++] = chapters[c].Id;
            for (int i = 0; i < _scenes.Length; i++)
                for (int j = 0; j < i; j++)
                    if (string.Equals(_scenes[i].Id, _scenes[j].Id, StringComparison.Ordinal))
                        throw new ArgumentException("Scene " + _scenes[i].Id + " is in " + _chapter[j] + " and " + _chapter[i] + ".", nameof(chapters));
        }

        private static List<SceneDef> ScenesOf(IReadOnlyList<ChapterDef> chapters)
        {
            if (chapters == null || chapters.Count == 0) throw new ArgumentException("No chapters to stream.", nameof(chapters));
            var all = new List<SceneDef>();
            foreach (var c in chapters) all.AddRange((c ?? throw new ArgumentException("A chapter is null.", nameof(chapters))).Scenes);
            return all;
        }

        /// <summary>Metres from a seam at which the scene past it is loaded (<see cref="StreamingRadii"/>).</summary>
        public double Radius { get; set; }
        public int Count => _scenes.Length;
        public int SlotCount { get; }
        public SceneDef this[int i] => _scenes[i];

        /// <summary>The chapter of scene <paramref name="i"/> (its view's folder, <see cref="ChapterScenes.ScenePath"/>); null when built from scenes alone.</summary>
        public string ChapterOf(int i) => _chapter?[i];

        /// <summary>The slot (stretch of lane) of scene <paramref name="i"/>.</summary>
        public int SlotOf(int i) => _slot[i];

        /// <summary>The index of <paramref name="scene"/> (by reference, then by ID), or −1.</summary>
        public int IndexOf(SceneDef scene)
        {
            if (scene == null) return -1;
            for (int i = 0; i < _scenes.Length; i++) if (ReferenceEquals(_scenes[i], scene)) return i;
            return IndexOf(scene.Id);
        }

        public int IndexOf(string sceneId)
        {
            if (sceneId == null) return -1;
            for (int i = 0; i < _scenes.Length; i++) if (string.Equals(_scenes[i].Id, sceneId, StringComparison.Ordinal)) return i;
            return -1;
        }

        /// <summary>Scenes with the same region and exactly the same stretch (<see cref="ChapterDef"/>'s "shares").</summary>
        public static bool SameStretch(SceneDef a, SceneDef b) => a.Region == b.Region && a.X0 == b.X0 && a.X1 == b.X1;

        /// <summary>
        /// The scenes to load and unload now. <paramref name="current"/> is the index of the scene that holds him (−1: not
        /// placed, or past the chapter: nothing changes); <paramref name="toLeftSeam"/>/<paramref name="toRightSeam"/> are
        /// <see cref="ChapterSim.DistanceToSeam"/> each way; <paramref name="resident"/>[i] is true while scene i is loaded or
        /// loading. <paramref name="load"/> and <paramref name="unload"/> are cleared and filled with indices in lane order.
        /// </summary>
        public void Plan(int current, double toLeftSeam, double toRightSeam, IReadOnlyList<bool> resident, List<int> load, List<int> unload)
        {
            if (resident == null) throw new ArgumentNullException(nameof(resident));
            if (resident.Count != _scenes.Length) throw new ArgumentException("One flag per scene.", nameof(resident));
            load.Clear();
            unload.Clear();
            if (current < 0 || current >= _scenes.Length) return;
            int here = _slot[current];
            bool wantLeft = toLeftSeam < Radius, wantRight = toRightSeam < Radius;
            for (int i = 0; i < _scenes.Length; i++)
            {
                int d = _slot[i] - here;
                bool want = d == 0 || (d == -1 && wantLeft) || (d == 1 && wantRight);
                bool keep = d >= -1 && d <= 1;
                if (want && !resident[i]) load.Add(i);
                else if (!keep && resident[i]) unload.Add(i);
            }
        }

        /// <summary>
        /// Placing him in scene <paramref name="scene"/> (a continue, respawn or begin there): every scene of its slot and of
        /// both neighbouring slots, in lane order (<paramref name="required"/> is cleared first). The caller loads them all
        /// before the sim places him, behind a fade (§7, "Checkpoint load / respawn").
        /// </summary>
        public void Placement(int scene, List<int> required)
        {
            required.Clear();
            if (scene < 0 || scene >= _scenes.Length) return;
            int here = _slot[scene];
            for (int i = 0; i < _scenes.Length; i++) if (Math.Abs(_slot[i] - here) <= 1) required.Add(i);
        }

        /// <summary>Scene <paramref name="i"/> must be resident for him to be in scene <paramref name="scene"/> (its own slot).</summary>
        public bool SameSlot(int i, int scene) => i >= 0 && scene >= 0 && _slot[i] == _slot[scene];
    }
}
