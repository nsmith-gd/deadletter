using System;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Plates
{
    public enum PresenceState { Empty, Present, Open }

    public enum PresenceEvent
    {
        /// <summary>Someone stepped (or was pushed) onto the strip: <c>Sound.plate</c> (L5384).</summary>
        Press,
        /// <summary>Present without the coat for 0.6 s: buzz and the register voice; Index 1 = <c>att_gate_1</c> (the first time), 2 = <c>att_gate_2</c> (L5387–L5390).</summary>
        AskForCoat,
        /// <summary>Present with the coat: <c>att_gate_3</c> and the bell, once (L5391).</summary>
        Thanks,
    }

    public sealed class PresenceStripParams
    {
        /// <summary>Who counts as present: him, or a term (the figure near the strip's middle). Any share &gt; 0 is presence.</summary>
        public PlateSensorParams Sensor = new PlateSensorParams();
        /// <summary>The second condition: this body placed (the coat on peg 7).</summary>
        public MechanismId Coat;
        public double AskAfter = 0.6;
        /// <summary>The register speaks only while he is left of this x (L5385).</summary>
        public double VoiceBeforeX = double.PositiveInfinity;
        /// <summary>From this checkpoint the thanks has been said (§4.28; see the class remarks).</summary>
        public string ThankedAfter;

        /// <summary>DL-12: him on the strip 208.0–208.8 below y 0.05, or the figure within 0.25 of 208.4; the coat on the peg (L286–L288, L5381–L5391).</summary>
        public static PresenceStripParams Dl12Strip() => new PresenceStripParams
        {
            Sensor = new PlateSensorParams
            {
                PlayerX0 = 208.0, PlayerX1 = 208.8, PlayerMaxY = 0.05, PlayerShare = 1,           // ATT.strip
                Terms = new[] { PlateTerm.Near("dl12.figure", 208.4, 0.25, 1) },                  // ATT.fig.strip
            },
            Coat = "dl12.coat", VoiceBeforeX = 212, ThankedAfter = "register",
        };
    }

    /// <summary>
    /// DL-12's register strip (§4.13a, L5381–L5408): present (him or the figure) AND the coat on its peg. Signals:
    /// <see cref="Load"/> = 1 when both (the follower gate reads it × 1.3 m), <see cref="Engaged"/> = both.
    /// Reset derives presence from the bodies (no Press) and the thanks from <see cref="PresenceStripParams.ThankedAfter"/>:
    /// the prototype resets <c>present = false, said = {}</c>, so on a reload at <c>register</c> it clicks and says
    /// <c>att_gate_3</c> again (L5235); a deliberate deviation.
    /// </summary>
    public sealed class PresenceStrip : Mechanism, ILoad, IEngageable
    {
        private readonly PresenceStripParams _p;
        private readonly PlateSensor _sensor;
        private IPlateBody _coat;
        private double _presentFor;
        private long _count, _askedFor;
        private bool _thanked;

        public PresenceStrip(MechanismId id, PresenceStripParams p) : base(id)
        {
            _p = p ?? throw new ArgumentNullException(nameof(p));
            _sensor = new PlateSensor(p.Sensor);
        }

        public PresenceState State => (PresenceState)StateCode;
        public bool Present { get; private set; }
        public bool CoatOn { get; private set; }
        public bool Engaged => State == PresenceState.Open;
        public double Load => Engaged ? 1 : 0;
        /// <summary>Times someone has arrived on the strip (<c>presentCount</c>).</summary>
        public long PresentCount => _count;

        public override void Link(MechanismLinker link)
        {
            _sensor.Link(link);
            _coat = link.Read<IPlateBody>(_p.Coat) ?? throw new InvalidOperationException(Id + " needs a Coat.");
        }

        public override void Reset(in Checkpoint cp)
        {
            Present = _sensor.Load(false) > 0;
            CoatOn = _coat.Support == BodySupport.Placed;
            _count = Present ? 1 : 0;
            _askedFor = 0;
            _thanked = cp.Past(_p.ThankedAfter);
            _presentFor = 1e3;                                                        // presentAt: −10
            Init((int)StateFor(Present, CoatOn));
        }

        public override void Step(in StepContext ctx)
        {
            bool present = _sensor.Load(_sensor.PlayerOn(ctx.Player)) > 0;          // L5382–L5383
            bool coat = _coat.Support == BodySupport.Placed;
            _presentFor += ctx.Dt;
            if (present && !Present) { _count++; _presentFor = 0; Emit(ctx, (int)PresenceEvent.Press); }   // L5384
            Present = present; CoatOn = coat;
            if (ctx.Player.X < _p.VoiceBeforeX)                                                             // L5385
            {
                if (present && !coat && _presentFor > _p.AskAfter && _askedFor != _count)                  // L5387
                {
                    _askedFor = _count;
                    Emit(ctx, (int)PresenceEvent.AskForCoat, _count > 1 ? 2 : 1);
                }
                if (present && coat && !_thanked) { _thanked = true; Emit(ctx, (int)PresenceEvent.Thanks); }   // L5391
            }
            Enter(ctx, (int)StateFor(present, coat));
        }

        private static PresenceState StateFor(bool present, bool coat) => present ? (coat ? PresenceState.Open : PresenceState.Present) : PresenceState.Empty;

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteBool("present", Present);
            w.WriteBool("coat", CoatOn);
            w.WriteDouble("for", _presentFor);
            w.WriteLong("count", _count);
            w.WriteLong("asked", _askedFor);
            w.WriteBool("thanked", _thanked);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            Present = r.ReadBool("present");
            CoatOn = r.ReadBool("coat");
            _presentFor = r.ReadDouble("for");
            _count = r.ReadLong("count");
            _askedFor = r.ReadLong("asked");
            _thanked = r.ReadBool("thanked");
        }
    }
}
