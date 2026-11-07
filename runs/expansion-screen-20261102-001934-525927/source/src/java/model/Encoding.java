package org.uma.jmetal.util.research.model;

/** Positional JS/FA/MA/WA contract; all identifiers are zero-based. */
final class Encoding {
    private Encoding() { }
    static void validate(Instance in, int[] js, int[] fa, int[] ma, int[] wa) {
        int n = in.jobs();
        if (js.length != n || fa.length != n || ma.length != n) throw new IllegalArgumentException("JS/FA/MA must have N entries");
        boolean[] seen = new boolean[n]; int[] factoryJobs = new int[in.factories()];
        for (int p = 0; p < n; p++) {
            range(js[p], n, "job"); range(fa[p], in.factories(), "factory");
            if (seen[js[p]]) throw new IllegalArgumentException("JS is not a permutation");
            seen[js[p]] = true; factoryJobs[fa[p]]++;
            range(ma[p], in.machines(fa[p], 0), "first-stage machine");
        }
        for (int count : factoryJobs) if (count == 0) throw new IllegalArgumentException("Every factory must receive a job");
        if (in.kind() == ModelKind.CHAPTER4_DUAL_RESOURCE) {
            if (wa.length != n) throw new IllegalArgumentException("Chapter4 WA must have N entries (first stage only)");
            for (int p = 0; p < n; p++) range(wa[p], in.workers(fa[p], 0), "first-stage worker");
        } else validateFixedWorkers(in, wa);
    }
    private static void validateFixedWorkers(Instance in, int[] wa) {
        int cursor = 0;
        for (int f = 0; f < in.factories(); f++) {
            int total = 0;
            for (int k = 0; k < in.stages(); k++) total += in.machines(f, k);
            if (cursor + total > wa.length || in.workers(f, 0) != total) throw new IllegalArgumentException("Invalid fixed worker count");
            boolean[] seen = new boolean[total];
            for (int m = 0; m < total; m++) {
                int w = wa[cursor++]; range(w, total, "fixed worker");
                if (seen[w]) throw new IllegalArgumentException("Fixed WA must permute each factory worker pool");
                seen[w] = true;
            }
        }
        if (cursor != wa.length) throw new IllegalArgumentException("Chapter3 WA length must equal total machines");
    }
    private static void range(int value, int bound, String name) {
        if (value < 0 || value >= bound) throw new IllegalArgumentException("Invalid " + name + " id " + value);
    }
}
