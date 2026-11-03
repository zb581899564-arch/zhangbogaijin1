package org.uma.jmetal.util.research.runtime;

import org.uma.jmetal.solution.Solution;

/** Optional paid-result diagnostics; never admits solutions or changes termination. */
public interface EvaluationAudit<S extends Solution<?>> {
    void completed(S candidate, long successful, double elapsedSeconds, boolean archiveChanged);
}
