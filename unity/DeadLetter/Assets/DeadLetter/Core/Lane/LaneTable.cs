using System;

namespace DeadLetter.Core.Lane
{
    /// <summary>Which ends of a <see cref="LaneSpan"/> belong to it. The prototype mixes <c>x &gt; a &amp;&amp; x &lt; b</c> and <c>x &gt;= a &amp;&amp; x &lt;= b</c>; the port keeps each test as written.</summary>
    public enum SpanEdges
    {
        /// <summary><c>x0 ≤ x ≤ x1</c> (platforms, boxes: <c>PLATFORMS</c>, L1722).</summary>
        Closed,
        /// <summary><c>x0 &lt; x &lt; x1</c> (pits and floors: <c>x &gt; PIT.x0 &amp;&amp; x &lt; PIT.x1</c>, L1716).</summary>
        Open,
        /// <summary><c>x0 ≤ x &lt; x1</c> (<c>onRamp</c>, L6351).</summary>
        ClosedOpen,
        /// <summary><c>x0 &lt; x ≤ x1</c>.</summary>
        OpenClosed,
    }

    /// <summary>A stretch of the lane with a height: a floor level, a standable top, or a ceiling's underside (metres).</summary>
    public readonly struct LaneSpan
    {
        public readonly double X0, X1, Y;
        public readonly SpanEdges Edges;

        public LaneSpan(double x0, double x1, double y, SpanEdges edges)
        {
            if (!(x1 >= x0)) throw new ArgumentException("A span needs x0 <= x1.");
            X0 = x0; X1 = x1; Y = y; Edges = edges;
        }

        public bool Contains(double x)
        {
            switch (Edges)
            {
                case SpanEdges.Open: return x > X0 && x < X1;
                case SpanEdges.ClosedOpen: return x >= X0 && x < X1;
                case SpanEdges.OpenClosed: return x > X0 && x <= X1;
                default: return x >= X0 && x <= X1;
            }
        }

        public override string ToString() => (Edges == SpanEdges.Closed || Edges == SpanEdges.ClosedOpen ? "[" : "(") + X0 + ", " + X1
            + (Edges == SpanEdges.Closed || Edges == SpanEdges.OpenClosed ? "]" : ")") + " @ " + Y;
    }

    /// <summary>
    /// One region's static lane (port_architecture §4.6): what never moves. Everything that moves (a cart, a shutter, a
    /// gate, a lift floor) is an <see cref="ILaneContributor"/> registered on the same region. A scene's table lives in
    /// <c>Lane/Tables/</c> (one static class per scene, every value cited to index.html), and is resolved into world x
    /// (the prototype's OFF offsets baked in, §0.1). Probes, in the prototype's order:
    /// <list type="number">
    /// <item><b>floor</b> = the first <see cref="Floors"/> span containing x, else <see cref="Floor"/> (<c>floorAt</c>'s if-chain, L1711–L1717); contributors may override.</item>
    /// <item><b>surface</b> = max(floor, every <see cref="Platforms"/> span containing x) (<c>surfaceAt</c>, L1719–L1723); contributors may raise it.</item>
    /// <item><b>ceiling</b> = min(<see cref="Ceiling"/>, every <see cref="Ceilings"/> span containing x) (<c>ceilingAt</c>, L1624–L1642); contributors may lower or replace it.</item>
    /// <item><b>limits</b> = [<see cref="Left"/>, <see cref="Right"/>] (<c>leftLimit0/rightLimit0</c>, L1752–L1769); contributors narrow them.</item>
    /// <item><b>ramp</b> = x in a <see cref="Ramps"/> zone: the step-up allowance is the motor's ramp value (<c>onRamp</c>, L6351, used at L2004).</item>
    /// </list>
    /// </summary>
    public sealed class LaneTable
    {
        /// <summary>For messages and tests, e.g. "DL-01 (region 1)".</summary>
        public string Name = "";
        /// <summary>Walls for D-17's centre.</summary>
        public double Left = -1000, Right = 1000;
        /// <summary>The floor where no <see cref="Floors"/> span applies.</summary>
        public double Floor;
        /// <summary>Floor levels that replace <see cref="Floor"/> (pits, raised floors). First match wins.</summary>
        public LaneSpan[] Floors = Array.Empty<LaneSpan>();
        /// <summary>Standable tops (steps, crates, tables). The highest that contains x wins over the floor.</summary>
        public LaneSpan[] Platforms = Array.Empty<LaneSpan>();
        /// <summary>The ceiling where nothing lower applies. <see cref="Motor.LaneProbe.NoCeiling"/> for none.</summary>
        public double Ceiling = Motor.LaneProbe.NoCeiling;
        /// <summary>Lower ceilings (undersides). The lowest that contains x wins.</summary>
        public LaneSpan[] Ceilings = Array.Empty<LaneSpan>();
        /// <summary>Ramp zones (stairs he walks up with the larger step allowance). <see cref="LaneSpan.Y"/> is unused.</summary>
        public LaneSpan[] Ramps = Array.Empty<LaneSpan>();
    }
}
