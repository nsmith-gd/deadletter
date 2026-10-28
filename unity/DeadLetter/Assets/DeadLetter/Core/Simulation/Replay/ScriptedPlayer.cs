using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Simulation.Replay
{
    /// <summary>A script gave up: it waited or walked past its limit (bot.js's <c>throw new Error('stuck: …')</c>).</summary>
    public sealed class SimStuckException : Exception
    {
        public SimStuckException(string message) : base(message) { }
    }

    /// <summary>Options for <see cref="ScriptedPlayer.Walk"/> (bot.js's <c>o</c>).</summary>
    public struct WalkOptions
    {
        /// <summary>Give up after this many seconds (default 240).</summary>
        public double Max;
        /// <summary>Return once he has stood still this long (0 = never).</summary>
        public double Stall;
        /// <summary>Don't hop when he stands still against something.</summary>
        public bool NoHop;
        /// <summary>Keep pressing the direction during an act (pushing).</summary>
        public bool KeepHolding;
        /// <summary>Hold the Run modifier, i.e. walk (auto-run is on).</summary>
        public bool Quiet;

        public static WalkOptions Default => new WalkOptions();
    }

    /// <summary>
    /// A C# port of bot.js's simulated player (tools/sim/bot.js L5–L110): coroutines over a 60 Hz step that drive the
    /// same input a pad does. A scene script is an iterator: <c>yield return null</c> ends the step, and nested helpers
    /// are spliced with <c>foreach (var s in Walk(...)) yield return s;</c> (C#'s <c>yield*</c>).
    /// <para>Every action is a real one in the game. In first-playthrough mode the <see cref="PlayerModel"/> adds the
    /// time a person spends looking, thinking and trying the wrong thing first; mechanical mode gives the shortest run.</para>
    /// <para>One call of <see cref="Tick"/> is bot.js's <c>__sim.bot()</c>: marks, then one step of the script, then
    /// the input for this step. Press flags are consumed by the step, as the game consumes them (L8527).</para>
    /// </summary>
    public abstract class ScriptedPlayer
    {
        private IEnumerator<object> _script;
        private double _move;
        private bool _jumpPressed, _jumpHeld, _usePressed, _shift;
        private int _jumpUp;

        protected ScriptedPlayer(PlayerModel player)
        {
            P = player;
            Out = new SimResult { Seed = player.Seed, Skill = player.Skill, Curious = player.Curious };
        }

        /// <summary>The scene being played (set by <see cref="Begin"/>).</summary>
        protected ISimView G { get; private set; }
        protected PlayerModel P { get; }
        public SimResult Out { get; }
        public bool Done => Out.Done;
        /// <summary>Whether the last <see cref="Walk"/> ended by stalling rather than arriving.</summary>
        protected bool LastWalkStalled { get; private set; }

        /// <summary>The scene's script, from the first step to the end (bot.js's <c>script</c>).</summary>
        protected abstract IEnumerable<object> Script();

        public void Begin(ISimView view)
        {
            G = view;
            _script = Script().GetEnumerator();
        }

        /// <summary>bot.js's <c>__sim.bot()</c>: called once before each step; returns that step's input.</summary>
        public MotorInput Tick()
        {
            if (_jumpUp > 0 && --_jumpUp == 0) _jumpHeld = false;
            if (!Out.Done)
            {
                if (G.Playing && G.Checkpoint != null) Mark("cp " + G.Checkpoint);
                if (G.Playing && Out.HasMark("play")) Mark(SceneKey(G.SceneName));
                try
                {
                    if (!_script.MoveNext()) Finish();
                }
                catch (SimStuckException e)
                {
                    Out.Error = e.Message;
                    Out.Done = true;
                    _move = 0;
                }
            }
            var input = new MotorInput
            {
                Move = _move,
                JumpPressed = _jumpPressed,
                JumpHeld = _jumpHeld,
                UsePressed = _usePressed,
                UseHeld = false,                         // bot.js never holds Use (it sets usePressed only, L29)
                RunModifierHeld = _shift,
            };
            _jumpPressed = false;
            _usePressed = false;
            return input;
        }

        /// <summary>The end of the script (bot.js: <c>out.deaths = G.deaths; out.found = …; out.done = true</c>).</summary>
        private void Finish()
        {
            Mark("end");
            Out.Deaths = G.Deaths;
            Out.Found = G.Found;
            Out.Done = true;
            _move = 0;
        }

        /// <summary>"DL-01 The Wake" → "DL-01" (<c>D.scene().split(' ')[0]</c>).</summary>
        public static string SceneKey(string sceneName)
        {
            if (string.IsNullOrEmpty(sceneName)) return "?";
            int sp = sceneName.IndexOf(' ');
            return sp < 0 ? sceneName : sceneName.Substring(0, sp);
        }

        // ---- input ----------------------------------------------------------------------------------------------
        protected void Move(double dir) { _move = dir > 0 ? 1 : dir < 0 ? -1 : 0; }
        /// <summary>Press jump and hold it for 8 steps (<c>jumpUp = 8</c>).</summary>
        protected void Jump() { _jumpPressed = true; _jumpHeld = true; _jumpUp = 8; }
        protected void Use() { _usePressed = true; }

        // ---- marks and notes --------------------------------------------------------------------------------------
        protected void Mark(string key) => Out.Mark(key, G.Clock);

        /// <summary>An event line, timed from the start of play (<c>note</c>, bot.js L24).</summary>
        protected void Note(string s)
        {
            double t = G.Clock - (Out.TryGetMark("play", out var play) ? play : G.Clock);
            Out.Events.Add(t.ToString("0.0", System.Globalization.CultureInfo.InvariantCulture) + " " + s);
        }

        // ---- coroutines -------------------------------------------------------------------------------------------
        protected IEnumerable<object> Wait(double sec)
        {
            double t = G.Clock + sec;
            while (G.Clock < t) yield return null;
        }

        protected IEnumerable<object> Until(Func<bool> pred, double max, string label)
        {
            double t = G.Clock + max;
            while (!pred())
            {
                if (G.Clock > t) throw new SimStuckException("stuck: " + label + " x=" + Fx(G.X));
                yield return null;
            }
        }

        /// <summary>Walk one way until <paramref name="pred"/>; hop when he has stood still against something for a reaction time.</summary>
        protected IEnumerable<object> Walk(int dir, Func<bool> pred, string label, WalkOptions o = default)
        {
            double last = G.X, still = 0, r = P.React(), t0 = G.Clock, max = o.Max > 0 ? o.Max : 240;
            LastWalkStalled = false;
            if (o.Quiet) _shift = true;
            try
            {
                while (!pred())
                {
                    if (G.Clock - t0 > max) throw new SimStuckException("stuck walking: " + label + " x=" + Fx(G.X));
                    Move(G.Act != null && !o.KeepHolding && !G.ActCancellable ? 0 : dir);   // a player's move cancels a quirk
                    bool moved = Math.Abs(G.X - last) > 0.0008;
                    last = G.X;
                    if (!moved && G.Grounded && !G.Mantling && G.Act == null && !G.Riding) still += 1.0 / 60; else still = 0;
                    if (o.Stall > 0 && still > o.Stall) { LastWalkStalled = true; yield break; }
                    if (!o.NoHop && still > r) { Jump(); still = 0; r = P.React(); }
                    yield return null;
                }
            }
            finally
            {
                Move(0);
                if (o.Quiet) _shift = false;
            }
        }

        protected IEnumerable<object> GoTo(double x, string label, WalkOptions o = default)
        {
            int d = Math.Sign(x - G.X);
            if (d == 0) d = 1;
            return Walk(d, () => d > 0 ? G.X >= x : G.X <= x, label, o);
        }

        /// <summary>Walk toward x until the game offers one of <paramref name="near"/>, then press Use until it starts.</summary>
        protected IEnumerable<object> UseAt(string[] near, double x, Func<bool> started, string label, WalkOptions o = default)
        {
            Func<bool> ok = () => Array.IndexOf(near, G.Near) >= 0;
            if (!ok())
            {
                int d = Math.Sign(x - G.X); if (d == 0) d = 1;
                foreach (var s in Walk(d, () => ok() || (d > 0 ? G.X >= x + 0.4 : G.X <= x - 0.4), label, o)) yield return s;
            }
            if (!ok())
            {
                int d = Math.Sign(x - G.X); if (d == 0) d = 1;
                var back = o; if (back.Max <= 0) back.Max = 30;   // { max: 30, ...o }: a caller's max wins (L56)
                foreach (var s in Walk(d, ok, label + " (back)", back)) yield return s;
            }
            for (int k = 0; k < 12; k++)
            {
                foreach (var s in Wait(P.React() * 0.5)) yield return s;
                Use(); yield return null; yield return null;
                double t = G.Clock + 1.2;
                while (G.Clock < t && !started()) yield return null;
                if (started()) yield break;
            }
            throw new SimStuckException("use failed: " + label + " near=" + (G.Near ?? "null") + " x=" + Fx(G.X) + " y=" + Fx(G.Y)
                + " act=" + (G.Act ?? "null") + " hold=" + G.Hold);
        }

        /// <summary>Until he is free and on the ground (<c>settle</c>).</summary>
        protected IEnumerable<object> Settle(double max = 30) =>
            Until(() => G.Act == null && !G.Mantling && G.Grounded, max, "settle");

        /// <summary>Wait for control (<c>opening</c>, bot.js L109–L113).</summary>
        protected IEnumerable<object> Opening()
        {
            Mark("opening");
            foreach (var s in Until(() => G.Playing, 120, "opening")) yield return s;
            Mark("play");
        }

        /// <summary>Run <paramref name="inner"/>, and stop it quietly if it gets stuck (bot.js's <c>try { … } catch (e) { }</c>).</summary>
        protected static IEnumerable<object> Attempt(IEnumerable<object> inner)
        {
            using (var e = inner.GetEnumerator())
            {
                while (true)
                {
                    try { if (!e.MoveNext()) yield break; }
                    catch (SimStuckException) { yield break; }
                    yield return null;
                }
            }
        }

        /// <summary>Walking about a room while working it out: to somewhere else in it and back (<c>wander</c>).</summary>
        protected IEnumerable<object> Wander(double lo, double hi, double p)
        {
            if (!P.Mistakes || !P.Chance(p)) yield break;
            double x = P.Uniform(lo, hi), back = G.X;
            Note("wanders to " + x.ToString("0.0", System.Globalization.CultureInfo.InvariantCulture));
            foreach (var s in Attempt(WanderLeg(x, back))) yield return s;
        }

        private IEnumerable<object> WanderLeg(double x, double back)
        {
            foreach (var s in GoTo(x, "wander", new WalkOptions { Max = 25 })) yield return s;
            foreach (var s in Wait(P.Think(2))) yield return s;
            foreach (var s in GoTo(back, "wander back", new WalkOptions { Max = 25 })) yield return s;
        }

        protected Func<bool> ActIs(string kind) => () => G.Act == kind;

        protected static string Fx(double v) => v.ToString("0.00", System.Globalization.CultureInfo.InvariantCulture);
    }
}
