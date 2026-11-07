package org.uma.jmetal.util.research.modelglobal;

import java.util.ArrayList;
import java.util.List;

/** Mean direct-position distance, canonical average-linkage and the observed source size filter. */
public final class QpaLinkageModel {
    public final double[][] affinity;
    public final List<int[]> fullSubsets, activeSubsets;
    public final int cutoff;

    public QpaLinkageModel(List<QpaIndividual> parents, QpaPaidEvaluation evaluation) {
        int n = evaluation.catalog().jobs();
        if (parents.size() != 100 || n < 2) throw new IllegalArgumentException("100 parents and at least2 jobs required");
        int[][] positions = new int[parents.size()][];
        for (int i = 0; i < positions.length; i++) positions[i] = parents.get(i).genome.positions();
        affinity = new double[n][n]; double denominator = (double)parents.size() * (n - 1);
        for (int a = 0; a < n; a++) {
            evaluation.checkpoint();
            for (int b = a + 1; b < n; b++) {
                long sum = 0; for (int[] values : positions) sum += Math.abs(values[a] - values[b]);
                affinity[a][b] = affinity[b][a] = 1.0 - sum / denominator;
            }
        }
        fullSubsets = new LinkageHierarchy(affinity).subsets();
        cutoff = (int)Math.rint((n / 12.0) * 10.0); activeSubsets = new ArrayList<>();
        for (int[] subset : fullSubsets) if (subset.length < cutoff) activeSubsets.add(subset);
        if (activeSubsets.isEmpty()) throw new IllegalArgumentException("No active masks for this instance size");
    }
}
