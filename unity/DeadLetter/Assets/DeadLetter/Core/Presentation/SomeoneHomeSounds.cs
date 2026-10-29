using System;
using System.Collections.Generic;
using DeadLetter.Core.Audio;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Folding;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl18;
using DeadLetter.Core.Scenes.Dl19;

namespace DeadLetter.Core.Presentation
{
    /// <summary>
    /// Chapter 2's sounds (region 7, DL-18 and DL-19; issue #57), for <see cref="ChapterSounds"/> to queue on its own queue
    /// and seed, as <see cref="AttendanceSounds"/> does for chapter 1. No prototype: each sound cites its scene doc's §8
    /// ("Music and sound"), §3 or §11, and uses the existing bank (docs/unity/audio_inventory.md). Where a dedicated
    /// asset is wanted, the stand-in played here is listed there under "Chapter 2: wanted". Read from the step:
    /// <list type="bullet">
    /// <item>the scenes' own cues (<see cref="ChapterSim.Cues"/>: they carry no <c>sound:</c> prefix, so
    /// <see cref="ChapterSounds"/> ignores them): the bench's rock and slide, the chain's clanks, the alarm clock, the
    /// sketch, the drip tube, the lurch and the rock, <c>Settle</c>;</item>
    /// <item>the mechanisms' events and transitions (<see cref="MechanismGraph.Log"/>): the leaves setting off, stopping
    /// and meeting the quilt or D-17; the jack's clunk, ratchet clicks, bind and heave; the pins' draw, strain, clink,
    /// take, seat and chatter; the half landing's drops;</item>
    /// <item>polls: the strained pin's creak (or its rattle, slack) on the platform's slow sway, the jack's wheels while
    /// it rolls, and the relay boxes' click every <see cref="SomeoneHomeLights.RelayPeriod"/> s in step with their pilot lamps.</item>
    /// </list>
    /// The half landing's <c>dl19.bang</c> cue is not read: its <see cref="HalfLandingEvent.Drop"/> says what it landed on.
    /// <c>held</c> and <c>witness</c> are music and a shot, not sounds. Allocation-free per step.
    /// </summary>
    public sealed class SomeoneHomeSounds
    {
        /// <summary>The drip tube (DL-19 §3: 363.3–363.5) and how far its tick is heard (as the depot's drops, <see cref="ChapterSounds.DripHear"/>).</summary>
        public const double DripX = 363.4, DripHear = ChapterSounds.DripHear;
        /// <summary>The bracket (§3: post at 363.65), where the bent pin creaks; heard within this.</summary>
        public const double PinX = 363.65, PinHear = 6;
        /// <summary>"The pin's creak in time with a slow sway" (§8): one creak (or rattle, slack) per sway.</summary>
        public const double SwaySeconds = 3.2;
        /// <summary>The relay boxes' click is heard within this of a box.</summary>
        public const double RelayHear = 6;
        /// <summary>The alarm clock rings 2 s (§6): a trill every 0.55 s while it rings (as DL-11's doorbell, audio_inventory "alarmBell").</summary>
        public const double RingEvery = 0.55;
        /// <summary>The spare seats with "a clean double click" (BracketPinsEvent.Seated): the second this long after the first.</summary>
        public const double DoubleClick = 0.12;
        /// <summary>The jack's wheels squeak as a pushed thing's do (<see cref="ChapterSounds.SqueakAbove"/>, <see cref="ChapterSounds.PushSqueakRate"/>).</summary>
        public const double SqueakAbove = ChapterSounds.SqueakAbove, SqueakRate = ChapterSounds.PushSqueakRate;

        private static readonly string KClank = SfxKeys.Simple["clank"], KThud = SfxKeys.Simple["thud"], KClunk = SfxKeys.Simple["clunk"],
            KTap = SfxKeys.Simple["tap"], KLand = SfxKeys.Simple["land"], KScrape = SfxKeys.Simple["scrape"], KStrain = SfxKeys.Simple["strain"],
            KClick = SfxKeys.Simple["click"], KClack = SfxKeys.Simple["clack"], KGateTick = SfxKeys.Simple["gateTick"],
            KPawlClatter = SfxKeys.Simple["pawlClatter"], KLurch = SfxKeys.Simple["lurch"], KAlarmBell = SfxKeys.Simple["alarmBell"],
            KDrip = SfxKeys.Simple["drip"], KSqueak = SfxKeys.Simple["squeak"],
            KCreakBed = SfxKeys.Creak(0.8), KCreakRock = SfxKeys.Creak(0.5), KCreakPin = SfxKeys.Creak(0.6),
            KChainBench = SfxKeys.Chain(1.2), KRattleChain = SfxKeys.Rattle(0.5), KRattlePin = SfxKeys.Rattle(0.5),
            KServoSettle = SfxKeys.Servo(0.3, 300, 420), KPaper = SfxKeys.Curio("paper");

