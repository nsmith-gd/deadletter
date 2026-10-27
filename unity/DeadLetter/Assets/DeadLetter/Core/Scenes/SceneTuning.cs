using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Scenes
{
    /// <summary>
    /// A scene's changes to the motor's tuning (<see cref="SceneDef.Motor"/>), applied to the chapter's one
    /// <see cref="MotorConfig"/> while he is in the scene and put back when he leaves it, at a seam only (never per step).
    /// The motor reads its config's fields as it goes and keeps the one it was built with, so the chapter edits that one
    /// in place. The only tuning so far is M10's (#28): DL-06's levers step in at 0.4, the motor's one station speed is
    /// 0.45. Copied field by field, not by reflection (IL2CPP stripping); once stations carry their own step-in speed
    /// this class goes.
    /// </summary>
    internal sealed class SceneTuning
    {
        private readonly double _sceneStepIn, _chapterStepIn;

        private SceneTuning(double sceneStepIn, double chapterStepIn) { _sceneStepIn = sceneStepIn; _chapterStepIn = chapterStepIn; }

        /// <summary>The tuning <paramref name="scene"/> changes from the prototype's, with <paramref name="chapter"/>'s values to put back; null if none.</summary>
        public static SceneTuning Of(MotorConfig scene, MotorConfig chapter)
        {
            if (scene == null || scene.StepInSpeed == MotorConfig.Prototype().StepInSpeed) return null;
            return new SceneTuning(scene.StepInSpeed, chapter.StepInSpeed);
        }

        public void Apply(MotorConfig live) => live.StepInSpeed = _sceneStepIn;
        public void Revert(MotorConfig live) => live.StepInSpeed = _chapterStepIn;
    }
}
