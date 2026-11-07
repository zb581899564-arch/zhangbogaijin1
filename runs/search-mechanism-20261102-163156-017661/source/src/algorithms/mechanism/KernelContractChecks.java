package org.uma.jmetal.util.research.mechanism;

import java.lang.reflect.Constructor;
import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.List;
import java.util.Random;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.classic.ClassicConfig;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import org.uma.jmetal.util.research.search.ParticleOperators;
import org.uma.jmetal.util.research.search.SearchConfig;

/** FE0 hand mappings and exact unchanged-kernel regressions; not a quality experiment. */
public final class KernelContractChecks {
    private KernelContractChecks() { }

    public static void main(String[] args) throws Exception {
        SeededRandom.reset(191);
        checkSwapIdentity();
        checkSegmentJobMapping();
        checkFactoryMutationEvents();
        checkIdentityOrderAgainstPaper();
        checkOriginalKernelsAndParents();
        System.out.println("KERNEL_CONTRACT_CHECKS_PASS attemptedFE=0 successfulFE=0 failedFE=0"
                + " (single-proposal contracts only; no QGS or quality claim)");
    }

    private static SearchConfig config() {
        SearchConfig config = new SearchConfig(); config.paperResourceOperators = true;
        return config.resolved(4);
    }

    private static void checkSwapIdentity() {
        KernelCheckFixture fixture = new KernelCheckFixture(true);
        PermutationSolution<Integer> parent = fixture.solution(new int[] {0, 1, 2, 3}, 0);
        int[][] original = KernelCheckFixture.byJob(parent);
        for (int first = 0; first < 4; first++) for (int second = 0; second < 4; second++) {
            PermutationSolution<Integer> child = copy(parent);
            JobAlignedPaperKernel.swapJobAndResources(child, first, second);
            require(Arrays.deepEquals(original, KernelCheckFixture.byJob(child)), "JS swap changed a job's resource tuple");
        }
        SearchConfig zero = config(); zero.randScale = 0;
        zero.factoryCrossover = zero.machineCrossover = zero.workerCrossover = 0;
        zero.factoryMutation = zero.machineMutation = zero.workerMutation = 0;
        JobAlignedPaperKernel kernel = new JobAlignedPaperKernel(fixture.instance, zero);
        for (long seed = 0; seed < 32; seed++) {
            SeededRandom.reset(seed);
            require(Arrays.deepEquals(original, KernelCheckFixture.byJob(kernel.child(parent, parent, parent))),
                    "No-resource-event update changed per-job resources");
        }
        System.out.println("PASS all 16 JS swaps and 32 no-resource-event updates preserve per-job FA/MA/WA");
    }

    private static void checkSegmentJobMapping() {
        KernelCheckFixture fixture = new KernelCheckFixture(false);
        PermutationSolution<Integer> donor = fixture.solution(new int[] {1, 3, 0, 2}, 1);
        int[][] donorGenes = KernelCheckFixture.byJob(donor);
        String frozenDonor = KernelCheckFixture.fingerprint(donor);
        SearchConfig config = halfProbabilities();
        for (int resource = 0; resource < 3; resource++) {
            for (int first = 0; first < 4; first++) for (int second = 0; second < 4; second++) {
                PermutationSolution<Integer> child = fixture.solution(new int[] {2, 0, 3, 1}, 0);
                int[][] before = KernelCheckFixture.byJob(child);
                ScriptedRandom random = new ScriptedRandom(resource, 4, first, 4, second);
                JobAlignedResources.apply(child, donor, fixture.instance, config, random); random.finished();
                for (int p = 0; p < 4; p++) for (int k = 0; k < 3; k++) {
                    int job = child.getVariableValue(p);
                    int expected = k == resource && p >= Math.min(first, second) && p <= Math.max(first, second)
                            ? donorGenes[job][k] : before[job][k];
                    require(KernelCheckFixture.byJob(child)[job][k] == expected, "Closed segment did not inherit donor's same-job gene");
                }
                require(child.getVariables().equals(Arrays.asList(2, 0, 3, 1)), "Resource crossover changed JS");
                require(frozenDonor.equals(KernelCheckFixture.fingerprint(donor)), "Resource crossover changed donor");
            }
        }
        System.out.println("PASS 48 closed FA/MA/WA intervals inherit by job across different JS permutations");
    }