        private readonly ChapterSim _sim;
        private readonly SfxQueue _q;
        private readonly AudioRng _rng;
        private readonly FoldingLeaf _bed, _bench;
        private readonly RatchetJack _jack;
        private readonly BracketPins _pins;
        private readonly HalfLanding _landing;
        private readonly Dictionary<string, FoldingLeaf> _leaves = new Dictionary<string, FoldingLeaf>(StringComparer.Ordinal);
        private FoldingLeafState _bedWas, _benchWas;
        private double _lastNow = double.NaN;

        public SomeoneHomeSounds(ChapterSim sim, SfxQueue queue, AudioRng rng)
        {
            _sim = sim ?? throw new ArgumentNullException(nameof(sim));
            _q = queue ?? throw new ArgumentNullException(nameof(queue));
            _rng = rng ?? throw new ArgumentNullException(nameof(rng));
            sim.Graph.TryGet(Dl18Scene.Bed.Value, out _bed);
            sim.Graph.TryGet(Dl18Scene.Bench.Value, out _bench);
            sim.Graph.TryGet(Dl19Scene.Jack.Value, out _jack);
            sim.Graph.TryGet(Dl19Scene.Pins.Value, out _pins);
            sim.Graph.TryGet(Dl19Scene.Landing.Value, out _landing);
            if (_bed != null) _leaves[Dl18Scene.Bed.Value] = _bed;
            if (_bench != null) _leaves[Dl18Scene.Bench.Value] = _bench;
            OnPlaced();
        }

        /// <summary>A new world: the leaves start from where they are, the clocks from the next step.</summary>
        public void OnPlaced()
        {
            _lastNow = double.NaN;
            if (_bed != null) _bedWas = _bed.State;
            if (_bench != null) _benchWas = _bench.State;
        }

        /// <summary>After each step (from <see cref="ChapterSounds.Step"/>, with its clock and dt).</summary>
        public void Step(double now, double dt)
        {
            double was = double.IsNaN(_lastNow) || now < _lastNow ? double.NaN : _lastNow;
            _lastNow = now;
            ReadCues(_sim.Cues, now);
            ReadLog(_sim.Graph.Log);
            Poll(was, now, dt);
        }

        // ---- The scenes' cues -----------------------------------------------------------------------------------------------
        private void ReadCues(IReadOnlyList<Cue> cues, double now)
        {
            for (int i = 0; i < cues.Count; i++)
            {
                CueId id = cues[i].Id;
                if (id == Dl18SlideAct.RockCue) _q.Play(KCreakRock);                                   // it rocks on the quilt (DL-18 §3 port)
                else if (id == Dl18SlideAct.SlideCue) { _q.Play(KScrape, 0.5); _q.Play(KLand, 0.5); }  // and slides him off with a soft bump
                else if (id == Dl18Rules.ChainClank) { _q.Play(KClank); _q.Play(KRattleChain); }      // a tug at the Works door's chain (§11 WorksDoor)
                else if (id == Dl18Rules.ClockRing)                                                    // rings 2 s (§6): a trill every 0.55 s
                {
                    _q.Play(KAlarmBell);
                    for (double t = RingEvery; t < Dl18Rules.RingSeconds - 0.1; t += RingEvery) _q.PlayAfter(now, t, KAlarmBell);
                }
                else if (id == Dl18Rules.ClockStill) _q.Play(KTap);                                    // the pat that stills it
                else if (id == Dl18Rules.SketchLook) _q.Play(KPaper);                                  // the close look (§6)
                else if (id == Dl19Rules.Drip)                                                         // the drip tube's tick, once a minute (DL-19 §8)
                {
                    double v = 1 - Math.Abs(_sim.X - DripX) / DripHear;
                    if (v > 0) _q.Play(KDrip, v, DripX);
                }
                else if (id == Dl19Rules.Lurch) _q.Play(KLurch);                                       // it lurches 3 cm and springs back (§3, §8 "Impacts")
                else if (id == Dl19Rules.Rock) { _q.Play(KLurch); _q.Play(KClank); }                  // on the stops it rocks toward the shaft and clangs
                else if (id == Dl19Rules.Settle) _q.Play(KServoSettle, 0.6);                          // a small servo whine on the knee dip, quiet (§8)
            }
        }

        // ---- Mechanisms ---------------------------------------------------------------------------------------------------
        private void ReadLog(MechanismLog log)
        {
            for (int i = 0; i < log.Count; i++)
            {
                MechanismEvent e = log[i];
                if (e.Id.IsNone) continue;
                string id = e.Id.Value;
                if (_leaves.TryGetValue(id, out FoldingLeaf leaf)) OnLeaf(leaf, e);
                else if (_jack != null && id == Dl19Scene.Jack.Value) OnJack(e);
                else if (_pins != null && id == Dl19Scene.Pins.Value) OnPins(e);
                else if (_landing != null && id == Dl19Scene.Landing.Value) OnLanding(e);
            }
        }

