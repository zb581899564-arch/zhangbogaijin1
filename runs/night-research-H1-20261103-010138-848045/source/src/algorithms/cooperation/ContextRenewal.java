package org.uma.jmetal.util.research.cooperation;

import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.DoubleSupplier;
import java.util.function.LongSupplier;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import org.uma.jmetal.util.research.search.Direction;
import org.uma.jmetal.util.research.search.ParetoTools;

/** Once per generation, compare elite versus random CURRENT free-particle FA contexts. */
final class ContextRenewal {
    private final String mode;
    private final LongSupplier successful;
    private final DoubleSupplier elapsed;
    private final Map<PermutationSolution<Integer>, Integer> pending = new IdentityHashMap<>();
    private final List<Map<String, Object>> first = new ArrayList<>(), tail = new ArrayList<>();
    private Map<String, Object> active;
    private List<double[]> newObjectives;
    private long events, completed, evaluations, skips;
    private int family = -1, activePaid;

    ContextRenewal(String mode, LongSupplier successful, DoubleSupplier elapsed) {
        if (!mode.equals("ELITE") && !mode.equals("RANDOM")) throw new IllegalArgumentException("Unknown renewal mode");
        this.mode = mode; this.successful = successful; this.elapsed = elapsed;
    }
    @SuppressWarnings("unchecked")
    Map<Integer, PermutationSolution<Integer>> prepare(List<PermutationSolution<Integer>> population,
            FamilyContexts contexts, long generation) {
        Map<Integer, PermutationSolution<Integer>> replacements = new LinkedHashMap<>();
        if (generation < 2) return replacements;
        if (active != null || !pending.isEmpty()) throw new IllegalStateException("Previous renewal was incomplete");
        List<Integer> candidates = new ArrayList<>(); List<PermutationSolution<Integer>> values = new ArrayList<>();
        for (int i = 0; i < population.size(); i++) {
            PermutationSolution<Integer> value = population.get(i);
            if (FamilyContexts.family(value) < 0 && !contexts.matchesAny(value)) { candidates.add(i); values.add(value); }
        }
        if (values.isEmpty()) { skips++; return replacements; }
        List<Integer> ranked = ParetoTools.order(values, Direction.CENTER);
        int random = SeededRandom.current().nextInt(values.size()); // Both controls pay the same draw/ranking.
        int ordinal = mode.equals("ELITE") ? ranked.get(0) : random;
        int donorIndex = candidates.get(ordinal); PermutationSolution<Integer> donor = population.get(donorIndex);
        family = (int) ((generation - 2) % 4);
        List<int[]> previous = new ArrayList<>();
        for (int f = 0; f < 4; f++) previous.add(contexts.assignment(f));
        int[] old = contexts.assignment(family), assignment = FamilyContexts.byJob(donor);
        long epoch = contexts.replace(family, assignment);
        beginEvent(generation, epoch, donorIndex, candidates.size(), random, ordinal, old, assignment, donor);
        active.put("previousFactoryAssignments", previous); active.put("candidatePopulationIndices", candidates);
        active.put("rankedCandidateOrdinals", ranked);
        List<double[]> objectives = new ArrayList<>();
        for (PermutationSolution<Integer> value : values) objectives.add(value.getObjectives().clone());
        active.put("candidateObjectives", objectives); active.put("donorFamily", FamilyContexts.family(donor));
        List<Integer> indices = new ArrayList<>();
        for (int i = 0; i < population.size(); i++) if (FamilyContexts.family(population.get(i)) == family) {
            PermutationSolution<Integer> child = (PermutationSolution<Integer>) population.get(i).copy();
            contexts.attachRenewed(child, family); replacements.put(i, child); pending.put(child, i); indices.add(i);
        }
        if (indices.size() != 5) throw new IllegalStateException("Renewed context must contain exactly five particles");
        active.put("particleIndices", indices); return replacements;
    }
    private void beginEvent(long generation, long epoch, int donorIndex, int candidateCount, int random, int ordinal,
            int[] old, int[] assignment, PermutationSolution<Integer> donor) {
        events++; activePaid = 0; newObjectives = new ArrayList<>(); active = new LinkedHashMap<>();
        active.put("type", "context-renewal"); active.put("event", events); active.put("mode", mode);
        active.put("generation", generation); active.put("family", family); active.put("epoch", epoch);
        active.put("startFE", successful.getAsLong()); active.put("startedSeconds", elapsed.getAsDouble());
        active.put("sourceIsCurrentFreeParticle", true); active.put("donorPopulationIndex", donorIndex);
        active.put("candidateCount", candidateCount); active.put("randomCandidateOrdinal", random);
        active.put("selectedCandidateOrdinal", ordinal); active.put("donorObjectives", donor.getObjectives().clone());
        active.put("oldFactoryByJob", old); active.put("newFactoryByJob", assignment.clone());
        active.put("expectedResetEvaluations", 5);
    }
    int family() { return family; }
    void poolsCleared(int records) { active.put("clearedPoolRecords", records); }
    void evaluated(PermutationSolution<Integer> solution) {
        Integer index = pending.remove(solution); if (index == null) return;
        activePaid++; evaluations++; newObjectives.add(solution.getObjectives().clone());
        long start = ((Number) active.get("startFE")).longValue();
        if (successful.getAsLong() != start + activePaid) throw new IllegalStateException("Renewal hid extra evaluations");
        if (!pending.isEmpty()) return;
        active.put("complete", true); active.put("successfulResetEvaluations", activePaid);
        active.put("endFE", successful.getAsLong()); active.put("endedSeconds", elapsed.getAsDouble());
        active.put("newObjectives", new ArrayList<>(newObjectives));
        capture(active); completed++; active = null; newObjectives = null;
    }
    private void capture(Map<String, Object> row) {
        if (first.size() < 4) first.add(row);
        else { if (tail.size() == 4) tail.remove(0); tail.add(row); }
    }
    Map<String, Object> summary() {
        Map<String, Object> out = new LinkedHashMap<>(); out.put("mode", mode); out.put("eventsStarted", events);
        out.put("eventsCompleted", completed); out.put("paidResetEvaluations", evaluations);
        out.put("skippedNoNovelFreeFA", skips); out.put("pendingResetEvaluations", pending.size());
        out.put("refreshFrequency", "One round-robin family at generation start after first completed generation");
        out.put("historyPolicy", "Reset all five personal histories after charged reevaluation; keep legitimate global archive");
        out.put("samplePolicy", "first4+last4 completed events plus current partial event"); return out;
    }
    List<Map<String, Object>> trace() {
        List<Map<String, Object>> out = new ArrayList<>(); Map<String, Object> header = summary();
        header.put("type", "context-renewal-summary"); out.add(header); out.addAll(first); out.addAll(tail);
        if (active != null) {
            Map<String, Object> partial = new LinkedHashMap<>(active); partial.put("complete", false);
            partial.put("successfulResetEvaluations", activePaid); partial.put("endFE", successful.getAsLong());
            partial.put("endedSeconds", elapsed.getAsDouble()); partial.put("newObjectives", new ArrayList<>(newObjectives));
            out.add(partial);
        }
        return out;
    }
}
