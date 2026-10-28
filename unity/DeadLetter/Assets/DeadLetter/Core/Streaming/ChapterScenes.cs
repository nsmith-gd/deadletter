using System;
using DeadLetter.Core.Scenes;

namespace DeadLetter.Core.Streaming
{
    /// <summary>
    /// Where a chapter's Unity scenes live and how a chapter is made from its ID: the one naming rule the Editor's scene
    /// builder writes by and the runtime streamer loads by (port_architecture §7).
    /// <list type="bullet">
    /// <item><c>Assets/Scenes/DL_Persistent.unity</c>: the bootstrap scene (GameHost, D-17, camera rig, audio). Never unloaded.</item>
    /// <item><c>Assets/Scenes/&lt;Chapter&gt;/&lt;SceneId&gt;.unity</c>: one view scene per <see cref="SceneDef"/>, e.g.
    /// <c>Assets/Scenes/Prologue/DL-03.unity</c>.</item>
    /// </list>
    /// </summary>
    public static class ChapterScenes
    {
        public const string Root = "Assets/Scenes";
        public const string BootstrapName = "DL_Persistent";
        public const string BootstrapPath = Root + "/" + BootstrapName + ".unity";

        /// <summary>The chapter IDs the runtime can build (<see cref="Create"/>).</summary>
        public static readonly string[] Ids = ChapterDefs.Ids;

        /// <summary>The chapter's folder under <see cref="Root"/>: its ID with a capital ("prologue" → "Prologue").</summary>
        public static string Folder(string chapterId)
        {
            if (string.IsNullOrEmpty(chapterId)) throw new ArgumentException("No chapter ID.", nameof(chapterId));
            return char.ToUpperInvariant(chapterId[0]) + chapterId.Substring(1);
        }

        /// <summary>The asset path of a scene's view: <c>Assets/Scenes/Prologue/DL-01.unity</c>.</summary>
        public static string ScenePath(string chapterId, string sceneId)
        {
            if (string.IsNullOrEmpty(sceneId)) throw new ArgumentException("No scene ID.", nameof(sceneId));
            return Root + "/" + Folder(chapterId) + "/" + sceneId + ".unity";
        }

        /// <summary>The Unity scene name of a scene's view (the file name without extension): the scene's ID.</summary>
        public static string SceneName(string sceneId) => sceneId;

        /// <summary>A new definition of chapter <paramref name="chapterId"/> (each call builds fresh factories), or null.</summary>
        public static ChapterDef Create(string chapterId) => ChapterDefs.Create(chapterId);
    }
}
