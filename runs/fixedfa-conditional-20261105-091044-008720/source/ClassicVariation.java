package org.uma.jmetal.util.research.classic;

import java.util.Arrays;
import java.util.List;
import java.util.Random;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** The same discrete kernel for all four algorithms; resources follow job identity. */
final class ClassicVariation {
    private final Instance instance;
    private final ClassicConfig config;
    private final Runnable checkpoint;
    ClassicVariation(Instance instance, ClassicConfig config, Runnable checkpoint) {
        this.instance = instance; this.config = config; this.checkpoint = checkpoint;
    }

    PermutationSolution<Integer> child(PermutationSolution<Integer> first, PermutationSolution<Integer> second) {
        checkpoint.run();
        Random random = SeededRandom.current();
        int n = instance.jobs();
        boolean cross = random.nextDouble() < config.crossoverProbability;
        int[] order = new int[n];
        for (int p = 0; p < n; p++) order[p] = first.getVariableValue(p);
        if (cross && n > 1) order = ox(first, second, random);
        int[][] a = byJob(first), b = byJob(second), genes = new int[n][3];
        double mutation = Math.min(1, config.mutationScale / n);
        for (int j = 0; j < n; j++) {
            checkpoint.run();
            for (int k = 0; k < 3; k++) genes[j][k] = cross && random.nextBoolean() ? b[j][k] : a[j][k];
            if (random.nextDouble() < mutation && !org.uma.jmetal.util.research.search.FixedFAMutationMask.skipClassic()) genes[j][0] = alternative(genes[j][0], instance.factories(), random);
            int f = genes[j][0];
            if (random.nextDouble() < mutation) genes[j][1] = alternative(genes[j][1], instance.machines(f, 0), random);
            if (random.nextDouble() < mutation) genes[j][2] = alternative(genes[j][2], instance.workers(f, 0), random);
        }
        for (int p = 0; p < n; p++) if (n > 1 && random.nextDouble() < mutation) {
            int q = alternative(p, n, random), saved = order[p]; order[p] = order[q]; order[q] = saved;
        }
        PermutationSolution<Integer> child = ClassicTools.copy(first);
        for (int p = 0; p < n; p++) {
            int j = order[p]; child.setVariableValue(p, j);
            child.setVariableValueid(p, genes[j][0]);
            machines(child).set(p, genes[j][1]);
            child.setVariableValueworker(p, genes[j][2]);
        }
        // Resource ids inherited across different factories are repaired by the common
        // SchedulingEncoding immediately before the one guarded, charged evaluation.
        return child;
    }

    private int[] ox(PermutationSolution<Integer> a, PermutationSolution<Integer> b, Random random) {
        int n = instance.jobs(), left = random.nextInt(n), right = alternative(left, n, random);
        if (left > right) { int saved = left; left = right; right = saved; }
        int[] order = new int[n]; Arrays.fill(order, -1);
        boolean[] present = new boolean[n];
        for (int p = left; p <= right; p++) { order[p] = a.getVariableValue(p); present[order[p]] = true; }
        int cursor = (right + 1) % n;
        for (int t = 1; t <= n; t++) {
            checkpoint.run();
            int job = b.getVariableValue((right + t) % n);
            if (!present[job]) { order[cursor] = job; cursor = (cursor + 1) % n; }
        }
        return order;
    }
    private int[][] byJob(PermutationSolution<Integer> solution) {
        int[][] genes = new int[instance.jobs()][3];
        for (int p = 0; p < genes.length; p++) {
            int job = solution.getVariableValue(p);
            genes[job][0] = solution.getVariableValueid(p);
            genes[job][1] = machines(solution).get(p);
            genes[job][2] = solution.getVariableValueworker(p);
        }
        return genes;
    }
    private static int alternative(int current, int bound, Random random) {
        if (bound == 1) return 0;
        int old = Math.floorMod(current, bound), next = random.nextInt(bound - 1);
        return next >= old ? next + 1 : next;
    }
    @SuppressWarnings("unchecked")
    private static List<Integer> machines(PermutationSolution<Integer> solution) {
        return (List<Integer>) solution.getAttribute("machine");
    }
}
