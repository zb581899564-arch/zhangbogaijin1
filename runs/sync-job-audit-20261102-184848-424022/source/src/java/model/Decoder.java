package org.uma.jmetal.util.research.model;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

/** Canonical sourced reconstruction: ECT/FIFO/FAM, common-gap insertion, safe right shift. */
public final class Decoder {
    private static final double EPS = 1e-9;
    private Decoder() { }
    public static Schedule decode(Instance in, int[] js, int[] fa, int[] ma, int[] wa) {
        return decode(in, js, fa, ma, wa, true);
    }
    public static Schedule decode(Instance in, int[] js, int[] fa, int[] ma, int[] wa, boolean rightShift) {
        Encoding.validate(in, js, fa, ma, wa);
        List<Operation> all = new ArrayList<Operation>(); int workerOffset = 0;
        for (int f = 0; f < in.factories(); f++) {
            List<Integer> positions = new ArrayList<Integer>();
            for (int p = 0; p < js.length; p++) if (fa[p] == f) positions.add(p);
            decodeFactory(in, f, positions, js, ma, wa, workerOffset, all);
            for (int k = 0; k < in.stages(); k++) workerOffset += in.machines(f, k);
        }
        if (rightShift) all = RightShift.apply(all, in.kind());
        return new Schedule(in, all, "canonical-v1; ECT/FIFO/FAM; lowest-id ties; dual-resource full-AT reservation; "
                + "common-gap insertion=" + (in.kind() == ModelKind.CHAPTER4_DUAL_RESOURCE)
                + "; monotone right-shift=" + rightShift);
    }
    private static void decodeFactory(Instance in, int f, List<Integer> positions,
            int[] js, int[] ma, int[] wa, int fixedOffset, List<Operation> all) {
        double[] release = new double[in.jobs()];
        int stageOffset = fixedOffset;
        for (int k = 0; k < in.stages(); k++) {
            final double[] ready = release;
            if (k > 0) Collections.sort(positions, new Comparator<Integer>() {
                public int compare(Integer a, Integer b) { return Double.compare(ready[js[a]], ready[js[b]]); }
            });
            List<Operation> stage = new ArrayList<Operation>();
            double[] machineEnd = new double[in.machines(f, k)];
            double[] workerEnd = new double[in.workers(f, k)];
            for (int p : positions) {
                int j = js[p], m = k == 0 ? ma[p] : firstAvailable(machineEnd);
                int w = in.kind() == ModelKind.CHAPTER3_FIXED_WORKER ? wa[stageOffset + m]
                        : k == 0 ? wa[p] : firstAvailable(workerEnd);
                double duration = in.duration(j, f, k, m, w);
                double start = in.kind() == ModelKind.CHAPTER4_DUAL_RESOURCE
                        ? commonGap(stage, m, w, release[j], duration)
                        : Math.max(machineEnd[m], release[j]);
                Operation op = new Operation(j, f, k, m, w, start, duration, in.setup(j, k) / in.efficiency(f, k, w));
                stage.add(op); all.add(op); release[j] = op.end();
                machineEnd[m] = Math.max(machineEnd[m], op.end());
                workerEnd[w] = Math.max(workerEnd[w], op.end());
            }
            stageOffset += in.machines(f, k);
        }
    }
    private static int firstAvailable(double[] ends) {
        int first = 0;
        for (int i = 1; i < ends.length; i++) if (ends[i] < ends[first]) first = i;
        return first;
    }
    private static double commonGap(List<Operation> stage, int machine, int worker, double release, double duration) {
        double start = release;
        boolean changed;
        do {
            changed = false;
            for (Operation op : stage) {
                if (op.machine() != machine && op.worker() != worker) continue;
                if (start < op.end() - EPS && start + duration > op.start() + EPS) {
                    start = op.end(); changed = true;
                }
            }
        } while (changed);
        return start;
    }
}