    private static void checkFactoryMutationEvents() {
        KernelCheckFixture fixture = new KernelCheckFixture(false);
        SearchConfig config = halfProbabilities();
        for (int factory = 0; factory < 2; factory++) {
            PermutationSolution<Integer> child = fixture.solution(new int[] {2, 0, 3, 1}, 0);
            PermutationSolution<Integer> donor = copy(child);
            ScriptedRandom random = new ScriptedRandom(3, 4, 0, 2, factory, 4, 1, 4, 2);
            JobAlignedResources.apply(child, donor, fixture.instance, config, random); random.finished();
            require(child.getVariableValueid(0) == factory && JobAlignedResources.vector(child, true).get(0) == 1
                    && child.getVariableValueworker(0) == 2, "FA mutation must redraw MA/WA for current or different factory");
        }
        System.out.println("PASS FA mutations retain both unchanged-factory and changed-factory paper redraw rules");
    }

    private static void checkIdentityOrderAgainstPaper() throws Exception {
        KernelCheckFixture fixture = new KernelCheckFixture(true);
        PermutationSolution<Integer> parent = fixture.solution(new int[] {2, 0, 3, 1}, 0);
        PermutationSolution<Integer> donor = fixture.solution(new int[] {2, 0, 3, 1}, 1);
        Method original = Class.forName("org.uma.jmetal.util.research.search.PaperResourceOperators")
                .getDeclaredMethod("apply", PermutationSolution.class, PermutationSolution.class,
                        Instance.class, SearchConfig.class, Random.class);
        original.setAccessible(true);
        for (long seed = 0; seed < 128; seed++) {
            PermutationSolution<Integer> paper = copy(parent), aligned = copy(parent);
            Random paperRandom = new Random(seed), alignedRandom = new Random(seed);
            original.invoke(null, paper, donor, fixture.instance, config(), paperRandom);
            JobAlignedResources.apply(aligned, donor, fixture.instance, config(), alignedRandom);
            require(KernelCheckFixture.fingerprint(paper).equals(KernelCheckFixture.fingerprint(aligned))
                    && paperRandom.nextLong() == alignedRandom.nextLong(), "Identity-map variant changed paper resource rules/random consumption");
        }
        System.out.println("PASS 128 matching-JS resource updates exactly match original paper outputs and next RNG state");
    }

    private static void checkOriginalKernelsAndParents() throws Exception {
        KernelCheckFixture fixture = new KernelCheckFixture(true);
        RunContext<PermutationSolution<Integer>> context = new RunContext<>(fixture, 0, 419);
        PermutationSolution<Integer> parent = fixture.solution(new int[] {0, 1, 2, 3}, 0);
        PermutationSolution<Integer> personal = fixture.solution(new int[] {2, 3, 0, 1}, 1);
        PermutationSolution<Integer> global = fixture.solution(new int[] {3, 0, 1, 2}, 2);
        List<String> before = fingerprints(parent, personal, global);
        KernelVariants variants = new KernelVariants(fixture.instance, config(), context::checkpoint);
        for (long seed = 0; seed < 64; seed++) {
            comparePaper(variants, fixture.instance, seed, parent, personal, global);
            compareClassic(variants, fixture.instance, seed, parent, personal, global);
            for (String kernel : new String[] {KernelVariants.PAPER, KernelVariants.JOB_ALIGNED,
                    KernelVariants.CLASSIC_GLOBAL, KernelVariants.CLASSIC_PERSONAL}) {
                SeededRandom.reset(seed);
                PermutationSolution<Integer> child = variants.child(kernel, parent, personal, global);
                require(before.equals(fingerprints(parent, personal, global)), "Kernel changed a parent/objective: " + kernel);
                SchedulingEncoding.repair(child, fixture.instance);
                require(SchedulingEncoding.repair(child, fixture.instance) == 0, "Common repair is not idempotent: " + kernel);
                child.setVariableValue(0, -99); child.setVariableValueid(0, -99);
                JobAlignedResources.vector(child, true).set(0, -99); child.setVariableValueworker(0, -99);
                child.setObjective(0, -99);
                require(before.equals(fingerprints(parent, personal, global)), "Child aliases a parent: " + kernel);
            }
        }
        require(context.budget().attempted() == 0 && context.budget().successful() == 0 && context.budget().failed() == 0,
                "FE0 checks incurred a paid evaluation");
        System.out.println("PASS 64 PAPER/direct and both classic/direct comparisons including next RNG; 256 independent children keep parents immutable; FE=0");
    }

