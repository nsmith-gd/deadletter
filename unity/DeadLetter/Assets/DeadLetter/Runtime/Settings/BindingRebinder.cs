using System;
using DeadLetter.Core.Settings;
using UnityEngine.InputSystem;

namespace DeadLetter.Runtime.Settings
{
    /// <summary>
    /// Interactive rebinding for the options screen, on the Input System's own machinery
    /// (<c>PerformInteractiveRebinding</c>). Overrides are kept in <see cref="GameSettings.BindingOverrides"/> as the
    /// asset's <c>SaveBindingOverridesAsJson</c> text, so they persist with the other settings.
    /// <para>
    /// Usage from the options UI: <c>BindingRebinder.Start(action, bindingIndex, ok => { draft.BindingOverrides =
    /// BindingRebinder.Capture(asset); refreshLabel(); })</c>, then <c>SettingsStore.Instance.Commit(draft)</c> on Confirm.
    /// For a composite (Move's A/D parts) pass the part's binding index, not the composite's. Escape cancels.
    /// </para>
    /// </summary>
    public static class BindingRebinder
    {
        /// <summary>
        /// Listen for the next control and bind it to <paramref name="action"/>'s binding <paramref name="bindingIndex"/>.
        /// The action is disabled while listening and re-enabled after. <paramref name="done"/> gets true on success.
        /// </summary>
        public static InputActionRebindingExtensions.RebindingOperation Start(
            InputAction action, int bindingIndex, Action<bool> done, bool excludeMouse = true)
        {
            if (action == null) throw new ArgumentNullException(nameof(action));
            if (bindingIndex < 0 || bindingIndex >= action.bindings.Count) throw new ArgumentOutOfRangeException(nameof(bindingIndex));

            bool wasEnabled = action.enabled;
            action.Disable();

            var op = action.PerformInteractiveRebinding(bindingIndex)
                .WithCancelingThrough("<Keyboard>/escape")
                .OnMatchWaitForAnother(0.1f);
            if (excludeMouse) op = op.WithControlsExcluding("<Mouse>");

            op.OnComplete(o =>
            {
                o.Dispose();
                if (wasEnabled) action.Enable();
                done?.Invoke(true);
            });
            op.OnCancel(o =>
            {
                o.Dispose();
                if (wasEnabled) action.Enable();
                done?.Invoke(false);
            });
            return op.Start();
        }

        /// <summary>The asset's current overrides as JSON (empty when none).</summary>
        public static string Capture(InputActionAsset asset)
        {
            if (asset == null) return "";
            return asset.SaveBindingOverridesAsJson() ?? "";
        }

        /// <summary>Drop one binding's override (the options screen's per-row Reset).</summary>
        public static void ResetBinding(InputAction action, int bindingIndex)
        {
            action?.RemoveBindingOverride(bindingIndex);
        }

        /// <summary>Human-readable label for a binding, for the options screen (e.g. "Space", "A").</summary>
        public static string Label(InputAction action, int bindingIndex)
        {
            return action == null ? "" : action.GetBindingDisplayString(bindingIndex);
        }
    }
}
