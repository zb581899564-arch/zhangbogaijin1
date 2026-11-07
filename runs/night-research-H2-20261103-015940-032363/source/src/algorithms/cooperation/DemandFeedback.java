package org.uma.jmetal.util.research.cooperation;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.search.Direction;
import org.uma.jmetal.util.research.search.SemanticAudit;

/** One fixed aspiration-cap supply rule, with a maintenance/query-matched SHAM control. */
final class DemandFeedback {
    private final String mode;
    private final SemanticAudit audit;
    private final double[] caps = new double[4];
    private final long[] requestFE = new long[4], requestGeneration = new long[4];
    private final List<Map<String, Object>> first = new ArrayList<>(), tail = new ArrayList<>();
    private long tightRequests, queries, eligible, actionable, overrides, resolved;
    DemandFeedback(String mode, SemanticAudit audit) {
        if (!mode.equals("DEMAND") && !mode.equals("SHAM")) throw new IllegalArgumentException("Demand mode must be DEMAND/SHAM");
        this.mode = mode; this.audit = audit; Arrays.fill(caps, Double.NaN);
    }
    void request(int family, double cap, long paidFE, long generation) {
        if (!audit.withinDeadline()) return;
        if (!(cap > 0) || !Double.isFinite(cap)) throw new IllegalArgumentException("Invalid demand cap");
        caps[family] = cap; requestFE[family] = paidFE; requestGeneration[family] = generation; tightRequests++;
    }
    int route(FactoryPool[] pools, int family, Direction group, int randomFactory, long paidFE, long generation) {
        double querySeconds = audit.elapsedSeconds();
        if (!audit.withinDeadline()) return randomFactory;
        queries++;
        if (family < 0 || group != Direction.MAKESPAN || Double.isNaN(caps[family])) return randomFactory;
        eligible++;
        double[] minima = new double[pools.length];
        for (int f = 0; f < pools.length; f++) {
            minima[f] = Double.POSITIVE_INFINITY;
            for (FactoryRecord record : pools[f].records()) minima[f] = Math.min(minima[f], record.objectives[0]);
            if (!Double.isFinite(minima[f])) throw new IllegalStateException("Demand queried an uninitialized factory pool");
        }
        int target = target(minima, caps[family]);
        if (target >= 0) actionable++; else resolved++;
        int selected = mode.equals("DEMAND") && target >= 0 ? target : randomFactory;
        if (selected != randomFactory) overrides++;
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("type", "demand-local-query"); row.put("query", queries); row.put("eligibleQuery", eligible);
        row.put("elapsedSeconds", querySeconds); row.put("deadlineValid", true);
        row.put("family", family); row.put("physicalGroup", group.name());
        row.put("generation", generation); row.put("queryFE", paidFE);
        row.put("requestFE", requestFE[family]); row.put("requestGeneration", requestGeneration[family]);
        row.put("cap", caps[family]); row.put("factoryMinC", minima);
        row.put("randomFactory", randomFactory); row.put("targetFactory", target); row.put("selectedFactory", selected);
        if (first.size() < 8) first.add(row);
        else { if (tail.size() == 8) tail.remove(0); tail.add(row); }
        return selected;
    }
    static int target(double[] minima, double cap) {
        int target = -1; double largest = 0;
        for (int f = 0; f < minima.length; f++) {
            double deficit = (minima[f] - cap) / cap;
            if (deficit > largest) { target = f; largest = deficit; }
        }
        return target;
    }
    Map<String, Object> summary() {
        Map<String, Object> out = new LinkedHashMap<>(); out.put("mode", mode);
        out.put("tightRequestsRecorded", tightRequests); out.put("queries", queries); out.put("eligibleQueries", eligible);
        out.put("actionableQueries", actionable); out.put("routedOverrides", overrides); out.put("resolvedOrNoGapQueries", resolved);
        out.put("samplePolicy", "first8+last8 eligible local queries; full counters");
        out.put("rule", "MAKESPAN family only; largest positive retained-pool minC/cap deficit; preserve original random draw");
        out.put("queryIsNotPaidCandidate", true); out.put("extraFE", 0); out.put("extraRNG", 0); return out;
    }
    List<Map<String, Object>> export() {
        List<Map<String, Object>> out = new ArrayList<>(); Map<String, Object> header = summary();
        header.put("type", "demand-feedback-summary"); out.add(header); out.addAll(first); out.addAll(tail); return out;
    }
}
