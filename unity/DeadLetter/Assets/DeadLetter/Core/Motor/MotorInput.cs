using System;

namespace DeadLetter.Core.Motor
{
    /// <summary>
    /// One Core step's input (port_architecture §4.4 <c>InputFrame</c>). Runtime fills it from the Input System;
    /// edge flags (<see cref="JumpPressed"/>, <see cref="UsePressed"/>) are latched by Runtime until a step consumes
    /// them (L8527), so a press between two fixed steps is never lost.
    /// </summary>
    public struct MotorInput
    {
        /// <summary>Lane axis in [-1, 1] after the deadzone (see <see cref="FromStick"/>). Keys give ±1.</summary>
        public double Move;
        /// <summary>True when <see cref="Move"/> came from an analog stick: then only |axis| &gt; 0.65 can run (L1927).</summary>
        public bool MoveIsAnalog;
        public bool JumpPressed;
        public bool JumpHeld;
        public bool UsePressed;
        public bool UseHeld;
        /// <summary>
        /// The Run action: Shift / B / RB. It inverts auto-run, as the prototype's walk modifier does (L1921–L1929):
        /// with auto-run on (default) holding it walks; with auto-run off holding it runs.
        /// </summary>
        public bool RunModifierHeld;
        /// <summary>
        /// Manual crouch (new in the port; the prototype only auto-crouches from ceiling clearance, L1975). Holding it
        /// on the ground keeps him crouched; releasing hands back to the clearance rule.
        /// </summary>
        public bool CrouchHeld;

        /// <summary>The prototype's stick rule (L1266): values inside the deadzone are 0, others pass unscaled.</summary>
        public static double FromStick(double raw, double deadzone = 0.22)
        {
            if (double.IsNaN(raw)) return 0;
            if (raw > 1) raw = 1; else if (raw < -1) raw = -1;
            return Math.Abs(raw) > deadzone ? raw : 0;
        }

        public static MotorInput None => default;
    }
}
