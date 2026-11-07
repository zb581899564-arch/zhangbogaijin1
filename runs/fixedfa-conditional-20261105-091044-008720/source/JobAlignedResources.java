package org.uma.jmetal.util.research.mechanism;

import java.util.List;
import java.util.Random;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.search.SearchConfig;

/** Paper Algorithm 4 with the sole crossover change: donor resources use the same job. */
final class JobAlignedResources {
    private JobAlignedResources() { }

    static void apply(PermutationSolution<Integer> child, PermutationSolution<Integer> donor,
            Instance instance, SearchConfig config, Random random) {
        int[] donorPosition = new int[instance.jobs()];
        for (int p = 0; p < donorPosition.length; p++) donorPosition[donor.getVariableValue(p)] = p;
        double r1 = random.nextDouble(), r2 = random.nextDouble(), r3 = random.nextDouble();
        double r4 = random.nextDouble(), r5 = random.nextDouble(), r6 = random.nextDouble();
        if (r1 < config.factoryCrossover) crossFactories(child, donor, donorPosition, instance, random);
        if (r2 < config.machineCrossover) crossResource(child, donor, donorPosition, instance, random, true);
        if (r3 < config.workerCrossover) crossResource(child, donor, donorPosition, instance, random, false);
        if (r4 < config.factoryMutation && !org.uma.jmetal.util.research.search.FixedFAMutationMask.skipAligned()) mutateFactory(child, instance, random);
        if (r5 < config.machineMutation) mutateResource(child, instance, random, true);
        if (r6 < config.workerMutation) mutateResource(child, instance, random, false);
    }

    private static void crossFactories(PermutationSolution<Integer> child, PermutationSolution<Integer> donor,
            int[] donorPosition, Instance instance, Random random) {
        int first = random.nextInt(instance.jobs()), second = random.nextInt(instance.jobs());
        int low = Math.min(first, second), high = Math.max(first, second);
        for (int p = low; p <= high; p++) {
            child.setVariableValueid(p, donor.getVariableValueid(donorPosition[child.getVariableValue(p)]));
        }
        for (int p = low; p <= high; p++) {
            repairResource(child, instance, random, p, true);
            repairResource(child, instance, random, p, false);
        }
    }

    private static void crossResource(PermutationSolution<Integer> child, PermutationSolution<Integer> donor,
            int[] donorPosition, Instance instance, Random random, boolean machine) {
        int first = random.nextInt(instance.jobs()), second = random.nextInt(instance.jobs());
        int low = Math.min(first, second), high = Math.max(first, second);
        for (int p = low; p <= high; p++) {
            vector(child, machine).set(p, vector(donor, machine).get(donorPosition[child.getVariableValue(p)]));
        }
        for (int p = low; p <= high; p++) repairResource(child, instance, random, p, machine);
    }

    private static void repairResource(PermutationSolution<Integer> child, Instance instance,
            Random random, int position, boolean machine) {
        List<Integer> values = vector(child, machine);
        int bound = count(instance, child.getVariableValueid(position), machine), value = values.get(position);
        if (value < 0 || value >= bound) values.set(position, random.nextInt(bound));
    }

    private static void mutateFactory(PermutationSolution<Integer> child, Instance instance, Random random) {
        int position = random.nextInt(instance.jobs()), factory = random.nextInt(instance.factories());
        child.setVariableValueid(position, factory);
        vector(child, true).set(position, random.nextInt(instance.machines(factory, 0)));
        vector(child, false).set(position, random.nextInt(instance.workers(factory, 0)));
    }

    private static void mutateResource(PermutationSolution<Integer> child, Instance instance,
            Random random, boolean machine) {
        int position = random.nextInt(instance.jobs()), factory = child.getVariableValueid(position);
        vector(child, machine).set(position, random.nextInt(count(instance, factory, machine)));
    }

    private static int count(Instance instance, int factory, boolean machine) {
        return machine ? instance.machines(factory, 0) : instance.workers(factory, 0);
    }

    @SuppressWarnings("unchecked")
    static List<Integer> vector(PermutationSolution<Integer> solution, boolean machine) {
        return machine ? (List<Integer>) solution.getAttribute("machine") : solution.getVariablesworker();
    }
}
