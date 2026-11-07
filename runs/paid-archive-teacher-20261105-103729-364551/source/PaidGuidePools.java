package research.dynamic;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;

/** Source membership and chronological ND construction, using only previously paid objectives. */
final class PaidGuidePools {
    static final String[] METHODS = {"PAID_ND", "HISTORY_ND", "CURRENT_ND", "INITIAL_ND", "RANDOM_KNOWN"};
    static final int INITIAL = 1, CURRENT = 2, HISTORY = 4, PAID = 8;

    static final class Entry {
        final String id, firstRole;
        final int membership;
        final long firstPaid;
        final PermutationSolution<Integer> value;
        Entry(String[] fields, PermutationSolution<Integer> point) {
            id = fields[1]; membership = Integer.parseInt(fields[2]);
            firstPaid = Long.parseLong(fields[3]); firstRole = fields[4]; value = point;
        }
    }

    private PaidGuidePools() { }

    static List<Entry> construct(List<Entry> known, String method) {
        List<Entry> selected = new ArrayList<>();
        int mask = method.equals("PAID_ND") ? PAID : method.equals("HISTORY_ND")
                ? INITIAL | CURRENT | HISTORY : method.equals("CURRENT_ND") ? CURRENT
                : method.equals("INITIAL_ND") ? INITIAL : 0;
        if (mask == 0 && !method.equals("RANDOM_KNOWN")) throw new IllegalArgumentException("Unknown pool");
        // Input is sorted by actual first-paid FE and then the complete encoding.
        for (Entry entry : known) {
            if (mask != 0 && (entry.membership & mask) == 0) continue;
            if (method.equals("PAID_ND") || method.equals("RANDOM_KNOWN")) selected.add(entry);
            else offer(selected, entry);
        }
        if (selected.isEmpty()) throw new AssertionError("Missing source pool");
        return selected;
    }

    private static void offer(List<Entry> values, Entry candidate) {
        for (Entry old : values) {
            if (Arrays.equals(old.value.getObjectives(), candidate.value.getObjectives())
                    || dominates(old.value, candidate.value)) return;
        }
        values.removeIf(old -> dominates(candidate.value, old.value));
        values.add(candidate);
    }

    private static boolean dominates(PermutationSolution<Integer> a, PermutationSolution<Integer> b) {
        boolean strict = false;
        for (int objective = 0; objective < 3; objective++) {
            if (a.getObjective(objective) > b.getObjective(objective)) return false;
            strict |= a.getObjective(objective) < b.getObjective(objective);
        }
        return strict;
    }
}
