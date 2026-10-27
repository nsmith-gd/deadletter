using DeadLetter.Core.Platform;

namespace DeadLetter.Runtime.Platform
{
    /// <summary>
    /// The DRM-free desktop build (Itch, via <c>butler push</c>) and the editor without <c>DL_STEAM</c>: no achievements,
    /// rich presence, overlay or cloud; every call is a harmless no-op (<see cref="NullPlatformServices"/>). Saves stay
    /// local under <c>Application.persistentDataPath</c>. Steam Deck is still detected from the environment, so an Itch
    /// build added to Steam as a non-Steam game gets Deck glyphs.
    /// </summary>
    public sealed class ItchPlatformServices : NullPlatformServices
    {
        private readonly bool _deck = PlatformServices.SteamDeckFromEnvironment();

        public override PlatformKind Kind => PlatformKind.Desktop;
        public override string Name => "Itch";
        public override bool IsSteamDeck => _deck;
    }
}
