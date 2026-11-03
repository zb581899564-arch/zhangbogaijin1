package org.uma.jmetal.util.research.cooperation;

import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.search.SemanticAudit;

/** Numeric provenance of actually evaluated assemblies. Never changes pool selection or RNG. */
final class CompositionTiming {
    private final SemanticAudit audit;
    private final Map<PermutationSolution<Integer>, Pending> pending = new IdentityHashMap<>();
    private final List<Map<String, Object>> first = new ArrayList<>(), tail = new ArrayList<>();
    private final Map<String, Long> producers = new LinkedHashMap<>(), sameGenerationProducers = new LinkedHashMap<>();
    private final Map<Long, GenerationCounts> byGeneration = new LinkedHashMap<>();
    private long generation, currentFE, paid, validPaid, admissions, fragments, sameGeneration, initialFragments;
    private long ageSum, maxAge, lateGroupFresh;
    CompositionTiming(SemanticAudit audit) { this.audit = audit; }
    void begin() { generation++; byGeneration.put(generation, new GenerationCounts(generation)); }
    void opportunity() { byGeneration.get(generation).opportunities++; }
    long generation() { return generation; }
    long currentFE() { return currentFE; }
    void observed(PermutationSolution<Integer> solution) {
        currentFE = SemanticAudit.paidSnapshotFE(solution);
        if (currentFE < 1) throw new IllegalStateException("Unpaid factory observation");
        Pending item = pending.remove(solution);
        if (item == null) return;
        paid++;
        GenerationCounts gen = byGeneration.get(item.generation); gen.paid++;
        double seconds = audit.elapsedSeconds();
        if (!audit.withinDeadline()) return;
        validPaid++;
        gen.validPaid++;
        boolean admitted = SemanticAudit.wasExternalAdmission(solution); if (admitted) admissions++;
        List<Map<String, Object>> sources = new ArrayList<>();
        for (int f = 0; f < item.records.length; f++) {
            FactoryRecord record = item.records[f]; long age = item.proposalFE - record.paidFE;
            if (record.paidFE < 1 || age < 0 || record.generation > item.generation)
                throw new IllegalStateException("Assembly chose a future/unpaid fragment");
            fragments++; ageSum += age; maxAge = Math.max(maxAge, age);
            gen.fragments++;
            producers.put(record.producer, producers.getOrDefault(record.producer, 0L) + 1);
            boolean fresh = record.generation == item.generation;
            if (fresh) {
                gen.fresh++;
                sameGeneration++; sameGenerationProducers.put(record.producer, sameGenerationProducers.getOrDefault(record.producer, 0L) + 1);
                if (record.producer.equals("ENERGY") || record.producer.equals("WORKER_COST")) { lateGroupFresh++; gen.lateFresh++; }
            }
            if (record.generation == 0) initialFragments++;
            Map<String, Object> source = new LinkedHashMap<>(); source.put("factory", f);
            source.put("paidFE", record.paidFE); source.put("generation", record.generation);
            source.put("stage", record.stage); source.put("producer", record.producer);
            source.put("ageFEAtProposal", age); source.put("sameGeneration", fresh); sources.add(source);
        }
        Map<String, Object> row = new LinkedHashMap<>(); row.put("type", "composition-paid");
        row.put("generation", item.generation); row.put("proposalFE", item.proposalFE); row.put("paidFE", currentFE);
        row.put("family", item.family); row.put("deadlineValid", true); row.put("elapsedSeconds", seconds);
        row.put("externalArchiveAdmission", admitted); row.put("objectives", solution.getObjectives().clone()); row.put("fragments", sources);
        if (first.size() < 16) first.add(row);
        else { if (tail.size() == 16) tail.remove(0); tail.add(row); }
    }
    void proposed(PermutationSolution<Integer> solution, FactoryRecord[] records, int family) {
        byGeneration.get(generation).proposed++;
        if (pending.put(solution, new Pending(generation, currentFE, family, records)) != null)
            throw new IllegalStateException("Assembly registered twice");
    }
    Map<String, Object> summary() {
        Map<String, Object> row = new LinkedHashMap<>(); row.put("enabled", true); row.put("observationOnly", true);
        row.put("generationsStarted", generation); row.put("paidAssemblies", paid); row.put("deadlineValidPaidAssemblies", validPaid);
        row.put("deadlineValidArchiveAdmissions", admissions); row.put("selectedFragments", fragments);
        row.put("sameGenerationFragments", sameGeneration); row.put("sameGenerationLateGroupFragments", lateGroupFresh);
        row.put("initializationFragments", initialFragments); row.put("fragmentAgeFESum", ageSum); row.put("fragmentAgeFEMax", maxAge);
        row.put("fragmentAgeFEMean", fragments == 0 ? null : (double) ageSum / fragments);
        row.put("fromProducer", new LinkedHashMap<>(producers)); row.put("sameGenerationFromProducer", new LinkedHashMap<>(sameGenerationProducers));
        row.put("unpaidPendingAssemblies", pending.size()); row.put("samplePolicy", "first16+last16 paid, full aggregate counters");
        List<Map<String, Object>> generations = new ArrayList<>();
        for (GenerationCounts item : byGeneration.values()) generations.add(item.record());
        row.put("perGeneration", generations);
        row.put("provenance", "Paid occurrence of the retained factory record; duplicate offers do not refresh its timestamp"); return row;
    }
    List<Map<String, Object>> export() {
        List<Map<String, Object>> out = new ArrayList<>(); Map<String, Object> header = summary();
        header.put("type", "composition-summary"); out.add(header); out.addAll(first); out.addAll(tail); return out;
    }
    private static final class Pending {
        final long generation, proposalFE; final int family; final FactoryRecord[] records;
        Pending(long generation, long proposalFE, int family, FactoryRecord[] records) {
            this.generation = generation; this.proposalFE = proposalFE; this.family = family; this.records = records.clone();
        }
    }
    private static final class GenerationCounts {
        final long id; long opportunities, proposed, paid, validPaid, fragments, fresh, lateFresh;
        GenerationCounts(long id) { this.id = id; }
        Map<String, Object> record() {
            Map<String, Object> row = new LinkedHashMap<>(); row.put("generation", id);
            row.put("eligibleCenterOpportunities", opportunities); row.put("proposedAssemblies", proposed);
            row.put("paidAssemblies", paid); row.put("validPaidAssemblies", validPaid); row.put("selectedFragments", fragments);
            row.put("sameGenerationFragments", fresh); row.put("sameGenerationLateGroupFragments", lateFresh); return row;
        }
    }
}
