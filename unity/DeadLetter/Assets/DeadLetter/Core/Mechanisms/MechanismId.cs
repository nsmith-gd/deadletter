using System;

namespace DeadLetter.Core.Mechanisms
{
    /// <summary>
    /// A mechanism's stable ID, as in port_architecture §4.13 and §5: <c>scope.name</c>, e.g. <c>dl01.latch</c>,
    /// <c>dl14a.nightLight</c>, <c>att.relays</c>. Scope is lower-case letters and digits; name starts with a letter and
    /// is letters and digits (camelCase). IDs are save data: never rename one that has shipped.
    /// <c>default(MechanismId)</c> is <see cref="None"/> (an unwired optional input).
    /// </summary>
    public readonly struct MechanismId : IEquatable<MechanismId>
    {
        public static readonly MechanismId None = default;

        public readonly string Value;

        public MechanismId(string value)
        {
            if (!IsValid(value)) throw new ArgumentException("Bad mechanism ID '" + value + "': expected scope.name, e.g. dl01.latch.", nameof(value));
            Value = value;
        }

        public bool IsNone => Value == null;

        public static implicit operator MechanismId(string value) => value == null ? None : new MechanismId(value);

        public static bool IsValid(string s)
        {
            if (string.IsNullOrEmpty(s)) return false;
            int dot = s.IndexOf('.');
            if (dot < 1 || dot == s.Length - 1 || s.IndexOf('.', dot + 1) >= 0) return false;
            if (s[0] < 'a' || s[0] > 'z') return false;
            for (int i = 1; i < dot; i++) if (!IsLower(s[i]) && !IsDigit(s[i])) return false;
            if (!IsLower(s[dot + 1]) && !IsUpper(s[dot + 1])) return false;
            for (int i = dot + 2; i < s.Length; i++) if (!IsLower(s[i]) && !IsUpper(s[i]) && !IsDigit(s[i])) return false;
            return true;
        }

        private static bool IsLower(char c) => c >= 'a' && c <= 'z';
        private static bool IsUpper(char c) => c >= 'A' && c <= 'Z';
        private static bool IsDigit(char c) => c >= '0' && c <= '9';

        public bool Equals(MechanismId other) => string.Equals(Value, other.Value, StringComparison.Ordinal);
        public override bool Equals(object obj) => obj is MechanismId o && Equals(o);
        public override int GetHashCode() => Value == null ? 0 : StringComparer.Ordinal.GetHashCode(Value);
        public static bool operator ==(MechanismId a, MechanismId b) => a.Equals(b);
        public static bool operator !=(MechanismId a, MechanismId b) => !a.Equals(b);
        public override string ToString() => Value ?? "(none)";
    }
}
