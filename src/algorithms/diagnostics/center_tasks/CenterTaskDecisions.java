package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;

/** One coherent task criterion for personal memory, global progress, local comparison and Q credit. */
final class CenterTaskDecisions {
    private CenterTaskDecisions() { }

    static PermutationSolution<Integer> personal(Particle particle, Direction preference) {
        if (!CenterTaskState.scalar() || preference != Direction.CENTER) return particle.personalBest(preference);
        CenterTaskState.Owner owner = CenterTaskState.owner(particle.current);
        if (owner.role != Direction.CENTER) return particle.personalBest(preference);
        double[] ideal = CenterTaskState.ideal();
        PermutationSolution<Integer> best = null; double minimum = Double.POSITIVE_INFINITY;
        for (PermutationSolution<Integer> point : particle.personalArchive()) {
            double value = CenterTaskState.score(point, owner, ideal);
            if (value < minimum) { best = point; minimum = value; }
        }
        if (best == null) throw new AssertionError("Empty task personal history");
        CenterTaskAudit.personal(owner, ideal, particle.personalArchive(), best);
        CenterTaskState.count("taskPersonalQueries"); return ParetoTools.copy(best);
    }

    static List<Particle> global(List<Particle> parents, List<Particle> children, Direction role) {
        if (parents.size() != children.size() || role != Direction.CENTER) throw new AssertionError("Invalid task batch");
        List<Particle> result = new ArrayList<>();
        double[] ideal = CenterTaskState.ideal(), pddr = null;
        if (!CenterTaskState.scalar()) {
            List<PermutationSolution<Integer>> pool = new ArrayList<>();
            for (Particle p : parents) pool.add(p.current);
            for (Particle p : children) pool.add(p.current);
            pddr = ParetoTools.fitness(pool);
        }
        for (int i = 0; i < parents.size(); i++) {
            Particle parent = parents.get(i), child = children.get(i);
            CenterTaskState.Owner owner = CenterTaskState.owner(parent.current);
            CenterTaskState.requireSameOwner(owner, CenterTaskState.owner(child.current));
            requireFamily(parent.current, child.current);
            boolean improve = CenterTaskState.scalar()
                    ? CenterTaskState.score(child.current, owner, ideal) < CenterTaskState.score(parent.current, owner, ideal)
                    : pddr[i + parents.size()] < pddr[i];
            CenterTaskAudit.comparison("GLOBAL", owner, ideal, parent.current, child.current, improve);
            result.add(improve ? child : parent);
            CenterTaskState.count("centerGlobalPairs"); if (improve) CenterTaskState.count("centerGlobalChildrenRetained");
        }
        return result;
    }

    static double reward(List<Particle> before, List<Particle> after, Direction role) {
        if (!CenterTaskState.scalar() || role != Direction.CENTER) return GroupReward.compute(before, after, role);
        double[] ideal = CenterTaskState.ideal(); double total = 0;
        for (int i = 0; i < before.size(); i++) {
            CenterTaskState.Owner owner = CenterTaskState.owner(before.get(i).current);
            CenterTaskState.requireSameOwner(owner, CenterTaskState.owner(after.get(i).current));
            double old = CenterTaskState.score(before.get(i).current, owner, ideal);
            double next = CenterTaskState.score(after.get(i).current, owner, ideal);
            total += (old - next) / Math.max(Math.abs(old), 1e-12);
        }
        CenterTaskState.count("taskGroupRewards"); return total / before.size();
    }

    static boolean localBetter(PermutationSolution<Integer> candidate, PermutationSolution<Integer> incumbent) {
        CenterTaskState.Owner owner = CenterTaskState.activeLocal;
        if (owner == null || owner.role != Direction.CENTER) throw new AssertionError("No active CENTER task");
        double[] ideal = CenterTaskState.ideal(); CenterTaskState.count("taskLocalComparisons");
        boolean improve = CenterTaskState.score(candidate, owner, ideal) < CenterTaskState.score(incumbent, owner, ideal);
        CenterTaskAudit.comparison("LOCAL", owner, ideal, incumbent, candidate, improve);
        if (improve) CenterTaskState.count("taskLocalBetter"); return improve;
    }

    static void requireFamily(PermutationSolution<Integer> first, PermutationSolution<Integer> second) {
        Object a = first.getAttribute("cooperation.family"), b = second.getAttribute("cooperation.family");
        if (!(a == null ? b == null : a.equals(b))) throw new AssertionError("Task crossed a fixedFA family category");
    }
}
