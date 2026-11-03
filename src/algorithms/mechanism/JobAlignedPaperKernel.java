package org.uma.jmetal.util.research.mechanism;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import org.uma.jmetal.util.research.search.SearchConfig;

/** Explicit identity-aligned hypothesis; paper triggers, segments, and mutation rules are retained. */
final class JobAlignedPaperKernel {
    private final Instance instance;
    private final SearchConfig config;
    JobAlignedPaperKernel(Instance instance, SearchConfig config) {
        this.instance = instance; this.config = config;
    }

    @SuppressWarnings("unchecked")
    PermutationSolution<Integer> child(PermutationSolution<Integer> parent,
            PermutationSolution<Integer> personal, PermutationSolution<Integer> global) {
        PermutationSolution<Integer> child = (PermutationSolution<Integer>) parent.copy();
        Random random = SeededRandom.current();
        swapJobAndResources(child, random.nextInt(instance.jobs()), random.nextInt(instance.jobs()));
        guide(child, personal, random);
        guide(child, global, random);
        SchedulingEncoding.repair(child, instance);
        return child;
    }

    private void guide(PermutationSolution<Integer> child, PermutationSolution<Integer> donor, Random random) {
        moveJobSequence(child, donor, random);
        JobAlignedResources.apply(child, donor, instance, config, random);
        SchedulingEncoding.repair(child, instance);
    }

    private void moveJobSequence(PermutationSolution<Integer> child,
            PermutationSolution<Integer> donor, Random random) {
        List<Integer> temporary = new ArrayList<>(child.getVariables());
        List<int[]> exchange = new ArrayList<>();
        for (int p = 0; p < temporary.size(); p++) {
            int desired = donor.getVariableValue(p);
            if (temporary.get(p) != desired) {
                int other = temporary.indexOf(desired);
                exchange.add(new int[] {p, other}); Collections.swap(temporary, p, other);
            }
        }
        int count = (int) (exchange.size() * random.nextDouble() * config.randScale);
        for (int i = 0; i < count; i++) {
            swapJobAndResources(child, exchange.get(i)[0], exchange.get(i)[1]);
        }
    }

    static void swapJobAndResources(PermutationSolution<Integer> child, int first, int second) {
        Collections.swap(child.getVariables(), first, second);
        Collections.swap(child.getVariablesid(), first, second);
        Collections.swap(JobAlignedResources.vector(child, true), first, second);
        Collections.swap(child.getVariablesworker(), first, second);
    }
}
