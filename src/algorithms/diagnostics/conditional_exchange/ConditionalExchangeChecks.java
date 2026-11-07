package org.uma.jmetal.util.research.search;

import java.util.HashSet;
import java.util.Map;
import java.util.Set;

/** Exhaustively compare rank sampling support with all original ordered unequal-valued pairs. */
public final class ConditionalExchangeChecks {
    private ConditionalExchangeChecks() { }
    public static void main(String[] args) {
        long vectors = 0, pairs = 0;
        for (int n = 0; n <= 6; n++) {
            int combinations = (int)Math.pow(3, n);
            for (int encoded = 0; encoded < combinations; encoded++) {
                int[] values = new int[n];int rest = encoded;
                for (int j = 0; j < n; j++) { values[j] = rest % 3;rest /= 3; }
                Map<Integer,Integer> counts = ConditionalResourceExchange.counts(values);
                Set<Integer> expected = new HashSet<>(), actual = new HashSet<>();
                for (int a = 0; a < n; a++) for (int b = 0; b < n; b++)
                    if (a != b && values[a] != values[b]) expected.add(a * n + b);
                int total = ConditionalResourceExchange.supportSize(n, counts);
                if (total != expected.size()) throw new AssertionError("Conditional support count differs");
                for (int rank = 0; rank < total; rank++) {
                    int[] pair = ConditionalResourceExchange.atRank(values, counts, rank);
                    if (!actual.add(pair[0] * n + pair[1])) throw new AssertionError("Rank mapping duplicates an ordered pair");
                }
                if (!actual.equals(expected)) throw new AssertionError("Conditional uniform distribution differs");
                vectors++;pairs += total;
            }
        }
        System.out.println("CONDITIONAL_EXCHANGE_FIXTURES_PASS vectors=" + vectors + " orderedPairs=" + pairs
                + " equal-mass rank bijection; empty support identified; zeroFE zeroDecoder");
    }
}
