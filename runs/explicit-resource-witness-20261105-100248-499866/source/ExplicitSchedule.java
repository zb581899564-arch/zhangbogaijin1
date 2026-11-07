package org.uma.jmetal.util.research.model;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Distinct schedule/cache type: it cannot be mistaken for dynamic-append-v1. */
public final class ExplicitSchedule implements Serializable {
    private static final long serialVersionUID = 1L;
    private final Instance instance;
    private final DynamicParameters parameters;
    private final int[] js, fa, ma, wa;
    private final StageResourcePlan plan;
    private final List<DynamicStep> steps;
    private final double[] objectives, makespan, energy, labor;

    ExplicitSchedule(Instance in, DynamicParameters params, int[] order, int[] factories,
            int[] machines, int[] workers, StageResourcePlan decisions, List<DynamicStep> operations) {
        instance = in; parameters = params;
        js = order.clone(); fa = factories.clone(); ma = machines.clone(); wa = workers.clone();
        plan = decisions;
        steps = Collections.unmodifiableList(new ArrayList<>(operations));
        objectives = new double[3]; makespan = new double[in.factories()];
        energy = new double[in.factories()]; labor = new double[in.factories()];
        for (DynamicStep operation : operations) {
            int factory = operation.factory();
            objectives[0] = Math.max(objectives[0], operation.completion());
            objectives[1] += operation.energy(); objectives[2] += operation.labor();
            makespan[factory] = Math.max(makespan[factory], operation.completion());
            energy[factory] += operation.energy(); labor[factory] += operation.labor();
        }
    }

    public void validateContext(Instance in, DynamicParameters params) {
        DynamicContext.requireSame(in, params, instance, parameters);
        plan.validate(in, js, fa);
    }

    public String policy() { return StageResourcePlan.POLICY; }
    public StageResourcePlan plan() { return plan; }
    public int[] js() { return js.clone(); }
    public int[] fa() { return fa.clone(); }
    public int[] ma() { return ma.clone(); }
    public int[] wa() { return wa.clone(); }
    public List<DynamicStep> steps() { return steps; }
    public double[] objectives() { return objectives.clone(); }
    public double[] factoryMakespan() { return makespan.clone(); }
    public double[] factoryEnergy() { return energy.clone(); }
    public double[] factoryCost() { return labor.clone(); }
}
