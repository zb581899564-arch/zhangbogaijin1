package org.uma.jmetal.util.research.modelglobal;

import java.util.Arrays;

/** By-job categorical resources and independent global priority keys. No repair, search or scoring. */
public final class TypedScheduleGenome {
    private final FirstStageCatalog catalog;
    private final int[] allocations;
    private final double[] priorities;

    private TypedScheduleGenome(FirstStageCatalog domain, int[] resources, double[] keys) {
        if (domain == null || resources == null || keys == null
                || resources.length != domain.jobs() || keys.length != domain.jobs())
            throw new IllegalArgumentException("Expected N categorical resources and N priority keys");
        catalog = domain; allocations = resources.clone(); priorities = keys.clone();
        int[] counts = new int[domain.factories()];
        for (int j = 0; j < allocations.length; j++) {
            counts[domain.factory(allocations[j])]++;
            if (!Double.isFinite(priorities[j]) || priorities[j] < 0 || priorities[j] > 1)
                throw new IllegalArgumentException("Priority outside finite closed [0,1]");
        }
        for (int count : counts) if (count == 0) throw new IllegalArgumentException("Empty factory");
    }

    public static TypedScheduleGenome of(FirstStageCatalog domain, int[] resources, double[] keys) {
        return new TypedScheduleGenome(domain, resources, keys);
    }

    public static TypedScheduleGenome fromVectors(FirstStageCatalog domain, FourVectors vectors) {
        if (domain == null || vectors == null) throw new IllegalArgumentException("Catalog and vectors required");
        int[] js = vectors.jobs(), fa = vectors.factories(), ma = vectors.machines(), wa = vectors.workers();
        int n = domain.jobs();
        if (js.length != n || fa.length != n || ma.length != n || wa.length != n)
            throw new IllegalArgumentException("Four vectors must all have N positions");
        boolean[] seen = new boolean[n]; int[] resources = new int[n]; double[] keys = new double[n];
        for (int p = 0; p < n; p++) {
            int j = js[p]; FirstStageCatalog.range(j, n, "job");
            if (seen[j]) throw new IllegalArgumentException("Repeated job");
            seen[j] = true; resources[j] = domain.id(fa[p], ma[p], wa[p]); keys[j] = (p + .5) / n;
        }
        return of(domain, resources, keys);
    }

    public int[] allocations() { return allocations.clone(); }
    public double[] priorities() { return priorities.clone(); }

    /** Change key magnitudes without changing the current global permutation or any resource. */
    public TypedScheduleGenome withOrderedKeys(double[] sortedKeys) {
        if (sortedKeys == null || sortedKeys.length != priorities.length)
            throw new IllegalArgumentException("Expected N sorted keys");
        int[] order = order(); double[] keys = new double[priorities.length];
        for (int p = 0; p < order.length; p++) {
            if (!Double.isFinite(sortedKeys[p]) || sortedKeys[p] < 0 || sortedKeys[p] > 1
                    || (p > 0 && sortedKeys[p] <= sortedKeys[p - 1]))
                throw new IllegalArgumentException("Reencoding needs strictly increasing finite keys in [0,1]");
            keys[order[p]] = sortedKeys[p];
        }
        return of(catalog, allocations, keys);
    }

    public FourVectors toVectors() {
        int[] js = order(), fa = new int[js.length], ma = new int[js.length], wa = new int[js.length];
        for (int p = 0; p < js.length; p++) {
            int[] tuple = catalog.tuple(allocations[js[p]]); fa[p] = tuple[0]; ma[p] = tuple[1]; wa[p] = tuple[2];
        }
        return new FourVectors(js, fa, ma, wa);
    }

    private int[] order() {
        Integer[] jobs = new Integer[priorities.length]; for (int j = 0; j < jobs.length; j++) jobs[j] = j;
        // Source merge sort takes the right half on equality, including -0.0 versus +0.0.
        Arrays.sort(jobs, (a, b) -> priorities[a] < priorities[b] ? -1
                : priorities[a] > priorities[b] ? 1 : Integer.compare(b, a));
        int[] result = new int[jobs.length]; for (int p = 0; p < jobs.length; p++) result[p] = jobs[p];
        return result;
    }
}
