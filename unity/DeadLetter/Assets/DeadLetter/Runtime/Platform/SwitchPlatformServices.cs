using DeadLetter.Core.Platform;

namespace DeadLetter.Runtime.Platform
{
    /// <summary>
    /// Nintendo Switch: a <b>stub</b>. The real implementation needs the Switch build module and the NintendoSDK, both
    /// under NDA and available only through the Nintendo Developer Portal, so it is written by a person with portal
    /// access on a licensed machine, never in this repo's cloud sessions. No SDK names are guessed here; each TODO names
    /// the area of the SDK documentation to follow. This file uses no SDK types, so it compiles everywhere; it is only
    /// chosen on <c>UNITY_SWITCH</c>.
    /// </summary>
    public sealed class SwitchPlatformServices : NullPlatformServices
    {
        public override PlatformKind Kind => PlatformKind.Switch;
        public override string Name => "Switch";

        public override bool Initialize()
        {
            // TODO(Switch, NDA): Account / user selection. Open the user selected at launch (or show the system user
            //   picker per the startup-user guidelines) and keep that user handle for the session; save data is per user.
            // TODO(Switch, NDA): Save data mount. Mount the user's save data before SettingsStore and the save system
            //   read anything, and point their file paths at the mount. Unity's persistentDataPath is not the save area.
            // TODO(Switch, NDA): Applet / focus handling. Subscribe to the system's focus / in-focus state and HOME-menu
            //   notifications and raise OverlayActiveChanged(true/false) so PauseGate pauses (lotcheck requires the game
            //   to pause and mute while not in focus). Also handle controller-applet (Joy-Con layout) and the
            //   operation-mode change (handheld ↔ docked: resolution / quality tier).
            return base.Initialize();
        }

        public override void Shutdown()
        {
            // TODO(Switch, NDA): Save data commit. Commit any pending writes to the mounted save data and unmount it.
            //   Every write must be followed by a commit to be durable; rate-limit commits (port_architecture §4.28:
            //   at most one save write per 2 s on Switch).
            base.Shutdown();
        }

        // Switch has no achievements or rich presence: the inherited no-ops are correct.
        // CloudSync stays null: save data is backed up by the system (Save Data Cloud), not by the game.
    }
}
