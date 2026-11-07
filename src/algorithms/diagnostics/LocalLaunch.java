package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;

/** Isolated continuation-origin experiment; unchanged four roles, QGS, neighborhoods and sharing. */
public final class LocalLaunch {
    private static final String MODE = System.getProperty("research.launch.mode", "CURRENT");
    private static final Map<String,Long> counts = new LinkedHashMap<>();
    private LocalLaunch() { }
    private static void count(String key) { counts.put(key, counts.getOrDefault(key, 0L) + 1); }
    static Particle choose(Particle parent, Direction role, List<PermutationSolution<Integer>> reference) {
        if (!Arrays.asList("CURRENT", "OWN_HISTORY", "POOLED_ELITE").contains(MODE)) throw new IllegalArgumentException("Unknown launch rule");
        count("visits");
        if (parent.current.getAttribute("cooperation.family") != null) { count("fixedFamilyUnchanged"); return parent; }
        if (MODE.equals("CURRENT")) return parent;
        List<PermutationSolution<Integer>> candidates = MODE.equals("OWN_HISTORY") ? parent.personalArchive() : reference;
        PermutationSolution<Integer> best = parent.current;
        for (PermutationSolution<Integer> s : candidates) {
            if (s.getAttribute("cooperation.family") == null && LocalPddrKernel.better(role, s, best, reference)) best = s;
        }
        if (best == parent.current || same(best, parent.current)) return parent;
        count("changed"); count("changed." + role.name());
        if (ParetoTools.dominates(best, parent.current)) count("dominatesPreviousCurrent");
        return parent.descend(ParetoTools.copy(best));
    }
    private static boolean same(PermutationSolution<Integer> a, PermutationSolution<Integer> b) {
        return a.getVariables().equals(b.getVariables()) && a.getVariablesid().equals(b.getVariablesid())
                && a.getAttribute("machine").equals(b.getAttribute("machine")) && a.getVariablesworker().equals(b.getVariablesworker());
    }
    public static Map<String,Object> diagnostics() {
        Map<String,Object> out = new LinkedHashMap<>(); out.put("mode", MODE); out.put("counts", counts);
        out.put("scope", "Only free particles; no new evaluation or uncharged donor creation; actual candidate evaluation remains guarded.");
        return out;
    }
}
