using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms.Bridges;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Actuators;

namespace DeadLetter.Core.Simulation.Replay.Scripts
{
    /// <summary>
    /// DL-01 The Wake, played as bot.js plays it (<c>opening()</c> + <c>wake()</c>, bot.js L109–L159): the latch, the
    /// step, the cart into the trench, the crank, then through the door into DL-02. Positions are bot.js's own literals
    /// (it walks to 2.98, uses the latch from 3.0, the crank from 9.62); everything else is read from the scene's
    /// mechanisms by their §5 ids, so the script follows the scene definition when it moves.
    /// <para>Curiosities and the cord are not in the scene sim yet: their chances are still drawn, so a seed's later
    /// hesitations match the prototype's, and the skipped beat is noted.</para>
    /// </summary>
    public sealed class Dl01WakeScript : ScriptedPlayer
    {
        public const string LatchId = "dl01.latch", CartId = "dl01.cart", CrankId = "dl01.crank", DoorId = "dl01.door";
        /// <summary>The scene act the trench fail starts (<c>trenchStuck</c>, L4764–L4766).</summary>
        public const string TrenchStuck = "trenchStuck";

        private readonly TippingBridgeParams _cart;

        /// <summary>The script ends when he is through the door, in DL-02 (marks <c>end</c> there).</summary>
        /// <param name="cart">The cart's parameters, as the scene definition gives them (default: the prototype's).</param>
        public Dl01WakeScript(PlayerModel player, TippingBridgeParams cart = null) : base(player)
        {
            _cart = cart ?? TippingBridgeParams.Dl01Cart();
        }

        private TippingBridge CartM => G.Mechanisms.Get<TippingBridge>(CartId);
        private bool CartFree => CartM.State == TippingBridgeState.Free || CartM.State == TippingBridgeState.AtLip;

        protected override IEnumerable<object> Script()
        {
            foreach (var s in Opening()) yield return s;
            foreach (var s in Wake()) yield return s;
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
    }
}
