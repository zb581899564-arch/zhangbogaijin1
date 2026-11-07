package org.uma.jmetal.util.research.model;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

/** Delays machine prefixes while retaining every machine's last finish and all resource orders. */
final class RightShift {
    private static final double EPS = 1e-9;
    private RightShift() { }
    static List<Operation> apply(List<Operation> source, ModelKind kind) {
        List<Operation> result = new ArrayList<Operation>(source);
        List<Integer> order = new ArrayList<Integer>();
        for (int i = 0; i < result.size(); i++) order.add(i);
        Collections.sort(order, new Comparator<Integer>() {
            public int compare(Integer a, Integer b) { return Double.compare(source.get(b).start(), source.get(a).start()); }
        });
        for (int index : order) {
            Operation op = result.get(index);
            Operation nextMachine = successor(result, op, 0), nextWorker = kind == ModelKind.CHAPTER4_DUAL_RESOURCE
                    ? successor(result, op, 1) : null;
            if (nextMachine == null) continue; // preserves each machine's final finish
            double endBound = nextMachine.start();
            if (nextWorker != null) endBound = Math.min(endBound, nextWorker.start());
            for (Operation other : result) if (other.job() == op.job() && other.stage() == op.stage() + 1) {
                endBound = Math.min(endBound, other.start());
            }
            double latestStart = endBound - op.duration();
            if (latestStart > op.start() + EPS) result.set(index, op.shifted(latestStart));
        }
        return result;
    }
    private static Operation successor(List<Operation> all, Operation op, int resource) {
        Operation next = null;
        for (Operation other : all) {
            boolean same = other.factory() == op.factory() && other.stage() == op.stage()
                    && (resource == 0 ? other.machine() == op.machine() : other.worker() == op.worker());
            if (same && other.start() >= op.end() - EPS && (next == null || other.start() < next.start())) next = other;
        }
        return next;
    }
}
