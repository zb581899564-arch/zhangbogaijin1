package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;

/** Paid references and systematic episode snapshots; no filtering on observed gains. */
final class ProgramGenomeEvidence {
    private final ProgramPaidHistory history;
    private final IdentityHashMap<List<PermutationSolution<Integer>>,Integer> referenceIds = new IdentityHashMap<>();
    final List<Map<String,Object>> references = new ArrayList<>(), samples = new ArrayList<>();
    ProgramGenomeEvidence(ProgramPaidHistory paid) { history = paid; }

    int reference(List<PermutationSolution<Integer>> values) {
        Integer old = referenceIds.get(values);if (old != null) return old;
        int id = references.size();referenceIds.put(values, id);
        List<Map<String,Object>> points = new ArrayList<>();
        for (PermutationSolution<Integer> value : values) points.add(genome(value));
        Map<String,Object> row = new LinkedHashMap<>();row.put("id", id);row.put("availableAtPaidFE", history.paid());
        row.put("points", points);references.add(row);return id;
    }
    @SuppressWarnings("unchecked")
    Map<String,Object> genome(PermutationSolution<Integer> value) {
        Map<String,Object> out = new LinkedHashMap<>();
        out.put("earliestEquivalentPhysicalPaidFE", history.physicalBirth(value));
        out.put("JS", new ArrayList<>(value.getVariables()));out.put("FA", new ArrayList<>(value.getVariablesid()));
        out.put("MA", new ArrayList<>((List<Integer>)value.getAttribute("machine")));
        out.put("WA", new ArrayList<>(value.getVariablesworker()));out.put("objectives", value.getObjectives().clone());
        return out;
    }
}
