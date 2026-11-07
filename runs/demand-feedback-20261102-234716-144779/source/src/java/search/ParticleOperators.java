package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.model.ModelKind;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Discrete PSO update: random JS exchange, personal guide, global guide and legal vector operators. */
public final class ParticleOperators {
    private final Instance instance;
    private final SearchConfig config;
    public ParticleOperators(Instance instance, SearchConfig resolvedConfig) {
        this.instance = instance; config = resolvedConfig;
    }
    public PermutationSolution<Integer> update(PermutationSolution<Integer> parent,
            PermutationSolution<Integer> personal, PermutationSolution<Integer> global) {
        PermutationSolution<Integer> child = ParetoTools.copy(parent);
        Random random = SeededRandom.current();
        Collections.swap(child.getVariables(), random.nextInt(instance.jobs()), random.nextInt(instance.jobs()));
        guide(child, personal); guide(child, global);
        SchedulingEncoding.repair(child, instance);
        return child;
    }
    private void guide(PermutationSolution<Integer> child, PermutationSolution<Integer> parent) {
        moveJobSequence(child, parent);
        if (config.paperResourceOperators && instance.kind() == ModelKind.CHAPTER4_DUAL_RESOURCE) {
            PaperResourceOperators.apply(child, parent, instance, config, SeededRandom.current());
            SchedulingEncoding.repair(child, instance);
            return;
        }
        Random random = SeededRandom.current();
        if (random.nextDouble() < config.factoryCrossover) copySuffix(child.getVariablesid(), parent.getVariablesid());
        SchedulingEncoding.repair(child, instance);
        if (random.nextDouble() < config.machineCrossover) copySuffix(machines(child), machines(parent));
        if (random.nextDouble() < config.workerCrossover) crossoverWorkers(child, parent);
        if (random.nextDouble() < config.factoryMutation) {
            child.setVariableValueid(random.nextInt(instance.jobs()), random.nextInt(instance.factories()));
        }
        SchedulingEncoding.repair(child, instance);
        if (random.nextDouble() < config.machineMutation) {
            int position = random.nextInt(instance.jobs());
            machines(child).set(position, random.nextInt(instance.machines(child.getVariableValueid(position), 0)));
        }
        if (random.nextDouble() < config.workerMutation) mutateWorkers(child);
        SchedulingEncoding.repair(child, instance);
    }
    private void moveJobSequence(PermutationSolution<Integer> child, PermutationSolution<Integer> guide) {
        List<Integer> temporary = new ArrayList<>(child.getVariables());
        List<int[]> exchange = new ArrayList<>();
        for (int p = 0; p < temporary.size(); p++) {
            int desired = guide.getVariableValue(p);
            if (temporary.get(p) != desired) {
                int other = temporary.indexOf(desired);
                exchange.add(new int[] {p, other}); Collections.swap(temporary, p, other);
            }
        }
        int count = (int) (exchange.size() * SeededRandom.current().nextDouble() * config.randScale);
        for (int i = 0; i < count; i++) Collections.swap(child.getVariables(), exchange.get(i)[0], exchange.get(i)[1]);
    }
    private static void copySuffix(List<Integer> child, List<Integer> parent) {
        int begin = SeededRandom.current().nextInt(child.size());
        for (int i = begin; i < child.size(); i++) child.set(i, parent.get(i));
    }
    private void crossoverWorkers(PermutationSolution<Integer> child, PermutationSolution<Integer> parent) {
        Random random = SeededRandom.current();
        if (instance.kind() == ModelKind.CHAPTER3_FIXED_WORKER) {
            int factory = random.nextInt(instance.factories()), offset = workerOffset(factory);
            int size = instance.workers(factory, 0);
            int a = random.nextInt(size), b = random.nextInt(size);
            int low = Math.min(a, b), high = Math.max(a, b);
            List<Integer> donor = parent.getVariablesworker().subList(offset, offset + size);
            List<Integer> old = new ArrayList<>(child.getVariablesworker().subList(offset, offset + size));
            List<Integer> remaining = new ArrayList<>(old);
            remaining.removeAll(donor.subList(low, high + 1));
            int cursor = 0;
            for (int i = 0; i < size; i++) child.setVariableValueworker(offset + i,
                    i >= low && i <= high ? donor.get(i) : remaining.get(cursor++));
        } else {
            int begin = random.nextInt(instance.jobs());
            for (int p = begin; p < instance.jobs(); p++) {
                if (child.getVariableValueid(p).equals(parent.getVariableValueid(p))) {
                    child.setVariableValueworker(p, parent.getVariableValueworker(p));
                }
            }
        }
    }
    private void mutateWorkers(PermutationSolution<Integer> child) {
        Random random = SeededRandom.current();
        if (instance.kind() == ModelKind.CHAPTER3_FIXED_WORKER) {
            int factory = random.nextInt(instance.factories()), length = instance.workers(factory, 0);
            if (length > 1) {
                int p = random.nextInt(length - 1) + workerOffset(factory);
                Collections.swap(child.getVariablesworker(), p, p + 1);
            }
        } else {
            int p = random.nextInt(instance.jobs());
            child.setVariableValueworker(p, random.nextInt(instance.workers(child.getVariableValueid(p), 0)));
        }
    }
    private int workerOffset(int factory) {
        int offset = 0;
        for (int f = 0; f < factory; f++) offset += instance.workers(f, 0);
        return offset;
    }
    @SuppressWarnings("unchecked")
    static List<Integer> machines(PermutationSolution<Integer> solution) {
        return (List<Integer>) solution.getAttribute("machine");
    }
}
