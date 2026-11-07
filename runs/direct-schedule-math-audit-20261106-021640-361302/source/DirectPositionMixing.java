package org.uma.jmetal.util.research.modelglobal;

import java.util.Arrays;

/** Independent integer formulation of differential-position/OX and subset-order mixing. */
public final class DirectPositionMixing {
    private DirectPositionMixing() { }

    static void requirePermutation(int[] values) {
        if (values == null || values.length == 0) throw new IllegalArgumentException("Nonempty permutation required");
        boolean[] seen = new boolean[values.length];
        for (int value : values) {
            if (value < 0 || value >= values.length || seen[value]) throw new IllegalArgumentException("Invalid permutation");
            seen[value] = true;
        }
    }

    private static boolean[] check(int[] parent, int[] donor, int[] subset) {
        requirePermutation(parent); requirePermutation(donor);
        if (parent.length != donor.length || subset == null || subset.length == 0)
            throw new IllegalArgumentException("Matching permutations and nonempty mask required");
        boolean[] selected = new boolean[parent.length];
        for (int job : subset) {
            if (job < 0 || job >= parent.length || selected[job]) throw new IllegalArgumentException("Invalid mask");
            selected[job] = true;
        }
        return selected;
    }

    /** The selected receiver pattern is translated to the donor's reference; remaining jobs keep relative order. */
    public static int[] position(int[] parent, int[] donor, int[] subset, int reference) {
        boolean[] selected = check(parent, donor, subset);
        if (reference < 0 || reference >= parent.length || !selected[reference])
            throw new IllegalArgumentException("Reference must belong to mask");
        int n = parent.length, minimum = n, maximum = -n;
        int[] virtual = new int[subset.length];
        for (int i = 0; i < subset.length; i++) {
            virtual[i] = donor[reference] + parent[subset[i]] - parent[reference];
            minimum = Math.min(minimum, virtual[i]); maximum = Math.max(maximum, virtual[i]);
        }
        int shift = minimum < 0 ? -minimum : maximum >= n ? n - 1 - maximum : 0;
        int[] order = new int[n]; Arrays.fill(order, -1);
        for (int i = 0; i < subset.length; i++) order[virtual[i] + shift] = subset[i];
        int[] oldOrder = inverse(parent); int free = 0;
        for (int job : oldOrder) if (!selected[job]) {
            while (order[free] != -1) free++;
            order[free] = job;
        }
        return inverse(order);
    }

    /** Selected jobs occupy the same position set in the donor's relative order; other positions are unchanged. */
    public static int[] order(int[] parent, int[] donor, int[] subset) {
        check(parent, donor, subset);
        int[] positions = new int[subset.length]; Integer[] jobs = new Integer[subset.length];
        for (int i = 0; i < subset.length; i++) { positions[i] = parent[subset[i]]; jobs[i] = subset[i]; }
        Arrays.sort(positions); Arrays.sort(jobs, (a, b) -> Integer.compare(donor[a], donor[b]));
        int[] result = parent.clone();
        for (int i = 0; i < subset.length; i++) result[jobs[i]] = positions[i];
        return result;
    }

    public static int[] inverse(int[] permutation) {
        requirePermutation(permutation); int[] result = new int[permutation.length];
        for (int i = 0; i < permutation.length; i++) result[permutation[i]] = i;
        return result;
    }
}
