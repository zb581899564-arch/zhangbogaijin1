package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;

/** Read-only attribution counters; no comparison result is returned to the optimizer. */
public final class BundleWitness {
    private static final Map<String,Long> counts = new LinkedHashMap<>();
    private static final List<Map<String,Object>> selections = new ArrayList<>();
    private static int generation;
    private BundleWitness() { }
    private static void add(String k) { counts.put(k, counts.getOrDefault(k, 0L) + 1); }
    static void begin() { generation++; }
    static void paid(Particle parent, Particle child, Direction role) {
        String prefix = "gen" + generation + "." + role.name() + ".";
        add(prefix + "globalPaid");
        if (ParetoTools.dominates(child.current, parent.current)) add(prefix + "dominatesParent");
        if (ParetoTools.dominates(parent.current, child.current)) add(prefix + "dominatedByParent");
        String key = genome(child.current);
        if (child.personalArchive().stream().anyMatch(s -> genome(s).equals(key))) add(prefix + "retainedInPbestHistory");
        if (genome(child.personalBest(role)).equals(key)) add(prefix + "selectedAsPbest");
    }
    static void selected(List<Particle> global, List<Particle> local, List<Particle> survivors) {
        Set<Long> a = new HashSet<>(), b = new HashSet<>();
        for (Particle p : global) a.add(p.branchId());
        for (Particle p : local) b.add(p.branchId());
        int fromGlobal = 0, fromLocal = 0;
        for (Particle p : survivors) { if (a.contains(p.branchId())) fromGlobal++; if (b.contains(p.branchId())) fromLocal++; }
        Map<String,Object> r = new LinkedHashMap<>();
        r.put("generation", generation); r.put("survivors", survivors.size());
        r.put("fromGlobalSnapshots", fromGlobal); r.put("fromLocalEndpoints", fromLocal);
        selections.add(r);
    }
    public static void archiveAdmission(Object stage, boolean changed) {
        if (changed) add("gen" + generation + ".archiveAdmission." + String.valueOf(stage));
    }
    private static String genome(PermutationSolution<Integer> s) {
        return s.getVariables() + "/" + s.getVariablesid() + "/" + s.getAttribute("machine") + "/" + s.getVariablesworker();
    }
    public static Map<String,Object> report() {
        Map<String,Object> out = new LinkedHashMap<>(); out.put("counts", counts);
        out.put("completedSelections", selections); out.put("generationsStarted", generation);
        out.put("lineageWarning", "Next-generation admissions are observed, not attributed causally to a particular ancestor.");
        return out;
    }
}
