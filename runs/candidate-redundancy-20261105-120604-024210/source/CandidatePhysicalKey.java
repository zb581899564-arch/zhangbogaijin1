package org.uma.jmetal.util.research.search;

import java.util.Arrays;
import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;

/** Exact full ordered factory encoding; ignore only physically neutral inter-factory interleaving. */
final class CandidatePhysicalKey {
    final int[] genes;
    private final int hash;
    private CandidatePhysicalKey(int[] values) { genes = values; hash = Arrays.hashCode(values); }

    @SuppressWarnings("unchecked")
    static CandidatePhysicalKey of(PermutationSolution<?> value, int factories) {
        List<?> machine = (List<?>) value.getAttribute("machine");
        int n = value.getNumberOfVariables(), at = 0;
        int[] result = new int[3 * n + factories];
        for (int f = 0; f < factories; f++) {
            result[at++] = -1 - f;
            for (int p = 0; p < n; p++) if (((Number)value.getVariableValueid(p)).intValue() == f) {
                result[at++] = ((Number)value.getVariableValue(p)).intValue();
                result[at++] = ((Number)machine.get(p)).intValue();
                result[at++] = ((Number)value.getVariablesworker().get(p)).intValue();
            }
        }
        if (at != result.length) throw new AssertionError("Invalid full physical key length");
        return new CandidatePhysicalKey(result);
    }
    @Override public int hashCode() { return hash; }
    @Override public boolean equals(Object other) {
        return other instanceof CandidatePhysicalKey && Arrays.equals(genes, ((CandidatePhysicalKey)other).genes);
    }
}
