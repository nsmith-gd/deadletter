using System;
using System.Collections.Generic;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Interaction
{
    /// <summary>What Use would do from a pose: a typed replacement for the prototype's string keys (§4.9).</summary>
    public struct Candidate
    {
        public Verb Verb;
        public InteractionCategory Category;
        /// <summary>The thing acted on (null for Release; the carried item for SetDown).</summary>
        public IInteractable Target;
        public double StandX;
        public double StandZ;
        /// <summary>Facing during the act (±1), or 0 to keep his facing.</summary>
        public int Face;
        /// <summary>Where the thing is, for the in-front preference.</summary>
        public double AnchorX;
        /// <summary>|x − StandX| at query time.</summary>
        public double Distance;
        /// <summary>The thing is in his facing direction (or level with him).</summary>
        public bool InFront;
        internal int Order;
    }

    /// <summary>
    /// "What would Use do here": a pure query over his pose, his hold and the registered interactables.
    /// Rules (index.html):
    /// <list type="bullet">
    /// <item>Nothing answers in the air or during an act (L4205).</item>
    /// <item>Pushing: Use lets go (L4208). Carrying: a context place target in reach, else set down, which never refuses (L4209–L4214).</item>
    /// <item>Items: he stands GRIP_FWD (0.29) short of the item on whichever side he is, within 0.4 of that point, at its
    /// level ±0.05 (L4218–L4221).</item>
    /// <item>Pushables: stand point X − Side·Gap; reach 0.34 in front of it, BackReach behind; floor level &lt; 0.05 (L4251–L4255).</item>
    /// <item>Stations (levers, cranks, seats, terminals): |x − StandX| &lt; Reach (L1812–L1814).</item>
    /// <item>Ranking: category priority (Item, Curio, Secret, Voice, Fixed, Letter, Push; L4204–L4257), then targets in
    /// front of him before targets behind (DL-01 §8 "nearest target in facing direction"), then the nearest stand
    /// point (the prototype's "nearest grip wins", L4252), then registration order.</item>
    /// </list>
    /// </summary>
    public sealed class InteractionResolver
    {
        private readonly List<IInteractable> _items = new List<IInteractable>();
        private readonly MotorConfig _cfg;

        public InteractionResolver(MotorConfig config = null)
        {
            _cfg = config ?? MotorConfig.Prototype();
        }

        public IReadOnlyList<IInteractable> Registered => _items;

        public void Register(IInteractable it)
        {
            if (it == null) throw new ArgumentNullException(nameof(it));
            if (!_items.Contains(it)) _items.Add(it);
        }

        public bool Unregister(IInteractable it) => _items.Remove(it);

        public void Clear() => _items.Clear();

        /// <summary>The best answer, optionally restricted to one category (the overlap audit asks each alone, L1780–L1785).</summary>
        public bool Resolve(in InteractionQuery q, out Candidate best, InteractionCategory? only = null)
        {
            best = default;
            if (!q.Grounded || q.Busy) return false;

            if (q.Hold == HoldKind.Push)
            {
                if (only.HasValue && only.Value != InteractionCategory.Item) return false;
                best = new Candidate { Verb = Verb.Release, Category = InteractionCategory.Item, Target = q.Pushed, StandX = q.X, AnchorX = q.X, InFront = true };
                return true;
            }

            bool found = false;
            for (int i = 0; i < _items.Count; i++)
            {
                var it = _items[i];
                if (only.HasValue && it.Category != only.Value) continue;
                if (!Offer(it, q, out var c)) continue;
                c.Order = i;
                if (!found || Better(c, best)) { best = c; found = true; }
            }

            if (!found && q.Hold == HoldKind.Item && q.Carried != null && (!only.HasValue || only.Value == InteractionCategory.Item))
            {
                best = new Candidate { Verb = Verb.SetDown, Category = InteractionCategory.Item, Target = q.Carried, StandX = q.X, AnchorX = q.X, InFront = true };
                found = true;
            }
            return found;
        }

        /// <summary>Every category that answers here (for the overlap audit: more than one is a priority clash).</summary>
        public int AnswersByCategory(in InteractionQuery q, List<Candidate> output)
        {
            output.Clear();
            for (int c = (int)InteractionCategory.Item; c <= (int)InteractionCategory.Push; c++)
                if (Resolve(q, out var cand, (InteractionCategory)c)) output.Add(cand);
            return output.Count;
        }

        private bool Offer(IInteractable it, in InteractionQuery q, out Candidate c)
        {
            c = default;
            if (q.Hold == HoldKind.Item)
            {
                // Carrying: only context set-downs answer.
                if (!(it is IPlaceTarget pt) || !pt.IsAvailable(q) || !pt.Accepts(q.Carried)) return false;
                return Station(pt, Verb.Place, q, out c);
            }
            if (it is IPlaceTarget) return false;

            if (it is ICarryable item)
            {
                if (ReferenceEquals(item, q.Carried) || !item.IsAvailable(q)) return false;
                if (Math.Abs(q.Y - item.BaseY) > _cfg.ItemLevelTolerance) return false;
                int side = Smooth.Sign(item.X - q.X);
                if (side == 0) side = q.Facing;
                double stand = item.X - side * _cfg.GripForward;
                double d = Math.Abs(q.X - stand);
                if (d >= _cfg.ItemReach) return false;
                c = Make(Verb.Lift, item, stand, 0, side, item.X, d, q);
                return true;
            }

            if (it is IPushable p)
            {
                if (!p.IsAvailable(q) || Math.Abs(q.Y - p.FloorY) >= 0.05) return false;
                double stand = p.X - p.Side * p.Gap;
                double dx = q.X - stand, d = Math.Abs(dx);
                double reach = dx * p.Side < 0 ? p.BackReach : p.ForwardReach;
                if (d >= reach) return false;
                c = Make(Verb.Grab, p, stand, p.Z, p.Side, p.X, d, q);
                return true;
            }

            if (it is IPresentTarget pr) return pr.IsAvailable(q) && Station(pr, Verb.Present, q, out c);
            if (it is ISeat seat) return seat.IsAvailable(q) && Station(seat, Verb.Sit, q, out c);
            if (it is IUsable u) return u.IsAvailable(q) && Station(u, Verb.Use, q, out c);
            return false;
        }

        private static bool Station(IStation s, Verb verb, in InteractionQuery q, out Candidate c)
        {
            double d = Math.Abs(q.X - s.StandX);
            if (d >= s.Reach) { c = default; return false; }
            c = Make(verb, s, s.StandX, s.StandZ, s.Face, s.AnchorX, d, q);
            return true;
        }

        private static Candidate Make(Verb verb, IInteractable target, double standX, double standZ, int face, double anchorX, double distance, in InteractionQuery q)
        {
            return new Candidate
            {
                Verb = verb, Category = target.Category, Target = target, StandX = standX, StandZ = standZ, Face = face,
                AnchorX = anchorX, Distance = distance, InFront = (anchorX - q.X) * q.Facing >= -1e-9,
            };
        }

        private static bool Better(in Candidate a, in Candidate b)
        {
            if (a.Category != b.Category) return a.Category < b.Category;
            if (a.InFront != b.InFront) return a.InFront;
            if (Math.Abs(a.Distance - b.Distance) > 1e-9) return a.Distance < b.Distance;
            return a.Order < b.Order;
        }
    }

    /// <summary>
    /// Lane set-down search, pass 3 "never refuse" (L4340–L4353): the spot GRIP_FWD in front, then +0.08, +0.16, −0.05;
    /// then the same behind him; failing all, in front anyway at min(his feet, the surface there).
    /// </summary>
    public static class PlaceSearch
    {
        public static void Find(IMotorWorld world, MotorConfig cfg, double x, double y, int facing, double radius,
            out double targetX, out double baseY, out int newFacing)
        {
            for (int s = 0; s < 2; s++)
            {
                int side = s == 0 ? facing : -facing;
                for (int i = 0; i < cfg.PlaceOffsets.Length; i++)
                {
                    double tx = x + side * (cfg.GripForward + cfg.PlaceOffsets[i]);
                    if (FlatAt(world, cfg, tx, y, radius, out double h))
                    {
                        targetX = tx; baseY = h; newFacing = side;
                        return;
                    }
                }
            }
            targetX = x + facing * cfg.GripForward;
            baseY = Math.Min(y, world.SurfaceAt(targetX, y));
            newFacing = facing;
        }

        private static bool FlatAt(IMotorWorld w, MotorConfig cfg, double x, double y, double r, out double h)
        {
            h = w.SurfaceAt(x, y);
            double tol = cfg.PlaceFlatTolerance;
            return Math.Abs(w.SurfaceAt(x - r, y) - h) < tol && Math.Abs(w.SurfaceAt(x + r, y) - h) < tol && h <= y + tol;
        }
    }
}
