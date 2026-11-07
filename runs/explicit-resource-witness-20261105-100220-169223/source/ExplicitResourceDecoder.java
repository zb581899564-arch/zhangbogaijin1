package org.uma.jmetal.util.research.model;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

/** Full recomputation only. Original physics/FIFO, with separately identified resource decisions. */
public final class ExplicitResourceDecoder {
    private ExplicitResourceDecoder() { }

    public static ExplicitSchedule full(Instance instance, DynamicParameters params,
            int[] js, int[] fa, int[] ma, int[] wa, StageResourcePlan plan, Runnable checkpoint) {
        params.validateFor(instance);
        Encoding.validate(instance, js, fa, ma, wa);
        plan.validate(instance, js, fa);
        List<DynamicStep> operations = new ArrayList<>();
        for (int f = 0; f < instance.factories(); f++) {
            List<Integer> positions = new ArrayList<>();
            for (int pos = 0; pos < js.length; pos++) if (fa[pos] == f) positions.add(pos);
            double[] completion = new double[instance.jobs()];
            for (int k = 0; k < instance.stages(); k++) {
                if (k > 0) stableSort(positions, js, completion);
                DynamicStageState state = new DynamicStageState(instance, params, f, k);
                for (int pos : positions) {
                    if (checkpoint != null) checkpoint.run();
                    int job = js[pos];
                    int machine = k == 0 ? ma[pos] : plan.specified(job, k)
                            ? plan.machine(job, k) : DynamicStageState.firstAvailable(state.machineEnd);
                    int worker = k == 0 ? wa[pos] : plan.specified(job, k)
                            ? plan.worker(job, k) : DynamicStageState.firstAvailable(state.workerEnd);
                    DynamicStep operation = state.preview(instance, params, job, machine, worker, completion[job]);
                    state.accept(operation); completion[job] = operation.completion(); operations.add(operation);
                }
            }
        }
        return new ExplicitSchedule(instance, params, js, fa, ma, wa, plan, operations);
    }

    private static void stableSort(List<Integer> positions, final int[] js, final double[] completion) {
        Collections.sort(positions, new Comparator<Integer>() {
            public int compare(Integer a, Integer b) { return Double.compare(completion[js[a]], completion[js[b]]); }
        });
    }
}
