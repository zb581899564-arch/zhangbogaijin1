package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;

/** Engineering-only decision evidence; disabled during all performance comparisons. */
public final class CenterTaskAudit {
    private static final boolean ENABLED = Boolean.getBoolean("research.centerTasks.audit");
    private static final List<Map<String,Object>> RECORDS = new ArrayList<>();
    private CenterTaskAudit() { }

    private static Map<String,Object> base(String stage, CenterTaskState.Owner owner, double[] ideal) {
        Map<String,Object> out = new LinkedHashMap<>();
        out.put("stage", stage); out.put("epoch", owner.epoch); out.put("slot", owner.slot);
        out.put("weight", owner.weight); out.put("mode", CenterTaskState.MODE.name());
        out.put("ideal", ideal.clone());
        out.put("paidFE", CenterTaskState.COUNTS.getOrDefault("successfulPaidIdealUpdates", 0L));
        return out;
    }

    static void comparison(String stage, CenterTaskState.Owner owner, double[] ideal,
            PermutationSolution<Integer> before, PermutationSolution<Integer> after, boolean accepted) {
        if (!ENABLED || !CenterTaskState.scalar()) return;
        Map<String,Object> out = base(stage, owner, ideal);
        out.put("before", before.getObjectives().clone()); out.put("after", after.getObjectives().clone());
        out.put("beforeScore", CenterTaskState.score(before, owner, ideal));
        out.put("afterScore", CenterTaskState.score(after, owner, ideal));
        out.put("accepted", accepted); RECORDS.add(out);
    }

    static void personal(CenterTaskState.Owner owner, double[] ideal,
            List<PermutationSolution<Integer>> history, PermutationSolution<Integer> chosen) {
        if (!ENABLED) return;
        Map<String,Object> out = base("PERSONAL", owner, ideal);
        List<double[]> points = new ArrayList<>();
        for (PermutationSolution<Integer> point : history) points.add(point.getObjectives().clone());
        out.put("history", points); out.put("chosen", chosen.getObjectives().clone()); RECORDS.add(out);
    }

    public static List<Map<String,Object>> records() { return new ArrayList<>(RECORDS); }
}
