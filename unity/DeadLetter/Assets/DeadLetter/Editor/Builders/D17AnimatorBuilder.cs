using System.Collections.Generic;
using System.Linq;
using DeadLetter.Core.Motor;
using DeadLetter.Runtime;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace DeadLetter.Editor.Builders
{
    /// <summary>
    /// Builds <c>Assets/Art/D17/D17.controller</c> from the glTFast clips of <c>Assets/Art/D17/d17.glb</c>.
    /// <para>
    /// The contract is <see cref="D17AnimatorParams"/>: Core picks the clip (<c>D17Motor.Clip</c>) and
    /// <c>D17Controller</c> cross-fades to the state of that name, so there is one base-layer state per clip in
    /// <see cref="ClipTimings.All"/>, named exactly as the clip, with its Speed Multiplier bound to
    /// <see cref="D17AnimatorParams.ClipSpeed"/> (Core's time scale: speed / authored clip speed for walk, run,
    /// crouch-walk, carry-walk and sad-walk; negative plays PushWalk / Walk backwards). Locomotion is not a blend tree:
    /// Core already chooses Walk / Run / CrouchWalk by speed (L2057–L2061) and sets the time scale, so a blend tree would
    /// be a second, disagreeing chooser that <c>CrossFadeInFixedTime("Walk")</c> could not enter anyway.
    /// </para>
    /// <para>
    /// glTFast marks every Mecanim clip as looping. Each one-shot clip (no <c>LOOP_FRAMES</c> entry) therefore gets a
    /// "<c>Name (hold)</c>" state playing the same clip at speed 0 just before its end, reached by an exit-time
    /// transition, so acts, landings and deaths hold their last pose instead of restarting.
    /// </para>
    /// The build is idempotent: an existing controller is cleared and refilled in place, so its GUID (and every
    /// Animator that references it) survives a rebuild.
    /// </summary>
    public static class D17AnimatorBuilder
    {
        public const string GlbPath = "Assets/Art/D17/d17.glb";
        public const string ControllerPath = "Assets/Art/D17/D17.controller";
        public const string HoldSuffix = " (hold)";

        /// <summary>Normalised time the hold state sits at: just short of 1 so a looping clip does not wrap to frame 0.</summary>
        private const float HoldTime = 0.9995f;

        // Grid layout so the graph is readable: one row per group, in ClipTimings order otherwise.
        private static readonly string[][] Rows =
        {
            new[] { ClipNames.Idle, ClipNames.Walk, ClipNames.Run, ClipNames.SadWalk, ClipNames.CrouchIdle, ClipNames.CrouchWalk },
            new[] { "JumpStart", ClipNames.JumpAir, ClipNames.Fall, ClipNames.Land, ClipNames.Mantle },
            new[] { ClipNames.Lift, ClipNames.CarryIdle, ClipNames.CarryWalk, ClipNames.SetDown, ClipNames.SetDownHigh },
            new[] { ClipNames.Grab, ClipNames.PushIdle, ClipNames.PushWalk, ClipNames.Nudge },
            new[] { ClipNames.Sit, ClipNames.SitIdle, ClipNames.SitUp, ClipNames.Present },
        };

        [MenuItem("Dead Letter/Build/D17 Animator")]
        public static void BuildMenu()
        {
            var controller = Build(out var report);
            if (controller != null)
            {
                EditorGUIUtility.PingObject(controller);
                Debug.Log("[D17] " + report, controller);
            }
            else Debug.LogError("[D17] " + report);
        }

        /// <summary>Builds (or rebuilds) the controller. Returns null and a reason when the GLB is missing or not Mecanim.</summary>
        public static AnimatorController Build(out string report)
        {
            var clips = new Dictionary<string, AnimationClip>();
            foreach (var o in AssetDatabase.LoadAllAssetsAtPath(GlbPath))
                if (o is AnimationClip c && !c.name.StartsWith("__preview__")) clips[c.name] = c;
            if (clips.Count == 0)
            {
                report = $"No clips in {GlbPath}. Is it imported by glTFast (com.unity.cloud.gltfast) with Animation = Mecanim?";
                return null;
            }
            var legacy = clips.Values.FirstOrDefault(c => c.legacy);
            if (legacy != null)
            {
                report = $"{GlbPath} imported legacy clips ({legacy.name}). Set Animation = Mecanim in its import settings and reimport.";
                return null;
            }

            var controller = AssetDatabase.LoadAssetAtPath<AnimatorController>(ControllerPath);
            if (controller == null) controller = AnimatorController.CreateAnimatorControllerAtPath(ControllerPath);
            Clear(controller);
            AddParameters(controller);

            var sm = controller.layers[0].stateMachine;
            var problems = new List<string>();
            var placed = new HashSet<string>();
            int holds = 0;

            for (int r = 0; r < Rows.Length; r++)
                for (int c = 0; c < Rows[r].Length; c++)
                    if (TryInfo(Rows[r][c], problems, out var info))
                    {
                        holds += AddClipState(sm, info, clips, new Vector2(c, r), problems);
                        placed.Add(info.Name);
                    }

            int i = 0;
            foreach (var info in ClipTimings.All)
            {
                if (placed.Contains(info.Name)) continue;
                holds += AddClipState(sm, info, clips, new Vector2(i % 8, Rows.Length + 1 + i / 8), problems);
                i++;
            }

            sm.defaultState = sm.states.First(s => s.state.name == ClipNames.Idle).state;

            foreach (var name in clips.Keys)
                if (!ClipTimings.TryGet(name, out _)) problems.Add($"clip {name} is in the GLB but not in ClipTimings (no state)");

            EditorUtility.SetDirty(controller);
            AssetDatabase.SaveAssets();

            report = $"Built {ControllerPath}: {ClipTimings.All.Length} clip states, {holds} hold states, " +
                     $"{controller.parameters.Length} parameters." +
                     (problems.Count > 0 ? "\n  " + string.Join("\n  ", problems) : "");
            if (problems.Count > 0) Debug.LogWarning("[D17] " + string.Join("\n", problems), controller);
            return controller;
        }

        private static bool TryInfo(string name, List<string> problems, out ClipInfo info)
        {
            if (ClipTimings.TryGet(name, out info)) return true;
            problems.Add($"layout names {name}, which is not in ClipTimings");
            return false;
        }

        /// <summary>Adds the clip's state (and its hold state for one-shots). Returns the number of hold states added.</summary>
        private static int AddClipState(AnimatorStateMachine sm, ClipInfo info, Dictionary<string, AnimationClip> clips,
                                        Vector2 cell, List<string> problems)
        {
            var pos = new Vector3(300 + cell.x * 240, cell.y * 120, 0);
            var state = sm.AddState(info.Name, pos);
            state.speed = 1f;
            state.speedParameter = D17AnimatorParams.ClipSpeed;
            state.speedParameterActive = true;
            state.writeDefaultValues = true;

            if (!clips.TryGetValue(info.Name, out var clip))
            {
                problems.Add($"clip {info.Name} missing from {GlbPath} (state left empty)");
                return 0;
            }
            state.motion = clip;

            double frames = clip.length * 24.0;
            if (System.Math.Abs(frames - info.Frames) > 0.05)
                problems.Add($"clip {info.Name}: {frames:0.##} frames in Unity vs {info.Frames} in ClipTimings");

            if (info.Loop) return 0;

            var hold = sm.AddState(info.Name + HoldSuffix, pos + new Vector3(0, 50, 0));
            hold.motion = clip;
            hold.speed = 0f;
            hold.speedParameterActive = false;
            hold.writeDefaultValues = true;

            var t = state.AddTransition(hold);
            t.hasExitTime = true;
            t.exitTime = HoldTime;
            t.hasFixedDuration = true;
            t.duration = 0f;
            t.offset = HoldTime;
            t.interruptionSource = TransitionInterruptionSource.None;
            return 1;
        }

        private static void AddParameters(AnimatorController c)
        {
            c.AddParameter(new AnimatorControllerParameter
                { name = D17AnimatorParams.ClipSpeed, type = AnimatorControllerParameterType.Float, defaultFloat = 1f });
            c.AddParameter(D17AnimatorParams.Speed, AnimatorControllerParameterType.Float);
            c.AddParameter(D17AnimatorParams.VerticalSpeed, AnimatorControllerParameterType.Float);
            c.AddParameter(new AnimatorControllerParameter
                { name = D17AnimatorParams.Grounded, type = AnimatorControllerParameterType.Bool, defaultBool = true });
            c.AddParameter(D17AnimatorParams.Crouched, AnimatorControllerParameterType.Bool);
            c.AddParameter(D17AnimatorParams.Carrying, AnimatorControllerParameterType.Bool);
            c.AddParameter(D17AnimatorParams.Pushing, AnimatorControllerParameterType.Bool);
            c.AddParameter(D17AnimatorParams.State, AnimatorControllerParameterType.Int);
            c.AddParameter(D17AnimatorParams.CarryBlend, AnimatorControllerParameterType.Float);
        }

        /// <summary>Empties the controller in place: one base layer, no parameters, no states (keeps the asset GUID).</summary>
        private static void Clear(AnimatorController c)
        {
            foreach (var p in c.parameters) c.RemoveParameter(p);
            while (c.layers.Length > 1) c.RemoveLayer(c.layers.Length - 1);
            if (c.layers.Length == 0) c.AddLayer("Base Layer");

            var sm = c.layers[0].stateMachine;
            foreach (var t in sm.anyStateTransitions) sm.RemoveAnyStateTransition(t);
            foreach (var t in sm.entryTransitions) sm.RemoveEntryTransition(t);
            foreach (var child in sm.stateMachines) sm.RemoveStateMachine(child.stateMachine);
            foreach (var child in sm.states) sm.RemoveState(child.state);
        }
    }
}
