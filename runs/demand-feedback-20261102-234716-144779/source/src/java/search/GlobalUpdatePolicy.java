package org.uma.jmetal.util.research.search;

import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;

/** Optional global offspring strategy; the default constructor keeps historical RNG calls. */
public interface GlobalUpdatePolicy {
    default void initialized(List<PermutationSolution<Integer>> population) { }
    default void beginBatch(Direction direction) { }
    PermutationSolution<Integer> propose(PermutationSolution<Integer> parent,
            PermutationSolution<Integer> personal, PermutationSolution<Integer> leader, Direction direction);
    default void evaluated(PermutationSolution<Integer> child, Direction direction) { }
    default void endBatch(Direction direction) { }
}
