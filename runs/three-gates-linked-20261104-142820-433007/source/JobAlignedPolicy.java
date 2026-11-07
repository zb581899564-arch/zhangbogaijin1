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
    private final LinkedGuideKernel linked;
    private static LinkedGuideKernel active;
    public static java.util.Map<String,Object> bundleDiagnostics() {
        return active == null ? new java.util.LinkedHashMap<>() : active.diagnostics();
    }

    public JobAlignedPolicy(Instance instance, SearchConfig config) {
        SearchConfig resolved = config.resolved(4);
        if (!resolved.paperResourceOperators || !resolved.mergeGlobalLocal)
            throw new IllegalArgumentException("JOB_ALIGNED closure requires the frozen SO profile");
        kernel = new JobAlignedPaperKernel(instance, resolved);
        String mode = System.getProperty("research.bundle.mode", "BASE");
        if (!mode.equals("BASE") && !mode.equals("LINKED") && !mode.equals("RANDOM"))
            throw new IllegalArgumentException("Unknown bundle arm");
        linked = mode.equals("BASE") ? null : new LinkedGuideKernel(instance, resolved, mode.equals("RANDOM"));
        active = linked;
    }

    @Override public PermutationSolution<Integer> propose(PermutationSolution<Integer> parent,
            PermutationSolution<Integer> personal, PermutationSolution<Integer> leader, Direction direction) {
        PermutationSolution<Integer> child = linked == null ? kernel.child(parent, personal, leader) : linked.child(parent, personal, leader);
        proposals++;
        return child;
    }
    public long proposals() { return proposals; }
}
