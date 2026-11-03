package org.uma.jmetal.util.research.mechanism;

import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import org.uma.jmetal.util.research.search.Direction;
import org.uma.jmetal.util.research.search.SearchConfig;

/** A policy adapter must call exactly the previously tested proposal kernel. No evaluations. */
public final class JobAlignedPolicyChecks {
    private JobAlignedPolicyChecks() { }
    public static void main(String[] args) {
        SeededRandom.reset(17);
        KernelCheckFixture fixture = new KernelCheckFixture(true);
        PermutationSolution<Integer> parent = fixture.solution(new int[] {0, 1, 2, 3}, 0);
        PermutationSolution<Integer> personal = fixture.solution(new int[] {2, 1, 3, 0}, 1);
        PermutationSolution<Integer> global = fixture.solution(new int[] {3, 2, 0, 1}, 0);
        String saved = KernelCheckFixture.fingerprint(parent);
        SearchConfig config = new SearchConfig(); config.mergeGlobalLocal = true; config.paperResourceOperators = true;
        JobAlignedPolicy policy = new JobAlignedPolicy(fixture.instance, config);
        KernelVariants reference = new KernelVariants(fixture.instance, config, () -> { });
        for (int seed = 0; seed < 64; seed++) {
            SeededRandom.reset(seed);
            PermutationSolution<Integer> expected = reference.child("JOB_ALIGNED", parent, personal, global);
            long nextExpected = SeededRandom.current().nextLong();
            SeededRandom.reset(seed);
            PermutationSolution<Integer> actual = policy.propose(parent, personal, global, Direction.CENTER);
            require(KernelCheckFixture.fingerprint(expected).equals(KernelCheckFixture.fingerprint(actual)), "Adapter changed kernel");
            require(nextExpected == SeededRandom.current().nextLong(), "Adapter consumed RNG");
            require(saved.equals(KernelCheckFixture.fingerprint(parent)), "Parent changed");
        }
        require(policy.proposals() == 64, "Unobservable policy applications");
        boolean rejected = false;
        try { new JobAlignedPolicy(fixture.instance, new SearchConfig()); } catch (IllegalArgumentException expected) { rejected = true; }
        require(rejected, "Non-SO profile was accepted");
        System.out.println("JOB_ALIGNED_POLICY_CHECKS_PASS FE=0;64 exact kernel/RNG cases;parent unchanged;explicit SO guard");
    }
    private static void require(boolean condition, String message) { if (!condition) throw new AssertionError(message); }
}
