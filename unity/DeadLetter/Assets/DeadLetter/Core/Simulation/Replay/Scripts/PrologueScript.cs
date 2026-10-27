using System;
using System.Collections.Generic;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Hazards;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Bridges;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Docks;
using DeadLetter.Core.Mechanisms.Routes;
using DeadLetter.Core.Push;
using DeadLetter.Core.Scenes.Dl02;
using DeadLetter.Core.Scenes.Dl03;
using DeadLetter.Core.Scenes.Dl06;

namespace DeadLetter.Core.Simulation.Replay.Scripts
{
    /// <summary>
    /// The prologue as far as Core has ported it (DL-01 to DL-06), played as bot.js plays it (<c>opening()</c>,
    /// <c>wake()</c>, <c>sortingHall()</c>, <c>weightRoom()</c>, <c>racks()</c>, <c>rationHall()</c>,
    /// <c>returnToSender()</c>; bot.js L109–L312). Positions are bot.js's own (its literals and the prototype's tables it
    /// reads, <c>D.k</c>, cited by line); state is read from the chapter's mechanisms by their §5 ids.
    /// <para>Curiosities, the cord and the letters are not in Core yet: their chances are still drawn, so a seed's later
    /// choices stay on the prototype's random sequence as long as possible, and the skipped beat is noted.</para>
    /// </summary>
    public sealed class PrologueScript : ScriptedPlayer
    {
        public const string LatchId = "dl01.latch", CartId = "dl01.cart", CrankId = "dl01.crank", DoorId = "dl01.door";
        /// <summary>The act the trench fail starts (<c>trenchStuck</c>, L4764–L4766): the motor's stuck act (<c>BeginStuck</c>).</summary>
        public const string TrenchStuck = "stuck";

        private readonly TippingBridgeParams _cart;
        private readonly int _last;

        /// <param name="lastScene">The last scene to play, "DL-01" … "DL-06": the script ends (marks <c>end</c>) as he leaves it.</param>
        /// <param name="cart">The cart's parameters, as the scene definition gives them (default: the prototype's).</param>
        public PrologueScript(PlayerModel player, string lastScene = "DL-06", TippingBridgeParams cart = null) : base(player)
        {
            _cart = cart ?? TippingBridgeParams.Dl01Cart();
            _last = Array.IndexOf(Scenes, lastScene);
            if (_last < 0) throw new ArgumentException("No bot script for " + lastScene + " yet.", nameof(lastScene));
        }

        /// <summary>The scenes this script plays, in order.</summary>
        public static readonly string[] Scenes = { "DL-01", "DL-02", "DL-03", "DL-04", "DL-05", "DL-06" };

        private TippingBridge CartM => G.Mechanisms.Get<TippingBridge>(CartId);
        private bool CartFree => CartM.State == TippingBridgeState.Free || CartM.State == TippingBridgeState.AtLip;

        protected override IEnumerable<object> Script()
        {
            foreach (var s in Opening()) yield return s;
            var parts = new Func<IEnumerable<object>>[] { Wake, SortingHall, WeightRoom, Racks, RationHall, ReturnToSender };
            for (int i = 0; i <= _last; i++)
                foreach (var s in parts[i]()) yield return s;
        }

        /// <summary>A curiosity bot.js would use (<c>curio</c>, L94–L99): the chance is drawn, the beat is skipped.</summary>
        private void Curio(string id, double p)
        {
            if (P.Mechanical) return;
            if (P.Chance(p)) Note("would use the " + id + " (not in the scene sim)");
        }

