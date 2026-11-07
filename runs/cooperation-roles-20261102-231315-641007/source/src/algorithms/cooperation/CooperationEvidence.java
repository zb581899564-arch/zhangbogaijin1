package org.uma.jmetal.util.research.cooperation;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.DynamicSchedule;
import org.uma.jmetal.util.research.search.SemanticAudit;

/** Retained-pool request evidence only. No candidate evaluation, RNG, or selection feedback. */
final class CooperationEvidence {
    private final SemanticAudit audit;
    private final List<Map<String, Object>> first = new ArrayList<>(), tail = new ArrayList<>();
    private long requests, tightRequests, tightMissing, feasible, improved;
    CooperationEvidence(SemanticAudit audit) { this.audit = audit; }

    void request(FactoryPool[] pools, PermutationSolution<Integer> parent, DynamicSchedule schedule,
            int family, int cycle, double cap, double eta, double energyScale, double wageScale,
            long generation, long paidFE, String outcome) {
        double seconds = audit.elapsedSeconds();
        if (!audit.withinDeadline()) return;
        requests++;
        List<Map<String, Object>> factories = new ArrayList<>();
        double[] combined = new double[3]; boolean possible = true;
        for (int f = 0; f < pools.length; f++) {
            FactoryRecord best = pools[f].choose(cap, eta, energyScale, wageScale);
            if (best == null) possible = false;
            else {
                combined[0] = Math.max(combined[0], best.objectives[0]);
                combined[1] += best.objectives[1]; combined[2] += best.objectives[2];
            }
            Map<String, Object> factory = new LinkedHashMap<>();
            factory.put("factory", f); factory.put("parent", record(new FactoryRecord(schedule, f)));
            List<Map<String, Object>> records = new ArrayList<>();
            for (FactoryRecord item : pools[f].records()) records.add(record(item));
            factory.put("records", records); factory.put("chosen", best == null ? null : record(best));
            factories.add(factory);
        }
        if (cycle / 3 == 0) { tightRequests++; if (!possible) tightMissing++; }
        double baseline = score(parent.getObjectives(), eta, energyScale, wageScale);
        double gain = possible && baseline > 0 ? (baseline - score(combined, eta, energyScale, wageScale)) / baseline : 0;
        if (possible) { feasible++; if (gain >= .001) improved++; }
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("type", "retained-pool-request"); row.put("request", requests);
        row.put("elapsedSeconds", seconds); row.put("deadlineValid", true);
        row.put("family", family); row.put("generation", generation); row.put("proposalFE", paidFE);
        row.put("cycle", cycle); row.put("cap", cap); row.put("eta", eta);
        row.put("energyScale", energyScale); row.put("wageScale", wageScale);
        row.put("parentObjectives", parent.getObjectives().clone()); row.put("outcome", outcome);
        row.put("feasible", possible); row.put("combinedObjectives", possible ? combined : null);
        row.put("weightedRelativeImprovement", possible ? gain : null); row.put("factories", factories);
        if (first.size() < 8) first.add(row);
        else { if (tail.size() == 8) tail.remove(0); tail.add(row); }
    }
    private static double score(double[] values, double eta, double energyScale, double wageScale) {
        return values[1] / energyScale + eta * values[2] / wageScale;
    }
    private static Map<String, Object> record(FactoryRecord item) {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("objectives", item.objectives.clone()); row.put("wholeObjectives", item.wholeObjectives.clone());
        row.put("jobs", item.jobs.clone()); row.put("machines", item.machines.clone()); row.put("workers", item.workers.clone());
        row.put("paidFE", item.paidFE); row.put("generation", item.generation);
        row.put("stage", item.stage); row.put("producer", item.producer); return row;
    }
    Map<String, Object> summary() {
        Map<String, Object> out = new LinkedHashMap<>(); out.put("requests", requests);
        out.put("tightRequests", tightRequests); out.put("tightRequestsMissingFactory", tightMissing);
        out.put("feasibleRequests", feasible); out.put("weightedImprovementAtLeast001", improved);
        out.put("samplePolicy", "first8+last8 requests; full counters; retained pools only");
        out.put("extraFE", 0); out.put("consumesRNG", false); return out;
    }
    List<Map<String, Object>> export() {
        List<Map<String, Object>> out = new ArrayList<>(); Map<String, Object> header = summary();
        header.put("type", "cooperation-evidence-summary"); out.add(header); out.addAll(first); out.addAll(tail); return out;
    }
}