    private static void comparePaper(KernelVariants variants, Instance instance, long seed,
            PermutationSolution<Integer> parent, PermutationSolution<Integer> personal, PermutationSolution<Integer> global) {
        SeededRandom.reset(seed);
        String expected = KernelCheckFixture.fingerprint(new ParticleOperators(instance, config()).update(parent, personal, global));
        long next = SeededRandom.current().nextLong();
        SeededRandom.reset(seed);
        require(expected.equals(KernelCheckFixture.fingerprint(variants.child(KernelVariants.PAPER, parent, personal, global)))
                && next == SeededRandom.current().nextLong(), "PAPER differs from original operator");
    }

    @SuppressWarnings("unchecked")
    private static void compareClassic(KernelVariants variants, Instance instance, long seed,
            PermutationSolution<Integer> parent, PermutationSolution<Integer> personal, PermutationSolution<Integer> global) throws Exception {
        Class<?> original = Class.forName("org.uma.jmetal.util.research.classic.ClassicVariation");
        Constructor<?> constructor = original.getDeclaredConstructor(Instance.class, ClassicConfig.class, Runnable.class);
        constructor.setAccessible(true);
        Object variation = constructor.newInstance(instance, new ClassicConfig("NSGA2_4V", 0), (Runnable) () -> { });
        Method child = original.getDeclaredMethod("child", PermutationSolution.class, PermutationSolution.class); child.setAccessible(true);
        for (String kernel : new String[] {KernelVariants.CLASSIC_GLOBAL, KernelVariants.CLASSIC_PERSONAL}) {
            SeededRandom.reset(seed);
            String expected = KernelCheckFixture.fingerprint((PermutationSolution<Integer>) child.invoke(variation, parent,
                    KernelVariants.CLASSIC_GLOBAL.equals(kernel) ? global : personal));
            long next = SeededRandom.current().nextLong();
            SeededRandom.reset(seed);
            require(expected.equals(KernelCheckFixture.fingerprint(variants.child(kernel, parent, personal, global)))
                    && next == SeededRandom.current().nextLong(), "Classic bridge differs from unchanged kernel");
        }
    }

    private static SearchConfig halfProbabilities() {
        SearchConfig config = config();
        config.factoryCrossover = config.machineCrossover = config.workerCrossover = .5;
        config.factoryMutation = config.machineMutation = config.workerMutation = .5;
        return config;
    }

    private static List<String> fingerprints(PermutationSolution<Integer> parent,
            PermutationSolution<Integer> personal, PermutationSolution<Integer> global) {
        return Arrays.asList(KernelCheckFixture.fingerprint(parent), KernelCheckFixture.fingerprint(personal), KernelCheckFixture.fingerprint(global));
    }

    @SuppressWarnings("unchecked")
    private static PermutationSolution<Integer> copy(PermutationSolution<Integer> value) {
        return (PermutationSolution<Integer>) value.copy();
    }
    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    /** Six trigger doubles must be drawn first; then strict (bound,value) pairs. */
    private static final class ScriptedRandom extends Random {
        private static final long serialVersionUID = 1L;
        private final int selected;
        private final int[] draws;
        private int doubles, integers;
        ScriptedRandom(int selected, int... draws) { this.selected = selected; this.draws = draws; }
        @Override public double nextDouble() {
            require(doubles < 6 && integers == 0, "Trigger order/number changed");
            return doubles++ == selected ? .1 : .9;
        }
        @Override public int nextInt(int bound) {
            require(doubles == 6 && integers + 1 < draws.length && draws[integers] == bound, "Operator RNG bound/order changed");
            int value = draws[integers + 1]; integers += 2;
            require(value >= 0 && value < bound, "Invalid scripted value");
            return value;
        }
        void finished() { require(doubles == 6 && integers == draws.length, "Operator left unused scripted draws"); }
    }
}
