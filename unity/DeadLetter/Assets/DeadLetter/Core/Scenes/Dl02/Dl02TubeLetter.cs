using System;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Scenes.Dl02
{
    /// <summary>The tube letter (<c>letterState.tube</c>, L3906, L4771–L4779).</summary>
    public enum TubeLetterState
    {
        /// <summary>In the tube's cup (<c>'cup'</c>, its start).</summary>
        Cup,
        /// <summary>The cup lets it go: it drops to the floor over <see cref="Dl02TubeLetter.FallSeconds"/> (<c>'falling'</c>).</summary>
        Falling,
        /// <summary>Flat on the lane at <see cref="Dl02TubeLetter.X"/>, to be picked up (<c>'floor'</c>).</summary>
        Floor,
    }

    public enum TubeLetterEvent
    {
        /// <summary>The cup lets go: a short chain rattle, and a tap 0.2 s later (<c>Sound.chain(0.3)</c>, L4772).</summary>
        Cough,
        /// <summary>It lands (<c>Sound.setDown(false)</c>, L4778).</summary>
        Landed,
    }

    /// <summary>
    /// DL-02's tube (§5 <c>dl02.tubeLetter</c>; scene doc §2 "The tube"): the first time D-17 passes x 14.3 the cup lets
    /// its letter go, and it lands flat on the lane 0.55 s later (L4770–L4779, in <c>updateCh1</c>, #7). The letter's state
    /// is the letters system's (<c>letterState</c> is never reset by a respawn, only by a new game, L4133, L4125), so
    /// <see cref="Reset"/> keeps it; a fall cut short by a respawn restarts from −1 s, as <c>resetCh1</c>'s
    /// <c>tubeT = -1</c> makes it (L4111). Picking it up and posting it (<c>pickLetter</c>, <c>postLetter</c>) are the
    /// letters system's (§4.26) and are not ported here.
    /// </summary>
    public sealed class Dl02TubeLetter : Mechanism, IPositionSource
    {
        /// <summary><c>SH.tubeX</c> (L3887): where the letter lands (<c>LETTERS[0].x</c>, L3906).</summary>
        public const double X = 14.6;
        /// <summary>The cup lets go once he is past <c>SH.tubeX − 0.3</c> (L4772).</summary>
        public const double TriggerX = X - 0.3;
        /// <summary><c>t = min(1, tubeT / 0.55)</c> (L4774).</summary>
        public const double FallSeconds = 0.55;

        public Dl02TubeLetter(MechanismId id) : base(id) { Init((int)TubeLetterState.Cup); }

        public TubeLetterState State => (TubeLetterState)StateCode;
        /// <summary>Seconds into the fall (<c>s.tubeT</c>).</summary>
        public double T { get; private set; }
        /// <summary>The fall's progress, 0..1, for the view (L4774–L4777: y eases down by t², it turns flat by smooth(t)).</summary>
        public double Fall => State == TubeLetterState.Floor ? 1 : State == TubeLetterState.Falling ? Math.Max(0, Math.Min(1, T / FallSeconds)) : 0;
        public double Position => Fall;

        public override void Reset(in Checkpoint cp)
        {
            if (State == TubeLetterState.Falling) T = -1;                                                   // resetCh1: tubeT: -1, L4111
        }

        public override void Step(in StepContext ctx)
        {
            if (State == TubeLetterState.Cup && ctx.Player.X > TriggerX)                                     // L4772
            {
                Enter(ctx, (int)TubeLetterState.Falling);
                T = 0;
                Emit(ctx, (int)TubeLetterEvent.Cough);
            }
            if (State == TubeLetterState.Falling)                                                             // L4773–L4778
            {
                T += ctx.Dt;
                if (Math.Min(1, T / FallSeconds) >= 1)
                {
                    Enter(ctx, (int)TubeLetterState.Floor);
                    Emit(ctx, (int)TubeLetterEvent.Landed);
                }
            }
        }

        protected override void WriteFields(ISnapshotWriter w) => w.WriteDouble("t", T);
        protected override void ReadFields(ISnapshotReader r) => T = r.ReadDouble("t");
    }
}
