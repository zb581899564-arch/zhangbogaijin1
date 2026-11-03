package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.uma.jmetal.solution.PermutationSolution;

/** Retains at most three immutable paid pools; full encoding export happens after search. */
final class SelectionCapture {
    private final List<Frame> first = new ArrayList<>();
    private Frame last;
    private long observed;

    void observe(List<PermutationSolution<Integer>> pool, int[] selected, double[] fitness,
            int[] categories, int[] quotas, long[][] identities, int split, String left, String right,
            String selector, double seconds, boolean deadlineValid) {
        Frame frame = new Frame(++observed, pool, selected, fitness, categories, quotas, identities,
                split, left, right, selector, seconds, deadlineValid);
        if (first.size() < 2) first.add(frame);
        else last = frame;
    }
    Map<String, Object> summary() {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("poolsObserved", observed); out.put("poolsCaptured", first.size() + (last == null ? 0 : 1));
        out.put("poolCapturePolicy", "first2+last");
        out.put("poolCostBoundary", "retain immutable paid references in search; materialize encoding after stop");
        return out;
    }
    List<Map<String, Object>> export(PropagationLedger ledger) {
        List<Map<String, Object>> out = new ArrayList<>();
        for (Frame frame : first) out.add(frame.record(ledger));
        if (last != null) out.add(last.record(ledger));
        return out;
    }

    private static final class Frame {
        final long generation;
        final List<PermutationSolution<Integer>> pool;
        final int[] selected, categories, quotas;
        final double[] fitness;
        final long[][] identities;
        final int split;
        final String left, right, selector;
        final double seconds;
        final boolean deadlineValid;
        Frame(long gen, List<PermutationSolution<Integer>> p, int[] picked, double[] f, int[] cats,
                int[] q, long[][] ids, int cut, String l, String r, String method, double t, boolean valid) {
            generation = gen; pool = new ArrayList<>(p); selected = picked.clone();
            fitness = f == null ? null : f.clone(); categories = cats == null ? null : cats.clone();
            quotas = q == null ? null : q.clone(); identities = ids; split = cut;
            left = l; right = r; selector = method; seconds = t; deadlineValid = valid;
        }
        Map<String, Object> record(PropagationLedger ledger) {
            Map<String, Object> out = new LinkedHashMap<>();
            out.put("type", "pool"); out.put("generation", generation); out.put("selector", selector);
            out.put("capacity", selected.length); out.put("elapsedSeconds", seconds); out.put("deadlineValid", deadlineValid);
            List<Map<String, Object>> candidates = new ArrayList<>();
            Set<String> unique = new HashSet<>(), retained = new HashSet<>();
            for (int i = 0; i < pool.size(); i++) {
                PermutationSolution<Integer> s = pool.get(i); unique.add(AuditEncoding.key(s));
                candidates.add(AuditEncoding.record(s, i, i < split ? left : right,
                        identities == null ? -1 : identities[i][0], identities == null ? -1 : identities[i][1],
                        ledger.exactId(s), categories == null ? 0 : categories[i]));
            }
            for (int i : selected) retained.add(AuditEncoding.key(pool.get(i)));
            out.put("candidates", candidates); out.put("selectedIndices", selected);
            out.put("fitness", fitness); out.put("quotas", quotas);
            out.put("uniqueGenotypes", unique.size()); out.put("selectedUniqueGenotypes", retained.size());
            out.put("pddrTiedRecords", tiedRecords()); out.put("extremeRetained", extremes());
            return out;
        }
        private int tiedRecords() {
            if (fitness == null) return 0;
            Map<Double, Integer> sizes = new LinkedHashMap<>();
            for (double f : fitness) sizes.put(f, sizes.getOrDefault(f, 0) + 1);
            int tied = 0; for (int n : sizes.values()) if (n > 1) tied += n;
            return tied;
        }
        private boolean[] extremes() {
            boolean[] kept = new boolean[3];
            for (int k = 0; k < 3; k++) {
                double best = Double.POSITIVE_INFINITY;
                for (PermutationSolution<Integer> s : pool) best = Math.min(best, s.getObjective(k));
                for (int index : selected) kept[k] |= pool.get(index).getObjective(k) == best;
            }
            return kept;
        }
    }
}
