package org.uma.jmetal.util.research.modelglobal;

import java.util.ArrayList;
import java.util.List;

/** Exact internal history archive. Notifications refer to the old archive, before insertion. */
public final class PaInternalArchive {
    public static final class Flags {
        public final boolean dominated, equal, fresh;
        public final int before, after;
        Flags(boolean d, boolean e, int oldSize, int newSize) {
            dominated = d; equal = e; fresh = !d && !e; before = oldSize; after = newSize;
        }
    }
    private final List<double[]> points = new ArrayList<>();

    public Flags offer(double[] candidate) {
        if (candidate.length != 3) throw new IllegalArgumentException("Three objectives required");
        for (double value : candidate) if (!Double.isFinite(value)) throw new IllegalArgumentException("Nonfinite objective");
        int before = points.size(); boolean dominated = false, equal = false;
        for (double[] point : points) { dominated |= dominates(point, candidate); equal |= same(point, candidate); }
        if (!dominated && !equal) { points.removeIf(point -> dominates(candidate, point)); points.add(candidate.clone()); }
        return new Flags(dominated, equal, before, points.size());
    }

    public double[][] snapshot() {
        double[][] result = new double[points.size()][];
        for (int i = 0; i < points.size(); i++) result[i] = points.get(i).clone(); return result;
    }

    public static boolean weaklyDominates(double[] a, double[] b) {
        for (int k = 0; k < 3; k++) if (a[k] > b[k]) return false; return true;
    }

    public static boolean dominates(double[] a, double[] b) { return weaklyDominates(a, b) && !same(a, b); }

    private static boolean same(double[] a, double[] b) {
        for (int k = 0; k < 3; k++) if (a[k] != b[k]) return false; return true;
    }
}
