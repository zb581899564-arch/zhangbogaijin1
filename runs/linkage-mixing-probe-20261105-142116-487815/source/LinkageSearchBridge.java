package org.uma.jmetal.util.research.search;

import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;

/** Access to the actually loaded common comparison and snapshot-copy kernels. */
public final class LinkageSearchBridge {
    private LinkageSearchBridge() { }
    public static boolean better(String role, PermutationSolution<Integer> candidate,
            PermutationSolution<Integer> incumbent, List<PermutationSolution<Integer>> reference) {
        return LocalPddrKernel.better(Direction.valueOf(role), candidate, incumbent, reference);
    }
    public static PermutationSolution<Integer> copy(PermutationSolution<Integer> value) {
        return ParetoTools.copy(value);
    }
}
