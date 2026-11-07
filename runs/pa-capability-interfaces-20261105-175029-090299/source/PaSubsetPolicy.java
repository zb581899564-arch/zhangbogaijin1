package org.uma.jmetal.util.research.modelglobal;

import java.util.*;

/** Explicit search policy, separate from observation. Relabel uses its own deterministic generation RNG. */
public interface PaSubsetPolicy {
    List<int[]> apply(int generation, int jobs, List<int[]> learned);

    static PaSubsetPolicy identity() { return (generation, jobs, learned) -> learned; }

    static PaSubsetPolicy relabel(long seed) {
        return (generation, jobs, learned) -> {
            List<Integer> labels = new ArrayList<>(); for (int j = 0; j < jobs; j++) labels.add(j);
            Collections.shuffle(labels, new Random(seed ^ (0x9e3779b97f4a7c15L * generation)));
            List<int[]> result = new ArrayList<>();
            for (int[] subset : learned) {
                int[] renamed = new int[subset.length]; for (int k = 0; k < subset.length; k++) renamed[k] = labels.get(subset[k]);
                Arrays.sort(renamed); result.add(renamed);
            }
            return result;
        };
    }
}