        public IEnumerable<object> Wake()
        {
            var cart = _cart;
            foreach (var s in Wait(P.Think(3))) yield return s;
            if (P.Chance(0.15 + 0.2 * (1 - P.Skill)))
            {
                Note("tries left first");
                foreach (var s in Walk(-1, () => G.X < 0.75, "left first")) yield return s;
                foreach (var s in Wait(P.Think(1))) yield return s;
            }
            if (P.Chance(0.3 + 0.45 * P.Curious)) Note("would pull the cord (not in the scene sim)");
            Curio("dispatch", 0.2 + 0.5 * P.Curious);
            Curio("scale", 0.6 + 0.35 * P.Curious);
            foreach (var s in Walk(1, () => G.X >= 2.98, "to the shutter", new WalkOptions { Stall = 1.2 })) yield return s;
            if (P.Mistakes && P.Chance(0.7 - 0.45 * P.Skill))
            {
                Note("pushes at the shutter");
                double stall = 1.5 + P.Next() * 2;
                foreach (var s in Attempt(Walk(1, () => false, "push", new WalkOptions { Stall = stall, NoHop = true, Max = 8 }))) yield return s;
            }
            foreach (var s in Wait(P.Think(8))) yield return s;
            foreach (var s in UseAt(new[] { LatchId }, 3.0, ActIs(LatchId), "latch")) yield return s;
            foreach (var s in Until(() => G.Mechanisms.Get<Latch>(LatchId).State == LatchState.Released && G.Act == null, 30, "latch done")) yield return s;
            Note("shutter up");
            foreach (var s in Wait(P.Look(1.2))) yield return s;

            // The trench: try to jump it from the cart, fall in, and be back at the shutter.
            foreach (var s in Walk(1, () => G.X > 4.5, "over the step")) yield return s;
            if (P.Mistakes && P.Chance(0.6 - 0.35 * P.Skill))
            {
                Note("tries to jump the trench");
                foreach (var s in Walk(1, () => G.Y > cart.Height - 0.05 && G.X > CartM.X + cart.Half - 0.3, "onto the cart", new WalkOptions { Max = 30 })) yield return s;
                Jump(); Move(1);
                foreach (var s in Wait(0.6)) yield return s;
                Move(0);
                foreach (var s in Until(() => G.Act == TrenchStuck || G.X > cart.PitX1 + 0.1, 10, "the jump")) yield return s;
                if (G.Act == TrenchStuck)
                {
                    foreach (var s in Until(() => G.Playing && G.Act == null && G.X < 3.5, 20, "respawned")) yield return s;
                    Note("back at the shutter");
                    foreach (var s in Wait(P.Think(8))) yield return s;
                    foreach (var s in Walk(1, () => G.X > 4.5, "over the step again")) yield return s;
                }
            }
            else foreach (var s in Wait(P.Think(6))) yield return s;

            if (CartFree)
            {
                foreach (var s in UseAt(new[] { CartId }, CartM.X - cart.Gap, ActIs(CartId), "cart", new WalkOptions { NoHop = true })) yield return s;
                foreach (var s in Until(() => G.Hold == HoldKind.Push, 10, "grip cart")) yield return s;
                foreach (var s in Walk(1, () => !CartFree, "push the cart", new WalkOptions { NoHop = true, KeepHolding = true, Max = 30 })) yield return s;
                Note("cart in the trench");
                foreach (var s in Until(() => CartM.State == TippingBridgeState.Bridge, 5, "bridge")) yield return s;
                foreach (var s in Wait(P.Look(1.0))) yield return s;
            }
            foreach (var s in Walk(1, () => G.X > 8.6, "to the hall")) yield return s;
            foreach (var s in Wait(P.Look(3.0))) yield return s;
            if (P.Mistakes && P.Chance(0.75 - 0.5 * P.Skill))
            {
                Note("tries the door");
                double stall = 1.0 + P.Next();
                foreach (var s in Attempt(Walk(1, () => false, "to the door", new WalkOptions { Stall = stall, NoHop = true, Max = 30 }))) yield return s;
                foreach (var s in Wait(P.Think(10))) yield return s;
            }
            else foreach (var s in Wait(P.Think(6))) yield return s;
            foreach (var s in UseAt(new[] { CrankId }, 9.62, ActIs(CrankId), "crank")) yield return s;
            foreach (var s in Until(() => G.Mechanisms.Get<Door>(DoorId).Position >= 1 && G.Act == null, 60, "door open")) yield return s;
            Note("door open");
            foreach (var s in Wait(P.Look(1.0))) yield return s;
            foreach (var s in Walk(1, () => G.Region == 2, "through the door")) yield return s;
        }