        /// <summary>The bed's springs and the bench's chains as a leaf sets off from rest; a clunk at its stop; the quilt's thump (DL-18 §8).</summary>
        private void OnLeaf(FoldingLeaf leaf, in MechanismEvent e)
        {
            bool bed = ReferenceEquals(leaf, _bed);
            if (e.Kind == MechanismEventKind.Event)
            {
                if (e.Code != (int)FoldingLeafEvent.Met) return;
                if (e.Index == 0) _q.Play(KThud, 0.35);                                                // the other leaf on the heaped quilt: a soft thump
                else _q.Play(KTap, 0.6);                                                               // it meets D-17 and waits: no crushing
                return;
            }
            var was = bed ? _bedWas : _benchWas;
            var now = (FoldingLeafState)e.Code;
            if (bed) _bedWas = now; else _benchWas = now;
            bool fromRest = was == FoldingLeafState.Down || was == FoldingLeafState.Folded || was == FoldingLeafState.Propped;
            if ((now == FoldingLeafState.Unfolding || now == FoldingLeafState.Folding) && fromRest)
                _q.Play(bed ? KCreakBed : KChainBench);
            else if (now == FoldingLeafState.Down || now == FoldingLeafState.Folded)
                _q.Play(KClunk, bed ? 0.7 : 0.6);
        }

        /// <summary>The jack (DL-19 §3, §8): its wheels drop into the pocket; a click per notch; the top of travel; a heave that moves nothing.</summary>
        private void OnJack(in MechanismEvent e)
        {
            if (e.Kind != MechanismEventKind.Event) return;
            switch (e.Code)
            {
                case (int)RatchetJackEvent.Clunk: _q.Play(KClunk); break;
                case (int)RatchetJackEvent.Click: _q.Play(KGateTick, e.Value > 0 ? 0.8 : 0.6, _jack.SaddleX); break;
                case (int)RatchetJackEvent.Bind: _q.Play(KClunk, 0.5); _q.Play(KStrain, 0.6); break;
                case (int)RatchetJackEvent.Heave: _q.Play(KStrain); break;
            }
        }

        /// <summary>The pins (DL-19 §3 "The pins", §11 BentPin and SparePin).</summary>
        private void OnPins(in MechanismEvent e)
        {
            if (e.Kind != MechanismEventKind.Event) return;
            switch (e.Code)
            {
                case (int)BracketPinsEvent.Draw: _q.Play(KScrape); break;                              // it slides part-way and bites
                case (int)BracketPinsEvent.Strain: _q.Play(KStrain); break;                            // a strain; nothing moves
                case (int)BracketPinsEvent.Clink: _q.Play(KClack, 0.4, PinX); break;                   // into the tin cup (stand-in: mech_pin_clink wanted)
                case (int)BracketPinsEvent.Taken: _q.Play(KTap); break;                                // the spare out of its clip
                case (int)BracketPinsEvent.Seated:                                                     // "a clean double click"
                    _q.Play(KClick, 1, PinX);
                    _q.PlayAfter(_sim.Clock, DoubleClick, KClick, 1, PinX);
                    break;
                case (int)BracketPinsEvent.Chatter: _q.Play(KPawlClatter, 1, PinX); break;             // against the lug; he keeps it
            }
        }

        /// <summary>The half landing's drops (§8 "Impacts": a bang): onto the stops, the bent pin, the jack's saddle.</summary>
        private void OnLanding(in MechanismEvent e)
        {
            if (e.Kind != MechanismEventKind.Event || e.Code != (int)HalfLandingEvent.Drop) return;
            double v = Math.Max(0.5, Math.Min(1, e.Value / 1.2));
            switch (e.Index)
            {
                case 0: _q.Play(KClank, v, PinX); _q.Play(KThud, 0.5 * v, PinX); break;
                case 1: _q.Play(KClank, v, PinX); break;
                default: _q.Play(KClunk, v, PinX); break;
            }
        }

        // ---- Polls --------------------------------------------------------------------------------------------------------
        private void Poll(double was, double now, double dt)
        {
            if (_sim.Region != Dl18Lane.Region) return;
            double x = _sim.X;
            if (!double.IsNaN(was))
            {
                if (Crossed(was, now, SomeoneHomeLights.RelayPeriod))                                 // the relay boxes' click, with their pilot lamps
                {
                    double v = 0, at = double.NaN;
                    foreach (double rx in SomeoneHomeLights.RelayX)
                    {
                        double k = 1 - Math.Abs(x - rx) / RelayHear;
                        if (k > v) { v = k; at = rx; }
                    }
                    if (v > 0) _q.Play(KClick, 0.5 * v, at);
                }
                if (_pins != null && _pins.Sound != PinSound.Quiet && Crossed(was, now, SwaySeconds))   // the pin, on the sway
                {
                    double v = 1 - Math.Abs(x - PinX) / PinHear;
                    if (v > 0) _q.Play(_pins.Sound == PinSound.Creak ? KCreakPin : KRattlePin, v, PinX);
                }
            }
            if (_jack != null && Math.Abs(_jack.Velocity) > SqueakAbove && _rng.NextDouble() < dt * SqueakRate) _q.Play(KSqueak, 1, _jack.X);
        }

        /// <summary>The clock passed a multiple of <paramref name="period"/> this step.</summary>
        private static bool Crossed(double was, double now, double period) => Math.Floor(now / period) > Math.Floor(was / period);
    }
}
