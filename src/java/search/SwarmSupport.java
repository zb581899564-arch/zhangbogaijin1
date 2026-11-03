package org.uma.jmetal.util.research.search;

import java.util.List;
import java.util.Map;
import java.util.Collections;
import org.uma.jmetal.solution.PermutationSolution;

/** Optional cooperation hooks. A null support leaves the original search path unchanged. */
public interface SwarmSupport {
    default void prepareInitialization(PermutationSolution<Integer> solution, int index) { }
    default void beforeEvaluation(PermutationSolution<Integer> solution, String stage, Direction direction) { }
    default void evaluated(PermutationSolution<Integer> solution, String stage, Direction direction) { }
    default void initialized(List<PermutationSolution<Integer>> population) { }
    default void beginGeneration() { }
    default Direction[] globalUpdateOrder() { return Direction.values(); }
    /** Preference may vary independently of the physical group and its accounting. */
    default Direction preference(Direction group) { return group; }
    /** Optional fixed-rule local factory routing; the original random draw is already paid. */
    default int localFactory(PermutationSolution<Integer> parent, Direction group, int randomFactory) { return randomFactory; }
    default boolean hasContextRenewal() { return false; }
    /** Replacements must receive ordinary charged evaluation and fresh personal histories. */
    default Map<Integer, PermutationSolution<Integer>> renewContexts(List<PermutationSolution<Integer>> population) {
        return Collections.emptyMap();
    }
    default Map<Direction, List<Integer>> grouping(List<PermutationSolution<Integer>> population, int boundary) { return null; }
    default PermutationSolution<Integer> compose(PermutationSolution<Integer> parent, Direction direction) { return null; }
    /** Optional survivor counts by category; scores always come from the complete candidate pool. */
    default int[] selectionQuotas() { return null; }
    default int selectionCategory(PermutationSolution<Integer> solution) { return -1; }
}
