package org.uma.jmetal.util.research.model;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

/** Deterministic append-only dynamic model, separate from the original static Decoder. */
public final class DynamicDecoder {
    private DynamicDecoder() { }

    public static DynamicSchedule full(Instance in, DynamicParameters p, int[] js, int[] fa,
            int[] ma, int[] wa, Runnable checkpoint) {
        return incremental(in, p, js, fa, ma, wa, null, null, checkpoint);
    }

    public static DynamicSchedule incremental(Instance in, DynamicParameters p, int[] js, int[] fa,
            int[] ma, int[] wa, DynamicSchedule previous, DynamicPrefix constructed, Runnable checkpoint) {
        validateInput(in, p, js, fa, ma, wa);
        if (previous != null) previous.validateContext(in, p);
        List<DynamicStep> prefix = validateConstructed(in, p, js, fa, ma, wa, constructed);
        List<DynamicStep> result = new ArrayList<DynamicStep>(in.jobs() * in.stages());
        int[] counters = new int[2];
        for (int f = 0; f < in.factories(); f++) {
            List<Integer> positions = positions(f, fa);
            List<DynamicStep> old = previous == null ? Collections.<DynamicStep>emptyList() : previous.factorySteps(f);
            List<DynamicStep> chosen = factoryPrefix(prefix, f);
            int common = commonPrefix(positions, js, ma, wa, old);
            if (common == positions.size() && old.size() == positions.size() * in.stages()) {
                for (DynamicStep step : old) { check(checkpoint); result.add(step); counters[0]++; }
            } else {
                decodeFactory(in, p, f, positions, js, ma, wa, old, common, chosen,
                        result, counters, checkpoint);
            }
        }
        return new DynamicSchedule(in, p, js, fa, ma, wa, result, counters[0], counters[1]);
    }

    private static void decodeFactory(Instance in, DynamicParameters p, int f, List<Integer> positions,
            int[] js, int[] ma, int[] wa, List<DynamicStep> old, int common,
            List<DynamicStep> chosen, List<DynamicStep> result, int[] counters, Runnable checkpoint) {
        double[] completion = new double[in.jobs()];
        for (int k = 0; k < in.stages(); k++) {
            if (k > 0) sortByCompletion(positions, js, completion);
            DynamicStageState state = new DynamicStageState(in, p, f, k);
            for (int q = 0; q < positions.size(); q++) {
                check(checkpoint);
                int pos = positions.get(q), j = js[pos];
                DynamicStep step;
                if (k == 0 && q < chosen.size()) {
                    step = chosen.get(q); counters[0]++;
                } else if (k == 0 && q < common) {
                    step = old.get(q); counters[0]++;
                } else {
                    int m = k == 0 ? ma[pos] : DynamicStageState.firstAvailable(state.machineEnd);
                    int w = k == 0 ? wa[pos] : DynamicStageState.firstAvailable(state.workerEnd);
                    step = state.preview(in, p, j, m, w, completion[j]); counters[1]++;
                }
                state.accept(step); completion[j] = step.completion(); result.add(step);
            }
        }
    }

    private static void sortByCompletion(List<Integer> positions, final int[] js, final double[] completion) {
        // Collections.sort is stable: equal completions preserve the preceding stage order.
        Collections.sort(positions, new Comparator<Integer>() {
            public int compare(Integer a, Integer b) { return Double.compare(completion[js[a]], completion[js[b]]); }
        });
    }

    private static int commonPrefix(List<Integer> positions, int[] js, int[] ma, int[] wa,
            List<DynamicStep> old) {
        int q = 0;
        while (q < positions.size() && q < old.size()) {
            int pos = positions.get(q); DynamicStep step = old.get(q);
            if (step.stage() != 0 || step.job() != js[pos] || step.machine() != ma[pos]
                    || step.worker() != wa[pos]) break;
            q++;
        }
        return q;
    }

    private static List<DynamicStep> validateConstructed(Instance in, DynamicParameters p,
            int[] js, int[] fa, int[] ma, int[] wa, DynamicPrefix constructed) {
        if (constructed == null) return Collections.emptyList();
        constructed.validateContext(in, p);
        List<DynamicStep> steps = constructed.steps();
        if (steps.size() > js.length) throw new IllegalArgumentException("Constructed prefix is too long");
        for (int q = 0; q < steps.size(); q++) {
            DynamicStep step = steps.get(q);
            if (step.job() != js[q] || step.factory() != fa[q] || step.machine() != ma[q]
                    || step.worker() != wa[q]) {
                throw new IllegalArgumentException("Constructed prefix differs from target genome at " + q);
            }
        }
        return steps;
    }

    private static List<DynamicStep> factoryPrefix(List<DynamicStep> prefix, int factory) {
        List<DynamicStep> result = new ArrayList<DynamicStep>();
        for (DynamicStep step : prefix) if (step.factory() == factory) result.add(step);
        return result;
    }

    private static List<Integer> positions(int factory, int[] fa) {
        List<Integer> result = new ArrayList<Integer>();
        for (int pos = 0; pos < fa.length; pos++) if (fa[pos] == factory) result.add(pos);
        return result;
    }

    private static void validateInput(Instance in, DynamicParameters p, int[] js, int[] fa, int[] ma, int[] wa) {
        if (p == null || js == null || fa == null || ma == null || wa == null) {
            throw new IllegalArgumentException("Instance, parameters and four vectors are required");
        }
        p.validateFor(in); Encoding.validate(in, js, fa, ma, wa);
    }

    private static void check(Runnable checkpoint) { if (checkpoint != null) checkpoint.run(); }
}
