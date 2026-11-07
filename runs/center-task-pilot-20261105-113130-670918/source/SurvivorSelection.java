package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;
import org.uma.jmetal.solution.PermutationSolution;

/** One complete-pool PDDR calculation followed by stable, optionally quota-constrained truncation. */
final class SurvivorSelection {
    private SurvivorSelection() { }

    static Result select(List<Particle> candidates, int count, SwarmSupport support, Runnable checkpoint) {
        if (CenterTaskState.enabled()) return CenterTaskRetention.select(candidates, count, support, checkpoint);
        Objects.requireNonNull(candidates, "candidates");
        Objects.requireNonNull(checkpoint, "checkpoint").run();
        if (count < 0 || count > candidates.size()) throw new IllegalArgumentException("Invalid survivor count: " + count);
        List<PermutationSolution<Integer>> solutions = new ArrayList<>();
        for (Particle particle : candidates) {
            checkpoint.run();
            solutions.add(Objects.requireNonNull(particle, "candidate").current);
        }
        int[] quotas = support == null ? null : support.selectionQuotas();
        if (quotas != null) quotas = quotas.clone();
        int[] categories = quotas == null ? null : categories(solutions, support, quotas, count, checkpoint);
        checkpoint.run();
        double[] fitness = ParetoTools.fitness(solutions);
        checkpoint.run();
        List<Integer> order = new ArrayList<>();
        for (int i = 0; i < candidates.size(); i++) order.add(i);
        // List.sort is stable: equal scores keep G-before-L and then original pool order.
        order.sort(Comparator.comparingDouble(i -> fitness[i]));
        checkpoint.run();
        int[] used = quotas == null ? null : new int[quotas.length];
        List<Particle> survivors = new ArrayList<>();
        int[] indices = new int[count];
        for (int index : order) {
            checkpoint.run();
            if (survivors.size() == count) break;
            if (used != null && used[categories[index]] == quotas[categories[index]]) continue;
            indices[survivors.size()] = index;
            survivors.add(candidates.get(index));
            if (used != null) used[categories[index]]++;
        }
        if (survivors.size() != count) throw new IllegalStateException("Validated survivor capacity was not filled");
        return new Result(survivors, indices, fitness, categories, quotas);
    }

    private static int[] categories(List<PermutationSolution<Integer>> solutions, SwarmSupport support,
            int[] quotas, int count, Runnable checkpoint) {
        if (quotas.length == 0) throw new IllegalArgumentException("Selection quotas must contain a category");
        long total = 0;
        for (int quota : quotas) {
            if (quota < 0) throw new IllegalArgumentException("Negative selection quota");
            total += quota;
        }
        if (total != count) throw new IllegalArgumentException("Selection quotas sum to " + total + ", expected " + count);
        int[] categories = new int[solutions.size()], capacity = new int[quotas.length];
        for (int i = 0; i < solutions.size(); i++) {
            checkpoint.run();
            int category = support.selectionCategory(solutions.get(i));
            if (category < 0 || category >= quotas.length) throw new IllegalArgumentException("Invalid selection category " + category + " at candidate " + i);
            categories[i] = category; capacity[category]++;
        }
        for (int i = 0; i < quotas.length; i++) if (capacity[i] < quotas[i])
            throw new IllegalArgumentException("Insufficient candidates in category " + i + ": " + capacity[i] + " < " + quotas[i]);
        return categories;
    }

    static final class Result {
        private final List<Particle> survivors;
        private final int[] indices, categories, quotas;
        private final double[] fitness;
        Result(List<Particle> survivors, int[] indices, double[] fitness, int[] categories, int[] quotas) {
            this.survivors = new ArrayList<>(survivors); this.indices = indices.clone(); this.fitness = fitness.clone();
            this.categories = categories == null ? null : categories.clone();
            this.quotas = quotas == null ? null : quotas.clone();
        }
        List<Particle> survivors() { return new ArrayList<>(survivors); }
        int[] indices() { return indices.clone(); }
        double[] fitness() { return fitness.clone(); }
        int[] categories() { return categories == null ? null : categories.clone(); }
        int[] quotas() { return quotas == null ? null : quotas.clone(); }
    }
}
