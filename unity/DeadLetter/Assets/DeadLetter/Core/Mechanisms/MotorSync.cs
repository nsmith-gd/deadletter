using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Mechanisms
{
    /// <summary>
    /// The motor's half of the step after the mechanisms (port_architecture §3.1, after #5–#7): an <see cref="IEscort"/>
    /// that has caught him starts the motor's escorted act (the trolley sets <c>game.act</c> in its update, L6399), then
    /// #9 ride sync (<c>syncRide</c>, L2959–L2964): he is placed on the carrier he rides (<see cref="D17Motor.SyncRide"/>)
    /// and on the floor of every <see cref="ILiftRide"/> that carries him (<see cref="D17Motor.SnapToFloor"/>).
    /// <para>Built once from a built graph (it collects the escorts and lifts); <see cref="AfterMechanisms"/> is
    /// allocation-free. A scene simulator calls it right after <c>MechanismGraph.Step</c> and its scene rules for the
    /// graph's transitions, before checkpoints and the camera (see Core/Motor/README.md).</para>
    /// </summary>
    public sealed class MotorSync
    {
        private readonly IEscort[] _escorts;
        private readonly ILiftRide[] _lifts;

        public MotorSync(MechanismGraph graph)
        {
            if (graph == null) throw new ArgumentNullException(nameof(graph));
            var escorts = new List<IEscort>();
            var lifts = new List<ILiftRide>();
            for (int i = 0; i < graph.Count; i++)
            {
                if (graph[i] is IEscort e) escorts.Add(e);
                if (graph[i] is ILiftRide l) lifts.Add(l);
            }
            _escorts = escorts.ToArray();
            _lifts = lifts.ToArray();
        }

        /// <summary>From explicit lists (tests, a Runtime rig without a graph).</summary>
        public MotorSync(IEscort[] escorts, ILiftRide[] lifts)
        {
            _escorts = escorts ?? Array.Empty<IEscort>();
            _lifts = lifts ?? Array.Empty<ILiftRide>();
        }

        public IReadOnlyList<IEscort> Escorts => _escorts;
        public IReadOnlyList<ILiftRide> Lifts => _lifts;

        /// <summary>Escort start, then ride sync: the prototype's order (L6399 at #6, L2959 at #9).</summary>
        public void AfterMechanisms(D17Motor m)
        {
            StartEscort(m);
            SyncRides(m);
        }

        /// <summary>The first escort that wants him starts the escorted act (ignored while already escorted or dead). True if one did.</summary>
        public bool StartEscort(D17Motor m)
        {
            if (m.IsEscorted) return false;
            for (int i = 0; i < _escorts.Length; i++)
            {
                if (!_escorts[i].WantsEscort) continue;
                m.BeginEscort(_escorts[i].Walk);
                return m.IsEscorted;
            }
            return false;
        }

        /// <summary>#9: on the carrier he rides, and on each carrying lift's floor (this tick's: the lifts moved at #6).</summary>
        public void SyncRides(D17Motor m)
        {
            m.SyncRide();
            for (int i = 0; i < _lifts.Length; i++)
                if (_lifts[i].Carrying) m.SnapToFloor(_lifts[i].FloorY);
        }
    }
}
