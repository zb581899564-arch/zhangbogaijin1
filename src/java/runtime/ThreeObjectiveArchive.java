package org.uma.jmetal.util.research.runtime;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import org.uma.jmetal.solution.Solution;

/** Exact, unbounded archive of evaluated solutions for three minimization objectives. */
public final class ThreeObjectiveArchive<S extends Solution<?>> {
    private final List<S> entries = new ArrayList<>();

    // Package-private: only the guarded evaluator may admit a solution.
    boolean addEvaluated(S candidate) {
        requireFiniteObjectives(candidate);
        for (S entry : entries) {
            if (dominates(entry, candidate) || sameObjectives(entry, candidate)) { return false; }
        }
        // Copy before mutating entries, so a snapshot failure cannot discard prior results.
        S snapshot = SolutionSnapshots.copy(candidate);
        entries.removeIf(entry -> dominates(candidate, entry));
        entries.add(snapshot);
        return true;
    }

    public List<S> snapshot() {
        List<S> result = new ArrayList<>(entries.size());
        for (S entry : entries) { result.add(SolutionSnapshots.copy(entry)); }
        return Collections.unmodifiableList(result);
    }

    public int size() { return entries.size(); }

    /** Numeric snapshots for monitoring: no encoding copies and no search feedback. */
    public double[][] objectiveSnapshot() {
        double[][] result = new double[entries.size()][3];
        for (int i = 0; i < entries.size(); i++) for (int k = 0; k < 3; k++) result[i][k] = entries.get(i).getObjective(k);
        return result;
    }

    private static void requireFiniteObjectives(Solution<?> solution) {
        if (solution.getNumberOfObjectives() != 3) {
            throw new IllegalArgumentException("Archive requires exactly three physical objectives");
        }
        for (int i = 0; i < 3; i++) {
            if (!Double.isFinite(solution.getObjective(i))) {
                throw new IllegalStateException("Non-finite physical objective " + i);
            }
        }
    }

    private static boolean dominates(Solution<?> first, Solution<?> second) {
        boolean strictlyBetter = false;
        for (int i = 0; i < 3; i++) {
            if (first.getObjective(i) > second.getObjective(i)) { return false; }
            strictlyBetter |= first.getObjective(i) < second.getObjective(i);
        }
        return strictlyBetter;
    }

    private static boolean sameObjectives(Solution<?> first, Solution<?> second) {
        for (int i = 0; i < 3; i++) {
            if (first.getObjective(i) != second.getObjective(i)) { return false; }
        }
        return true;
    }
}
