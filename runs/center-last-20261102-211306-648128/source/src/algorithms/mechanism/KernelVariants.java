package org.uma.jmetal.util.research.mechanism;

import java.util.Objects;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.classic.ClassicKernelBridge;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.model.ModelKind;
import org.uma.jmetal.util.research.search.ParticleOperators;
import org.uma.jmetal.util.research.search.SearchConfig;

/** Single-proposal kernels only: no selection, QGS, evaluation, or RNG reset. */
public final class KernelVariants {
    public static final String PAPER = "PAPER";
    public static final String JOB_ALIGNED = "JOB_ALIGNED";
    public static final String CLASSIC_GLOBAL = "CLASSIC_GLOBAL";
    public static final String CLASSIC_PERSONAL = "CLASSIC_PERSONAL";

    private final ParticleOperators paper;
    private final JobAlignedPaperKernel aligned;
    private final ClassicKernelBridge classic;
    private final Runnable checkpoint;

    public KernelVariants(Instance instance, SearchConfig paperConfig, Runnable checkpoint) {
        Objects.requireNonNull(instance, "instance");
        if (instance.kind() != ModelKind.CHAPTER4_DUAL_RESOURCE) {
            throw new IllegalArgumentException("This probe requires chapter 4 four-vector semantics");
        }
        SearchConfig resolved = Objects.requireNonNull(paperConfig, "paperConfig").resolved(4);
        if (!resolved.paperResourceOperators) {
            throw new IllegalArgumentException("PAPER requires the frozen O resource semantics");
        }
        this.checkpoint = Objects.requireNonNull(checkpoint, "checkpoint");
        paper = new ParticleOperators(instance, resolved);
        aligned = new JobAlignedPaperKernel(instance, resolved);
        classic = new ClassicKernelBridge(instance, checkpoint);
    }

    /**
     * PAPER/aligned keep their internal stage repairs. Every returned candidate still
     * needs the same final common repair and one guarded paid evaluation by the caller.
     * Equal seeds do not imply equal random draws between different kernels.
     */
    public PermutationSolution<Integer> child(String kernel, PermutationSolution<Integer> parent,
            PermutationSolution<Integer> personal, PermutationSolution<Integer> global) {
        checkpoint.run();
        if (PAPER.equals(kernel)) return paper.update(parent, personal, global);
        if (JOB_ALIGNED.equals(kernel)) return aligned.child(parent, personal, global);
        if (CLASSIC_GLOBAL.equals(kernel)) return classic.child(parent, global);
        if (CLASSIC_PERSONAL.equals(kernel)) return classic.child(parent, personal);
        throw new IllegalArgumentException("Unknown probe kernel: " + kernel);
    }
}
