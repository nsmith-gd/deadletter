using System;
using DeadLetter.Core.Audio;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Cycles;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl03;
using DeadLetter.Core.Scenes.Dl04;
using DeadLetter.Core.Scenes.Dl18;
using DeadLetter.Core.Streaming;

namespace DeadLetter.Core.Presentation
{
    /// <summary>
    /// The prototype's <c>Ambience</c> module as the game drives it (port_architecture §4.24–§4.25; index.html
    /// <c>sceneAmbience</c>/<c>updateAmbience</c> L8145–L8168, <c>Ambience.update</c> L1196–L1209, <c>EMITTERS</c>
    /// L6577–L6598): the bed each region wants (<see cref="AmbienceRules"/> over <see cref="ChapterPresenter.Ambience"/>) and
    /// every placed emitter, stepped here from the sim's state (his x, region, deck, the named conditions) so the runtime
    /// only plays what this decides: <see cref="Gain"/> for a loop, <see cref="Blip"/> for a drip, tick or fan. The same
    /// state answers the tannoys' conditions (<see cref="Condition"/>). Allocation-free per frame.
    /// </summary>
    public sealed class AmbienceWorld
    {
        /// <summary><c>game.released</c>: the DL-01 latch has let the shutter go (L1675).</summary>
        public const string Released = "released";

        private readonly ChapterSim _sim;
        private readonly ChapterPresenter _presenter;
        private readonly EmitterDef[] _defs;
        private readonly EmitterState[] _states;
        private readonly EmitterStep[] _steps;
        private readonly Latch _latch;
        private readonly RacksReveal _reveal;
        // Chapter 1's conditions (null elsewhere).
        private readonly CycleClock _lesson;
        private readonly CycleBrake _lessonBrake;
        private readonly Door _restDoor;
        private readonly SeatRow _seats;

        public AmbienceWorld(ChapterSim sim, ChapterPresenter presenter = null, EmitterDef[] emitters = null, uint seed = 41)
        {
            _sim = sim ?? throw new ArgumentNullException(nameof(sim));
            _presenter = presenter ?? new ChapterPresenter(sim);
            _defs = emitters ?? PrologueEmitters.All;
            _states = new EmitterState[_defs.Length];
            _steps = new EmitterStep[_defs.Length];
            for (int i = 0; i < _defs.Length; i++) _states[i] = new EmitterState(seed + (uint)i * 7919u);
            sim.Graph.TryGet("dl01.latch", out _latch);
            sim.Graph.TryGet("dl13.lesson", out _lesson);
            sim.Graph.TryGet("dl13.brake", out _lessonBrake);
            sim.Graph.TryGet("dl14a.door", out _restDoor);
            sim.Graph.TryGet("dl15.seats", out _seats);
            _reveal = sim.Def.Scene(Dl03Scene.Id) != null || sim.Def.Scene(Dl04Scene.Id) != null ? sim.Shared<RacksReveal>() : null;
        }

        public int Count => _defs.Length;
        public EmitterDef this[int i] => _defs[i];

        /// <summary><c>game.region</c>.</summary>
        public int Region => _sim.Region;
        /// <summary><c>game.upper</c>: on DL-07's gallery (never in the ported scenes yet: <c>ReturnToSender06.Upper</c>).</summary>
        public bool Upper => false;
        /// <summary>His lane x, as the sim reports it (a scene act's pose included).</summary>
        public double X => _sim.X;

        /// <summary>The named condition an emitter or a tannoy waits on (null or empty: none).</summary>
        public bool Condition(string name)
        {
            if (string.IsNullOrEmpty(name)) return true;
            switch (name)
            {
                case Released: return _latch != null && _latch.Engaged;
                case PrologueEmitters.Revealed: return _reveal != null && _reveal.Revealed;
                // Chapter 1: the lesson's clockwork runs while the lesson does and is not braked (L6595–L6596); rest hour's
                // tannoy until DL-14a's door opens (!f14a.open, L6569); the bell once the class is dismissed (L6570).
                case PrologueEmitters.LessonRunning: return _lesson != null && _lesson.On && !(_lessonBrake != null && _lessonBrake.Engaged);
                case VoiceCatalog.RestDoorShut: return _restDoor != null && _restDoor.State == DoorState.Closed;
                case VoiceCatalog.Dismissed: return _seats != null && _seats.Engaged;
                // Chapter 2: DL-18's alarm clock ticks, except while it rings (its act, §6).
                case SomeoneHomeEmitters.ClockTicking: return !(_sim.Act != null && _sim.Act.Kind == Dl18Rules.AlarmClock);
                default: return false;
            }
        }

        /// <summary>The bed <c>sceneAmbience()</c> wants now (L8147–L8162).</summary>
        public AmbienceChoice Bed => AmbienceRules.SceneAmbience(_presenter.Ambience());

        /// <summary>The inputs of the bed (<see cref="AmbienceRules.Apply"/> takes them).</summary>
        public AmbienceContext Context => _presenter.Ambience();

        /// <summary><c>Ambience.update</c> for every emitter, at <paramref name="now"/> (audio clock) after <paramref name="dt"/>.</summary>
        public void Update(double now, double dt)
        {
            double px = X;
            int region = Region;
            bool upper = Upper;
            for (int i = 0; i < _defs.Length; i++)
                _steps[i] = _states[i].Update(_defs[i], px, region, upper, Condition(_defs[i].Condition), now, dt);
        }

        /// <summary>Emitter <paramref name="i"/>'s gain now (glided), 0–1.</summary>
        public double Gain(int i) => _states[i].Gain;
        /// <summary>Its graph exists (in reach, or fading out for up to 3 s).</summary>
        public bool Live(int i) => _states[i].Live;
        /// <summary>An event kind fires a blip this frame.</summary>
        public bool Blip(int i) => _steps[i].Blip;
        /// <summary>It just went out of reach for good: fade and free its source after <see cref="EmitterState.FreeAfter"/>.</summary>
        public bool Freed(int i) => _steps[i].Freed;
    }
}
