package org.uma.jmetal.util.research;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.model.ModelKind;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Paper inter-factory moves: highest-load factory to lowest-load factory. */
public final class FactoryNeighborhoods {
    private FactoryNeighborhoods() { }

    @SuppressWarnings("unchecked")
    public static PermutationSolution<Integer> move(PermutationSolution<Integer> parent,
            int group, boolean exchange, Instance instance) {
        PermutationSolution<Integer> child = (PermutationSolution<Integer>) parent.copy();
        Random random = SeededRandom.current();
        // The paper does not specify the center swarm's critical objective.
        // Freeze an explicit uniform choice, shared across both reconstructed baselines.
        int objective = group == 1 ? 0 : group == 3 ? 1 : group == 4 ? 2 : random.nextInt(3);
        SchedulingMetadata metrics = SchedulingMetadata.of(parent);
        int high = metrics.extremum(objective, true), low = metrics.extremum(objective, false);
        if (high == low) return child;
        List<Integer> highPositions = positions(parent, high), lowPositions = positions(parent, low);
        if (highPositions.isEmpty() || lowPositions.isEmpty() || (!exchange && highPositions.size() < 2)) return child;
        int a = highPositions.get(random.nextInt(highPositions.size()));
        int b = lowPositions.get(random.nextInt(lowPositions.size()));
        if (exchange) {
            child.setVariableValue(a, parent.getVariableValue(b));
            child.setVariableValue(b, parent.getVariableValue(a));
        } else {
            // Move the entire positional tuple, putting the migrated job at a
            // randomly chosen position in the destination sequence.
            moveEntry(child.getVariables(), a, b);
            moveEntry(child.getVariablesid(), a, b);
            List<Integer> machines = (List<Integer>) child.getAttribute("machine");
            moveEntry(machines, a, b);
            if (instance.kind() == ModelKind.CHAPTER4_DUAL_RESOURCE) moveEntry(child.getVariablesworker(), a, b);
            child.setVariableValueid(b, low);
        }
        SchedulingEncoding.repair(child, instance);
        return child;
    }

    private static List<Integer> positions(PermutationSolution<Integer> solution, int factory) {
        List<Integer> result = new ArrayList<>();
        for (int i = 0; i < solution.getNumberOfVariables(); i++) if (solution.getVariableValueid(i) == factory) result.add(i);
        return result;
    }
    private static void moveEntry(List<Integer> values, int from, int to) {
        Integer value = values.remove(from); values.add(to, value);
    }
}
