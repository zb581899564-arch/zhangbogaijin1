package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.util.research.modelglobal.*;

/** Source PA model on free members; source single-factory model within each fixed factory. */
final class GomDomainModels {
    private GomDomainModels() { }
    static List<int[]> build(GomWorkspace w, int family, List<Integer> slots) {
        List<int[]> result = new ArrayList<>(); int n = w.catalog.jobs();
        if (family < 0) {
            int[] jobs = new int[n]; for (int j = 0; j < n; j++) jobs[j] = j;
            result.addAll(one(w, family, -1, slots, jobs));
        } else {
            int[] resources = w.values.get(slots.get(0)).genes.allocations();
            for (int f = 0; f < w.catalog.factories(); f++) {
                List<Integer> ids = new ArrayList<>();
                for (int j = 0; j < n; j++) if (w.catalog.factory(resources[j]) == f) ids.add(j);
                int[] jobs = new int[ids.size()]; for (int j = 0; j < jobs.length; j++) jobs[j] = ids.get(j);
                result.addAll(one(w, family, f, slots, jobs));
            }
        }
        return result;
    }
    private static List<int[]> one(GomWorkspace w, int family, int factory, List<Integer> slots, int[] jobs) {
        int[][] fa = new int[slots.size()][jobs.length]; double[][] keys = new double[slots.size()][jobs.length];
        for (int row = 0; row < slots.size(); row++) {
            GomRecords.State s = w.values.get(slots.get(row)); int[] resources = s.genes.allocations(); double[] k = s.genes.priorities();
            for (int j = 0; j < jobs.length; j++) { fa[row][j] = family < 0 ? w.catalog.factory(resources[jobs[j]]) : 0; keys[row][j] = k[jobs[j]]; }
        }
        PaDependencyModel model = new PaDependencyModel(fa, keys, family < 0 ? w.catalog.factories() : 1);
        double[][] matrix = new double[jobs.length][jobs.length];
        for (int a = 0; a < jobs.length; a++) {
            w.scope.guard("MODEL_ROW"); for (int b = a+1; b < jobs.length; b++) matrix[a][b] = matrix[b][a] = model.components(a,b)[0];
        }
        List<int[]> local = new LinkageHierarchy(matrix).subsets(), global = new ArrayList<>(); w.scope.guard("MODEL_COMPLETE");
        for (int[] subset : local) { int[] mapped = new int[subset.length]; for (int j = 0; j < mapped.length; j++) mapped[j] = jobs[subset[j]]; global.add(mapped); }
        w.scope.evidence.record(GomRecords.row("kind", "model", "pass", w.scope.passes, "family", family, "factory", factory,
            "slots", slots, "jobs", jobs, "dependency", matrix, "localSubsets", local, "subsets", global));
        return global;
    }
}
