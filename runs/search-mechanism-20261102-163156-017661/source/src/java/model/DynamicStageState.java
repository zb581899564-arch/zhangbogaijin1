package org.uma.jmetal.util.research.model;

import java.io.Serializable;

/** Mutable private availability state for one factory and stage. */
final class DynamicStageState implements Serializable {
    private static final long serialVersionUID = 1L;
    final int factory, stage;
    final double[] machineEnd, workerEnd, workerFatigue, workerExposure;
    final boolean[] machineUsed;

    DynamicStageState(Instance in, DynamicParameters p, int f, int k) {
        factory = f; stage = k;
        machineEnd = new double[in.machines(f, k)];
        machineUsed = new boolean[machineEnd.length];
        workerEnd = new double[in.workers(f, k)];
        workerFatigue = new double[workerEnd.length];
        workerExposure = new double[workerEnd.length];
        for (int w = 0; w < workerEnd.length; w++) workerFatigue[w] = p.h0(f, k, w);
    }

    private DynamicStageState(DynamicStageState source) {
        factory = source.factory; stage = source.stage;
        machineEnd = source.machineEnd.clone(); machineUsed = source.machineUsed.clone();
        workerEnd = source.workerEnd.clone(); workerFatigue = source.workerFatigue.clone();
        workerExposure = source.workerExposure.clone();
    }

    DynamicStageState copy() { return new DynamicStageState(this); }

    DynamicStep preview(Instance in, DynamicParameters p, int j, int m, int w, double ready) {
        return DynamicPhysics.transition(in, p, j, factory, stage, m, w, ready,
                machineEnd[m], machineUsed[m], workerEnd[w], workerFatigue[w]);
    }

    void accept(DynamicStep step) {
        int m = step.machine(), w = step.worker();
        machineEnd[m] = step.completion(); machineUsed[m] = true;
        workerEnd[w] = step.completion(); workerFatigue[w] = step.v();
        workerExposure[w] += step.exposure();
    }

    static int firstAvailable(double[] availability) {
        int best = 0;
        for (int i = 1; i < availability.length; i++) if (availability[i] < availability[best]) best = i;
        return best;
    }
}
