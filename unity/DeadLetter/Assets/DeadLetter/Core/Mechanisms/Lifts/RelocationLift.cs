using System;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Save;
using DeadLetter.Core.Simulation;

namespace DeadLetter.Core.Mechanisms.Lifts
{
    /// <summary>The prototype's <c>uo.phase</c> (L4629–L4636).</summary>
    public enum RelocationLiftState
    {
        Idle,
        Up,
        /// <summary>Sent up from the lobby: waits 3 s at the top, then comes back down.</summary>
        Top,
        Down,
        /// <summary>Sent up from the counterweight's panel: the car is gone for good and he is down the shaft.</summary>
        Gone,
    }

    public enum RelocationLiftEvent
    {
        /// <summary>UP pressed and it goes (clunk, chain, shake 0.15; L4585). Index 1 = from the counterweight: he rides it down, the <c>ringc</c> moment starts (L4588).</summary>
        Go,
        /// <summary>UP pressed and it will not go (L4590). Index 1 = the car is loaded (gate open or not idle); 0 = empty: Pips flash <c>car10</c>.</summary>
        Buzz,
        /// <summary>It stopped at the end of a run (clunk; L4631, L4635). Value = shake: 0.35 when it landed with him, 0.12 otherwise, 0 at the bottom.</summary>
        Arrive,
        /// <summary>A random squeak while it moves up or down (<c>Math.random() &lt; dt · 1.5</c>, L4637).</summary>
        Squeak,
    }

    public sealed class RelocationLiftParams
    {
        /// <summary>The car's floor plate (an <see cref="ILoad"/>): it has a passenger while Load &gt; 0 (<c>uo.loaded</c>, L4549).</summary>
        public MechanismId CarPlate;
        /// <summary>Optional: the car's gate (an <see cref="IPositionSource"/>, 0 open … 1 shut; <c>uo.gate</c>, L4620–L4624): the
        /// <c>dl10.carGate</c> <see cref="Actuators.Door"/> (<see cref="Plates.PlateOutputs.Dl10CarGate"/>). None: always shut.</summary>
        public MechanismId CarGate;
        /// <summary>The deck: the counterweight's top at rest; he rides it down to Deck − Travel (L4600).</summary>
        public double Deck = 1.6;
        /// <summary><c>UO.travel</c> 1.6 m, <c>UO.ride</c> 5.5 s (smoothstep), 3 s at the top (L3461, L4629–L4635).</summary>
        public double Travel = 1.6, RideTime = 5.5, TopHold = 3;
        /// <summary>Gone (car up, counterweight down) past this checkpoint (resetCh1, L4101).</summary>
        public string GoneAfter;
        /// <summary>Squeaks per second while moving (L4637), drawn from a <see cref="SimRng"/> seeded with <see cref="Seed"/> on Reset.</summary>
        public double SqueakRate = 1.5;
        public ulong Seed = 0x0D11_0A10_4637UL;

        /// <summary>DL-10: the relocation lift and its counterweight (<c>UO</c>, L3455–L3461; L4526–L4675).</summary>
        public static RelocationLiftParams Dl10Lift() => new RelocationLiftParams
        {
            CarPlate = "dl10.carPlate",
            CarGate = "dl10.carGate",                          // the Door the plate triggers: shut 0.8 s + 1.4 s after the case (§4.13a)
            GoneAfter = "ringc",
        };
    }

    /// <summary>
    /// The DL-10 relocation lift (<c>dl10.lift</c>, with <c>dl10.counterweight</c>; §4.13f; <c>updateUpOnly</c>
    /// L4613–L4636, the UP press L4580–L4595). It only goes up, and only with a passenger in the car and the gate shut:
    /// sent from the lobby it rises over 5.5 s, waits 3 s and comes down; sent from the counterweight's own panel it
    /// leaves for good and he rides the counterweight down the shaft to ring C.
    /// Signals: <see cref="Position"/> = the car's rise d, metres (0 … 1.6); <see cref="ILiftRide"/>: the counterweight,
    /// FloorY = Deck − d, carrying him while it moves with him on it (<c>game.y = DECK − uo.d</c>, L4600).
    /// Inputs: <see cref="PressUp"/> from the button acts at PressButtonHigh f16 (L4582); <see cref="FollowCue"/> from the
    /// cue clock while he rides (the car's climb is the <c>ringc</c> cue's, L4616–L4617).
    /// The random squeak (L4637) draws from its own <see cref="SimRng"/>. The gauges, lamps and ropes (L4638–L4665) are view.
    /// </summary>
    public sealed class RelocationLift : Lift
    {
        private const int PressNone = 0, PressLobby = 1, PressCounterweight = 2;

        private readonly RelocationLiftParams _p;
        private ILoad _plate;
        private IPositionSource _gate;
        private double _t, _cue;
        private bool _riding, _hasCue;
        private int _press;
        private SimRng _rng;

        public RelocationLift(MechanismId id, RelocationLiftParams p) : base(id) { _p = p; _rng = SimRng.Xorshift(p.Seed); }

