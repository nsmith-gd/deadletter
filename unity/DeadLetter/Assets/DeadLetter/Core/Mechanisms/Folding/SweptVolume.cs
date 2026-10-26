namespace DeadLetter.Core.Mechanisms.Folding
{
    /// <summary>
    /// A box of a leaf, in lane x and in the leaf's own frame: U along the leaf from the hinge, V across it (V+ is the
    /// side that faces up when the leaf is down).
    /// </summary>
    public readonly struct LeafBox
    {
        public readonly double X0, X1, U0, U1, V0, V1;

        public LeafBox(double x0, double x1, double u0, double u1, double v0, double v1)
        {
            X0 = x0; X1 = x1; U0 = u0; U1 = u1; V0 = v0; V1 = v1;
        }
    }

}
