using System.Collections.Generic;
using System.Globalization;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Water;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl17;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-17 in Chapter 1's replay (<see cref="AttendanceChapterTraceTests"/>): <c>workshop</c> (#17921), the tray off the plan
    /// chest (#18102) and set down, the drawer (#18683), her drawing read (#18805–#19221) and his label checked (#19240), sluices
    /// A and C shut (#19877, #19999), the valve (#20141), bed 1's float latched (#20521), the stair door, and out by the stair
    /// at the trace's last step (#20841), from DL-17's first step (#17898). The rig is compared from the chapter's first step.
    /// </summary>
    internal sealed class Dl17ChapterProbe : ChapterTraceProbe<Dl17ChapterProbe.S>
    {
        internal struct S
        {
            public double TrayX, TrayBase, Drawer, Tank, Run, Bed0, Bed1, Bed2, Latch, Door;
            public string Tray, Sluices;
            public bool Read, Latched, Ended;
        }

        private CarriedItem _tray; private Dl17Drawer _drawer; private Sluice[] _sluices; private SluiceRig _rig; private FloatLatch _latch; private Door _door;
        private Dl17Rules _rules;

        public override string Scene => "DL-17";
        public override int FirstStep => 17898;
        public override IReadOnlyList<string> KeyActs => new[] { "dl17.tray:Lift", "dl17.drawer:Tug", "dl17.read:ReadRoute", "quirk:CheckLabel", "dl17.sluiceA:Clip", "dl17.valve:Clip" };
        public override IReadOnlyList<(int step, string cue)> KeyCues => new[] { (20841, "music:endAtt") };

        public override void Bind(ChapterSim sim, Trace t)
        {
            var g = sim.Graph;
            _tray = g.Get<CarriedItem>("dl17.tray"); _drawer = g.Get<Dl17Drawer>("dl17.drawer");
            _sluices = new[] { g.Get<Sluice>("dl17.sluiceA"), g.Get<Sluice>("dl17.sluiceB"), g.Get<Sluice>("dl17.sluiceC") };
            _rig = g.Get<SluiceRig>("dl17.rig"); _latch = g.Get<FloatLatch>("dl17.latch"); _door = g.Get<Door>("dl17.stairDoor");
            _rules = (Dl17Rules)sim.RulesOf(sim.Def.Scene("DL-17"));
        }

        protected override S Sample(ChapterSim sim) => new S
        {
            TrayX = _tray.X, TrayBase = _tray.BaseY, Tray = _tray.State == ItemState.Placed ? "wedged" : _tray.State == ItemState.Carried ? "carried" : "floor",
            Drawer = _drawer.Position, Read = _rules.Read,
            Sluices = (_sluices[0].Engaged ? "1" : "0") + "," + (_sluices[1].Engaged ? "1" : "0") + "," + (_sluices[2].Engaged ? "1" : "0"),
            Tank = _rig.Tank, Run = _rig.RunLeft, Bed0 = _rig.Bed(0), Bed1 = _rig.Bed(1), Bed2 = _rig.Bed(2),
            Latch = _latch.Lift, Latched = _latch.Engaged, Door = _door.Position, Ended = _rules.Ended,
        };

        public override string ExpectedAct(Trace t, TraceStep p) => AttendanceActs.Expected(p);

        public override void CheckMechanisms(ChapterTraceRun run, List<string> bad)
        {
            var rows = run.Rows;
            int to = run.RowAfter(Scene);
            for (int k = 0; k <= to; k++)
            {
                var p = rows[k].P; var w = Samples[k];
                var ty = p.Ty17.Split(',');
                Check(bad, p.I, "tray.x", double.Parse(ty[0], CultureInfo.InvariantCulture), w.TrayX);
                Check(bad, p.I, "tray.base", double.Parse(ty[1], CultureInfo.InvariantCulture), w.TrayBase);
                if (ty[2] != w.Tray) bad.Add($"#{p.I} tray {ty[2]} vs {w.Tray}");
                Check(bad, p.I, "drawer", p.Dr17.Value, w.Drawer);
                if (p.Rd17.Value != w.Read || p.Ky17.Value != w.Read) bad.Add($"#{p.I} read/key {p.Rd17}/{p.Ky17} vs {w.Read}");
                if (p.Sl17 != w.Sluices) bad.Add($"#{p.I} sluices {p.Sl17} vs {w.Sluices}");
                Check(bad, p.I, "tank", p.Tk17.Value, w.Tank);
                Check(bad, p.I, "run", p.Ru17.Value, w.Run);
                var beds = TraceStep.Numbers(p.Be17);
                Check(bad, p.I, "bed1", beds[0], w.Bed0); Check(bad, p.I, "bed2", beds[1], w.Bed1); Check(bad, p.I, "bed3", beds[2], w.Bed2);
                Check(bad, p.I, "latch", p.Lt17.Value, w.Latch);
                if (p.Ld17.Value != w.Latched) bad.Add($"#{p.I} latched {p.Ld17} vs {w.Latched}");
                Check(bad, p.I, "door", p.Do17.Value, w.Door);
                if (p.En17.Value != w.Ended) bad.Add($"#{p.I} ended {p.En17} vs {w.Ended}");
            }
            Assert.Equal(20841, rows[to].P.I);
            Assert.True(rows[to].Exited);
        }
    }
}
