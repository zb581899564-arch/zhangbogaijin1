package org.uma.jmetal.util.research.classic;

import java.util.Objects;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.Instance;

/** Public research access to the unchanged setting-0 classic generation kernel. */
public final class ClassicKernelBridge {
    private final ClassicVariation variation;

    public ClassicKernelBridge(Instance instance, Runnable checkpoint) {
        variation = new ClassicVariation(Objects.requireNonNull(instance, "instance"),
                new ClassicConfig("NSGA2_4V", 0), Objects.requireNonNull(checkpoint, "checkpoint"));
    }

    /** Uses the caller's RNG; leaves common repair and the charged evaluation to the caller. */
    public PermutationSolution<Integer> child(PermutationSolution<Integer> first,
            PermutationSolution<Integer> second) {
        return variation.child(first, second);
    }
}
