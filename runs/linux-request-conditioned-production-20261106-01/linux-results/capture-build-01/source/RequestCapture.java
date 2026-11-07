package org.uma.jmetal.util.research.cooperation;

import java.io.BufferedWriter;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.DynamicSchedule;
import org.uma.jmetal.util.research.search.GomRecords;
import org.uma.jmetal.util.research.search.RequestCaptureBridge;
import research.dynamic.DynamicJson;

/** Full real compose-request snapshots; no evaluation, random draw, or search feedback. */
public final class RequestCapture {
    private static final String PROPERTY = "research.request.capture";
    private static BufferedWriter writer;
    private static long sourceBefore, sourceAfter, requestOrdinal, capturedOrdinal;
    private static final long[] familyOrdinals = new long[4];
    private static boolean configured, closed;

    private RequestCapture() { }

    public static void observe(FactoryPool[] pools, PermutationSolution<Integer> parent,
            DynamicSchedule schedule, int family, int cycle, double cap, double eta,
            double energyScale, double wageScale, long generation, String outcome) {
        String folder = System.getProperty(PROPERTY);
        if (folder == null || closed) return;
        configure();
        requestOrdinal++;
        long paidFE = RequestCaptureBridge.currentFE();
        if (paidFE > sourceAfter) { close(); return; }
        if (paidFE < sourceBefore) return;
        if (family < 0 || family >= familyOrdinals.length) throw new IllegalStateException("Invalid request family");
        try {
            if (writer == null) open(Paths.get(folder));
            write(request(pools, parent, schedule, family, cycle, cap, eta, energyScale,
                wageScale, generation, paidFE, outcome));
        } catch (IOException error) {
            throw new UncheckedIOException("Request capture failed; retained partial evidence", error);
        }
    }

    private static void configure() {
        if (configured) return;
        sourceBefore = requiredLong("research.request.sourceBefore");
        sourceAfter = requiredLong("research.request.sourceAfter");
        if (sourceBefore < 0 || sourceAfter < sourceBefore)
            throw new IllegalArgumentException("Invalid inclusive request capture FE window");
        configured = true;
    }

    private static long requiredLong(String key) {
        String value = System.getProperty(key);
        if (value == null) throw new IllegalArgumentException("Missing required property: " + key);
        return Long.parseLong(value);
    }

    private static void open(Path folder) throws IOException {
        Files.createDirectories(folder);
        writer = Files.newBufferedWriter(folder.resolve("requests.jsonl"), StandardCharsets.UTF_8,
            StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        Map<String, Object> header = GomRecords.row("type", "request-capture-metadata", "schemaVersion", 1,
            "sourceBeforeGlobalFE", sourceBefore, "sourceAfterGlobalFE", sourceAfter,
            "window", "inclusive current successful FE at observeRequest; before next candidate evaluation",
            "capturePolicy", "all real observeRequest calls in FE window; complete A0 for each call",
            "requestOrdinalPolicy", "one-based among real requests since JVM capture enabled",
            "familyOrdinalPolicy", "one-based per family within capture window",
            "paidFEProvenance", "request paidFE is snapshot cutoff, not parent or record birth FE",
            "recordProvenance", "raw paidFE/generation are preserved; -1 means untracked, never inferred",
            "poolProvenance", "retained pool records come from successfully paid evaluated observations",
            "chosenSemantics", "pure FactoryPool.choose replay on unchanged pools; selectionVisited marks original prefix",
            "archiveSemantics", "A0 contains paid nondominated objective triples at request time; excludes proposed child",
            "extraFE", 0, "consumesRNG", false, "changesSelection", false);
        try { header.put("loaded", RequestCaptureBridge.loadedClasses(true)); }
        catch (Exception error) { throw new IOException("Cannot identify actual loaded classes", error); }
        write(header);
    }

    private static Map<String, Object> request(FactoryPool[] pools, PermutationSolution<Integer> parent,
            DynamicSchedule schedule, int family, int cycle, double cap, double eta,
            double energyScale, double wageScale, long generation, long paidFE, String outcome) {
        Map<String, Object> parentRow = GomRecords.raw(parent);
        List<Map<String, Object>> parentFactories = new ArrayList<>();
        List<Map<String, Object>> factoryPools = new ArrayList<>();
        boolean visited = true, feasible = true;
        double[] combined = new double[3];
        for (int f = 0; f < pools.length; f++) {
            parentFactories.add(GomRecords.row("factory", f, "record", record(new FactoryRecord(schedule, f), paidFE)));
            FactoryRecord chosen = pools[f].choose(cap, eta, energyScale, wageScale);
            List<Map<String, Object>> records = new ArrayList<>();
            int chosenIndex = -1, index = 0;
            for (FactoryRecord item : pools[f].records()) {
                if (item == chosen) chosenIndex = index;
                records.add(record(item, paidFE)); index++;
            }
            factoryPools.add(GomRecords.row("factory", f, "records", records, "selectionVisited", visited,
                "chosenIndex", chosenIndex, "chosen", chosen == null ? null : record(chosen, paidFE)));
            if (chosen == null) { feasible = false; visited = false; }
            else {
                combined[0] = Math.max(combined[0], chosen.objectives[0]);
                combined[1] += chosen.objectives[1]; combined[2] += chosen.objectives[2];
            }
        }
        parentRow.put("factories", parentFactories);
        parentRow.put("paidByFE", paidFE);
        parentRow.put("birthPaidFE", -1);
        parentRow.put("birthPaidFETracked", false);
        double[][] archive = RequestCaptureBridge.archive();
        return GomRecords.row("type", "compose-request", "requestOrdinal", requestOrdinal,
            "captureOrdinal", ++capturedOrdinal, "familyRequestOrdinal", ++familyOrdinals[family],
            "family", family, "cycle", cycle, "cap", cap, "eta", eta,
            "energyScale", energyScale, "wageScale", wageScale,
            "generation", generation, "paidFE", paidFE, "outcome", outcome,
            "parent", parentRow, "pools", factoryPools, "feasible", feasible,
            "combinedObjectives", feasible ? combined : null, "A0", archive,
            "A0Points", archive.length, "A0PaidThroughFE", paidFE);
    }

    private static Map<String, Object> record(FactoryRecord item, long snapshotFE) {
        return GomRecords.row("jobs", item.jobs.clone(), "machines", item.machines.clone(),
            "workers", item.workers.clone(), "objectives", item.objectives.clone(),
            "wholeObjectives", item.wholeObjectives.clone(), "paidFE", item.paidFE,
            "generation", item.generation, "stage", item.stage, "producer", item.producer,
            "paidFETracked", item.paidFE >= 0, "paidByFE", snapshotFE,
            "paidFEProvenance", item.paidFE >= 0 ? "original-record-metadata" : "untracked");
    }

    private static void write(Map<String, Object> row) throws IOException {
        writer.write(DynamicJson.encode(row)); writer.newLine(); writer.flush();
    }

    private static void close() {
        closed = true;
        if (writer == null) return;
        try { writer.close(); }
        catch (IOException error) { throw new UncheckedIOException(error); }
    }
}
