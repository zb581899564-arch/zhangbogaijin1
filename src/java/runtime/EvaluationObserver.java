package org.uma.jmetal.util.research.runtime;

import org.uma.jmetal.solution.Solution;

/** Read-only monitor invoked after a successful, paid archive admission attempt. */
public interface EvaluationObserver {
    void completed(long evaluations, double seconds, boolean changed, ThreeObjectiveArchive<?> archive);

    /** Optional paid-solution evidence; existing observers keep their original callback. */
    default void completedSolution(Solution<?> solution, long evaluations, double seconds,
            boolean changed, ThreeObjectiveArchive<?> archive) {
        completed(evaluations, seconds, changed, archive);
    }
}
