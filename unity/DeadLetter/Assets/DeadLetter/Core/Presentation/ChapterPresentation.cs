using System;
using DeadLetter.Core.Mechanisms.Routes;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Streaming;

namespace DeadLetter.Core.Presentation
{
    /// <summary>
    /// Everything the runtime's sound, light and carrier views read from a <see cref="ChapterSim"/>, in one place for
    /// <c>GameHost</c> (port_architecture §3.1 #10–#11): the step's one-shots and layers (<see cref="Sounds"/>), the ambience
    /// beds and emitters (<see cref="Ambience"/>), the carrier line's pooled views (<see cref="Carriers"/>), the light pool
    /// (<see cref="Lighting"/>) and the mix (<see cref="Mix"/>). The host calls <see cref="AfterStep"/> after each Core step,
    /// <see cref="OnPlaced"/> after a placement, and <see cref="Frame"/> once per rendered frame. Allocation-free after construction.
    /// </summary>
    public sealed class ChapterPresentation
    {
        public ChapterPresentation(ChapterSim sim, ChapterPresenter presenter = null, LightPoolBudget budget = null, uint seed = 23)
        {
            Sim = sim ?? throw new ArgumentNullException(nameof(sim));
            Presenter = presenter ?? new ChapterPresenter(sim);
            Sounds = new ChapterSounds(sim, seed);
            Ambience = new AmbienceWorld(sim, Presenter, null, seed + 18);
            Lighting = new PrologueLighting(sim, Presenter, Sounds, budget, LightsFor(sim.Def.Id, budget != null && budget.Touch));
            Mix = new MixState();
            if (sim.Graph.TryGet("dl06.line", out CarrierLine line)) Carriers = new CarrierViews(line);
        }

        /// <summary>
        /// The chapter's light proxies: the prologue's (<see cref="PrologueLights"/>), or for chapter 1 the prologue's
        /// always-on ones (hemisphere, rim, kick) and <see cref="AttendanceLights"/>.
        /// </summary>
        public static LightDef[] LightsFor(string chapterId, bool touch)
        {
            LightDef[] prologue = PrologueLights.Build(touch);
            if (chapterId != ChapterDefs.AttendanceId) return prologue;
            var all = new System.Collections.Generic.List<LightDef>();
            foreach (LightDef d in prologue) if (d.Group == LightGroup.Always) all.Add(d);
            all.AddRange(AttendanceLights.Build(touch));
            return all.ToArray();
        }

        public ChapterSim Sim { get; }
        public ChapterPresenter Presenter { get; }
        public ChapterSounds Sounds { get; }
        public AmbienceWorld Ambience { get; }
        public PrologueLighting Lighting { get; }
        public MixState Mix { get; }
        /// <summary>The DL-06 line's views, or null when the chapter has none.</summary>
        public CarrierViews Carriers { get; }

        /// <summary>A directed moment's shot holds (<see cref="Cues.MomentDirector.VoicesHeld"/>): voices wait, the mix ducks.</summary>
        public bool MomentHeld
        {
            get
            {
                var m = Presenter.Moment;
                return m != null && m.VoicesHeld(Sim.Clock);
            }
        }

        /// <summary>After each Core step. <paramref name="voicePlaying"/>: a voice is playing (the runtime's VoicePlayer).</summary>
        public void AfterStep(bool voicePlaying, bool calm)
        {
            Sounds.Step(voicePlaying || MomentHeld, calm);
            Carriers?.Sample();
        }

        /// <summary>He was placed (new game, continue, begin, respawn): nothing carries over from the old world.</summary>
        public void OnPlaced()
        {
            Sounds.OnPlaced();
            if (Carriers != null) { Carriers.Sample(); Carriers.Snap(); }
            Lighting.Place();
            Mix.Place(Sim.Region, Lighting.Regions.Zone);
        }

        /// <summary>Once per rendered frame: the emitters on the audio clock, the lights around the camera, the mix.</summary>
        public void Frame(double audioNow, double dt, double cameraX, bool calm)
        {
            Ambience.Update(audioNow, dt);
            Lighting.Update(cameraX, calm);
            Mix.Update(Sim.Region, Lighting.Regions.Zone, MomentHeld, dt);
        }
    }
}