        // ---- DL-02 The Sorting Hall (sortingHall, bot.js L164–L193) -------------------------------------------------
        /// <summary><c>SH</c> (L3887–L3888): the tube, the slot, the table, the hall's end; <c>GRIP_FWD</c> (L320).</summary>
        private const double TubeX = 14.6, SlotX = 16.0, TableX0 = 18.6, HallX1 = 25.0, GripFwd = 0.29;

        private bool Dying => G.Act == "death";

        private IEnumerable<object> Respawned(string label) =>
            Until(() => G.Playing && G.Act == null, 15, label);

        /// <summary>The franking press: wait for the ram to rise, then go; the impatient walk in on the slam (<c>passPress</c>, L86–L96).</summary>
        private IEnumerable<object> PassPress(int tries = 0)
        {
            var press = G.Mechanisms.Get<PeriodicCrusher>("dl02.press");
            var pr = press.Params;
            if (G.Region != 2 || G.X > pr.X1) yield break;
            foreach (var s in GoTo(pr.X0 - 0.3, "to the press", new WalkOptions { NoHop = true })) yield return s;
            if (tries == 0) foreach (var s in Wait(P.Look(2.5))) yield return s;
            if (P.Mistakes && tries == 0 && P.Chance(0.45 - 0.35 * P.Skill)) Note("walks under the press");
            else foreach (var s in Until(() => press.Phase > 1.45 && press.Phase < 1.75, 10, "press up")) yield return s;
            foreach (var s in Walk(1, () => G.X > pr.X1 + 0.05 || Dying, "under the press", new WalkOptions { NoHop = true, Max = 10 })) yield return s;
            if (Dying)
            {
                Note("crushed by the press");
                foreach (var s in Respawned("after the press")) yield return s;
                foreach (var s in Wait(P.Think(3))) yield return s;
                foreach (var s in PassPress(tries + 1)) yield return s;
            }
        }

        public IEnumerable<object> SortingHall()
        {
            foreach (var s in Until(() => !G.InTransit, 60, "passage")) yield return s;
            foreach (var s in Wait(P.Look(2.5))) yield return s;
            Curio("franker", 0.35 + 0.5 * P.Curious);
            foreach (var s in PassPress()) yield return s;
            foreach (var s in Walk(1, () => G.X > TubeX + 0.1, "past the tube")) yield return s;
            var letter = G.Mechanisms.Get<Dl02TubeLetter>("dl02.tubeLetter");
            foreach (var s in Until(() => letter.State == TubeLetterState.Floor, 3, "tube letter")) yield return s;
            foreach (var s in Wait(P.Look(1.2))) yield return s;
            if (P.Chance(0.55 + 0.4 * P.Curious)) Note("would pick up the tube letter (letters are not in Core)");   // letter(), L78–L82
            Curio("mug", 0.25 + 0.5 * P.Curious);                                                                         // post() draws nothing: no letter held
            foreach (var s in Wait(P.Look(1.5))) yield return s;
            // The table is too high; the floor is closed. Try the jump, then the box.
            if (P.Mistakes && P.Chance(0.8 - 0.35 * P.Skill))
            {
                Note("tries to climb the table");
                double max = 6 + 6 * P.Next();
                foreach (var s in Attempt(Walk(1, () => G.X > TableX0 + 0.3 && G.Y > 0.5, "at the table", new WalkOptions { Max = max }))) yield return s;
                foreach (var s in Wait(P.Think(9))) yield return s;
            }
            else foreach (var s in Wait(P.Think(5))) yield return s;
            if (G.Y > 0.5) Note("is on the table already");
            else
            {
                var box = G.Mechanisms.Get<CarriedItem>("dl02.box");
                foreach (var s in UseAt(new[] { "dl02.box" }, box.X, ActIs("dl02.box"), "box")) yield return s;
                foreach (var s in Until(() => G.Hold == HoldKind.Item, 10, "carrying")) yield return s;
                foreach (var s in Walk(1, () => G.X >= TableX0 - 0.22 - GripFwd, "to the table", new WalkOptions { NoHop = true, Max = 30 })) yield return s;
                Use();
                foreach (var s in Until(() => G.Act != null, 3, "set down")) yield return s;
                foreach (var s in Settle()) yield return s;
                Note("box at the table");
            }
            foreach (var s in Wait(P.Think(2))) yield return s;
            foreach (var s in Walk(1, () => G.X > HallX1 + 0.6 && G.Y < 0.05, "up and over", new WalkOptions { Max = 60 })) yield return s;
        }

