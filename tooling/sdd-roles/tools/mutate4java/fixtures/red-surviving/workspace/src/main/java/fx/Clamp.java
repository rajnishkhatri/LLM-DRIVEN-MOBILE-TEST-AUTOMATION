package fx;

public final class Clamp {
    /**
     * The untested branch is deliberate: the conditional-boundary mutant
     * (&gt; to &gt;=) survives a suite that never probes x = 100/101, and the
     * upper branch is never covered at all.
     */
    public int clamp(int x) {
        if (x > 100) {
            return 100;
        }
        return x;
    }
}
