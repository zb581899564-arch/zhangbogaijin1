package org.uma.jmetal.util.research.mechanism;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import org.uma.jmetal.util.research.search.SearchConfig;

/** Isolated hypothesis: align joint resource inheritance with jobs touched by QGS order guidance. */
public final class LinkedGuideKernel {
    private final Instance in;
    private final SearchConfig cfg;
    private final boolean shuffled;
    private long guides, eligible, inheritedJobs;

    public LinkedGuideKernel(Instance in, SearchConfig cfg, boolean shuffled) {
        this.in = in; this.cfg = cfg; this.shuffled = shuffled;
    }

    @SuppressWarnings("unchecked")
    public PermutationSolution<Integer> child(PermutationSolution<Integer> parent,
            PermutationSolution<Integer> personal, PermutationSolution<Integer> leader) {
        PermutationSolution<Integer> out = (PermutationSolution<Integer>) parent.copy();
        Random rng = SeededRandom.current();
        JobAlignedPaperKernel.swapJobAndResources(out, rng.nextInt(in.jobs()), rng.nextInt(in.jobs()));
        guide(out, personal, rng); guide(out, leader, rng);
        SchedulingEncoding.repair(out, in);
        return out;
    }

    private void guide(PermutationSolution<Integer> out, PermutationSolution<Integer> donor, Random rng) {
        boolean[] moved = move(out, donor, rng);
        List<Integer> randomJobs = new ArrayList<>();
        int count = 0;
        for (int j = 0; j < in.jobs(); j++) { randomJobs.add(j); if (moved[j]) count++; }
        // Both arms perform the identical shuffle, so the random-set control has the same draw cost.
        Collections.shuffle(randomJobs, rng);
        if (shuffled) {
            Arrays.fill(moved, false);
            for (int i = 0; i < count; i++) moved[randomJobs.get(i)] = true;
        }
        int[] pos = new int[in.jobs()];
        for (int p = 0; p < in.jobs(); p++) pos[donor.getVariableValue(p)] = p;
        double[] trigger = new double[6];
        for (int i = 0; i < trigger.length; i++) trigger[i] = rng.nextDouble();
        guides++; if (count > 0) eligible++;
        // A joint tuple uses the existing FA crossover probability, with no probability sweep.
        if (trigger[0] < cfg.factoryCrossover) for (int p = 0; p < in.jobs(); p++) {
            int j = out.getVariableValue(p);
            if (moved[j]) {
                int d = pos[j];
                out.setVariableValueid(p, donor.getVariableValueid(d));
                JobAlignedResources.vector(out, true).set(p, JobAlignedResources.vector(donor, true).get(d));
                out.setVariableValueworker(p, donor.getVariableValueworker(d)); inheritedJobs++;
            }
        }
        // Retain the three original independent mutation probabilities and their legal draws.
        if (trigger[3] < cfg.factoryMutation) {
            int p = rng.nextInt(in.jobs()), f = rng.nextInt(in.factories());
            out.setVariableValueid(p, f);
            JobAlignedResources.vector(out, true).set(p, rng.nextInt(in.machines(f, 0)));
            out.setVariableValueworker(p, rng.nextInt(in.workers(f, 0)));
        }
        if (trigger[4] < cfg.machineMutation) mutate(out, rng, true);
        if (trigger[5] < cfg.workerMutation) mutate(out, rng, false);
        SchedulingEncoding.repair(out, in);
    }

    private boolean[] move(PermutationSolution<Integer> out, PermutationSolution<Integer> donor, Random rng) {
        List<Integer> order = new ArrayList<>(out.getVariables());
        List<int[]> swaps = new ArrayList<>();
        for (int p = 0; p < order.size(); p++) {
            int desired = donor.getVariableValue(p);
            if (order.get(p) != desired) {
                int other = order.indexOf(desired);
                swaps.add(new int[] {p, other}); Collections.swap(order, p, other);
            }
        }
        boolean[] touched = new boolean[in.jobs()];
        int count = (int) (swaps.size() * rng.nextDouble() * cfg.randScale);
        for (int i = 0; i < count; i++) {
            int a = swaps.get(i)[0], b = swaps.get(i)[1];
            touched[out.getVariableValue(a)] = touched[out.getVariableValue(b)] = true;
            JobAlignedPaperKernel.swapJobAndResources(out, a, b);
        }
        return touched;
    }

    private void mutate(PermutationSolution<Integer> out, Random rng, boolean machine) {
        int p = rng.nextInt(in.jobs()), f = out.getVariableValueid(p);
        JobAlignedResources.vector(out, machine).set(p, rng.nextInt(machine ? in.machines(f, 0) : in.workers(f, 0)));
    }

    public Map<String,Object> diagnostics() {
        Map<String,Object> r = new LinkedHashMap<>();
        r.put("guides", guides); r.put("nonemptyGuides", eligible); r.put("inheritedJobs", inheritedJobs);
        r.put("randomSet", shuffled); return r;
    }
}