        // ---- DL-03 The Weight of the Job (weightRoom, L196–L226) ----------------------------------------------------
        /// <summary><c>OFF2</c> + 16.1 (the plate), + 12.7 (the weight), <c>GATE_X</c> = OFF2 + 17.6 (L323).</summary>
        private const double Off2 = 13, PlateX = Off2 + 16.1, WeightX = Off2 + 12.7, GateX = Off2 + 17.6;

        public IEnumerable<object> WeightRoom()
        {
            var gate = G.Mechanisms.Get<IPositionSource>("dl03.gate");
            var trolley = G.Mechanisms.Get<Pushable>("dl03.trolley");
            var weight = G.Mechanisms.Get<Dl03Weight>("dl03.weight");
            foreach (var s in Wait(P.Look(2.5))) yield return s;
            int tries = P.Mistakes ? (P.Chance(0.85 - 0.3 * P.Skill) ? (P.Chance(0.45) ? 2 : 1) : 0) : 0;
            for (int k = 0; k < tries; k++)
            {
                Note("stands on the plate");
                foreach (var s in Walk(1, () => G.X > PlateX, "to the plate")) yield return s;
                foreach (var s in Until(() => gate.Position > 1.15, 20, "gate up")) yield return s;
                foreach (var s in Wait(P.Think(1.2))) yield return s;
                foreach (var s in Walk(1, () => G.X > Off2 + 16.9 || gate.Position < 0.5, "for the gate")) yield return s;
                foreach (var s in Wait(1.2 + P.Think(3))) yield return s;
                foreach (var s in GoTo(Off2 + 15.6, "back off")) yield return s;
            }
            foreach (var s in Wander(Off2 + 12.6, Off2 + 15.4, 0.5 - 0.3 * P.Skill)) yield return s;
            foreach (var s in Wait(P.Think(tries > 0 ? 20 : 14))) yield return s;
            foreach (var s in UseAt(new[] { "dl03.weight" }, WeightX, ActIs("dl03.weight"), "lift")) yield return s;
            foreach (var s in Until(() => G.Hold == HoldKind.Item, 20, "carrying")) yield return s;
            foreach (var s in Wait(P.Think(6))) yield return s;
            foreach (var s in Walk(1, () => G.X >= trolley.X - 0.42, "to the trolley", new WalkOptions { Stall = 0.3, NoHop = true })) yield return s;
            // The set-down is a scene act whose kind is the weight's id (Dl03SetDownAct); he is holding it until then.
            Func<bool> settingDown = () => G.Act == "dl03.weight";
            for (int k = 0; k < 8 && !settingDown(); k++)
            {
                Use(); yield return null; yield return null;
                foreach (var s in Wait(0.3)) yield return s;
                if (!settingDown())
                {
                    Move(1);
                    foreach (var s in Wait(0.08)) yield return s;
                    Move(0);
                }
            }
            foreach (var s in Until(() => weight.State == Dl03WeightState.OnTrolley && G.Act == null, 20, "weight on trolley")) yield return s;
            Note("weight on the trolley");
            foreach (var s in Wait(P.Think(8))) yield return s;
            foreach (var s in UseAt(new[] { "dl03.trolley" }, trolley.X - 0.62, () => G.Hold == HoldKind.Push, "grab")) yield return s;
            foreach (var s in Walk(1, () => trolley.X > PlateX, "push to the plate", new WalkOptions { NoHop = true, KeepHolding = true })) yield return s;
            Use();
            foreach (var s in Until(() => G.Hold == HoldKind.None, 10, "let go")) yield return s;
            var reveal = G.Shared<RacksReveal>();
            foreach (var s in Until(() => reveal.Revealed, 30, "revealed")) yield return s;
            Note("racks light");
            foreach (var s in Until(() => G.Act == null, 30, "reveal act")) yield return s;
            foreach (var s in Wait(P.Look(3.0))) yield return s;
            foreach (var s in Walk(1, () => G.X > GateX + 0.4, "over the trolley, through the gate")) yield return s;
        }

