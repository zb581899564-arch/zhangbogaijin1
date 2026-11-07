package org.uma.jmetal.util.research.search;

import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.cooperation.CooperationSupport;
import org.uma.jmetal.util.research.model.Instance;

/** Reuse the existing common initialization, then release family guards for an ordinary method. */
public final class PaInitialBridge {
    private final CooperationSupport initializer;
    public PaInitialBridge(Instance instance) { initializer = new CooperationSupport(instance, null, false); }
    public void prepare(PermutationSolution<Integer> point, int index) {
        initializer.prepareInitialization(point, index);
        point.getAttributes().remove("cooperation.family"); point.getAttributes().remove("cooperation.fixedFactoryByJob");
    }
}
