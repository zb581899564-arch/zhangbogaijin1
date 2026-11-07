package org.uma.jmetal.util.research.search;

import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.cooperation.CooperationSupport;
import org.uma.jmetal.util.research.model.Instance;

/** Supply the same paid initial vectors to a non-cooperative comparison, then remove family guards. */
public final class CommonInitials {
    private static CooperationSupport initializer;
    private CommonInitials() { }
    static void prepare(PermutationSolution<Integer> s, int index, Instance instance) {
        if (!Boolean.getBoolean("research.common.initials")) return;
        if (initializer == null) initializer = new CooperationSupport(instance, null, false);
        initializer.prepareInitialization(s, index);
        s.getAttributes().remove("cooperation.family");
        s.getAttributes().remove("cooperation.fixedFactoryByJob");
    }
}
