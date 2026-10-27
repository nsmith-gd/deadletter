using System;
using System.Collections.Generic;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Bridges;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Drives;
using DeadLetter.Core.Scenes;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-01 in the chapter replay (as <see cref="Dl01TraceTests"/>): the shutter, the latch, the counterweight, the crank and
    /// its door, the cart and the relay, to <c>room</c>. It names the acts to <c>room</c>: the passage's last legs are in
    /// region 2, DL-02 by <c>sceneName</c>.
    /// </summary>
    internal sealed class Dl01ChapterProbe : ChapterTraceProbe<Dl01ChapterProbe.S>
    {
        internal struct S
        {
            public double Shutter, Lever, WeightY, Door, Wheel, CartX, CartDrop, Relay;
            public bool Released, Lip;
            public string CartState;
            public int RelaySets;
        }

        private Door _shutter; private Latch _latch; private CrankActuator _crank; private TippingBridge _cart; private PulseSequencer _relay;
        private MechanismGraph _g;
        private int _room;

        public override string Scene => "DL-01";
        public override int FirstStep => 1768;                                         // the opening's last step: play starts
        public override IReadOnlyList<string> KeyActs => new[] { "quirk:CheckLabel", "dl01.latch:Flinch", "transit:3" };
        public override IReadOnlyList<(int step, string cue)> KeyCues => new[] { (1768, "voice:dispatch_item"), (0, "music:threshold") };

        public override void Bind(ChapterSim sim, Trace t)
        {
            _g = sim.Graph;
            _shutter = _g.Get<Door>("dl01.shutter"); _latch = _g.Get<Latch>("dl01.latch");
            _crank = _g.Get<CrankActuator>("dl01.crank"); _cart = _g.Get<TippingBridge>("dl01.cart");
            _relay = _g.Get<PulseSequencer>("dl01.relay");
            _room = t.FirstIndex(p => p.Cp == "room");
        }

        protected override S Sample(ChapterSim sim)
        {
            int sets = 0;
            var log = _g.Log;
            for (int e = 0; e < log.Count; e++)
                if (log[e].Id == "dl01.relay" && log[e].Kind == MechanismEventKind.Event && log[e].Code == (int)PulseEvent.LampLit && log[e].Index == 0) sets++;
            return new S
            {
                Shutter = _shutter.Position, Lever = _latch.LeverDeg, WeightY = Door.ShutterCounterweightY(_shutter.Elapsed),
                Released = _latch.State == LatchState.Released, Door = _crank.Position, Wheel = _crank.WheelDeg,
                CartX = _cart.X, CartDrop = _cart.Drop, CartState = _cart.State.ToString(), Lip = _cart.State == TippingBridgeState.AtLip,
                Relay = _relay.Units, RelaySets = sets,
            };
        }

        public override bool ClaimsAct(TraceStep p) => p.I <= _room;

        public override string ExpectedAct(Trace t, TraceStep p) => Dl01TraceTests.ExpectedAct(p);

        public override void CheckMechanisms(ChapterTraceRun run, List<string> bad)
        {
            var rows = run.Rows;
            int room = rows.FindIndex(w => w.P.Cp == "room"), relays = 0;
            for (int k = 0; k <= room; k++)
            {
                var p = rows[k].P; var w = Samples[k];
                Check(bad, p.I, "shutterAngle", p.Sh, w.Shutter);
                Check(bad, p.I, "leverAngle", p.Lv, w.Lever);
                Check(bad, p.I, "weightY", p.Wy, w.WeightY);
                Check(bad, p.I, "doorOpen", p.Door, w.Door);
                double d = Math.Abs(w.Wheel - p.Wh);
                if (Math.Min(d, Math.Abs(d - 60)) > Tol) bad.Add($"#{p.I} wheel {p.Wh} vs {w.Wheel}");   // modulo a stroke, as there
                Check(bad, p.I, "cart.x", p.Cx.Value, w.CartX);
                Check(bad, p.I, "cart.drop", p.Cd.Value, w.CartDrop);
                Check(bad, p.I, "frame (relay clock)", p.Fr, w.Relay);
                string cs = w.CartState == "AtLip" ? "free" : w.CartState.ToLowerInvariant();
                if (cs != p.Cs) bad.Add($"#{p.I} cart.state {p.Cs} vs {w.CartState}");
                if (w.Lip != p.Cl) bad.Add($"#{p.I} cart.lip {p.Cl} vs {w.Lip}");
                if (w.Released != p.Rel) bad.Add($"#{p.I} released {p.Rel} vs {w.Released}");
                bool protoSet = k == 0 ? p.Nr != 480 : p.Nr != rows[k - 1].P.Nr;
                if (protoSet != (w.RelaySets > 0)) bad.Add($"#{p.I} relay set {protoSet} vs {w.RelaySets}");
                relays += w.RelaySets;
            }
            Assert.Equal(7, relays);
        }
    }
}
