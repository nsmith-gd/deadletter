using System;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Plates
{
    /// <summary>The scale's reading (L4891). Served latches it at Person.</summary>
    public enum WeighReading { Empty, Under, Person, Over }

    public enum WeighState { Weighing, Served }

    public enum WeighEvent
    {
        /// <summary>The reading changed; Index = the new <see cref="WeighReading"/> (L4892–L4898). Value = delay, s, of its sound:
        /// Under buzzes at +0.35 s; Over clanks now and rings the alarm with a 0.2 shake at +0.3 s; Person clicks now (not once served).</summary>
        Reading,
        /// <summary>A person held more than 1.0 s: ratchet and chain (L4899).</summary>
        Served,
        /// <summary>The needle crossed one of the dial's 20° detents (L4904; the view plays it only in region 2).</summary>
        Tick,
        /// <summary>The needle swung into the PERSON band: the hatch jerks up (ratchet now, clunk at +0.26 s; L4909).</summary>
        Twitch,
    }

    public sealed class WeighScaleParams
    {
        public PlateSensorParams Sensor = new PlateSensorParams();
        /// <summary>Bands: Empty below EmptyBelow, Under below UnderBelow, Person up to PersonMax, else Over (L4891).</summary>
        public double EmptyBelow = 0.05, UnderBelow = 0.85, PersonMax = 1.15;
        /// <summary>Person held more than this → served (L4899).</summary>
        public double ServeAfter = 1.0;
        /// <summary>Needle degrees (<c>RH5.needle</c>, L3453): a person's weight reads PersonDeg; the target is PersonDeg · min(W, MaxW).</summary>
        public double PersonDeg = -140, UnderDeg = -28, OverDeg = -236, MaxW = 1.75;
        /// <summary>Damped spring: <c>nv += ((target − needle)·K − nv·Damping)·dt</c> (L4903).</summary>
        public double SpringK = 30, Damping = 7;
        public double DetentDeg = 20;
        /// <summary>Twitch when the needle enters ±TwitchBand of PersonDeg, at most every TwitchCooldown s; the hatch jerk lasts TwitchTime s and lifts TwitchLift m (L4908–L4920).</summary>
        public double TwitchBand = 22, TwitchCooldown = 1.2, TwitchTime = 0.9, TwitchLift = 0.14;
        /// <summary>Plate dip easing rate /s (L4913).</summary>
        public double DipRate = 8;
        public double UnderSoundDelay = 0.35, OverSoundDelay = 0.3;
        public string ServedAfter;

        /// <summary>
        /// DL-05 weigh-in, plate 53.85–55.75: body (half 0.83) share 1, drum (half 0.225) share 1.7, D-17 0.2 below y
        /// 0.05 (L3451–L3453, L4886–L4890); served from <c>hatch</c> (L4098).
        /// </summary>
        public static WeighScaleParams Dl05WeighIn() => new WeighScaleParams
        {
            Sensor = new PlateSensorParams
            {
                X0 = 13 + 40.85, X1 = 13 + 42.75,                                    // RH5.plate
                PlayerX0 = 13 + 40.85, PlayerX1 = 13 + 42.75, PlayerMaxY = 0.05, PlayerShare = 0.2,
                Terms = new[] { PlateTerm.Overlap("dl05.body", 0.83, 1), PlateTerm.Overlap("dl05.drum", 0.225, 1.7) },   // RH5.bodyHalf
            },
            ServedAfter = "hatch",
        };
    }

    /// <summary>
    /// DL-05's weigh-in (§4.13a): a banded reading of the weighed shares; PERSON held 1.0 s serves (latched). The
    /// needle swings on a damped spring and ticks through detents; entering the PERSON band twitches the hatch.
    /// L4878–L4921. Signals: <see cref="Engaged"/> = served (the hatch and the flag are <see cref="Door"/>s, see
    /// <see cref="PlateOutputs"/>), <see cref="Load"/> = W, <see cref="Position"/> = needle degrees.
    /// </summary>
    public sealed class WeighScale : Mechanism, IEngageable, ILoad, IPositionSource
    {
        private readonly WeighScaleParams _p;
        private readonly PlateSensor _sensor;
        private double _since, _nv, _sinceTwitch;
        private bool _inBand;

        public WeighScale(MechanismId id, WeighScaleParams p) : base(id)
        {
            _p = p ?? throw new ArgumentNullException(nameof(p));
            _sensor = new PlateSensor(p.Sensor);
        }

        public WeighState State => (WeighState)StateCode;
        public bool Engaged => State == WeighState.Served;
        public WeighReading Reading { get; private set; }
        /// <summary>W, in a person's weights.</summary>
        public double Load { get; private set; }
        /// <summary>Needle, degrees (negative is clockwise on the dial).</summary>
        public double Needle { get; private set; }
        public double Position => Needle;
        /// <summary>The plate's dip, 0..1 (× 0.01 m in the view, L4914).</summary>
        public double Dip { get; private set; }
        /// <summary>Seconds the current reading has held.</summary>
        public double ReadingFor => _since;
        /// <summary>The hatch's extra lift from the twitch, metres (L4920): added to the hatch door's height.</summary>
        public double TwitchOffset
        {
            get
            {
                if (Engaged) return 0;
                double tw = Math.Max(0, 1 - _sinceTwitch / _p.TwitchTime);
                return tw > 0 ? _p.TwitchLift * Math.Sin(Math.PI * (1 - tw)) : 0;
            }
        }

        public override void Link(MechanismLinker link) => _sensor.Link(link);

        /// <summary><c>rh.served = past(hatch)</c>; reading and needle PERSON once served, else empty at 0 (L4097–L4098).</summary>
        public override void Reset(in Checkpoint cp)
        {
            bool served = cp.Past(_p.ServedAfter);
            Init((int)(served ? WeighState.Served : WeighState.Weighing));
            Reading = served ? WeighReading.Person : WeighReading.Empty;
            Needle = served ? _p.PersonDeg : 0;
            Load = _sensor.Load(false);
            _nv = 0; Dip = 0; _since = 0;
            _sinceTwitch = 1e3;                                                       // twitchAt ?? −9
            _inBand = false;
        }

        public override void Step(in StepContext ctx)
        {
            double dt = ctx.Dt;
            bool served = Engaged;
            Load = _sensor.Load(_sensor.PlayerOn(ctx.Player));
            double w = Load;
            var reading = served ? WeighReading.Person : w < _p.EmptyBelow ? WeighReading.Empty : w < _p.UnderBelow ? WeighReading.Under
                : w <= _p.PersonMax ? WeighReading.Person : WeighReading.Over;     // L4891
            _since += dt;
            _sinceTwitch += dt;
            if (reading != Reading)                                                   // L4892–L4898
            {
                Reading = reading; _since = 0;
                double delay = reading == WeighReading.Under ? _p.UnderSoundDelay : reading == WeighReading.Over ? _p.OverSoundDelay : 0;
                if (reading != WeighReading.Person || !served) Emit(ctx, (int)WeighEvent.Reading, (int)reading, delay);
            }
            if (reading == WeighReading.Person && !served && _since > _p.ServeAfter)          // L4899
            {
                served = true;
                Enter(ctx, (int)WeighState.Served);
                Emit(ctx, (int)WeighEvent.Served);
            }

            double target = served ? _p.PersonDeg : _p.PersonDeg * Math.Min(w, _p.MaxW);   // L4901
            double was = Needle;
            _nv += ((target - Needle) * _p.SpringK - _nv * _p.Damping) * dt;               // L4903
            Needle += _nv * dt;
            if (Math.Floor(was / _p.DetentDeg) != Math.Floor(Needle / _p.DetentDeg)) Emit(ctx, (int)WeighEvent.Tick);   // L4904

            bool inBand = Math.Abs(Needle - _p.PersonDeg) < _p.TwitchBand;                  // L4908–L4910
            if (inBand && !_inBand && !served && _sinceTwitch > _p.TwitchCooldown) { _sinceTwitch = 0; Emit(ctx, (int)WeighEvent.Twitch); }
            _inBand = inBand;

            Dip += ((reading == WeighReading.Empty ? 0 : 1) - Dip) * (1 - Smooth.DecayFactor(_p.DipRate, dt));   // L4913
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteLong("reading", (long)Reading);
            w.WriteDouble("load", Load);
            w.WriteDouble("needle", Needle);
            w.WriteDouble("nv", _nv);
            w.WriteDouble("dip", Dip);
            w.WriteDouble("since", _since);
            w.WriteDouble("twitch", _sinceTwitch);
            w.WriteBool("inBand", _inBand);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            Reading = (WeighReading)r.ReadLong("reading");
            Load = r.ReadDouble("load");
            Needle = r.ReadDouble("needle");
            _nv = r.ReadDouble("nv");
            Dip = r.ReadDouble("dip");
            _since = r.ReadDouble("since");
            _sinceTwitch = r.ReadDouble("twitch");
            _inBand = r.ReadBool("inBand");
        }
    }
}
