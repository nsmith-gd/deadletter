using System;
using System.Collections.Generic;

namespace DeadLetter.Core.Scenes
{
    /// <summary>
    /// Where a checkpoint puts D-17 (<c>CHECKPOINTS</c>, L7975–L8014): lane x, feet y, facing, the lane region, and the
    /// scene that owns it. A chapter's are in one <see cref="CheckpointTable"/>.
    /// </summary>
    public readonly struct CheckpointDef
    {
        public readonly string Name;
        public readonly double X, Y;
        /// <summary>The lane region he is in there (<c>c.region || 1</c>, L8026); 0 = the owning scene's.</summary>
        public readonly int Region;
        /// <summary>+1 or −1: <c>resetWorld</c> always faces him +x (L8019).</summary>
        public readonly int Facing;
        /// <summary>The scene the checkpoint is in ("DL-03"; <c>sceneName</c> at its spot, L8135); null if unowned.</summary>
        public readonly string Scene;

        public CheckpointDef(string name, double x, double y = 0, int region = 0, int facing = 1, string scene = null)
        {
            Name = name ?? throw new ArgumentNullException(nameof(name));
            if (facing != 1 && facing != -1) throw new ArgumentOutOfRangeException(nameof(facing), "Facing is +1 or -1.");
            X = x; Y = y; Region = region; Facing = facing; Scene = scene;
        }
    }

    /// <summary>
    /// A chapter's checkpoints (port_architecture §5, §4.28): the save's total order (<c>CP_ORDER</c>, L3976, which
    /// <see cref="Save.CheckpointService"/> and every mechanism's <c>past()</c> reads) and, for each checkpoint the
    /// chapter can put him at, its place and owning scene. <see cref="ChapterSim"/> begins, respawns and continues at
    /// any placed checkpoint, whichever scene owns it, because the chapter's world is one.
    /// </summary>
    public sealed class CheckpointTable
    {
        private readonly CheckpointDef[] _places;

        /// <param name="order">Every checkpoint name the save knows, in play order (more than this chapter places).</param>
        /// <param name="places">Where the chapter's checkpoints put him, in play order; each name must be in <paramref name="order"/>.</param>
        public CheckpointTable(IReadOnlyList<string> order, params CheckpointDef[] places)
        {
            Order = order ?? throw new ArgumentNullException(nameof(order));
            if (order.Count == 0) throw new ArgumentException("Empty checkpoint order.", nameof(order));
            _places = places ?? throw new ArgumentNullException(nameof(places));
            int last = -1;
            for (int i = 0; i < places.Length; i++)
            {
                int at = IndexIn(order, places[i].Name);
                if (at < 0) throw new ArgumentException("Checkpoint '" + places[i].Name + "' is not in the order.", nameof(places));
                if (at <= last) throw new ArgumentException("Checkpoint '" + places[i].Name + "' is out of play order or repeated.", nameof(places));
                last = at;
            }
        }

        /// <summary>The save's checkpoint order.</summary>
        public IReadOnlyList<string> Order { get; }
        /// <summary>Every placed checkpoint, in play order.</summary>
        public IReadOnlyList<CheckpointDef> All => _places;

        /// <summary>The place of <paramref name="name"/>; false for a name this chapter does not place.</summary>
        public bool TryGet(string name, out CheckpointDef cp)
        {
            for (int i = 0; i < _places.Length; i++)
                if (string.Equals(_places[i].Name, name, StringComparison.Ordinal)) { cp = _places[i]; return true; }
            cp = default;
            return false;
        }

        /// <summary>The place of <paramref name="name"/>; throws for a name this chapter does not place.</summary>
        public CheckpointDef Get(string name)
            => TryGet(name, out var cp) ? cp : throw new ArgumentException("No checkpoint '" + name + "' in this table.", nameof(name));

        /// <summary>The scene that owns <paramref name="name"/> ("DL-03"), or null for a name not placed here.</summary>
        public string SceneOf(string name) => TryGet(name, out var cp) ? cp.Scene : null;

        /// <summary>The checkpoints <paramref name="sceneId"/> owns, in play order (a new array).</summary>
        public CheckpointDef[] Of(string sceneId)
        {
            var list = new List<CheckpointDef>();
            for (int i = 0; i < _places.Length; i++) if (string.Equals(_places[i].Scene, sceneId, StringComparison.Ordinal)) list.Add(_places[i]);
            return list.ToArray();
        }

        private static int IndexIn(IReadOnlyList<string> order, string name)
        {
            for (int i = 0; i < order.Count; i++) if (string.Equals(order[i], name, StringComparison.Ordinal)) return i;
            return -1;
        }
    }
}
