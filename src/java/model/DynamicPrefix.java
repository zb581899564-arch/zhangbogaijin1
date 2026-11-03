package org.uma.jmetal.util.research.model;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Exact stage-zero prefix, in global JS order; factories may be interleaved. */
public final class DynamicPrefix implements Serializable {
    private static final long serialVersionUID = 1L;
    private final Instance instance;
    private final DynamicParameters parameters;
    private final String policy;
    private final DynamicStageState[] states;
    private final boolean[] completed;
    private final double[] firstCompletion, objectives;
    private final List<DynamicStep> steps;

    public DynamicPrefix(Instance instance, DynamicParameters parameters) {
        if (parameters == null) throw new IllegalArgumentException("Fatigue parameters are required");
        parameters.validateFor(instance);
        this.instance = instance; this.parameters = parameters; policy = DynamicSchedule.POLICY;
        states = new DynamicStageState[instance.factories()];
        for (int f = 0; f < states.length; f++) states[f] = new DynamicStageState(instance, parameters, f, 0);
        completed = new boolean[instance.jobs()];
        firstCompletion = new double[instance.jobs()];
        objectives = new double[3];
        steps = new ArrayList<DynamicStep>();
    }

    private DynamicPrefix(DynamicPrefix source) {
        instance = source.instance; parameters = source.parameters; policy = source.policy;
        states = new DynamicStageState[source.states.length];
        for (int f = 0; f < states.length; f++) states[f] = source.states[f].copy();
        completed = source.completed.clone(); firstCompletion = source.firstCompletion.clone();
        objectives = source.objectives.clone(); steps = new ArrayList<DynamicStep>(source.steps);
    }

    public DynamicPrefix copy() { return new DynamicPrefix(this); }

    public DynamicStep preview(int j, int f, int m, int w) {
        range(j, completed.length, "job"); range(f, states.length, "factory");
        range(m, states[f].machineEnd.length, "machine");
        range(w, states[f].workerEnd.length, "worker");
        if (completed[j]) throw new IllegalArgumentException("Job already exists in prefix: " + j);
        return states[f].preview(instance, parameters, j, m, w, 0.0);
    }

    public DynamicStep append(int j, int f, int m, int w) {
        DynamicStep step = preview(j, f, m, w);
        states[f].accept(step); steps.add(step); completed[j] = true;
        firstCompletion[j] = step.completion();
        objectives[0] = Math.max(objectives[0], step.completion());
        objectives[1] += step.energy(); objectives[2] += step.labor();
        return step;
    }

    public double[] partialObjectives() { return objectives.clone(); }
    public int size() { return steps.size(); }
    public List<DynamicStep> steps() {
        return Collections.unmodifiableList(new ArrayList<DynamicStep>(steps));
    }
    public boolean completed(int j) { range(j, completed.length, "job"); return completed[j]; }
    public double firstCompletion(int j) {
        range(j, firstCompletion.length, "job"); return firstCompletion[j];
    }
    public double machineEnd(int f, int m) { return states[f].machineEnd[m]; }
    public double workerEnd(int f, int w) { return states[f].workerEnd[w]; }
    /** Fatigue at this worker's last completion, or h0 if it has not worked. */
    public double workerFatigue(int f, int w) { return states[f].workerFatigue[w]; }
    public double workerExposure(int f, int w) { return states[f].workerExposure[w]; }

    void validateContext(Instance in, DynamicParameters p) {
        if (!DynamicSchedule.POLICY.equals(policy)) throw new IllegalArgumentException("Dynamic prefix decoder policy differs");
        DynamicContext.requireSame(in, p, instance, parameters);
    }

    private static void range(int value, int bound, String name) {
        if (value < 0 || value >= bound) throw new IllegalArgumentException("Invalid " + name + " id " + value);
    }
}
