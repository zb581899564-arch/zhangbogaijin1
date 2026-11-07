package org.uma.jmetal.util.research.joint;

import java.util.List;
import org.uma.jmetal.util.research.model.DynamicParameters;
import org.uma.jmetal.util.research.model.DynamicPrefix;
import org.uma.jmetal.util.research.model.DynamicStep;
import org.uma.jmetal.util.research.model.Instance;

/** Twenty fixed physics summaries, with a cheap completion heuristic rather than a claimed bound. */
final class JointFeatures {
    static final int DIMENSION = 20;
    private final Instance in;
    private final DynamicParameters parameters;
    private final double[][] chain, energy, labor;
    private final double[][] firstEnergy, firstLabor;

    JointFeatures(Instance in, DynamicParameters parameters, Runnable checkpoint) {
        this.in = in; this.parameters = parameters;
        chain = new double[in.jobs()][in.factories()]; energy = new double[in.jobs()][in.factories()];
        labor = new double[in.jobs()][in.factories()]; firstEnergy = new double[in.jobs()][in.factories()];
        firstLabor = new double[in.jobs()][in.factories()];
        for (int j = 0; j < in.jobs(); j++) for (int f = 0; f < in.factories(); f++) {
            for (int k = 0; k < in.stages(); k++) {
                checkpoint.run();
                double minTime = Double.POSITIVE_INFINITY, minEnergy = minTime, minLabor = minTime;
                for (int m = 0; m < in.machines(f, k); m++) for (int w = 0; w < in.workers(f, k); w++) {
                    double duration = in.duration(j, f, k, m, w);
                    minTime = Math.min(minTime, duration);
                    minEnergy = Math.min(minEnergy, duration * in.power(f, k, m));
                    minLabor = Math.min(minLabor, duration * in.cost(f, k, w));
                }
                if (k == 0) { firstEnergy[j][f] = minEnergy; firstLabor[j][f] = minLabor; }
                else { chain[j][f] += minTime; energy[j][f] += minEnergy; labor[j][f] += minLabor; }
            }
        }
    }
    State summarize(DynamicPrefix prefix, JointAction[] assignments, List<JointAction> future,
            int remainingBlock, double[] scales) {
        double[] partial = prefix.partialObjectives();
        double tailFinish = partial[0], tailEnergy = 0, tailLabor = 0;
        double[][] load = new double[in.factories()][];
        for (int f = 0; f < in.factories(); f++) load[f] = new double[in.workers(f, 0)];
        for (JointAction a : future) {
            int j = a.job(), f = a.factory(), m = a.machine(), w = a.worker();
            double start = Math.max(prefix.machineEnd(f, m), prefix.workerEnd(f, w));
            double fatigue = prefix.workerFatigue(f, w) * Math.exp(-parameters.mu(f, 0, w) * (start - prefix.workerEnd(f, w)));
            double base = in.duration(j, f, 0, m, w);
            double completion = start + base * (1 + parameters.beta(f, 0, w) * fatigue);
            tailFinish = Math.max(tailFinish, completion + chain[j][f]);
            tailEnergy += firstEnergy[j][f]; tailLabor += firstLabor[j][f]; load[f][w] += base;
        }
        double exitMax = 0, exitSum = 0; int emitted = 0;
        for (DynamicStep step : prefix.steps()) {
            if (step.stage() != 0) throw new IllegalStateException("Joint features require a first-stage prefix");
            double exit = step.completion() + chain[step.job()][step.factory()];
            tailFinish = Math.max(tailFinish, exit); exitMax = Math.max(exitMax, exit); exitSum += exit; emitted++;
        }
        for (JointAction a : assignments) {
            tailEnergy += energy[a.job()][a.factory()]; tailLabor += labor[a.job()][a.factory()];
        }
        double[] tail = new double[] {Math.max(0, tailFinish - partial[0]), tailEnergy, tailLabor};
        double[] features = new double[DIMENSION]; int p = 0;
        features[p++] = prefix.size() / (double) in.jobs();
        for (int q = 0; q < 3; q++) features[p++] = partial[q] / scales[q];
        for (int q = 0; q < 3; q++) features[p++] = tail[q] / scales[q];
        double machineMax = 0, machineSum = 0, workerMax = 0, workerSum = 0;
        double fatigueMax = 0, fatigueSum = 0, loadMax = 0, loadSum = 0, interactionMax = 0, interactionSum = 0;
        int machineCount = 0, workerCount = 0;
        for (int f = 0; f < in.factories(); f++) {
            for (int m = 0; m < in.machines(f, 0); m++) {
                double end = prefix.machineEnd(f, m); machineMax = Math.max(machineMax, end); machineSum += end; machineCount++;
            }
            for (int w = 0; w < in.workers(f, 0); w++) {
                double end = prefix.workerEnd(f, w), fatigue = prefix.workerFatigue(f, w), work = load[f][w];
                workerMax = Math.max(workerMax, end); workerSum += end;
                fatigueMax = Math.max(fatigueMax, fatigue); fatigueSum += fatigue;
                loadMax = Math.max(loadMax, work); loadSum += work;
                interactionMax = Math.max(interactionMax, fatigue * work); interactionSum += fatigue * work; workerCount++;
            }
        }
        features[p++] = machineMax / scales[0]; features[p++] = machineSum / machineCount / scales[0];
        features[p++] = workerMax / scales[0]; features[p++] = workerSum / workerCount / scales[0];
        features[p++] = fatigueMax; features[p++] = fatigueSum / workerCount;
        features[p++] = loadMax / scales[0]; features[p++] = loadSum / workerCount / scales[0];
        features[p++] = interactionMax / scales[0]; features[p++] = interactionSum / workerCount / scales[0];
        features[p++] = exitMax / scales[0]; features[p++] = emitted == 0 ? 0 : exitSum / emitted / scales[0];
        features[p++] = remainingBlock / (double) JointPolicy.BLOCK_LENGTH;
        if (p != DIMENSION) throw new IllegalStateException("Feature contract changed");
        for (double value : features) if (!Double.isFinite(value)) throw new IllegalStateException("Non-finite physics feature");
        return new State(features, partial, tail);
    }
    static final class State {
        final double[] features, partial, tail;
        State(double[] features, double[] partial, double[] tail) {
            this.features = features; this.partial = partial; this.tail = tail;
        }
    }
}
