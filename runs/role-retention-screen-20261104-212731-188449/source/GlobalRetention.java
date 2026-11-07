package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;

/** Isolated global survivor semantics, not a correction to the published PSO model. */
public final class GlobalRetention {
    private static final String MODE = System.getProperty("research.retention.mode", "FORCE");
    private static final Map<String,Long> counts = new LinkedHashMap<>();
    private GlobalRetention() { }
    private static void count(String s) { counts.put(s, counts.getOrDefault(s, 0L) + 1); }
    static Particle next(Particle parent, PermutationSolution<Integer> child, Direction role,
            List<PermutationSolution<Integer>> reference) {
        count("paid");
        boolean worse = ParetoTools.dominates(parent.current, child);
        if (worse) count("dominatedByParent");
        boolean accept;
        switch (MODE) {
            case "FORCE": accept = true; break;
            case "DOM_GUARD": accept = !worse; break;
            case "ROLE_GREEDY": accept = LocalPddrKernel.better(role, child, parent.current, reference); break;
            case "CENTER_GREEDY": accept = LocalPddrKernel.better(Direction.CENTER, child, parent.current, reference); break;
            default: throw new IllegalArgumentException("Unknown global retention");
        }
        if (!accept) { count("rejected"); count("rejected." + role.name()); return parent; }
        count("accepted"); return parent.descend(child);
    }
    public static Map<String,Object> diagnostics() {
        Map<String,Object> out = new LinkedHashMap<>(); out.put("mode", MODE); out.put("counts", counts); return out;
    }
}
