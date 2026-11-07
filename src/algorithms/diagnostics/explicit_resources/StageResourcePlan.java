package org.uma.jmetal.util.research.model;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** Immutable job/stage decisions. The default remains the original earliest-resource rule. */
public final class StageResourcePlan implements Serializable {
    private static final long serialVersionUID = 1L;
    public static final String POLICY = "explicit-resource-append-v1";
    private final int jobs, stages;
    private final int[][] machines, workers;

    private StageResourcePlan(int n, int s, int[][] m, int[][] w) {
        jobs = n; stages = s; machines = m; workers = w;
    }

    public static StageResourcePlan empty(int jobs, int stages) {
        if (jobs < 1 || stages < 1) throw new IllegalArgumentException("Empty plan dimensions");
        int[][] machines = new int[jobs][stages], workers = new int[jobs][stages];
        for (int j = 0; j < jobs; j++) {
            Arrays.fill(machines[j], -1); Arrays.fill(workers[j], -1);
        }
        return new StageResourcePlan(jobs, stages, machines, workers);
    }

    public StageResourcePlan with(int job, int stage, int machine, int worker) {
        if (job < 0 || job >= jobs || stage <= 0 || stage >= stages || machine < 0 || worker < 0)
            throw new IllegalArgumentException("Only later-stage nonnegative resource pairs are explicit");
        int[][] nextMachines = copy(machines), nextWorkers = copy(workers);
        nextMachines[job][stage] = machine; nextWorkers[job][stage] = worker;
        return new StageResourcePlan(jobs, stages, nextMachines, nextWorkers);
    }

    public boolean specified(int job, int stage) { return machines[job][stage] >= 0; }
    public int machine(int job, int stage) { return machines[job][stage]; }
    public int worker(int job, int stage) { return workers[job][stage]; }

    public void validate(Instance instance, int[] js, int[] factory) {
        if (jobs != instance.jobs() || stages != instance.stages())
            throw new IllegalArgumentException("Explicit plan dimensions differ from instance");
        int[] byJob = new int[jobs];
        for (int pos = 0; pos < jobs; pos++) byJob[js[pos]] = factory[pos];
        for (int j = 0; j < jobs; j++) for (int k = 1; k < stages; k++) {
            if (specified(j, k) && (machines[j][k] >= instance.machines(byJob[j], k)
                    || workers[j][k] >= instance.workers(byJob[j], k)))
                throw new IllegalArgumentException("Explicit resource outside its factory/stage");
        }
    }

    public List<int[]> entries() {
        List<int[]> out = new ArrayList<>();
        for (int j = 0; j < jobs; j++) for (int k = 1; k < stages; k++)
            if (specified(j, k)) out.add(new int[] {j, k, machines[j][k], workers[j][k]});
        return out;
    }

    public String identity() {
        StringBuilder out = new StringBuilder(POLICY).append(':').append(jobs).append(':').append(stages);
        for (int[] entry : entries()) out.append(';').append(Arrays.toString(entry));
        return out.toString();
    }

    private static int[][] copy(int[][] values) {
        int[][] out = new int[values.length][];
        for (int j = 0; j < values.length; j++) out[j] = values[j].clone();
        return out;
    }
}
