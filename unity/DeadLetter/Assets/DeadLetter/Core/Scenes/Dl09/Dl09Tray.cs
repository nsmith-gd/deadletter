using System;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms.Lifts;

namespace DeadLetter.Core.Scenes.Dl09
{
    /// <summary>
    /// The plates' context set-down into the counterweight's tray (<c>nearCh1</c>'s <c>loadTray</c>, L4213; <c>beginUse</c>
    /// L4355–L4357; <c>updateActCh1</c> L4428–L4438): with a plate in his hands within <c>CW8.trayX − 0.8</c> and the shaft's far
    /// side while the cage stands at the top, he walks to <c>clamp(x, trayX − 0.7, trayX − 0.42)</c>, faces +1, turns into the
    /// set and sets it in with SetDownHigh; at f14 it is in the tray (<see cref="ItemState.Placed"/>, its seat the count of
    /// plates already there), which the tray (<c>dl09.tray</c>, a <see cref="Mechanisms.Plates.LoadPlate"/>) weighs from this
    /// step's mechanisms. The motor plays the act; this answers where he stands and takes the plate.
    /// </summary>
    public sealed class Dl09TrayLoader : IPlaceTarget
    {
        /// <summary><c>CW8.trayX</c> (L7320); its reach (L4213) and stand (L4356).</summary>
        public const double TrayX = Dl09Lane.Off3 + 68.45, ReachBack = 0.8, StandMin = TrayX - 0.7, StandMax = TrayX - 0.42;

        private readonly CarriedItem _p0, _p1;
        private readonly SlippingCage _cage;

        public Dl09TrayLoader(CarriedItem plate0, CarriedItem plate1, SlippingCage cage)
        {
            _p0 = plate0 ?? throw new ArgumentNullException(nameof(plate0));
            _p1 = plate1 ?? throw new ArgumentNullException(nameof(plate1));
            _cage = cage ?? throw new ArgumentNullException(nameof(cage));
        }

        public InteractionCategory Category => InteractionCategory.Item;
        public string Clip => "SetDownHigh";
        public bool TurnIntoSet => true;

        /// <summary>L4213: a plate in his hands (<c>game.carry.key[0] === 'p'</c>), within reach, the cage at the top.</summary>
        public bool Offer(in InteractionQuery q, out StationPose pose)
        {
            pose = default;
            if (q.Hold != HoldKind.Item || !Accepts(q.Carried)) return false;
            if (!(q.X > TrayX - ReachBack && q.X < Dl09Lane.ShaftX1) || _cage.State != SlippingCageState.Top) return false;
            pose = new StationPose(Smooth.Clamp(q.X, StandMin, StandMax), +1);
            return true;
        }

        public bool IsAvailable(in InteractionQuery q) => Offer(q, out _);

        public bool Accepts(ICarryable item) => ReferenceEquals(item, _p0) || ReferenceEquals(item, _p1);

        /// <summary>
        /// SetDownHigh f14 (L4433–L4435): it goes into the tray, seated after the plates already there (<c>it.seat</c>); it
        /// keeps its lane x and base, as the prototype's does (the view seats it on the counterweight). The plate moves at its
        /// own step, this step's #6, before the tray weighs it.
        /// </summary>
        public void OnPlaced(ICarryable item)
        {
            var plate = item as CarriedItem;
            if (plate == null || !Accepts(item)) return;
            var other = ReferenceEquals(plate, _p0) ? _p1 : _p0;
            plate.MoveTo(ItemState.Placed, plate.X, plate.BaseY, other.State == ItemState.Placed ? 1 : 0);
        }
    }
}
