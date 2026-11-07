package org.uma.jmetal.util.research.search;

import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;

/** Optional cooperation hooks. A null support leaves the original search path unchanged. */
public interface SwarmSupport {
    default void prepareInitialization(PermutationSolution<Integer> solution, int index) { }
    default void beforeEvaluation(PermutationSolution<Integer> solution, String stage, Direction direction) { }
    default void evaluated(PermutationSolution<Integer> solution, String stage, Direction direction) { }
    default void initialized(List<PermutationSolution<Integer>> population) { }
    default Map<Direction, List<Integer>> grouping(List<PermutationSolution<Integer>> population, int boundary) { return null; }
    default PermutationSolution<Integer> compose(PermutationSolution<Integer> parent, Direction direction) { return null; }
}
