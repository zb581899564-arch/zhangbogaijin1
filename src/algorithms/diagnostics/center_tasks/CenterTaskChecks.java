package org.uma.jmetal.util.research.search;

import java.util.Arrays;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Zero-decoder scalarization/ownership fixtures. Physical correctness is checked by the real runs. */
public final class CenterTaskChecks {
    private CenterTaskChecks() { }

    public static void main(String[] args) throws Exception {
        System.setProperty("dhfsp.dataDir", args[0]); System.setProperty("dhfsp.setupFile", args[1]);
        System.setProperty("dhfsp.standbyPower", "1"); SeededRandom.reset(0);
        EDHHFSPW problem = new EDHHFSPW(20, 8, 5, 1);
        if (!CenterTaskState.scalar()) throw new AssertionError("Scalar fixture requires FIXED mode");
        Arrays.fill(CenterTaskState.IDEAL, 0.0); // Synthetic scalar fixture, not a paid search observation.
        CenterTaskState.Owner owner = new CenterTaskState.Owner(1, Direction.CENTER, 0, 0);
        PermutationSolution<Integer> first = point(problem, .2, .2, .2), second = point(problem, .9, .9, 0);
        first.setAttribute(CenterTaskState.KEY, owner); second.setAttribute(CenterTaskState.KEY, owner);
        if (Math.abs(CenterTaskState.score(first, owner, new double[3]) - 1.0 / 6) > 1e-12
                || Math.abs(CenterTaskState.score(second, owner, new double[3]) - .075) > 1e-12)
            throw new AssertionError("Fixed known Tchebycheff values differ");
        Particle particle = new Particle(first).descend(second);
        if (!Arrays.equals(CenterTaskDecisions.personal(particle, Direction.CENTER).getObjectives(), second.getObjectives()))
            throw new AssertionError("Task personal best ignored its target");
        double[] unchanged = second.getObjectives().clone();
        CenterTaskState.activeLocal = owner;
        if (!CenterTaskDecisions.localBetter(second, first) || CenterTaskDecisions.localBetter(first, second))
            throw new AssertionError("Task comparison reversed");
        CenterTaskLifecycle.localEnd();
        if (!Arrays.equals(unchanged, second.getObjectives())) throw new AssertionError("Scoring changed physics outputs");
        boolean rejected = false;
        try { CenterTaskState.requireSameOwner(owner, new CenterTaskState.Owner(1, Direction.CENTER, 1, 0)); }
        catch (AssertionError expected) { rejected = true; }
        if (!rejected || CenterTaskState.activeLocal != null) throw new AssertionError("Ownership/cleanup fixture failed");
        System.out.println("CENTER_TASK_FIXTURES_PASS exact scalar values; own target pbest; immutable objectives; slot mismatch; zeroFE zeroDecoderCalls");
    }

    private static PermutationSolution<Integer> point(EDHHFSPW source, double a, double b, double c) {
        PermutationSolution<Integer> value = source.createSolution();
        value.setObjective(0, a); value.setObjective(1, b); value.setObjective(2, c); return value;
    }
}
