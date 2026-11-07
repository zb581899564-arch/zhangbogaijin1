package org.uma.jmetal.util.research.cooperation;

import java.util.ArrayList;
import java.util.List;
import java.util.Arrays;

/** Exact nondominated finite pool. Keep extremes, then deterministic max-min diversity. */
final class FactoryPool {
    private final List<FactoryRecord> records = new ArrayList<>();
    private int[] jobSet;
    long accepted, rejected, truncated;
    void offer(FactoryRecord candidate) {
        int[] set = candidate.jobs.clone(); Arrays.sort(set);
        if (jobSet == null) jobSet = set;
        else if (!Arrays.equals(jobSet, set)) throw new IllegalArgumentException("Factory pool job set mismatch");
        PoolRetentionTrace.observe(this, candidate);
        for (FactoryRecord r : records) if (r.same(candidate) || r.dominates(candidate)) { rejected++; return; }
        records.removeIf(candidate::dominates); records.add(candidate); accepted++;
        if (records.size() > 8) truncate();
    }
    FactoryRecord choose(double cap, double eta, double energyScale, double wageScale) {
        FactoryRecord best = null; double score = Double.POSITIVE_INFINITY;
        for (FactoryRecord r : records) if (r.objectives[0] <= cap) {
            double value = r.objectives[1] / energyScale + eta * r.objectives[2] / wageScale;
            if (value < score) { score = value; best = r; }
        }
        return best;
    }
    int size() { return records.size(); }
    List<FactoryRecord> records() { return new ArrayList<>(records); }
    private void truncate() {
        truncated++; List<FactoryRecord> keep = new ArrayList<>();
        double[] low = new double[3], high = new double[3]; Arrays.fill(low, Double.POSITIVE_INFINITY);
        for (int k = 0; k < 3; k++) {
            FactoryRecord best = records.get(0);
            for (FactoryRecord r : records) {
                low[k] = Math.min(low[k], r.objectives[k]); high[k] = Math.max(high[k], r.objectives[k]);
                if (r.objectives[k] < best.objectives[k]) best = r;
            }
            if (!keep.contains(best)) keep.add(best);
        }
        while (keep.size() < 8) {
            FactoryRecord best = null; double distance = -1;
            for (FactoryRecord r : records) if (!keep.contains(r)) {
                double nearest = Double.POSITIVE_INFINITY;
                for (FactoryRecord chosen : keep) {
                    double d = 0;
                    for (int k = 0; k < 3; k++) { double v = (r.objectives[k] - chosen.objectives[k]) / Math.max(1e-12, high[k] - low[k]); d += v*v; }
                    nearest = Math.min(nearest, d);
                }
                if (nearest > distance) { distance = nearest; best = r; }
            }
            keep.add(best);
        }
        records.clear(); records.addAll(keep);
    }
}
