package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;

/** Isolated local acceptance. Production Direction and global leader selection remain untouched. */
public final class LocalPddrKernel {
    private enum Mode { LEGACY, AUDIT, LINEAR }
    private static final Mode MODE = Mode.valueOf(System.getProperty("research.pddr.mode", "LEGACY"));
    private static long audited, ties;
    private LocalPddrKernel() {}

    static boolean better(Direction direction, PermutationSolution<Integer> candidate,
            PermutationSolution<Integer> incumbent, List<PermutationSolution<Integer>> reference) {
        if (direction == Direction.CENTER && CenterTaskState.scalar())
            return CenterTaskDecisions.localBetter(candidate, incumbent);
        if (direction == Direction.MAKESPAN) return MakespanTiePolicy.better(candidate,incumbent);
        if (direction != Direction.CENTER || MODE == Mode.LEGACY)
            return direction.better(candidate, incumbent, reference);
        return linear(candidate, incumbent, reference, MODE == Mode.AUDIT);
    }

    private static boolean linear(PermutationSolution<Integer> c, PermutationSolution<Integer> i,
            List<PermutationSolution<Integer>> reference, boolean audit) {
        int pC = 0, qC = 0, pI = 0, qI = 0;
        for (PermutationSolution<Integer> r : reference) {
            if (ParetoTools.dominates(c, r)) pC++;
            if (ParetoTools.dominates(r, c)) qC++;
            if (ParetoTools.dominates(i, r)) pI++;
            if (ParetoTools.dominates(r, i)) qI++;
        }
        if (ParetoTools.dominates(c, i)) { pC++; qI++; }
        if (ParetoTools.dominates(i, c)) { pI++; qC++; }
        double candidate = qC + 1.0 / (pC + 1), incumbent = qI + 1.0 / (pI + 1);
        if (audit) check(c, i, reference, candidate, incumbent);
        return candidate < incumbent;
    }

    private static void check(PermutationSolution<Integer> c, PermutationSolution<Integer> i,
            List<PermutationSolution<Integer>> reference, double candidate, double incumbent) {
        List<PermutationSolution<Integer>> legacyPool = new ArrayList<>(reference);
        legacyPool.add(i); legacyPool.add(c);
        double[] old = ParetoTools.fitness(legacyPool);
        int n = old.length;
        if (Double.doubleToLongBits(old[n - 1]) != Double.doubleToLongBits(candidate)
                || Double.doubleToLongBits(old[n - 2]) != Double.doubleToLongBits(incumbent)
                || (old[n - 1] < old[n - 2]) != (candidate < incumbent))
            throw new AssertionError("PDDR score/decision mismatch, comparison=" + audited);
        audited++;
        if (candidate == incumbent) ties++;
    }

    public static void selfCheck(PermutationSolution<Integer> template) {
        List<PermutationSolution<Integer>> points = new ArrayList<>();
        for (double[] v : new double[][] {{0,0,0}, {1,1,1}, {0,1,2}, {2,0,1}, {1,1,1}}) {
            PermutationSolution<Integer> s = ParetoTools.copy(template);
            for (int j = 0; j < 3; j++) s.setObjective(j, v[j]);
            points.add(s);
        }
        for (PermutationSolution<Integer> c : points) for (PermutationSolution<Integer> i : points) {
            linear(c, i, points, true);
            linear(c, i, java.util.Collections.emptyList(), true);
        }
        audited = ties = 0;
    }

    public static Map<String, Object> diagnostics() {
        Map<String, Object> out = new java.util.LinkedHashMap<>();
        out.put("mode", MODE.name()); out.put("auditedCenterComparisons", audited);
        out.put("auditedTies", ties); out.put("scoreAndDecisionMismatches", 0);
        return out;
    }
}
