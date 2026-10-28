using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms
{
    /// <summary>
    /// A moment on the game clock that a timer counts from (the prototype's <c>game.clock − since</c>: <c>darkSince</c>,
    /// <c>latchAt</c>, <c>b.fullAt</c>, <c>allSince</c>, <c>dismissedAt</c>). The clock is the session's: a Continue builds a
    /// fresh world whose clock starts again at 0. So a snapshot keeps the time elapsed since the mark (as of the last step
    /// that read it), and the first step after a restore re-bases the mark on that step's clock: the timer runs on from where
    /// it was saved. NaN: no mark (or no game clock), the owner falls back to its own sum of dt.
    /// </summary>
    public struct ClockMark
    {
        private double _at, _last, _carry;

        public static ClockMark None => new ClockMark { _at = double.NaN, _last = double.NaN, _carry = double.NaN };

        /// <summary>Marks this step's clock.</summary>
        public void Mark(in StepContext ctx) { _at = ctx.Clock; _last = ctx.Clock; _carry = double.NaN; }

        public void Clear() { _at = _last = _carry = double.NaN; }

        /// <summary>Seconds since the mark on this step's clock (re-based first if restored from a snapshot); NaN: none.</summary>
        public double Since(in StepContext ctx)
        {
            _last = ctx.Clock;
            if (double.IsNaN(ctx.Clock)) return double.NaN;
            if (double.IsNaN(_at) && !double.IsNaN(_carry)) { _at = ctx.Clock - ctx.Dt - _carry; _carry = double.NaN; }
            return double.IsNaN(_at) ? double.NaN : ctx.Clock - _at;
        }

        /// <summary>Writes the time elapsed since the mark as of the last step that read it (NaN: none).</summary>
        public void Write(ISnapshotWriter w, string key)
            => w.WriteDouble(key, !double.IsNaN(_at) && !double.IsNaN(_last) ? _last - _at : _carry);

        public void Read(ISnapshotReader r, string key) { _at = _last = double.NaN; _carry = r.ReadDouble(key); }
    }
}
