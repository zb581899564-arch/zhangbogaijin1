package org.uma.jmetal.util.research.search;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;

/** Numeric immutable diagnostic payloads, independent from live solution objects. */
final class AuditEncoding {
    private AuditEncoding() { }
    static String key(PermutationSolution<Integer> s) {
        return s.getVariables().toString() + '|' + s.getVariablesid() + '|'
                + s.getAttribute("machine") + '|' + s.getVariablesworker();
    }
    private static int[] vector(List<Integer> values) {
        int[] out = new int[values.size()];
        for (int i = 0; i < out.length; i++) out[i] = values.get(i);
        return out;
    }
    @SuppressWarnings("unchecked")
    static Map<String, Object> record(PermutationSolution<Integer> s, int index, String source,
            long lineage, long branch, long sharedId, int category) {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("index", index); out.put("source", source);
        out.put("lineageId", lineage); out.put("branchId", branch);
        out.put("objectives", s.getObjectives().clone());
        out.put("JS", vector(s.getVariables())); out.put("FA", vector(s.getVariablesid()));
        out.put("MA", vector((List<Integer>) s.getAttribute("machine")));
        out.put("WA", vector(s.getVariablesworker()));
        out.put("sharedOriginId", sharedId); out.put("category", category);
        return out;
    }
}
