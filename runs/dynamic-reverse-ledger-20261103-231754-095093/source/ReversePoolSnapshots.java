package org.uma.jmetal.util.research.cooperation;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.DynamicSchedule;
import org.uma.jmetal.util.research.search.ReverseAudit;

/** Retains first/last requests per family in the first and most recent entered CENTER stage. */
public final class ReversePoolSnapshots {
    private static Stage first, latest;
    private static long request;
    private ReversePoolSnapshots() {}

    private static final class Stage {
        final long generation;
        final Map<Integer, Map<String, Object>> head = new LinkedHashMap<>(), tail = new LinkedHashMap<>();
        Stage(long generation) { this.generation = generation; }
        void emit(Map<Long, Map<String, Object>> rows) {
            for (Map<String, Object> r : head.values()) rows.put((Long) r.get("request"), r);
            for (Map<String, Object> r : tail.values()) rows.put((Long) r.get("request"), r);
        }
    }

    public static void enter(long generation) {
        latest = new Stage(generation);
        if (first == null) first = latest;
    }

    static void capture(FactoryPool[] pools, PermutationSolution<Integer> parent, DynamicSchedule schedule,
            int family, int cycle, double cap, double eta, double energyScale, double wageScale, String outcome) {
        if (latest == null) throw new IllegalStateException("Request without entered CENTER stage");
        long start = System.nanoTime();
        ReverseAudit audit = ReverseAudit.run();
        List<Map<String, Object>> factories = new ArrayList<>();
        for (int f = 0; f < pools.length; f++) {
            List<Map<String, Object>> records = new ArrayList<>();
            for (FactoryRecord r : pools[f].records()) records.add(record(r));
            FactoryRecord chosen = pools[f].choose(cap, eta, energyScale, wageScale);
            factories.add(ReverseAudit.row("factory", f, "parent", record(new FactoryRecord(schedule, f)),
                    "records", records, "chosen", chosen == null ? null : record(chosen)));
        }
        Map<String, Object> row = ReverseAudit.row("request", ++request, "generation", latest.generation,
                "family", family, "paidFE", audit.fe(), "cycle", cycle, "cap", cap, "eta", eta,
                "energyScale", energyScale, "wageScale", wageScale, "outcome", outcome,
                "parent", ReverseAudit.genome(parent), "parentObjectives", parent.getObjectives().clone(),
                "archive", audit.archive(), "factories", factories);
        latest.head.putIfAbsent(family, row);
        latest.tail.put(family, row);
        audit.chargedTime(System.nanoTime() - start);
    }

    public static void finish(Path out) throws IOException {
        Map<Long, Map<String, Object>> rows = new java.util.TreeMap<>();
        if (first != null) first.emit(rows);
        if (latest != null) latest.emit(rows);
        ReverseAudit.writeRows(out.resolve("pool-snapshots.jsonl"), new ArrayList<>(rows.values()));
        ReverseAudit.writeRows(out.resolve("pool-window.jsonl"), java.util.Collections.singletonList(
                ReverseAudit.row("first", first == null ? null : first.generation,
                        "last", latest == null ? null : latest.generation, "requests", request)));
    }

    private static Map<String, Object> record(FactoryRecord r) {
        return ReverseAudit.row("jobs", r.jobs.clone(), "machines", r.machines.clone(), "workers", r.workers.clone(),
                "objectives", r.objectives.clone(), "paidFE", r.paidFE, "generation", r.generation,
                "stage", r.stage, "producer", r.producer);
    }
}