        // ---- DL-04 The Racks (racks, L229–L249) ----------------------------------------------------------------------
        /// <summary><c>RK</c> (L3890): the fallen courier, the grip gap, the bay plate; <c>RATION5.x0</c> (L3447).</summary>
        private const double CourierX = 41.2, CourierGap = 0.67, BayPlateX0 = 44.0, Ration5X0 = Off2 + 34.9;

        public IEnumerable<object> Racks()
        {
            var courier = G.Mechanisms.Get<Pushable>("dl04.courier");
            var cradle = G.Mechanisms.Get<Cradle>("dl04.cradle");
            var bayDoor = G.Mechanisms.Get<IPositionSource>("dl04.bayDoor");
            if (P.Chance(0.3 + 0.5 * P.Curious))
            {
                foreach (var s in Walk(1, () => G.X > Off2 + 20.5, "among the couriers")) yield return s;
                Note("looks at the couriers");
                foreach (var s in Wait(P.Look(3))) yield return s;
            }
            foreach (var s in Walk(1, () => G.X > CourierX + 0.6, "to the fallen courier", new WalkOptions { Max = 120 })) yield return s;
            foreach (var s in Wait(P.Look(3.0))) yield return s;
            if (P.Mistakes && P.Chance(0.8 - 0.3 * P.Skill))
            {
                Note("stands on the bay plate");
                foreach (var s in Walk(1, () => G.X > BayPlateX0 + 0.3, "on the plate")) yield return s;
                foreach (var s in Until(() => bayDoor.Position > 0.6, 5, "door opens")) yield return s;
                foreach (var s in Wait(P.Think(1.5))) yield return s;
                foreach (var s in Attempt(Walk(1, () => false, "for the door", new WalkOptions { Stall = 0.6, NoHop = true, Max = 6 }))) yield return s;
                foreach (var s in Wait(P.Think(8))) yield return s;
                if (P.Chance(0.45 - 0.25 * P.Skill))
                {
                    Note("goes back for the trolley");
                    foreach (var s in Attempt(GoTo(GateX + 1.0, "back toward the trolley", new WalkOptions { Max = 40 }))) yield return s;
                    foreach (var s in Wait(P.Think(6))) yield return s;
                }
            }
            else foreach (var s in Wait(P.Think(6))) yield return s;
            foreach (var s in UseAt(new[] { "dl04.courier" }, courier.X + CourierGap, ActIs("dl04.courier"), "courier", new WalkOptions { NoHop = true })) yield return s;
            foreach (var s in Until(() => G.Hold == HoldKind.Push, 10, "grip courier")) yield return s;
            // courier.state !== 'free': the cradle has taken it.
            foreach (var s in Walk(1, () => cradle.State != CradleState.Free, "drag the courier", new WalkOptions { NoHop = true, KeepHolding = true, Max = 40 })) yield return s;
            Note("courier on the bay");
            foreach (var s in Until(() => cradle.State == CradleState.Seated && G.Act == null && !G.Mantling, 30, "the cradle")) yield return s;
            foreach (var s in Settle()) yield return s;
            foreach (var s in Wait(P.Look(3.5))) yield return s;
            Curio("rack", 0.1 + 0.4 * P.Curious);
            foreach (var s in Walk(1, () => G.X > Ration5X0 + 1.0, "through the bay door", new WalkOptions { Max = 60 })) yield return s;
        }

