package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.Instance;

/** Routes every candidate through the supplied guarded problem and records actual stage completions. */
final class SearchState {
    private final Problem<PermutationSolution<Integer>> problem;
    private final Instance instance;
    private final SwarmSupport support;
    private int initialized;
    private final List<PermutationSolution<Integer>> archive = new ArrayList<>();
    private final Map<String, Long> counts = new LinkedHashMap<>();
    SearchState(Problem<PermutationSolution<Integer>> problem, Instance instance, SwarmSupport support) {
        this.problem = problem; this.instance = instance; this.support = support;
    }
    PermutationSolution<Integer> initialize() {
        PermutationSolution<Integer> solution = problem.createSolution();
        if (support != null) support.prepareInitialization(solution, initialized);
        initialized++;
        evaluate(solution, "initialization", null);
        ParetoTools.offer(archive, solution);
        return solution;
    }
    PermutationSolution<Integer> evaluate(PermutationSolution<Integer> candidate, String stage, Direction direction) {
        count(stage + ".proposals");
        if (direction != null) count(stage + ".g" + direction.id() + ".proposals");
        if (support != null) support.beforeEvaluation(candidate, stage, direction);
        SchedulingEncoding.repair(candidate, instance);
        problem.evaluate(candidate);
        if (support != null) support.evaluated(candidate, stage, direction);
        count(stage + ".evaluations");
        if (direction != null) count(stage + ".g" + direction.id() + ".evaluations");
        return candidate;
    }
    void remember(List<PermutationSolution<Integer>> personalArchive) {
        for (PermutationSolution<Integer> solution : personalArchive) ParetoTools.offer(archive, solution);
    }
    void count(String key) { counts.put(key, counts.getOrDefault(key, 0L) + 1); }
    List<PermutationSolution<Integer>> archive() { return ParetoTools.copies(archive); }
    Map<String, Long> diagnostics() { return Collections.unmodifiableMap(new LinkedHashMap<>(counts)); }
}
