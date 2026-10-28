using System.Collections.Generic;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Cycles;
using DeadLetter.Core.Mechanisms.Drives;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl14a;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-14a in Chapter 1's replay (<see cref="AttendanceChapterTraceTests"/>): out of the duct at <c>dorm</c>, the brake
    /// pulled in the dark (#8692), a wind (W1 down, W2 up; the gown rides up), the bag out of its basket (#9547) and onto
    /// W1's hook (#9696; the gown falls), a wind (W2 down alone), the door, from DL-14a's first step (#8265) to DL-14b's
    /// (#10392). The night-light runs from the chapter's first step, so it is compared from there.
    /// </summary>
    internal sealed class Dl14aChapterProbe : ChapterTraceProbe<Dl14aChapterProbe.S>
    {
        internal struct S
        {
            public double T, W1, W2, Door, GownX, GownBase, BagX, BagBase;
            public int T1, T2, Winds;
            public bool Braked, Open;
            public string Gown, Bag;
        }

        private CycleClock _light; private CycleBrake _brake; private PairedBlindDrive _blinds; private Door _door; private CarriedItem _gown, _bag;

        public override string Scene => "DL-14a";
        public override int FirstStep => 8265;
        public override IReadOnlyList<string> KeyActs => new[] { "dl14a.brake:Clip", "dl14a.crank:Clip", "dl14a.basket:Lift", "dl14a.hook:SetDownHigh" };
        public override IReadOnlyList<(int step, string cue)> KeyCues => new[] { (0, "sound:door") };

        public override void Bind(ChapterSim sim, Trace t)
        {
            var g = sim.Graph;
            _light = g.Get<CycleClock>("dl14a.nightLight"); _brake = g.Get<CycleBrake>("dl14a.brake"); _blinds = g.Get<PairedBlindDrive>("dl14a.blinds");
            _door = g.Get<Door>("dl14a.door"); _gown = g.Get<CarriedItem>("dl14a.gown"); _bag = g.Get<CarriedItem>("dl14a.bag");
        }

        protected override S Sample(ChapterSim sim) => new S
        {
            T = _light.Phase, Braked = _brake.Engaged, W1 = _blinds.A, W2 = _blinds.B, T1 = (int)_blinds.TargetA, T2 = (int)_blinds.TargetB,
            Winds = _blinds.Winds, Door = _door.Position, Open = _door.State != DoorState.Closed,
            GownX = _gown.X, GownBase = _gown.BaseY, Gown = Name(_gown, false), BagX = _bag.X, BagBase = _bag.BaseY, Bag = Name(_bag, true),
        };

        public override string ExpectedAct(Trace t, TraceStep p) => AttendanceActs.Expected(p);

        public override void CheckMechanisms(ChapterTraceRun run, List<string> bad)
        {
            var rows = run.Rows;
            int to = run.RowAfter(Scene);
            for (int k = 0; k <= to; k++)
            {
                var p = rows[k].P; var w = Samples[k];
                Check(bad, p.I, "night.t", p.Nt14a.Value, w.T);
                if (p.Nk14a.Value != w.Braked) bad.Add($"#{p.I} braked {p.Nk14a} vs {w.Braked}");
                Check(bad, p.I, "w1", p.W1a.Value, w.W1);
                Check(bad, p.I, "w2", p.W2a.Value, w.W2);
                if (p.T1a.Value != w.T1 || p.T2a.Value != w.T2) bad.Add($"#{p.I} targets {p.T1a}/{p.T2a} vs {w.T1}/{w.T2}");
                if (p.Wn14a.Value != w.Winds) bad.Add($"#{p.I} winds {p.Wn14a} vs {w.Winds}");
                Check(bad, p.I, "door", p.Do14a.Value, w.Door);
                if (p.Op14a.Value != w.Open) bad.Add($"#{p.I} open {p.Op14a} vs {w.Open}");
                Check(bad, p.I, "gown.x", p.Gx14a.Value, w.GownX);
                Check(bad, p.I, "gown.base", p.Gb14a.Value, w.GownBase);
                if (p.Gs14a != w.Gown) bad.Add($"#{p.I} gown {p.Gs14a} vs {w.Gown}");
                Check(bad, p.I, "bag.x", p.Bx14a.Value, w.BagX);
                Check(bad, p.I, "bag.base", p.Bb14a.Value, w.BagBase);
                if (p.Bs14a != w.Bag) bad.Add($"#{p.I} bag {p.Bs14a} vs {w.Bag}");
            }
            Assert.Equal(10392, rows[to].P.I);
        }

        private static string Name(CarriedItem c, bool bag)
        {
            switch (c.State)
            {
                case ItemState.Placed:
                    return c.Slot == Dl14aScene.HookSlot ? "hook" : bag ? "basket" : "wallpeg";
                case ItemState.Carried: return "carried";
                case ItemState.Floor: return "floor";
                default: return c.State.ToString();
            }
        }
    }
}