        // ---- DL-05 The Ration Hall (rationHall, L252–L270) -----------------------------------------------------------
        /// <summary><c>RH5</c> (L3451–L3454): the plate's start, the drum on the plate, the grip gaps, the hatch on the drum, the crawl's end.</summary>
        private const double Rh5Plate0 = Off2 + 40.85, DrumPlate = Off2 + 41.80, DrumGap = 0.55, BodyGap = 1.05, OnDrum = 0.64, CrawlX1 = Off2 + 43.70;

        private IEnumerable<object> PushOff(string id, double x, string label)
        {
            foreach (var s in UseAt(new[] { id }, x, ActIs(id), label, new WalkOptions { NoHop = true })) yield return s;
            foreach (var s in Until(() => G.Hold == HoldKind.Push, 10, "grip " + label)) yield return s;
            foreach (var s in Walk(1, () => G.Hold == HoldKind.None, label, new WalkOptions { NoHop = true, KeepHolding = true, Max = 40 })) yield return s;
            foreach (var s in Settle()) yield return s;
        }

        public IEnumerable<object> RationHall()
        {
            var drum = G.Mechanisms.Get<Pushable>("dl05.drum");
            var body = G.Mechanisms.Get<Pushable>("dl05.body");
            var hatch = G.Mechanisms.Get<Door>("dl05.hatch");
            var served = G.Mechanisms.Get<Door>("dl05.servedFlag");
            foreach (var s in Wait(P.Look(4.0))) yield return s;
            if (P.Chance(0.3 + 0.5 * P.Curious))
            {
                Note("looks at the dead");
                foreach (var s in Wait(P.Look(4))) yield return s;
            }
            foreach (var s in Walk(1, () => G.X > Rh5Plate0 + 0.6, "onto the plate", new WalkOptions { Max = 40 })) yield return s;
            Note("stands on the plate: too light");
            foreach (var s in Wait(P.Think(6))) yield return s;
            if (drum.X < DrumPlate - 0.01)
            {
                foreach (var s in PushOff("dl05.drum", drum.X - DrumGap, "drum onto the plate")) yield return s;
                Note("drum: OVER");
                foreach (var s in Wait(P.Think(10))) yield return s;
            }
            if (drum.State == PushableState.Free)
            {
                foreach (var s in PushOff("dl05.drum", drum.X - DrumGap, "drum off the plate")) yield return s;
                Note("drum past the plate");
                foreach (var s in Wait(P.Think(12))) yield return s;
            }
            if (body.State == PushableState.Free)
            {
                foreach (var s in PushOff("dl05.body", body.X + BodyGap, "drag the body")) yield return s;
                Note("the body on the plate");
            }
            foreach (var s in Until(() => served.State != DoorState.Closed && hatch.Position >= OnDrum - 0.01, 10, "served")) yield return s;
            Note("served");
            foreach (var s in Settle()) yield return s;
            foreach (var s in Wait(P.Look(2.0))) yield return s;
            foreach (var s in Walk(1, () => G.X > CrawlX1 + 0.3, "under the shutter", new WalkOptions { Max = 30 })) yield return s;
            foreach (var s in Walk(1, () => G.Region == 3, "to the scanner corridor", new WalkOptions { Max = 60 })) yield return s;
        }

