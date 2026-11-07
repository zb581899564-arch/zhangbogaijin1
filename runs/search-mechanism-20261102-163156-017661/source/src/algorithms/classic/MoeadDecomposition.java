package org.uma.jmetal.util.research.classic;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;

/** Zhang/Li Tchebycheff decomposition with an explicit fixed 100-direction adaptation. */
final class MoeadDecomposition {
    static final double ZERO_WEIGHT = 1e-6;
    final double[][] weights;
    final int[][] neighbors;
    final double[] scale, ideal = new double[3];

    MoeadDecomposition(List<PermutationSolution<Integer>> initial, int neighborhoodSize, Runnable checkpoint) {
        scale = FrozenObjectiveScale.from(initial, checkpoint);
        weights = weights(checkpoint);
        neighbors = new int[weights.length][neighborhoodSize];
        for (int i = 0; i < weights.length; i++) {
            checkpoint.run(); final int index = i;
            List<Integer> order = ClassicTools.indices(weights.length);
            order.sort((a, b) -> { checkpoint.run(); int c = Double.compare(distance(weights[index], weights[a]), distance(weights[index], weights[b]));
                return c == 0 ? Integer.compare(a, b) : c; });
            for (int k = 0; k < neighborhoodSize; k++) neighbors[i][k] = order.get(k);
        }
        Arrays.fill(ideal, Double.POSITIVE_INFINITY);
        for (PermutationSolution<Integer> solution : initial) {
            checkpoint.run(); updateIdeal(solution);
        }
    }

    void updateIdeal(PermutationSolution<Integer> paid) {
        for (int m = 0; m < 3; m++) ideal[m] = Math.min(ideal[m], paid.getObjective(m));
    }
    double scalar(PermutationSolution<Integer> solution, int subproblem) {
        double value = 0;
        for (int m = 0; m < 3; m++) value = Math.max(value, Math.max(weights[subproblem][m], ZERO_WEIGHT)
                * Math.abs(solution.getObjective(m) - ideal[m]) / scale[m]);
        return value;
    }

    /** Maximin subset of H=30 lattice; vertices first, all ties lexicographic, no RNG calls. */
    static double[][] weights(Runnable checkpoint) {
        List<double[]> lattice = new ArrayList<>();
        for (int a = 0; a <= 30; a++) for (int b = 0; b <= 30 - a; b++)
            lattice.add(new double[] {a / 30.0, b / 30.0, (30 - a - b) / 30.0});
        double[][] result = new double[ClassicConfig.POPULATION][3];
        result[0] = new double[] {1, 0, 0}; result[1] = new double[] {0, 1, 0}; result[2] = new double[] {0, 0, 1};
        double[] nearest = new double[lattice.size()]; Arrays.fill(nearest, Double.POSITIVE_INFINITY);
        for (int p = 0; p < result.length; p++) {
            checkpoint.run();
            if (p >= 3) {
                int best = 0;
                for (int c = 1; c < nearest.length; c++) if (nearest[c] > nearest[best]) best = c;
                result[p] = lattice.get(best).clone();
            }
            for (int c = 0; c < lattice.size(); c++) nearest[c] = Math.min(nearest[c], distance(lattice.get(c), result[p]));
        }
        return result;
    }
    private static double distance(double[] a, double[] b) {
        double sum = 0; for (int m = 0; m < 3; m++) { double d = a[m] - b[m]; sum += d * d; } return sum;
    }
}
