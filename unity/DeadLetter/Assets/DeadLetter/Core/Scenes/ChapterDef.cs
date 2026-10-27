using System;
using System.Collections.Generic;

namespace DeadLetter.Core.Scenes
{
    /// <summary>
    /// A chapter's definition (port_architecture §7: "Core state is global"): its scenes in lane order and its
    /// checkpoints. <see cref="ChapterSim"/> builds every scene's mechanisms into one graph and every scene's lane into
    /// one geometry, so walking back, respawning or continuing anywhere in the chapter finds the world as it was.
    /// <para>Lane order: regions never go back (1, 2, 2, 3 ...); within a region each scene starts where the one before
    /// it ends (X0 = the previous X1), or shares its stretch exactly when the two are told apart by state
    /// (<see cref="SceneRules.HasLeft"/>: DL-06 and DL-07 on one floor). The save's scene key is <see cref="Id"/>.</para>
    /// </summary>
    public sealed class ChapterDef
    {
        private readonly SceneDef[] _scenes;

        public ChapterDef(string id, CheckpointTable checkpoints, params SceneDef[] scenes)
        {
            if (string.IsNullOrEmpty(id)) throw new ArgumentException("A chapter needs an ID.", nameof(id));
            Id = id;
            Checkpoints = checkpoints ?? throw new ArgumentNullException(nameof(checkpoints));
            if (scenes == null || scenes.Length == 0) throw new ArgumentException("A chapter needs a scene.", nameof(scenes));
            _scenes = (SceneDef[])scenes.Clone();
            for (int i = 0; i < _scenes.Length; i++)
            {
                var s = _scenes[i] ?? throw new ArgumentException("Scene " + i + " is null.", nameof(scenes));
                if (!(s.X1 > s.X0)) throw new ArgumentException(s.Id + ": X1 must be past X0.", nameof(scenes));
                for (int j = 0; j < i; j++)
                    if (string.Equals(_scenes[j].Id, s.Id, StringComparison.Ordinal)) throw new ArgumentException("Scene " + s.Id + " is listed twice.", nameof(scenes));
                if (i == 0) continue;
                var p = _scenes[i - 1];
                if (s.Region < p.Region) throw new ArgumentException(s.Id + " is in region " + s.Region + ", before " + p.Id + "'s " + p.Region + ": scenes go in lane order.", nameof(scenes));
                bool follows = s.X0 == p.X1, shares = s.X0 == p.X0 && s.X1 == p.X1;
                if (s.Region == p.Region && !follows && !shares)
                    throw new ArgumentException(s.Id + " starts at " + s.X0 + ", not where " + p.Id + " ends (" + p.X1 + ").", nameof(scenes));
            }
        }

        /// <summary>"prologue": also the save's scene key (a snapshot is applied only to the chapter it was taken in).</summary>
        public string Id { get; }
        /// <summary>The scenes, in lane order.</summary>
        public IReadOnlyList<SceneDef> Scenes => _scenes;
        public CheckpointTable Checkpoints { get; }

        /// <summary>The scene called <paramref name="id"/> ("DL-03"), or null.</summary>
        public SceneDef Scene(string id)
        {
            for (int i = 0; i < _scenes.Length; i++) if (string.Equals(_scenes[i].Id, id, StringComparison.Ordinal)) return _scenes[i];
            return null;
        }
    }
}
