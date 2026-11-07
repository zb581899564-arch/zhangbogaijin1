package org.uma.jmetal.util.research.mechanism;

import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.search.Direction;
import org.uma.jmetal.util.research.search.GlobalUpdatePolicy;
import org.uma.jmetal.util.research.search.SearchConfig;

/** The already-probed identity-aligned kernel, with no extra learning or acceptance rule. */
public final class JobAlignedPolicy implements GlobalUpdatePolicy {
    private final JobAlignedPaperKernel kernel;
    private long proposals;

    public JobAlignedPolicy(Instance instance, SearchConfig config) {
        SearchConfig resolved = config.resolved(4);
        if (!resolved.paperResourceOperators || !resolved.mergeGlobalLocal)
            throw new IllegalArgumentException("JOB_ALIGNED closure requires the frozen SO profile");
        kernel = new JobAlignedPaperKernel(instance, resolved);
    }

    @Override public PermutationSolution<Integer> propose(PermutationSolution<Integer> parent,
            PermutationSolution<Integer> personal, PermutationSolution<Integer> leader, Direction direction) {
        PermutationSolution<Integer> child = kernel.child(parent, personal, leader);
        proposals++;
        return child;
    }
    public long proposals() { return proposals; }
}
