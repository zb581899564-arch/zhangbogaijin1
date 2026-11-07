package org.uma.jmetal.util.research.classic;

import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;

/** Numerical unit adaptation from the same paid initial population; never updated. */
final class FrozenObjectiveScale {
    private FrozenObjectiveScale() { }
    static double[] from(List<PermutationSolution<Integer>> initial, Runnable checkpoint) {
        if (initial.isEmpty()) throw new IllegalArgumentException("Paid initial population required for scaling");
        double[] scale = new double[3];
        for (PermutationSolution<Integer> solution : initial) {
            checkpoint.run();
            for (int m = 0; m < 3; m++) scale[m] += solution.getObjective(m) / initial.size();
        }
        for (int m = 0; m < 3; m++) { scale[m] = Math.abs(scale[m]); if (scale[m] == 0) scale[m] = 1; }
        return scale;
    }
}