        public RelocationLiftState State => (RelocationLiftState)StateCode;
        /// <summary>The car's rise, metres (<c>uo.d</c>).</summary>
        public override double Position => D;
        public double D { get; private set; }
        public double CarY => _p.Deck + D;
        public double CounterweightY => _p.Deck - D;
        /// <summary>He was sent down on the counterweight (<c>uo.riding</c>).</summary>
        public bool Riding => _riding;
        public bool Loaded => _plate.Load > 0;
        public bool GateShut => _gate == null || _gate.Position >= 1;
        /// <summary>UP will send it (<c>ready</c>, L4660; the UP lamps).</summary>
        public bool Ready => Loaded && GateShut && State == RelocationLiftState.Idle;
        /// <summary>At rest at the bottom: the counterweight's panel answers (<c>uo.d &lt; 0.01 &amp;&amp; idle</c>, L4236).</summary>
        public bool AtRest => State == RelocationLiftState.Idle && D < 0.01;

        /// <summary>UP pressed at PressButtonHigh f16 (L4582): from the lobby, or from the counterweight's panel (he rides).</summary>
        public void PressUp(bool fromCounterweight) => _press = fromCounterweight ? PressCounterweight : PressLobby;

        /// <summary>This tick's <c>Music.momentTime('ringc')</c>, seconds; call before the graph steps while he rides.</summary>
        public void FollowCue(double t) { _cue = t; _hasCue = true; }

        public override void Link(MechanismLinker link)
        {
            _plate = link.Read<ILoad>(_p.CarPlate) ?? throw new InvalidOperationException(Id + " needs a CarPlate.");
            _gate = link.Read<IPositionSource>(_p.CarGate);
        }

        public override void Reset(in Checkpoint cp)
        {
            _rng = SimRng.Xorshift(_p.Seed);   // the same checkpoint replays the same sounds and crates
            bool gone = cp.Past(_p.GoneAfter);                                                     // L4101
            D = gone ? _p.Travel : 0;
            Init((int)(gone ? RelocationLiftState.Gone : RelocationLiftState.Idle));
            _t = 0;
            _riding = false;
            _press = PressNone;
            _cue = 0; _hasCue = false;
            _rng.Reseed((long)_p.Seed);
            InitFloor(CounterweightY);
        }

        public override void Step(in StepContext ctx)
        {
            double dt = ctx.Dt;
            // The UP press (#4).
            if (_press != PressNone)
            {
                if (Ready)                                                                        // L4584
                {
                    Enter(ctx, (int)RelocationLiftState.Up); _t = 0;
                    _riding = _press == PressCounterweight;
                    Emit(ctx, (int)RelocationLiftEvent.Go, _riding ? 1 : 0);
                }
                else Emit(ctx, (int)RelocationLiftEvent.Buzz, Loaded ? 1 : 0);                    // L4590
            }
            _press = PressNone;

            // updateUpOnly (#7).
            _t += dt;                                                                             // L4615
            if (_riding && _hasCue && State == RelocationLiftState.Up) _t = Math.Max(_t - dt, _cue);   // L4617
            _hasCue = false;
            double T = _p.RideTime;
            switch (State)
            {
                case RelocationLiftState.Up:
                    D = _p.Travel * Smooth.Step(Math.Min(1, _t / T));                             // L4630
                    if (Reached(_t, T))
                    {
                        Enter(ctx, (int)(_riding ? RelocationLiftState.Gone : RelocationLiftState.Top)); _t = 0;
                        Emit(ctx, (int)RelocationLiftEvent.Arrive, 0, _riding ? 0.35 : 0.12);      // L4631
                    }
                    break;
                case RelocationLiftState.Top:
                    if (After(_t, _p.TopHold)) { Enter(ctx, (int)RelocationLiftState.Down); _t = 0; }   // L4632
                    break;
                case RelocationLiftState.Down:
                    D = _p.Travel * (1 - Smooth.Step(Math.Min(1, _t / T)));                       // L4634
                    if (Reached(_t, T)) { Enter(ctx, (int)RelocationLiftState.Idle); D = 0; Emit(ctx, (int)RelocationLiftEvent.Arrive); }   // L4635
                    break;
            }
            if ((State == RelocationLiftState.Up || State == RelocationLiftState.Down) && _rng.Chance(dt * _p.SqueakRate))
                Emit(ctx, (int)RelocationLiftEvent.Squeak);                                      // L4637
            MoveFloor(ctx, CounterweightY);
            Carrying = _riding && State == RelocationLiftState.Up;
        }

        protected override void WriteLift(ISnapshotWriter w)
        {
            w.WriteDouble("d", D);
            w.WriteDouble("t", _t);
            w.WriteDouble("cue", _cue);
            w.WriteBool("hasCue", _hasCue);
            w.WriteBool("riding", _riding);
            w.WriteLong("press", _press);
            _rng.Write(w, "rng");
        }

        protected override void ReadLift(ISnapshotReader r)
        {
            D = r.ReadDouble("d");
            _t = r.ReadDouble("t");
            _cue = r.ReadDouble("cue");
            _hasCue = r.ReadBool("hasCue");
            _riding = r.ReadBool("riding");
            _press = (int)r.ReadLong("press");
            _rng.Read(r, "rng");
        }
    }
}
