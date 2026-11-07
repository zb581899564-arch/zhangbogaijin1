package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;

/** Strict three-objective dominance and the paper's q + 1/(p+1) fitness. */
public final class ParetoTools {
    private ParetoTools() { }
    public static boolean dominates(PermutationSolution<Integer> first, PermutationSolution<Integer> second) {
        boolean strict = false;
        for (int i = 0; i < 3; i++) {
            if (first.getObjective(i) > second.getObjective(i)) return false;
            strict |= first.getObjective(i) < second.getObjective(i);
        }
        return strict;
    }
    public static double[] fitness(List<PermutationSolution<Integer>> solutions) {
        double[] result = new double[solutions.size()];
        for (int i = 0; i < solutions.size(); i++) {
            int p = 0, q = 0;
            for (int j = 0; j < solutions.size(); j++) if (i != j) {
                if (dominates(solutions.get(i), solutions.get(j))) p++;
                if (dominates(solutions.get(j), solutions.get(i))) q++;
            }
            result[i] = q + 1.0 / (p + 1);
        }
        return result;
    }
    public static List<Integer> order(List<PermutationSolution<Integer>> solutions, Direction direction) {
        List<Integer> indices = new ArrayList<>();
        for (int i = 0; i < solutions.size(); i++) indices.add(i);
        double[] fitness = direction == Direction.CENTER ? fitness(solutions) : null;
        indices.sort(Comparator.comparingDouble(i -> direction == Direction.CENTER
                ? fitness[i] : solutions.get(i).getObjective(direction.objective())));
        return indices;
    }
    static void offer(List<PermutationSolution<Integer>> archive, PermutationSolution<Integer> candidate) {
        for (PermutationSolution<Integer> item : archive) {
            if (dominates(item, candidate) || same(item, candidate)) return;
        }
        archive.removeIf(item -> dominates(candidate, item));
        archive.add(copy(candidate));
    }
    static List<PermutationSolution<Integer>> copies(List<PermutationSolution<Integer>> values) {
        List<PermutationSolution<Integer>> result = new ArrayList<>();
        for (PermutationSolution<Integer> value : values) result.add(copy(value));
        return result;
    }
    @SuppressWarnings("unchecked")
    static PermutationSolution<Integer> copy(PermutationSolution<Integer> value) {
        return (PermutationSolution<Integer>) value.copy();
    }
    private static boolean same(PermutationSolution<Integer> first, PermutationSolution<Integer> second) {
        for (int i = 0; i < 3; i++) if (first.getObjective(i) != second.getObjective(i)) return false;
        return true;
    }
}
