package org.uma.jmetal.util.research.search;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Exact original exchange distribution conditional on unequal resource values, when support is nonempty. */
public final class ConditionalResourceExchange {
    private static final boolean ENABLED = Boolean.getBoolean("research.conditionalExchange.enabled");
    private static long requests, applied, homogeneousFallback;
    private ConditionalResourceExchange() { }

    /** False keeps the original proposal and its charged evaluation, including genuinely empty neighborhoods. */
    static boolean apply(List<Integer> vector, List<Integer> positions) {
        if (!ENABLED) return false;
        requests++;
        int[] values = new int[positions.size()];
        for (int i = 0; i < values.length; i++) values[i] = vector.get(positions.get(i));
        Map<Integer,Integer> counts = counts(values); int total = supportSize(values.length, counts);
        if (total == 0) { homogeneousFallback++; return false; }
        int[] pair = atRank(values, counts, SeededRandom.current().nextInt(total));
        int a = positions.get(pair[0]), b = positions.get(pair[1]);
        Integer first = vector.get(a), second = vector.get(b);
        if (first.equals(second)) throw new AssertionError("Conditional draw generated an identical exchange");
        vector.set(a, second); vector.set(b, first); applied++; return true;
    }

    static Map<Integer,Integer> counts(int[] values) {
        Map<Integer,Integer> result = new HashMap<>();
        for (int value : values) result.put(value, result.getOrDefault(value, 0) + 1);
        return result;
    }
    static int supportSize(int n, Map<Integer,Integer> counts) {
        int result = n * n;
        for (int count : counts.values()) result -= count * count;
        return result;
    }
    static int[] atRank(int[] values, Map<Integer,Integer> counts, int rank) {
        if (rank < 0 || rank >= supportSize(values.length, counts)) throw new IllegalArgumentException("Invalid pair rank");
        for (int a = 0; a < values.length; a++) {
            int width = values.length - counts.get(values[a]);
            if (rank >= width) { rank -= width; continue; }
            for (int b = 0; b < values.length; b++) if (values[b] != values[a]) {
                if (rank-- == 0) return new int[] {a, b};
            }
        }
        throw new AssertionError("Conditional pair rank not covered");
    }
    public static Map<String,Object> diagnostics() {
        Map<String,Object> out = new LinkedHashMap<>();
        out.put("enabled", ENABLED); out.put("requests", requests); out.put("appliedNonidentity", applied);
        out.put("emptySupportOriginalPaidFallback", homogeneousFallback);
        out.put("preGeneratedCandidateRejections", 0);out.put("historyLookups", 0);return out;
    }
}
