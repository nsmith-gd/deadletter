using DeadLetter.Core.Mechanisms;

namespace DeadLetter.Core.Scenes.Dl03
{
    /// <summary>
    /// The racks' reveal (<c>game.revealed</c>, <c>revealPending</c>, <c>revealTime</c>; L2394–L2403, L8029), which DL-03 and
    /// DL-04 share: DL-03's plate solves it with the racks left dark (<see cref="Solve"/>); DL-04 lights them the moment he
    /// is through the gate (<see cref="Reveal"/>) and realises among them a second later. One per chapter
    /// (<see cref="ChapterSim.Shared{T}"/>), so it holds whichever scene's rules run.
    /// </summary>
    public sealed class RacksReveal
    {
        /// <summary><c>revealTime</c> at a reset (L8029) and while pending (L2398).</summary>
        public const double NotYet = -100, Pending0 = 1e9;

        /// <summary>The plate is solved or he has been through the gate (<c>game.revealed</c>).</summary>
        public bool Revealed { get; private set; }
        /// <summary>Solved, the racks still dark until he passes the gate (<c>game.revealPending</c>).</summary>
        public bool Pending { get; private set; }
        /// <summary>Game-clock time the racks lit (<c>game.revealTime</c>).</summary>
        public double Time { get; private set; } = NotYet;

        /// <summary><c>resetWorld</c> (L8029): revealed from <c>solved</c> on, lit long ago, nothing pending.</summary>
        public void Reset(in Checkpoint cp)
        {
            Revealed = cp.Past("solved");
            Pending = false;
            Time = NotYet;
        }

        /// <summary>The plate holds the gate open without him (L2398): revealed, but dark until he walks through.</summary>
        public void Solve()
        {
            Revealed = true;
            Pending = true;
            Time = Pending0;
        }

        /// <summary>He is through the gate (L2402): the racks light now.</summary>
        public void Reveal(double clock)
        {
            Revealed = true;
            Pending = false;
            Time = clock;
        }
    }
}
