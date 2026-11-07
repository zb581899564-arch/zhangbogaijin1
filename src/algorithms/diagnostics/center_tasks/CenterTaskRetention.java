package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;

/** Matched lifecycle control: one global/local pair per actual slot, with unchanged family totals. */
final class CenterTaskRetention {
    private CenterTaskRetention() { }

    static SurvivorSelection.Result select(List<Particle> candidates, int count, SwarmSupport support,
            Runnable checkpoint) {
        checkpoint.run();
        if (candidates.size() != 2 * count || count != 100 || support == null)
            throw new AssertionError("Task lifecycle requires the real100global+100local pool");
        List<PermutationSolution<Integer>> values = new ArrayList<>();
        for (Particle particle : candidates) values.add(particle.current);
        // Keep the original full-pool PDDR diagnostic, even when it is not the decision criterion.
        double[] fitness = ParetoTools.fitness(values), ideal = CenterTaskState.ideal();
        int[] quotas = support.selectionQuotas().clone(), used = new int[quotas.length];
        int[] categories = new int[candidates.size()], indices = new int[count];
        for (int i = 0; i < candidates.size(); i++) categories[i] = support.selectionCategory(values.get(i));
        List<Particle> selected = new ArrayList<>(), center = new ArrayList<>();
        boolean[] centerSlots = new boolean[55];
        for (int i = 0; i < count; i++) {
            checkpoint.run();
            Particle global = candidates.get(i), local = candidates.get(count + i);
            CenterTaskState.Owner owner = CenterTaskState.owner(global.current);
            CenterTaskState.requireSameOwner(owner, CenterTaskState.owner(local.current));
            CenterTaskDecisions.requireFamily(global.current, local.current);
            if (categories[i] != categories[i + count]) throw new AssertionError("Family category changed inside slot");
            boolean chooseLocal;
            if (owner.role == Direction.CENTER) {
                if (centerSlots[owner.slot]) throw new AssertionError("Duplicated CENTER slot at retention");
                centerSlots[owner.slot] = true;
                chooseLocal = CenterTaskState.scalar()
                        ? CenterTaskState.score(local.current, owner, ideal) < CenterTaskState.score(global.current, owner, ideal)
                        : fitness[i + count] < fitness[i];
                CenterTaskAudit.comparison("RETENTION", owner, ideal, global.current, local.current, chooseLocal);
            } else chooseLocal = local.current.getObjective(owner.role.objective()) < global.current.getObjective(owner.role.objective());
            int index = chooseLocal ? i + count : i;
            indices[i] = index; selected.add(candidates.get(index)); used[categories[index]]++;
            if (owner.role == Direction.CENTER) center.add(candidates.get(index));
            CenterTaskState.count("endGlobalLocalPairs"); if (chooseLocal) CenterTaskState.count("endLocalRetained");
        }
        if (center.size() != 55 || !java.util.Arrays.equals(used, quotas))
            throw new AssertionError("CENTER ownership or original80/5/5/5/5quota changed");
        CenterTaskState.count("completeTaskRetentions"); CenterTaskState.event("AFTER_RETENTION", center);
        return new SurvivorSelection.Result(selected, indices, fitness, categories, quotas);
    }
}
