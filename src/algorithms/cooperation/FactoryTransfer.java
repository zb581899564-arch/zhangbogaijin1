package org.uma.jmetal.util.research.cooperation;

import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.DoubleSupplier;
import java.util.function.LongSupplier;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.DynamicSchedule;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import org.uma.jmetal.util.research.search.Direction;

/** Factorial packet/mosaic and role/uniform experiment; one constructed child always pays one FE. */
final class FactoryTransfer {
    private final String mode;
    private final boolean packet, role;
    private final LongSupplier successful;
    private final DoubleSupplier elapsed;
    private final double limit;
    private final long[][] opportunities = new long[4][4];
    private final Map<PermutationSolution<Integer>, Pending> pending = new IdentityHashMap<>();
    private final List<Map<String, Object>> first = new ArrayList<>(), tail = new ArrayList<>();
    private long eligible, attempts, draws, paid, validPaid, sourcePreserved, sourceTimeline, unchangedOthers;

    FactoryTransfer(String mode, LongSupplier successful, DoubleSupplier elapsed, double limit) {
        if (!mode.equals("PACKET_ROLE") && !mode.equals("MOSAIC_ROLE") && !mode.equals("PACKET_RANDOM") && !mode.equals("MOSAIC_RANDOM"))
            throw new IllegalArgumentException("Unknown factory transfer mode");
        this.mode = mode; packet = mode.startsWith("PACKET"); role = mode.endsWith("ROLE");
        this.successful = successful; this.elapsed = elapsed; this.limit = limit;
    }
    PermutationSolution<Integer> propose(PermutationSolution<Integer> parent, Direction direction,
            int family, FactoryPool[] pools, long generation) {
        if (family < 0 || direction == Direction.CENTER) return null;
        eligible++;
        if (++opportunities[family][direction.ordinal()] % 4 != 0) return null;
        attempts++; DynamicSchedule before = (DynamicSchedule) parent.getAttribute(DynamicEvaluation.KEY);
        int factory = TransferEncoding.target(before, direction);
        List<FactoryRecord> candidates = pools[factory].records();
        if (candidates.isEmpty()) throw new IllegalStateException("Paid family pool is empty");
        FactoryRecord[] sources = new FactoryRecord[3]; List<Map<String, Object>> sampled = new ArrayList<>();
        for (int component = 0; component < 3; component++) {
            int a = SeededRandom.current().nextInt(candidates.size()), b = SeededRandom.current().nextInt(candidates.size()); draws += 2;
            FactoryRecord first = candidates.get(a), second = candidates.get(b);
            boolean pickSecond = role && second.objectives[direction.objective()] < first.objectives[direction.objective()];
            sources[component] = pickSecond ? second : first;
            Map<String, Object> pair = new LinkedHashMap<>(); pair.put("firstOrdinal", a); pair.put("secondOrdinal", b);
            pair.put("first", TransferEncoding.record(first)); pair.put("second", TransferEncoding.record(second));
            pair.put("selectedSecond", pickSecond); sampled.add(pair);
        }
        FactoryRecord ma = packet ? sources[0] : sources[1], wa = packet ? sources[0] : sources[2];
        PermutationSolution<Integer> child = TransferEncoding.build(parent, factory, sources[0], ma, wa);
        Pending item = new Pending(family, factory, direction, generation, successful.getAsLong(), before, sources[0], sampled,
                TransferEncoding.encoding(child, factory));
        if (pending.put(child, item) != null) throw new IllegalStateException("Transfer child registered twice");
        return child; // Duplicates are deliberately evaluated, never silently replaced by another operator.
    }
    void evaluated(PermutationSolution<Integer> child) {
        Pending item = pending.remove(child); if (item == null) return;
        paid++;
        if (successful.getAsLong() != item.proposalFE + 1) throw new IllegalStateException("Transfer hid extra FE");
        DynamicSchedule actual = (DynamicSchedule) child.getAttribute(DynamicEvaluation.KEY);
        FactoryRecord local = new FactoryRecord(actual, item.factory);
        boolean intact = item.source.same(local);
        boolean timeline = TransferEncoding.timelineMatches(item.source.sourceSchedule, actual, item.factory);
        boolean others = TransferEncoding.othersPreserved(item.parent, actual, item.factory);
        if (!others || packet && (!intact || !timeline)) throw new IllegalStateException("Factory transfer broke its declared context");
        if (intact) sourcePreserved++; if (timeline) sourceTimeline++; if (others) unchangedOthers++;
        double seconds = elapsed.getAsDouble(); if (seconds <= limit) validPaid++;
        Map<String, Object> row = new LinkedHashMap<>(); row.put("type", "factory-transfer-paid"); row.put("event", paid);
        row.put("mode", mode); row.put("family", item.family); row.put("factory", item.factory); row.put("direction", item.direction.name());
        row.put("generation", item.generation); row.put("proposalFE", item.proposalFE); row.put("paidFE", successful.getAsLong());
        row.put("elapsedSeconds", seconds); row.put("deadlineValid", seconds <= limit);
        row.put("parentObjectives", item.parent.objectives()); row.put("objectives", child.getObjectives().clone());
        row.put("sampledPairs", item.sampled); row.put("source0", TransferEncoding.record(item.source));
        row.put("beforeRepairLocal", item.beforeRepairLocal);
        row.put("actualLocal", TransferEncoding.record(local)); row.put("source0EncodingPreserved", intact);
        row.put("source0TimelineMatched", timeline); row.put("otherFactoriesPreserved", others);
        if (first.size() < 8) first.add(row); else { if (tail.size() == 8) tail.remove(0); tail.add(row); }
    }
    Map<String, Object> summary() {
        Map<String, Object> out = new LinkedHashMap<>(); out.put("mode", mode); out.put("eligibleOpportunities", eligible);
        out.put("scheduledAttempts", attempts); out.put("sourceRandomDraws", draws); out.put("paidTransfers", paid);
        out.put("deadlineValidPaidTransfers", validPaid); out.put("source0EncodingPreserved", sourcePreserved);
        out.put("source0TimelineMatched", sourceTimeline); out.put("otherFactoriesPreserved", unchangedOthers);
        out.put("pendingTransfers", pending.size()); out.put("samplePolicy", "first8+last8 paid transfers; full counters");
        out.put("duplicatesArePaid", true); out.put("sourceMarginals", "Three pairs/six draws in every mode; packet uses first selected record for all components");
        List<Map<String, Object>> counts = new ArrayList<>();
        for (int f = 0; f < 4; f++) for (Direction d : Direction.values()) if (d != Direction.CENTER) {
            Map<String, Object> cell = new LinkedHashMap<>(); cell.put("family", f); cell.put("direction", d.name());
            cell.put("opportunities", opportunities[f][d.ordinal()]); counts.add(cell);
        }
        out.put("perFamilyDirection", counts); return out;
    }
    List<Map<String, Object>> trace() {
        List<Map<String, Object>> out = new ArrayList<>(); Map<String, Object> header = summary();
        header.put("type", "factory-transfer-summary"); out.add(header); out.addAll(first); out.addAll(tail); return out;
    }
    private static final class Pending {
        final int family, factory; final Direction direction; final long generation, proposalFE;
        final DynamicSchedule parent; final FactoryRecord source; final List<Map<String, Object>> sampled;
        final Map<String, Object> beforeRepairLocal;
        Pending(int family, int factory, Direction direction, long generation, long proposalFE,
                DynamicSchedule parent, FactoryRecord source, List<Map<String, Object>> sampled, Map<String, Object> beforeRepairLocal) {
            this.family = family; this.factory = factory; this.direction = direction; this.generation = generation;
            this.proposalFE = proposalFE; this.parent = parent; this.source = source; this.sampled = sampled;
            this.beforeRepairLocal = beforeRepairLocal;
        }
    }
}
