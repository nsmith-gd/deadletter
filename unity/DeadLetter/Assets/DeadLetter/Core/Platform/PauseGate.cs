using System;

namespace DeadLetter.Core.Platform
{
    [Flags]
    public enum PauseReason
    {
        None = 0,
        /// <summary>The player's pause card (Esc / P / Menu, <c>togglePause</c> L8123).</summary>
        Player = 1,
        /// <summary>Steam overlay or Switch HOME / applet in front of the game.</summary>
        Overlay = 2,
        /// <summary>The window lost focus (desktop) or the app was suspended.</summary>
        Focus = 4,
    }

    /// <summary>
    /// Who is holding the game paused. The simulation runs only when nothing is. A system interruption (overlay,
    /// HOME menu, focus loss) also raises <see cref="PauseReason.Player"/> when it happens during play, so when it ends
    /// the player is left on the pause card and resumes on their own, which is what Steam's overlay guidance and
    /// Switch's focus handling expect (no surprise un-pause into danger). The prototype only released held keys on blur
    /// (L1229–1230); pausing is new in the port.
    /// </summary>
    public sealed class PauseGate
    {
        private PauseReason _held;

        /// <summary>Raised whenever <see cref="IsPaused"/> or <see cref="ShowPauseCard"/> may have changed.</summary>
        public event Action Changed;

        public PauseReason Held => _held;
        public bool IsPaused => _held != PauseReason.None;
        /// <summary>The pause card is up (the player has to resume).</summary>
        public bool ShowPauseCard => (_held & PauseReason.Player) != 0;

        /// <summary>Whether focus loss pauses (desktop option; always true on Switch). Default on.</summary>
        public bool PauseOnFocusLoss = true;

        /// <summary>The player pressed pause / resume. Resuming while an overlay is still up keeps the game paused.</summary>
        public void TogglePlayer()
        {
            if ((_held & PauseReason.Player) != 0) Set(_held & ~PauseReason.Player);
            else Set(_held | PauseReason.Player);
        }

        public void SetPlayer(bool paused) => Set(paused ? _held | PauseReason.Player : _held & ~PauseReason.Player);

        /// <summary>Overlay opened / closed (<see cref="IPlatformServices.OverlayActiveChanged"/>).</summary>
        public void OnOverlay(bool active, bool inPlay) => SystemPause(PauseReason.Overlay, active, inPlay);

        /// <summary>Window or app focus changed.</summary>
        public void OnFocus(bool focused, bool inPlay)
        {
            if (!PauseOnFocusLoss && !focused) return;
            SystemPause(PauseReason.Focus, !focused, inPlay);
        }

        private void SystemPause(PauseReason reason, bool active, bool inPlay)
        {
            if (active) Set(_held | reason | (inPlay ? PauseReason.Player : PauseReason.None));
            else Set(_held & ~reason);
        }

        private void Set(PauseReason next)
        {
            if (next == _held) return;
            _held = next;
            Changed?.Invoke();
        }
    }
}
