package org.uma.jmetal.util.research.classic;

import java.util.ArrayList;
import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;

/** Three minimization objectives, strict dominance, and ownership-preserving copies. */
final class ClassicTools {
    private ClassicTools() { }
    static boolean dominates(PermutationSolution<Integer> a, PermutationSolution<Integer> b) {
        boolean strict = false;
        for (int m = 0; m < 3; m++) {
            if (a.getObjective(m) > b.getObjective(m)) return false;
            strict |= a.getObjective(m) < b.getObjective(m);
        }
        return strict;
    }
    static List<Integer> indices(int size) {
        List<Integer> result = new ArrayList<>();
        for (int i = 0; i < size; i++) result.add(i);
        return result;
    }
    @SuppressWarnings("unchecked")
    static PermutationSolution<Integer> copy(PermutationSolution<Integer> value) {
        return (PermutationSolution<Integer>) value.copy();
    }
    static List<PermutationSolution<Integer>> copies(List<PermutationSolution<Integer>> values) {
        List<PermutationSolution<Integer>> result = new ArrayList<>();
        for (PermutationSolution<Integer> value : values) result.add(copy(value));
        return result;
    }
    static List<PermutationSolution<Integer>> union(List<PermutationSolution<Integer>> a,
            List<PermutationSolution<Integer>> b) {
        List<PermutationSolution<Integer>> result = new ArrayList<>(a);
        result.addAll(b); return result;
    }
}
