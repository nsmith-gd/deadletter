using System;
using System.Collections.Generic;

namespace DeadLetter.Core.Simulation
{
    /// <summary>
    /// Interns names into small integers (0 is the empty name): the table behind <see cref="Cues.CueId"/> and
    /// <see cref="Scenes.ActId"/>, so a step names a cue or an act by an integer and allocates nothing. Interning locks;
    /// reading a name back does not (the array is copy-on-write). Intern once, into a static field, not per step.
    /// </summary>
    internal sealed class NameTable
    {
        private readonly object _gate = new object();
        private readonly Dictionary<string, int> _ids = new Dictionary<string, int>(StringComparer.Ordinal);
        private string[] _names = { "" };

        /// <summary>The number of <paramref name="name"/>, interned on first use.</summary>
        public int Of(string name, string what)
        {
            if (string.IsNullOrEmpty(name)) throw new ArgumentException("A " + what + " needs a name.", nameof(name));
            lock (_gate)
            {
                if (_ids.TryGetValue(name, out int id)) return id;
                var names = new string[_names.Length + 1];
                Array.Copy(_names, names, _names.Length);
                names[_names.Length] = name;
                _ids.Add(name, _names.Length);
                _names = names;
                return names.Length - 1;
            }
        }

        public string Name(int id) => _names[id];
    }
}
