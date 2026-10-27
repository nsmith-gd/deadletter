using System.Collections.Generic;

namespace DeadLetter.Core.Beings
{
    public enum NoiseKind
    {
        /// <summary><c>makeNoise(x, loud, region)</c>, L7096–L7103: running 1 (L7120), a real landing 1.1 (L2028), a
        /// splash or a slam 1.5 (the duct falling into the flood L4855, the doorbell L7244).</summary>
        Sound,
        /// <summary><c>lureWhite(x, sec, dir)</c>, L7105: it swims there and noses at it until the time runs out.</summary>
        Lure,
        /// <summary><c>scareWhite(sec)</c>, L7106: it flees for <see cref="NoiseEvent.Seconds"/>.</summary>
        Scare,
        /// <summary>A scripted first sighting of the water <see cref="NoiseEvent.Water"/> (it surfaces at the water's
        /// ShowX): the sump's first rise L7372 and the heap's first bucket weight L4996. The lane's is positional (L7271).</summary>
        Show,
    }

    /// <summary>
    /// Something a being can sense this step: a sound, or a cue from a mechanism (a bell's lure, a shorted cable's scare).
    /// Posted to the <see cref="NoiseBus"/> by the motor (through <see cref="BeingSenses.ReadMotor"/>) and by mechanisms;
    /// beings read it in their Step (port_architecture §4.15: "the same NoiseEvent bus will serve the attendant").
    /// </summary>
    public readonly struct NoiseEvent
    {
        public readonly NoiseKind Kind;
        /// <summary>Lane x of the sound or the lure.</summary>
        public readonly double X;
        /// <summary>Loudness: 1 running, 1.1 landing, 1.5 splash or bell. Hearing reaches 2.5·loud past the water (L7099).</summary>
        public readonly double Loud;
        /// <summary>Lure or scare duration, seconds.</summary>
        public readonly double Seconds;
        /// <summary>Lure: the side it noses from (−1, +1), or 0 for "whichever side it is on" (L7128).</summary>
        public readonly int Dir;
        /// <summary>The prototype's <c>game.region</c> where the sound was made; a water only hears its own region (L7098).</summary>
        public readonly int Region;
        /// <summary>His own footfall (the prototype's <c>x === game.x</c>, L7101): only his running breaks a lure (L7132).</summary>
        public readonly bool FromHim;
        /// <summary>Show: the <see cref="WaterBody.Id"/> to surface in.</summary>
        public readonly string Water;

        private NoiseEvent(NoiseKind kind, double x, double loud, double seconds, int dir, int region, bool fromHim, string water)
        {
            Kind = kind; X = x; Loud = loud; Seconds = seconds; Dir = dir; Region = region; FromHim = fromHim; Water = water;
        }

        public static NoiseEvent Sound(double x, double loud, int region, bool fromHim = false)
            => new NoiseEvent(NoiseKind.Sound, x, loud, 0, 0, region, fromHim, null);

        public static NoiseEvent Lure(double x, double seconds, int dir = 0)
            => new NoiseEvent(NoiseKind.Lure, x, 0, seconds, dir, 0, false, null);

        public static NoiseEvent Scare(double seconds) => new NoiseEvent(NoiseKind.Scare, 0, 0, seconds, 0, 0, false, null);

        public static NoiseEvent Show(string water) => new NoiseEvent(NoiseKind.Show, 0, 0, 0, 0, 0, false, water);

        public override string ToString() => Kind + " x=" + X.ToString("R") + " loud=" + Loud.ToString("R") + " s=" + Seconds.ToString("R")
            + (FromHim ? " him" : "") + (Water != null ? " " + Water : "");
    }

    /// <summary>
    /// This step's noises and cues, in the order they were made. The step driver clears it at the start of each fixed step
    /// (<see cref="BeingSenses.BeginStep"/>); the motor's noises go in after the motor steps (#4), mechanisms post during
    /// the graph step (#6–#7), and beings, added to the graph after every noise source (the prototype's
    /// <c>updateWhite</c> is #8, §3.1), read all of them. Preallocated: posting does not allocate below the capacity.
    /// </summary>
    public sealed class NoiseBus
    {
        private readonly List<NoiseEvent> _events;

        public NoiseBus(int capacity = 16) { _events = new List<NoiseEvent>(capacity); }

        public int Count => _events.Count;
        public NoiseEvent this[int i] => _events[i];

        public void Post(in NoiseEvent e) => _events.Add(e);
        public void Clear() => _events.Clear();
    }
}
