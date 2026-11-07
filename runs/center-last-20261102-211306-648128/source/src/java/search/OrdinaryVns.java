package org.uma.jmetal.util.research.search;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.Instance;

/** Narrow facade over the same chapter-4 ordinary inter/intra search; no QGS or support. */
public final class OrdinaryVns {
    private final SearchState state;
    private final LocalSearch search;
    private final Runnable checkpoint;
    private long calls;

    public OrdinaryVns(Problem<PermutationSolution<Integer>> guarded, Instance instance,
            int localProposalCap, Runnable checkpoint) {
        this(guarded, instance, localProposalCap, checkpoint, null);
    }
    public OrdinaryVns(Problem<PermutationSolution<Integer>> guarded, Instance instance,
            int localProposalCap, Runnable checkpoint, SemanticAudit audit) {
        if (localProposalCap < 1 || checkpoint == null) throw new IllegalArgumentException("VNS cap/checkpoint required");
        this.checkpoint = checkpoint;
        SearchConfig config = new SearchConfig(); config.localProposalCap = localProposalCap;
        state = new SearchState(new CheckedProblem(guarded, checkpoint), instance, null, audit);
        search = new LocalSearch(instance, 4, config.resolved(4), state);
    }

    public PermutationSolution<Integer> improve(PermutationSolution<Integer> evaluated,
            List<PermutationSolution<Integer>> currentPopulation) {
        checkpoint.run(); calls++;
        return search.improve(new Particle(ParetoTools.copy(evaluated)), Direction.CENTER, currentPopulation).current;
    }
    public Map<String, Long> diagnostics() {
        Map<String, Long> result = new LinkedHashMap<>(state.diagnostics());
        result.put("calls", calls); return result;
    }

    private static final class CheckedProblem implements Problem<PermutationSolution<Integer>> {
        private static final long serialVersionUID = 1L;
        private final Problem<PermutationSolution<Integer>> delegate;
        private final Runnable checkpoint;
        CheckedProblem(Problem<PermutationSolution<Integer>> delegate, Runnable checkpoint) {
            this.delegate = delegate; this.checkpoint = checkpoint;
        }
        @Override public void evaluate(PermutationSolution<Integer> solution) { checkpoint.run(); delegate.evaluate(solution); checkpoint.run(); }
        @Override public PermutationSolution<Integer> createSolution() { checkpoint.run(); return delegate.createSolution(); }
        @Override public int getNumberOfVariables() { return delegate.getNumberOfVariables(); }
        @Override public int getNumberOfObjectives() { return delegate.getNumberOfObjectives(); }
        @Override public int getNumberOfConstraints() { return delegate.getNumberOfConstraints(); }
        @Override public String getName() { return delegate.getName(); }
    }
}
