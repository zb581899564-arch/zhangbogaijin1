package org.uma.jmetal.util.research.model;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Immutable evaluated timeline and its original genome/context, suitable for exact reuse. */
public final class DynamicSchedule implements Serializable {
    private static final long serialVersionUID = 1L;
    public static final String POLICY = "dynamic-append-v1; FIFO; independent earliest resources; lowest-id ties; work-period exposure";
    private final Instance instance;
    private final DynamicParameters parameters;
    private final String policy;
    private final int[] js, fa, ma, wa;
    private final List<DynamicStep> steps;
    private final List<List<DynamicStep>> byFactory;
    private final double[] objectives, makespan, energy, cost;
    private final double totalExposure, maxExposure, peakFatigue;
    private final int reusedOperations, recomputedOperations;

    DynamicSchedule(Instance in, DynamicParameters p, int[] js, int[] fa, int[] ma, int[] wa,
            List<DynamicStep> operations, int reused, int recomputed) {
        instance = in; parameters = p; policy = POLICY;
        this.js = js.clone(); this.fa = fa.clone(); this.ma = ma.clone(); this.wa = wa.clone();
        steps = Collections.unmodifiableList(new ArrayList<DynamicStep>(operations));
        reusedOperations = reused; recomputedOperations = recomputed;
        objectives = new double[3]; makespan = new double[in.factories()];
        energy = new double[in.factories()]; cost = new double[in.factories()];
        List<List<DynamicStep>> factories = new ArrayList<List<DynamicStep>>();
        double[][][] exposure = new double[in.factories()][in.stages()][];
        double peak = 0.0, total = 0.0, max = 0.0;
        for (int f = 0; f < in.factories(); f++) {
            factories.add(new ArrayList<DynamicStep>());
            for (int k = 0; k < in.stages(); k++) {
                exposure[f][k] = new double[in.workers(f, k)];
                for (int w = 0; w < in.workers(f, k); w++) peak = Math.max(peak, p.h0(f, k, w));
            }
        }
        for (DynamicStep op : steps) {
            int f = op.factory(); factories.get(f).add(op);
            makespan[f] = Math.max(makespan[f], op.completion());
            energy[f] += op.energy(); cost[f] += op.labor();
            objectives[0] = Math.max(objectives[0], op.completion());
            objectives[1] += op.energy(); objectives[2] += op.labor();
            exposure[f][op.stage()][op.worker()] += op.exposure(); total += op.exposure();
            peak = Math.max(peak, Math.max(op.u(), op.v()));
        }
        for (int f = 0; f < in.factories(); f++) {
            factories.set(f, Collections.unmodifiableList(factories.get(f)));
            for (int k = 0; k < in.stages(); k++) for (double value : exposure[f][k]) max = Math.max(max, value);
        }
        byFactory = Collections.unmodifiableList(factories);
        totalExposure = total; maxExposure = max; peakFatigue = peak;
    }

    public List<DynamicStep> steps() { return steps; }
    public double[] objectives() { return objectives.clone(); }
    public double[] factoryMakespan() { return makespan.clone(); }
    public double[] factoryEnergy() { return energy.clone(); }
    public double[] factoryCost() { return cost.clone(); }
    public double totalExposure() { return totalExposure; }
    public double maxExposure() { return maxExposure; }
    /** Includes the initial fatigue at time zero, including initially unused workers. */
    public double peakFatigue() { return peakFatigue; }
    public int reusedOperations() { return reusedOperations; }
    public int recomputedOperations() { return recomputedOperations; }
    public int[] js() { return js.clone(); }
    public int[] fa() { return fa.clone(); }
    public int[] ma() { return ma.clone(); }
    public int[] wa() { return wa.clone(); }
    public DynamicParameters parameters() { return parameters; }
    public String decodingPolicy() { return policy; }

    List<DynamicStep> factorySteps(int f) { return byFactory.get(f); }
    void validateContext(Instance in, DynamicParameters p) {
        if (!POLICY.equals(policy)) throw new IllegalArgumentException("Dynamic cache decoder policy differs");
        DynamicContext.requireSame(in, p, instance, parameters);
    }
}
