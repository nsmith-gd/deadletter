using System;
using DeadLetter.Core.Mechanisms.Routes;

namespace DeadLetter.Core.Presentation
{
    /// <summary>One carrier's pose for its view (lane axes; Unity z = <see cref="CarrierLineParams.RailZ"/>, into the set).</summary>
    public struct CarrierPose
    {
        /// <summary>Rail x, y (metres) and the rail segment's angle about lane z (radians, three.js's <c>rotation.z</c> sign).</summary>
        public double X, Y, Angle;
        /// <summary>The tub about its pivot (radians: + toward the gallery's bucket, − into the chute).</summary>
        public double Tip;

        public static CarrierPose Lerp(in CarrierPose a, in CarrierPose b, double k) => new CarrierPose
        {
            X = a.X + (b.X - a.X) * k, Y = a.Y + (b.Y - a.Y) * k, Angle = a.Angle + (b.Angle - a.Angle) * k, Tip = a.Tip + (b.Tip - a.Tip) * k,
        };
    }

    /// <summary>
    /// The DL-06 carrier line's views (port_architecture §4.13h; <c>spawnCarrier</c>/<c>updateCarriers</c> L2660–L2751): a
    /// fixed pool of <see cref="CarrierLineParams.Capacity"/> view slots, one per live carrier. A carrier keeps its slot from
    /// the step it rises (<see cref="CarrierLineEvent.Spawned"/>) to the step it is removed, so its view never jumps to
    /// another; a freed slot goes dark. <see cref="Sample"/> after each Core step keeps the last two poses, so the runtime
    /// can draw between steps (<see cref="Pose"/>). Nothing here allocates after construction.
    /// </summary>
    public sealed class CarrierViews
    {
        private readonly CarrierLine _line;
        private readonly int[] _seq;
        private readonly bool[] _fresh;
        private readonly CarrierPose[] _prev, _now;
        private readonly int[] _parcels, _load1, _load2;
        private readonly bool[] _ridden;
        private readonly bool[] _seen;

        public CarrierViews(CarrierLine line, int capacity = 0)
        {
            _line = line ?? throw new ArgumentNullException(nameof(line));
            int n = capacity > 0 ? capacity : new CarrierLineParams().Capacity;
            _seq = new int[n];
            _fresh = new bool[n];
            _prev = new CarrierPose[n];
            _now = new CarrierPose[n];
            _parcels = new int[n];
            _load1 = new int[n];
            _load2 = new int[n];
            _ridden = new bool[n];
            _seen = new bool[n];
            for (int i = 0; i < n; i++) _seq[i] = -1;
        }

        public CarrierLine Line => _line;
        /// <summary>View slots (the pool's size).</summary>
        public int Capacity => _seq.Length;
        /// <summary>Slot <paramref name="slot"/> shows a carrier.</summary>
        public bool Active(int slot) => _seq[slot] >= 0;
        /// <summary>The carrier's sequence number (<see cref="Carrier.Seq"/>), or −1.</summary>
        public int SeqOf(int slot) => _seq[slot];
        /// <summary>The parcels it shows (0 once a weight is in them), and its loads (0 = none).</summary>
        public int Parcels(int slot) => _parcels[slot];
        public int Load1(int slot) => _load1[slot];
        public int Load2(int slot) => _load2[slot];
        public bool Ridden(int slot) => _ridden[slot];
        /// <summary>Live carriers the pool had no slot for (a line over capacity); stays 0 for DL-06.</summary>
        public int Overflow { get; private set; }

        /// <summary>The pose between the last two samples (<paramref name="alpha"/> 0 = the one before, 1 = the last).</summary>
        public CarrierPose Pose(int slot, double alpha) => CarrierPose.Lerp(_prev[slot], _now[slot], alpha < 0 ? 0 : alpha > 1 ? 1 : alpha);

        /// <summary>Reads the line after a Core step: binds new carriers to free slots, frees the removed, keeps the poses.</summary>
        public void Sample()
        {
            int n = _seq.Length;
            for (int s = 0; s < n; s++) _seen[s] = false;
            for (int i = 0; i < _line.Count; i++)
            {
                Carrier c = _line.At(i);
                int slot = SlotOf(c.Seq);
                if (slot < 0)
                {
                    slot = FreeSlot();
                    if (slot < 0) { Overflow++; continue; }
                    _seq[slot] = c.Seq;
                    _fresh[slot] = true;
                }
                _seen[slot] = true;
                _prev[slot] = _fresh[slot] ? PoseOf(c) : _now[slot];
                _fresh[slot] = false;
                _now[slot] = PoseOf(c);
                _parcels[slot] = c.ParcelsHidden ? 0 : c.Parcels;
                _load1[slot] = c.Load1;
                _load2[slot] = c.Load2;
                _ridden[slot] = c.Ridden;
            }
            for (int s = 0; s < n; s++) if (!_seen[s]) _seq[s] = -1;
        }

        /// <summary>After a placement (respawn, continue): nothing interpolates from the old world.</summary>
        public void Snap()
        {
            for (int s = 0; s < _seq.Length; s++) _prev[s] = _now[s];
        }

        private static CarrierPose PoseOf(Carrier c) => new CarrierPose { X = c.Position, Y = c.Y, Angle = c.Angle, Tip = c.TipRad };

        private int SlotOf(int seq)
        {
            for (int s = 0; s < _seq.Length; s++) if (_seq[s] == seq) return s;
            return -1;
        }

        private int FreeSlot()
        {
            for (int s = 0; s < _seq.Length; s++) if (_seq[s] < 0 && !_seen[s]) return s;
            return -1;
        }
    }
}
