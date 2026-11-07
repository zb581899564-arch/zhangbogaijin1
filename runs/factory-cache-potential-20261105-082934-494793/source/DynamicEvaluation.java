package org.uma.jmetal.util.research;

import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.*;

/** Per-run adapter. Immutable schedules survive copying; mutable prepared prefixes do not. */
public final class DynamicEvaluation implements Problem<PermutationSolution<Integer>> {
    private static final long serialVersionUID = 1L;
    public static final String KEY = "dynamic.schedule";
    private final Problem<PermutationSolution<Integer>> source;
    private final Instance instance;
    private final DynamicParameters parameters;
    private final boolean incremental;
    private transient Runnable checkpoint = () -> { };
    private transient Map<PermutationSolution<Integer>, DynamicPrefix> prepared = new IdentityHashMap<>();
    private long evaluations, recomputed, reused, decodeNanos, preparedCount;

    public DynamicEvaluation(Problem<PermutationSolution<Integer>> source, Instance instance,
            DynamicParameters parameters, boolean incremental) {
        this.source = source; this.instance = instance; this.parameters = parameters; this.incremental = incremental;
    }
    public void setCheckpoint(Runnable checkpoint) { this.checkpoint = checkpoint; }
    public void prepare(PermutationSolution<Integer> child, DynamicPrefix prefix) {
        if (prepared.put(child, prefix) != null) throw new IllegalStateException("Child prepared twice");
        preparedCount++;
    }
    public void clearPrepared() { prepared.clear(); }
    @Override public PermutationSolution<Integer> createSolution() { return source.createSolution(); }
    @Override public int getNumberOfVariables() { return source.getNumberOfVariables(); }
    @Override public int getNumberOfObjectives() { return 3; }
    @Override public int getNumberOfConstraints() { return source.getNumberOfConstraints(); }
    @Override public String getName() { return "A0-D; dynamic-append-v1"; }

    @Override public void evaluate(PermutationSolution<Integer> child) {
        int[] js = SchedulingEncoding.integers(child.getVariables());
        int[] fa = SchedulingEncoding.integers(child.getVariablesid());
        int[] ma = SchedulingEncoding.machineIntegers(child);
        int[] wa = SchedulingEncoding.integers(child.getVariablesworker());
        DynamicPrefix prefix = prepared.remove(child);
        Object previous = child.getAttribute(KEY);
        long start = System.nanoTime();
        DynamicSchedule schedule;
        try {
            schedule = incremental || prefix != null
                    ? DynamicDecoder.incremental(instance, parameters, js, fa, ma, wa,
                            incremental && previous instanceof DynamicSchedule ? (DynamicSchedule) previous : null,
                            prefix, checkpoint)
                    : DynamicDecoder.full(instance, parameters, js, fa, ma, wa, checkpoint);
        } finally { decodeNanos += System.nanoTime() - start; }
        FactoryCachePotential.observe(instance,parameters,js,fa,ma,wa,
            incremental && previous instanceof DynamicSchedule?(DynamicSchedule)previous:null,schedule,prefix!=null);
        double[] objectives = schedule.objectives();
        for (int i = 0; i < 3; i++) child.setObjective(i, objectives[i]);
        child.setAttribute(KEY, schedule);
        child.setAttribute(SchedulingMetadata.KEY, new SchedulingMetadata(
                schedule.factoryMakespan(), schedule.factoryEnergy(), schedule.factoryCost()));
        // The static schedule has different duration/validator semantics.
        child.setAttribute(SchedulingMetadata.SCHEDULE_KEY, null);
        child.setAttribute("dhfsp.modelProvenance", instance.provenance() + "; " + parameters.source());
        evaluations++; reused += schedule.reusedOperations(); recomputed += schedule.recomputedOperations();
    }
    public Map<String, Long> diagnostics() {
        Map<String, Long> counts = new LinkedHashMap<>();
        counts.put("dynamic.evaluations", evaluations); counts.put("dynamic.reusedOperations", reused);
        counts.put("dynamic.recomputedOperations", recomputed); counts.put("dynamic.decodeNanos", decodeNanos);
        counts.put("dynamic.preparedChildren", preparedCount); return counts;
    }
}
