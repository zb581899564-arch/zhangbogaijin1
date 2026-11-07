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

/** Nine chapter-specific neighborhoods, all operating on a copied candidate in one factory. */
public final class IntraNeighborhoods {
    public static final int COUNT = 9;
    private final Instance instance;
    public IntraNeighborhoods(Instance instance) { this.instance = instance; }

    public PermutationSolution<Integer> propose(PermutationSolution<Integer> parent, int factory, int operator) {
        if (operator < 0 || operator >= COUNT) throw new IllegalArgumentException("Neighborhood must be 0..8");
        PermutationSolution<Integer> child = ParetoTools.copy(parent);
        List<Integer> positions = positions(child, factory);
        if (operator < 3) permute(child.getVariables(), positions, operator);
        else if (instance.kind() == ModelKind.CHAPTER3_FIXED_WORKER) {
            if (operator < 6) permute(ParticleOperators.machines(child), positions, operator - 3);
            else permute(child.getVariablesworker(), fixedWorkerPositions(factory), operator - 6);
        } else if (operator == 5) permute(ParticleOperators.machines(child), positions, 2);
        else if (operator == 8) permute(child.getVariablesworker(), positions, 2);
        else reallocate(child, factory, positions, operator < 6, operator == 4 || operator == 7);
        SchedulingEncoding.repair(child, instance);
        CandidateRedundancy.intra(parent, child, instance, factory, operator);
        return child;
    }

    private void reallocate(PermutationSolution<Integer> child, int factory, List<Integer> positions,
            boolean machine, boolean capacity) {
        if (positions.isEmpty()) return;
        List<Integer> vector = machine ? ParticleOperators.machines(child) : child.getVariablesworker();
        int size = machine ? instance.machines(factory, 0) : instance.workers(factory, 0);
        if (size < 2) return;
        int[] load = new int[size];
        for (int p : positions) load[vector.get(p)]++;
        int source = -1, target = 0;
        for (int resource = 0; resource < size; resource++) {
            if (load[resource] > 0 && (source < 0 || (capacity
                    ? capacity(factory, resource, machine) < capacity(factory, source, machine)
                    : load[resource] > load[source]))) source = resource;
            if (capacity ? capacity(factory, resource, machine) > capacity(factory, target, machine)
                         : load[resource] < load[target]) target = resource;
        }
        if (source == target) return;
        List<Integer> movable = new ArrayList<>();
        for (int p : positions) if (vector.get(p) == source) movable.add(p);
        int chosen = movable.get(SeededRandom.current().nextInt(movable.size()));
        vector.set(chosen, target);
    }
    private double capacity(int factory, int resource, boolean machine) {
        return machine ? instance.speed(factory, 0, resource) : instance.efficiency(factory, 0, resource);
    }
    private static List<Integer> positions(PermutationSolution<Integer> solution, int factory) {
        List<Integer> result = new ArrayList<>();
        for (int p = 0; p < solution.getNumberOfVariables(); p++) if (solution.getVariableValueid(p) == factory) result.add(p);
        return result;
    }
    private List<Integer> fixedWorkerPositions(int factory) {
        int offset = 0;
        for (int f = 0; f < factory; f++) offset += instance.workers(f, 0);
        List<Integer> result = new ArrayList<>();
        for (int i = 0; i < instance.workers(factory, 0); i++) result.add(offset + i);
        return result;
    }
    private static void permute(List<Integer> vector, List<Integer> positions, int operation) {
        if (positions.size() < 2) return;
        Random random = SeededRandom.current();
        int a = random.nextInt(positions.size()), b = random.nextInt(positions.size() - 1);
        if (b >= a) b++;
        List<Integer> values = new ArrayList<>();
        for (int p : positions) values.add(vector.get(p));
        if (operation == 0) { Integer value = values.remove(b); values.add(a, value); }
        else if (operation == 1) Collections.reverse(values.subList(Math.min(a, b), Math.max(a, b) + 1));
        else Collections.swap(values, a, b);
        for (int i = 0; i < positions.size(); i++) vector.set(positions.get(i), values.get(i));
    }
}
