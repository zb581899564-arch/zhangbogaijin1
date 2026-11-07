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
    private final SemanticAudit audit;
    private int initialized;
    private Direction observationGroup;
    private final List<PermutationSolution<Integer>> archive = new ArrayList<>();
    private final Map<String, Long> counts = new LinkedHashMap<>();
    SearchState(Problem<PermutationSolution<Integer>> problem, Instance instance, SwarmSupport support) {
        this(problem, instance, support, null);
    }
    SearchState(Problem<PermutationSolution<Integer>> problem, Instance instance, SwarmSupport support, SemanticAudit audit) {
        this.problem = problem; this.instance = instance; this.support = support;
        this.audit = audit;
    }
    PermutationSolution<Integer> initialize() {
        PermutationSolution<Integer> solution = problem.createSolution();
        if (support != null) support.prepareInitialization(solution, initialized);
        else CommonInitials.prepare(solution, initialized, instance);
        initialized++;
        evaluate(solution, "initialization", null);
        offerInternal(solution, true);
        return solution;
    }
    PermutationSolution<Integer> evaluate(PermutationSolution<Integer> candidate, String stage, Direction direction) {
        if (observationGroup != null) direction = observationGroup;
        count(stage + ".proposals");
        if (direction != null) count(stage + ".g" + direction.id() + ".proposals");
        FactoryAssignmentAudit.begin(candidate,stage,direction);
        if (support != null) support.beforeEvaluation(candidate, stage, direction);
        SchedulingEncoding.repair(candidate, instance);
        if (audit != null) audit.proposal(candidate, stage);
        FactoryAssignmentAudit.ready(candidate);
        problem.evaluate(candidate);
        if (support != null) support.evaluated(candidate, stage, direction);
        count(stage + ".evaluations");
        if (direction != null) count(stage + ".g" + direction.id() + ".evaluations");
        return candidate;
    }
    void remember(List<PermutationSolution<Integer>> personalArchive) {
        for (PermutationSolution<Integer> solution : personalArchive) offerInternal(solution, false);
    }
    private void offerInternal(PermutationSolution<Integer> solution, boolean initial) {
        PermutationSolution<Integer> previousLast = archive.isEmpty() ? null : archive.get(archive.size() - 1);
        ParetoTools.offer(archive, solution);
        if (audit != null) {
            PermutationSolution<Integer> nextLast = archive.isEmpty() ? null : archive.get(archive.size() - 1);
            audit.feedbackOffer(solution, previousLast != nextLast, initial);
        }
    }
    void count(String key) { counts.put(key, counts.getOrDefault(key, 0L) + 1); }
    void observationGroup(Direction group) { observationGroup = group; }
    void checkLocalSlot() {
        ((org.uma.jmetal.util.research.runtime.BudgetedProblem<?>) problem).checkpoint();
    }
    int ledgerGroup(Direction preference) {
        return (observationGroup == null ? preference : observationGroup).id();
    }
    int localFactory(PermutationSolution<Integer> parent, Direction preference, int randomFactory) {
        Direction group = observationGroup == null ? preference : observationGroup;
        int selected = support == null ? randomFactory : support.localFactory(parent, group, randomFactory);
        if (selected < 0 || selected >= instance.factories()) throw new IllegalStateException("Invalid local factory route");
        return selected;
    }
    List<PermutationSolution<Integer>> archive() { return ParetoTools.copies(archive); }
    Map<String, Long> diagnostics() { return Collections.unmodifiableMap(new LinkedHashMap<>(counts)); }
}
