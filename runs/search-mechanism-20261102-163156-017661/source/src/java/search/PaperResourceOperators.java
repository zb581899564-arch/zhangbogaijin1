package org.uma.jmetal.util.research.search;

import java.util.List;
import java.util.Random;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.model.ModelKind;

/** ESWA Algorithm 4 resource updates; JS and final common feasibility repair remain outside. */
final class PaperResourceOperators {
    private PaperResourceOperators() { }

    static void apply(PermutationSolution<Integer> child, PermutationSolution<Integer> donor,
            Instance instance, SearchConfig config, Random random) {
        if (instance.kind() != ModelKind.CHAPTER4_DUAL_RESOURCE) {
            throw new IllegalArgumentException("Paper resource operators require the chapter 4 model");
        }
        // Algorithm 4 draws all six independent triggers before any operator draws.
        double r1 = random.nextDouble(), r2 = random.nextDouble(), r3 = random.nextDouble();
        double r4 = random.nextDouble(), r5 = random.nextDouble(), r6 = random.nextDouble();
        if (r1 < config.factoryCrossover) crossFactories(child, donor, instance, random);
        if (r2 < config.machineCrossover) crossResource(child, donor, instance, random, true);
        if (r3 < config.workerCrossover) crossResource(child, donor, instance, random, false);
        if (r4 < config.factoryMutation) mutateFactory(child, instance, random);
        if (r5 < config.machineMutation) mutateResource(child, instance, random, true);
        if (r6 < config.workerMutation) mutateResource(child, instance, random, false);
    }

    private static void crossFactories(PermutationSolution<Integer> child,
            PermutationSolution<Integer> donor, Instance instance, Random random) {
        int first = random.nextInt(instance.jobs()), second = random.nextInt(instance.jobs());
        int low = Math.min(first, second), high = Math.max(first, second);
        copySegment(child.getVariablesid(), donor.getVariablesid(), low, high);
        for (int p = low; p <= high; p++) {
            repairResource(child, instance, random, p, true);
            repairResource(child, instance, random, p, false);
        }
    }

    private static void crossResource(PermutationSolution<Integer> child,
            PermutationSolution<Integer> donor, Instance instance, Random random, boolean machine) {
        int first = random.nextInt(instance.jobs()), second = random.nextInt(instance.jobs());
        int low = Math.min(first, second), high = Math.max(first, second);
        copySegment(vector(child, machine), vector(donor, machine), low, high);
        for (int p = low; p <= high; p++) repairResource(child, instance, random, p, machine);
    }

    private static void copySegment(List<Integer> child, List<Integer> donor, int low, int high) {
        for (int p = low; p <= high; p++) child.set(p, donor.get(p));
    }

    private static void repairResource(PermutationSolution<Integer> child, Instance instance,
            Random random, int position, boolean machine) {
        List<Integer> values = vector(child, machine);
        int bound = resourceCount(instance, child.getVariableValueid(position), machine);
        int value = values.get(position);
        if (value < 0 || value >= bound) values.set(position, random.nextInt(bound));
    }

    private static void mutateFactory(PermutationSolution<Integer> child, Instance instance, Random random) {
        int position = random.nextInt(instance.jobs()), factory = random.nextInt(instance.factories());
        child.setVariableValueid(position, factory);
        // A mutation event redraws both resources even when the factory/value remains unchanged.
        vector(child, true).set(position, random.nextInt(instance.machines(factory, 0)));
        vector(child, false).set(position, random.nextInt(instance.workers(factory, 0)));
    }

    private static void mutateResource(PermutationSolution<Integer> child, Instance instance,
            Random random, boolean machine) {
        int position = random.nextInt(instance.jobs()), factory = child.getVariableValueid(position);
        vector(child, machine).set(position, random.nextInt(resourceCount(instance, factory, machine)));
    }

    private static int resourceCount(Instance instance, int factory, boolean machine) {
        return machine ? instance.machines(factory, 0) : instance.workers(factory, 0);
    }

    private static List<Integer> vector(PermutationSolution<Integer> solution, boolean machine) {
        return machine ? ParticleOperators.machines(solution) : solution.getVariablesworker();
    }
}
