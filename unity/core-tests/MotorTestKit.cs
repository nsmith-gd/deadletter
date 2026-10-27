using System;
using System.Collections.Generic;
using System.Text;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Tests
{
    /// <summary>Shared helpers: a 60 Hz stepper and minimal implementations of the U-10 contracts.</summary>
    internal static class Sim
    {
        public const double Dt = 1.0 / 60.0;

        public static D17Motor Make(BoxWorld world, double x = 0, double y = 0, InteractionResolver resolver = null, int facing = 1,
            MotorConfig config = null)
        {
            var m = new D17Motor(config ?? MotorConfig.Prototype(), world, resolver);
            m.Place(x, y, facing);
            return m;
        }

        public static MotorInput Move(double move) => new MotorInput { Move = move };
        public static MotorInput Jump(double move = 0) => new MotorInput { Move = move, JumpPressed = true, JumpHeld = true };
        public static MotorInput Use() => new MotorInput { UsePressed = true, UseHeld = true };

        /// <summary>Steps <paramref name="steps"/> times; returns true if an event of <paramref name="kind"/> fired.</summary>
        public static bool Run(D17Motor m, MotorInput input, int steps, MotorEventKind? kind = null)
        {
            bool seen = false;
            for (int i = 0; i < steps; i++)
            {
                m.Step(input, Dt);
                if (kind.HasValue && Has(m, kind.Value)) seen = true;
            }
            return seen;
        }

        /// <summary>Steps until <paramref name="until"/> holds; returns the number of steps taken (or -1).</summary>
        public static int RunUntil(D17Motor m, MotorInput input, Func<D17Motor, bool> until, int max = 2000)
        {
            for (int i = 1; i <= max; i++)
            {
                m.Step(input, Dt);
                if (until(m)) return i;
            }
            return -1;
        }

        public static bool Has(D17Motor m, MotorEventKind kind, string name = null)
        {
            foreach (var e in m.Events)
                if (e.Kind == kind && (name == null || e.Name == name)) return true;
            return false;
        }

        public static string Snapshot(D17Motor m)
        {
            var sb = new StringBuilder();
            sb.Append(m.X.ToString("R")).Append(',').Append(m.Y.ToString("R")).Append(',').Append(m.Z.ToString("R")).Append(',')
              .Append(m.Vx.ToString("R")).Append(',').Append(m.Vy.ToString("R")).Append(',').Append(m.Facing).Append(',')
              .Append(m.Yaw.ToString("R")).Append(',').Append(m.State).Append(',').Append(m.Clip).Append(',')
              .Append(m.ClipTimeScale.ToString("R"));
            foreach (var e in m.Events) sb.Append('|').Append(e);
            return sb.ToString();
        }
    }

    internal sealed class TestItem : ICarryable
    {
        public double X { get; set; }
        public double BaseY { get; set; }
        public double Radius { get; set; } = 0.1;
        public double BelowWrist { get; set; } = 0.28;
        public bool IsLight { get; set; }
        public bool Carried;
        public int LiftedAtStep = -1;
        public D17Motor Motor;
        public InteractionCategory Category => InteractionCategory.Item;
        public bool IsAvailable(in InteractionQuery q) => !Carried;
        public void OnLifted() { Carried = true; LiftedAtStep = Motor != null ? (int)Motor.StepCount : 0; }
        public void OnSetDown(double x, double baseY) { Carried = false; X = x; BaseY = baseY; }
    }

    internal sealed class TestPushable : IPushable
    {
        public double X { get; set; }
        public int Side { get; set; } = 1;
        public double Gap { get; set; } = 0.6;
        public double Speed { get; set; } = 0.4;
        public double Min { get; set; }
        public double Max { get; set; }
        public double FloorY { get; set; }
        public double Z { get; set; }
        public double ForwardReach { get; set; } = 0.34;
        public double BackReach { get; set; } = 0.34;
        public bool TipsIntoPit { get; set; }
        public bool HasDetents { get; set; }
        public bool Released, Tipped, Ended, Shoved, AtLip;
        public InteractionCategory Category => InteractionCategory.Push;
        public bool IsAvailable(in InteractionQuery q) => true;
        public void MoveTo(double x, double velocity) { X = x; }
        public void SetAtLip(bool atLip) { AtLip = atLip; }
        public void OnReleased(bool atLip) { Released = true; Tipped |= atLip; }
        public void OnShoved() { Shoved = true; Tipped = true; }
        public void OnTravelEnd() { Ended = true; }
    }

    internal class TestStation : IStation
    {
        public double StandX { get; set; }
        public double Reach { get; set; } = 0.3;
        public double StandZ { get; set; }
        public int Face { get; set; } = 1;
        public double AnchorX => StandX;
        public InteractionCategory Category { get; set; } = InteractionCategory.Fixed;
        public bool IsAvailable(in InteractionQuery q) => true;
    }

    internal sealed class TestPresent : TestStation, IPresentTarget
    {
        public readonly List<(PresentBeat beat, double frame)> Beats = new List<(PresentBeat, double)>();
        public D17Motor Motor;
        public void OnPresentBeat(PresentBeat beat) => Beats.Add((beat, Motor.ClipTime * 24));
    }

    internal sealed class TestSeat : TestStation, ISeat
    {
        public readonly List<bool> Calls = new List<bool>();
        public void OnSeated(bool seated) => Calls.Add(seated);
    }

    internal sealed class TestLever : TestStation, IUsable
    {
        public ActProfile Profile { get; set; } = new ActProfile("LeverPull", turnIntoSet: true);
        public int ThrownCount;
        public double LastFrame;
        public bool OnActFrame(in ActFrame f)
        {
            LastFrame = f.Frame;
            if (f.Crossed(ClipTimings.LeverEvents.Throw)) ThrownCount++;
            return ClipClock.Reached(f.Frame, ClipTimings.LeverEvents.Out);
        }
    }
}
