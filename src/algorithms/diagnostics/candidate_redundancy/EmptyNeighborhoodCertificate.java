package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.model.ModelKind;

/** Algebraic certificate for the actual chapter-four operator, without generating another candidate. */
final class EmptyNeighborhoodCertificate {
    private EmptyNeighborhoodCertificate() { }

    static List<Integer> positions(PermutationSolution<Integer> parent, int factory) {
        List<Integer> result = new ArrayList<>();
        for (int p = 0; p < parent.getNumberOfVariables(); p++) if (parent.getVariableValueid(p) == factory) result.add(p);
        return result;
    }

    static boolean empty(Instance in, PermutationSolution<Integer> parent, int factory, int operator) {
        if (in.kind() != ModelKind.CHAPTER4_DUAL_RESOURCE) throw new AssertionError("Chapter four only");
        List<Integer> pos = positions(parent, factory);
        if (operator < 3) return pos.size() < 2;
        boolean machine = operator < 6;
        List<Integer> vector = machine ? ParticleOperators.machines(parent) : parent.getVariablesworker();
        if (operator == 5 || operator == 8) {
            if (pos.size() < 2) return true;
            int first = vector.get(pos.get(0));
            for (int p : pos) if (vector.get(p) != first) return false;
            return true;
        }
        int size = machine ? in.machines(factory, 0) : in.workers(factory, 0);
        if (pos.isEmpty() || size < 2) return true;
        int[] load = new int[size]; for (int p : pos) load[vector.get(p)]++;
        boolean capacity = operator == 4 || operator == 7;
        int source = -1, target = 0;
        for (int resource = 0; resource < size; resource++) {
            if (load[resource] > 0 && (source < 0 || (capacity
                    ? capacity(in, factory, resource, machine) < capacity(in, factory, source, machine)
                    : load[resource] > load[source]))) source = resource;
            if (capacity ? capacity(in, factory, resource, machine) > capacity(in, factory, target, machine)
                         : load[resource] < load[target]) target = resource;
        }
        return source == target;
    }

    private static double capacity(Instance in, int f, int r, boolean machine) {
        return machine ? in.speed(f, 0, r) : in.efficiency(f, 0, r);
    }
}
