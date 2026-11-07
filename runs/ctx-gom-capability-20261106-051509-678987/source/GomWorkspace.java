package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.modelglobal.*;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** One complete local pass; donor domains and models are fixed, accepted working states are live. */
final class GomWorkspace {
    final GomRunScope scope;
    final Instance instance;
    final FirstStageCatalog catalog;
    final List<GomRecords.State> values = new ArrayList<>();
    final Map<Integer,List<Integer>> domains = new TreeMap<>();
    final Map<Integer,List<int[]>> masks = new TreeMap<>();
    final List<Integer> families = new ArrayList<>();
    private final IdentityHashMap<PermutationSolution<Integer>,List<Integer>> inputSlots = new IdentityHashMap<>();
    private final boolean[] visited = new boolean[100];
    int programs, slot = -1, step = -1, subset = -1, donorSlot = -1;
    Map<String,Object> pending;
    GomWorkspace(GomRunScope value, Instance input) { scope = value; instance = input; catalog = new FirstStageCatalog(input); }
    void prepare(List<PermutationSolution<Integer>> population) {
        if (population.size() != 100) throw new AssertionError("100 working members required");
        for (int i = 0; i < population.size(); i++) {
            scope.guard("VIEW"); PermutationSolution<Integer> point = population.get(i);
            int family = point.getAttribute("cooperation.family") == null ? -1 : (Integer)point.getAttribute("cooperation.family");
            if (family < -1 || family > 3) throw new AssertionError("Unknown context");
            TypedScheduleGenome before = TypedScheduleGenome.fromVectors(catalog, GomRecords.vectors(point));
            TypedScheduleGenome after = FactoryKeyReencoder.apply(catalog, before, SeededRandom.current());
            if (scope.recording()) scope.evidence.view(point, GomRecords.copy(point, after)); scope.views++;
            GomRecords.State state = new GomRecords.State(++scope.states, scope.sourceFee(point), after, point);
            values.add(state); families.add(family); domains.computeIfAbsent(family, unused -> new ArrayList<>()).add(i);
            inputSlots.computeIfAbsent(point, unused -> new ArrayList<>()).add(i);
            if (scope.recording()) {
                Map<String,Object> event = state.record(true); event.putAll(GomRecords.row("kind", "view", "pass", scope.passes, "slot", i,
                    "family", family, "source", GomRecords.raw(point))); scope.evidence.record(event);
            }
        }
        validateDomains(); scope.stage = "LEARNING";
        for (Map.Entry<Integer,List<Integer>> d : domains.entrySet()) masks.put(d.getKey(), GomDomainModels.build(this, d.getKey(), d.getValue()));
        scope.stage = "LOCAL";
        if (scope.recording()) scope.evidence.record(GomRecords.row("kind", "ready", "pass", scope.passes, "families", families));
    }
    private void validateDomains() {
        if (domains.size() == 1) { if (domains.get(-1) == null || domains.get(-1).size() != 100) throw new AssertionError("Generic free100 expected"); return; }
        if (domains.size() != 5 || domains.get(-1).size() != 80) throw new AssertionError("Free80 plus four families required");
        for (int f = 0; f < 4; f++) {
            List<Integer> ids = domains.get(f); if (ids == null || ids.size() != 5) throw new AssertionError("Family quota changed");
            int[] reference = values.get(ids.get(0)).genes.allocations();
            for (int id : ids) {
                int[] actual = values.get(id).genes.allocations(); Object attr = values.get(id).point.getAttribute("cooperation.fixedFactoryByJob");
                if (!(attr instanceof int[])) throw new AssertionError("Missing fixed assignment");
                for (int j = 0; j < actual.length; j++) if (catalog.factory(actual[j]) != catalog.factory(reference[j]) || catalog.factory(actual[j]) != ((int[])attr)[j])
                    throw new AssertionError("Family assignments disagree");
            }
        }
    }
    int claim(PermutationSolution<Integer> point) {
        List<Integer> candidates = inputSlots.get(point);
        if (candidates != null) for (int id : candidates) if (!visited[id]) { visited[id] = true; return id; }
        throw new AssertionError("Receiver not in this paid workspace or visited twice");
    }
    Map<String,Object> receipt() {
        List<Map<String,Object>> states = new ArrayList<>(); for (GomRecords.State s : values) states.add(s.record(false));
        return GomRecords.row("slot", slot, "step", step, "subset", subset, "donorSlot", donorSlot, "programs", programs,
            "families", families, "population", states, "pending", pending);
    }
}
