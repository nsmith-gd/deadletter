using System;

namespace DeadLetter.Core.Cues
{
    /// <summary>
    /// One directed moment's timing, seconds from its trigger (= its cue's first sample). index.html <c>MOMENTS</c>, L948;
    /// design in docs/directed_moments.md.
    /// <list type="bullet">
    /// <item><see cref="Lock"/>: before it, input is ignored; from it, any input cuts the hold (<c>momentFree</c>, L955).</item>
    /// <item><see cref="Release"/>: the shot lets go (<c>momentShot</c>, L952) and voices may play again (L958).</item>
    /// <item><see cref="Control"/>: control is back at the latest (L954).</item>
    /// </list>
    /// </summary>
    public sealed class DirectedMoment
    {
        /// <summary>The prototype's "never" (the ending's lock/control, L949).</summary>
        public const double Never = 99;

        public readonly string Name;
        public readonly double Lock, Release, Control;
        /// <summary>The peak's design time (directed_moments.md) — the frame the music and camera land on.</summary>
        public readonly double Peak;
        /// <summary>
        /// When the moment's act stops waiting for <c>momentFree</c> and lets go on its own, if earlier than
        /// <see cref="Control"/>: the awe act checks it only while <c>t &lt; release + 0.6</c> (L3390), so the city hands
        /// control back at 16.6 s plus his turn home, not at <c>control</c> 18.5. NaN = none.
        /// </summary>
        public readonly double ActLetsGoAt;

        public DirectedMoment(string name, double lockAt, double release, double control, double peak, double actLetsGoAt = double.NaN)
        {
            Name = name ?? throw new ArgumentNullException(nameof(name));
            Lock = lockAt; Release = release; Control = control; Peak = peak; ActLetsGoAt = actLetsGoAt;
        }

        /// <summary>The time control comes back without any input: <see cref="Control"/>, or <see cref="ActLetsGoAt"/> if earlier.</summary>
        public double FreeAt => double.IsNaN(ActLetsGoAt) ? Control : Math.Min(Control, ActLetsGoAt);

        /// <summary>True if the moment ever hands control back by itself (the ending does not: its sequence owns him).</summary>
        public bool ReturnsControl => FreeAt < Never;
    }

    /// <summary>The prologue's four moments (L948–L949).</summary>
    public static class PrologueMoments
    {
        /// <summary>DL-04, grief, quiet. Trigger: the first <c>realise</c> past the gate (L1956–L1958). Peak 15 (the wide).</summary>
        public static readonly DirectedMoment Kin = new DirectedMoment("kin", 19, 21, 22.5, 15);
        /// <summary>DL-09, wonder, full swell. Trigger: x &gt; AWE_X 113.3 (L3431–L3433). Peak 10. The awe act lets go at
        /// release + 0.6 (L3390).</summary>
        public static readonly DirectedMoment Refuge = new DirectedMoment("refuge", 14, 16, 18.5, 10, 16 + 0.6);
        /// <summary>DL-10, grief and horror, full swell. Trigger: UP on the counterweight with the case loaded (L4584–L4588).
        /// Peak 12 (the cold light full on the lane).</summary>
        public static readonly DirectedMoment RingC = new DirectedMoment("ringc", 16, 20, 22, 12);
        /// <summary>The end, intrigue. Trigger: the landing's look phase at x 173.2 (L2105). Peak 6.5; he checks his label at
        /// <see cref="WindowLabelAt"/>; lock and control are "never".</summary>
        public static readonly DirectedMoment Window = new DirectedMoment("window", DirectedMoment.Never, 13.6, DirectedMoment.Never, 6.5);

        /// <summary>The ending checks his label at 13.6 s on the window cue's clock (L2113).</summary>
        public const double WindowLabelAt = 13.6;
        /// <summary>DL-04's realise act idles once its clip passes frame 155 and the cue is past 9.5 s (L2313).</summary>
        public const double KinIdleAfter = 9.5;
        public const int KinIdleFrame = 155;

        public static readonly DirectedMoment[] All = { Kin, Refuge, RingC, Window };

        public static DirectedMoment Find(string name)
        {
            for (int i = 0; i < All.Length; i++) if (All[i].Name == name) return All[i];
            return null;
        }
    }
}