        // ---- DL-06 Return to Sender (returnToSender, L273–L312), without the ride into the pile ----------------------
        /// <summary><c>OFF3</c> (L274): the stop lever at + 29.5, the points at + 30.3.</summary>
        private const double Off3 = 33, StopLeverX = Off3 + 29.5, PointsX = Off3 + 30.3;

        public IEnumerable<object> ReturnToSender()
        {
            var scanner = G.Mechanisms.Get<Dl06Scanner>("dl06.scanner");
            var line = G.Mechanisms.Get<CarrierLine>("dl06.line");
            Curio("chair", 0.1 + 0.35 * P.Curious);
            foreach (var s in Walk(1, () => scanner.Phase != Dl06ScanPhase.Idle, "to the scanner")) yield return s;
            foreach (var s in Until(() => scanner.Phase == Dl06ScanPhase.Reveal, 60, "refusal")) yield return s;
            foreach (var s in Wait(P.Look(2.5))) yield return s;
            double slow = P.Uniform(1, 4);
            foreach (var s in Attempt(Walk(1, () => false, "slow walk", new WalkOptions { Max = slow, NoHop = true }))) yield return s;
            foreach (var s in Until(() => scanner.Phase == Dl06ScanPhase.Done, 90, "label check")) yield return s;
            foreach (var s in Wait(P.Look(2.0))) yield return s;
            if (P.Mistakes && P.Chance(0.35 + 0.25 * P.Curious + 0.15 * (1 - P.Skill)))
                Note("would ride a carrier to the chute (rides need #22's carriers in the bot; skipped)");
            foreach (var s in Wander(Off3 + 30.0, Off3 + 35.8, 0.6 - 0.3 * P.Skill)) yield return s;
            foreach (var s in Wait(P.Think(15))) yield return s;
            bool triedLocked = false;
            for (int guard = 0; guard < 12 && !(line.Route == CarrierRoute.Exit && line.Running); guard++)
            {
                if (line.Running && line.Route != CarrierRoute.Exit)
                {
                    if (P.Mistakes && !triedLocked && P.Chance(0.75 - 0.3 * P.Skill))
                    {
                        triedLocked = true; Note("tries the points: locked");
                        foreach (var s in UseAt(new[] { "dl06.points" }, PointsX, ActIs("dl06.points"), "points (locked)")) yield return s;
                        foreach (var s in Until(() => G.Act == null, 20, "locked")) yield return s;
                        foreach (var s in Wait(P.Think(10))) yield return s;
                    }
                    foreach (var s in UseAt(new[] { "dl06.stopLever" }, StopLeverX, ActIs("dl06.stopLever"), "stop")) yield return s;
                    foreach (var s in Until(() => G.Act == null, 20, "stopped")) yield return s;
                    Note("belt stopped");
                    foreach (var s in Wait(P.Think(4))) yield return s;
                }
                else if (!line.Running && line.Route != CarrierRoute.Exit)
                {
                    foreach (var s in UseAt(new[] { "dl06.points" }, PointsX, ActIs("dl06.points"), "points")) yield return s;
                    foreach (var s in Until(() => G.Act == null, 20, "thrown")) yield return s;
                    Note("points thrown");
                    foreach (var s in Wait(P.Look(2.5))) yield return s;
                }
                else if (!line.Running && line.Route == CarrierRoute.Exit)
                {
                    foreach (var s in UseAt(new[] { "dl06.stopLever" }, StopLeverX, ActIs("dl06.stopLever"), "start")) yield return s;
                    // The belt running to the exit is DL-07 (sceneName, L8141): past the ported prologue the chapter
                    // stops the motor, so the pull's step-out is the next chapter's to finish.
                    foreach (var s in Until(() => G.Act == null || G.SceneName == null, 20, "started")) yield return s;
                    Note("belt started");
                }
                yield return null;
            }
            foreach (var s in Wait(P.Think(1.5))) yield return s;
        }
    }
}
