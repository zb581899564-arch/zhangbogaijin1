package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;

/** Existing factory helper ids: 1=makespan, 2=center, 3=energy, 4=worker cost. */
public enum Direction {
    MAKESPAN(1, 0), CENTER(2, -1), ENERGY(3, 1), WORKER_COST(4, 2);
    private final int id, objective;
    Direction(int id, int objective) { this.id = id; this.objective = objective; }
    public int id() { return id; }
    public int objective() { return objective; }

    public double reward(PermutationSolution<Integer> before, PermutationSolution<Integer> after) {
        if (objective >= 0) return before.getObjective(objective) - after.getObjective(objective);
        double total = 0;
        for (int i = 0; i < 3; i++) {
            double old = before.getObjective(i);
            // A zero physical cost is legal in synthetic inputs; freeze denominator=1 there.
            total += (old - after.getObjective(i)) / (old == 0 ? 1.0 : Math.abs(old));
        }
        return total;
    }

    public boolean better(PermutationSolution<Integer> candidate, PermutationSolution<Integer> incumbent,
            List<PermutationSolution<Integer>> reference) {
        if (objective >= 0) return candidate.getObjective(objective) < incumbent.getObjective(objective);
        List<PermutationSolution<Integer>> pool = new ArrayList<>(reference);
        pool.add(incumbent); pool.add(candidate);
        double[] score = ParetoTools.fitness(pool);
        return score[score.length - 1] < score[score.length - 2];
    }

    public int state(double improvement, int chapter) {
        return (chapter == 3 ? improvement > 0 : improvement >= 0) ? 0 : 1;
    }
}
