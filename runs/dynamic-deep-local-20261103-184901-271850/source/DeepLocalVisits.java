package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.cooperation.CooperationSupport;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.runtime.BudgetedProblem;

/** Isolated NSGA-II control: share the initial genomes and local kernel, not swarm breeding. */
public final class DeepLocalVisits {
    private static final SearchConfig SETTINGS = new SearchConfig().resolved(4);
    private final CooperationSupport initializer;
    private final SearchState state;
    private final LocalSearch local;
    private final BudgetedProblem<?> guarded;

    public DeepLocalVisits(Problem<PermutationSolution<Integer>> problem, Instance instance) {
        initializer = new CooperationSupport(instance, null, false);
        state = new SearchState(problem, instance, null);
        local = new LocalSearch(instance, 4, SETTINGS, state);
        guarded = (BudgetedProblem<?>) problem;
    }

    public void prepareInitial(PermutationSolution<Integer> solution, int index) {
        initializer.prepareInitialization(solution, index);
        // NSGA-II starts from the same vectors but has no persistent family restrictions.
        solution.getAttributes().remove("cooperation.family");
        solution.getAttributes().remove("cooperation.fixedFactoryByJob");
    }

    public boolean due(long globalOffspring) {
        return globalOffspring % (SETTINGS.populationSize * SETTINGS.qIterations) == 0;
    }

    public List<PermutationSolution<Integer>> improve(List<PermutationSolution<Integer>> population) {
        Map<Direction, List<PermutationSolution<Integer>>> slots = localRoles(population);
        List<PermutationSolution<Integer>> results = new ArrayList<>();
        for (Direction direction : Direction.values()) {
            state.observationGroup(direction);
            for (PermutationSolution<Integer> parent : slots.get(direction)) {
                guarded.checkpoint();
                results.add(local.improve(new Particle(parent), direction, population).current);
            }
        }
        state.count("deepLocal.completedBlocks");
        return results;
    }

    private static Map<Direction, List<PermutationSolution<Integer>>> localRoles(
            List<PermutationSolution<Integer>> population) {
        List<PermutationSolution<Integer>> remaining = new ArrayList<>(population);
        Map<Direction, List<PermutationSolution<Integer>>> slots = new EnumMap<>(Direction.class);
        for (Direction d : new Direction[] {Direction.MAKESPAN, Direction.ENERGY, Direction.WORKER_COST}) {
            slots.put(d, take(remaining, d, SETTINGS.boundarySize));
        }
        slots.put(Direction.CENTER, take(remaining, Direction.CENTER, remaining.size()));
        return slots;
    }

    private static List<PermutationSolution<Integer>> take(List<PermutationSolution<Integer>> population,
            Direction direction, int count) {
        List<Integer> order = ParetoTools.order(population, direction);
        List<PermutationSolution<Integer>> chosen = new ArrayList<>();
        List<Integer> indexes = new ArrayList<>(order.subList(0, count));
        for (int index : indexes) chosen.add(population.get(index));
        indexes.sort(java.util.Collections.reverseOrder());
        for (int index : indexes) population.remove(index);
        return chosen;
    }

    public Map<String, Long> diagnostics() { return state.diagnostics(); }
}
