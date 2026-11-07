package org.uma.jmetal.util.research.search;

import java.util.Arrays;
import java.util.List;
import java.util.Random;
import org.uma.jmetal.problem.PermutationProblem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.impl.DefaultIntegerPermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.SchedulingProblemData;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.model.ModelKind;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Fixed-random operator checks; no scheduling evaluation or performance search is run. */
public final class ResourceSemanticsChecks {
    private ResourceSemanticsChecks() { }

    public static void main(String[] args) {
        SeededRandom.reset(17);
        if (args.length > 0 && args[0].equals("--legacy-fixtures")) {
            printLegacyFixtures();
            return;
        }
        checkClosedSegments();
        checkRandomRepairs();
        checkIndependentTriggers();
        checkFactoryMutationEvents();
        checkTeachersAndChapterGuard();
        checkSingleJob();
        System.out.println("RESOURCE_SEMANTICS_CHECKS_PASS (operator contracts only; no quality claim)");
    }

    private static void checkClosedSegments() {
        Instance in = instance(4, 5, new int[] {3, 3}, new int[] {3, 3});
        for (int vector = 0; vector < 3; vector++) {
            for (int first = 0; first < in.jobs(); first++) for (int second = 0; second < in.jobs(); second++) {
                PermutationSolution<Integer> child = solution(in, false), donor = solution(in, true);
                String originalDonor = fingerprint(donor);
                ScriptedRandom random = new ScriptedRandom(triggers(vector), 5, first, 5, second);
                PaperResourceOperators.apply(child, donor, in, config(), random);
                random.finished();
                int low = Math.min(first, second), high = Math.max(first, second);
                for (int p = 0; p < in.jobs(); p++) {
                    int expected = p >= low && p <= high ? 1 : 0;
                    require(resourceVector(child, vector).get(p) == expected, "Closed segment boundary/vector mismatch");
                    require(child.getVariableValue(p) == p, "Resource crossover changed positional JS");
                    for (int other = 0; other < 3; other++) if (other != vector) {
                        require(resourceVector(child, other).get(p) == 0, "Crossover changed another resource vector");
                    }
                }
                require(originalDonor.equals(fingerprint(donor)), "Crossover changed its donor");
            }
        }
        System.out.println("PASS 75 FA/MA/WA endpoint pairs, reversed/equal/full intervals, positional JS and donor immutability");
    }

    private static void checkRandomRepairs() {
        Instance in = instance(4, 5, new int[] {2, 4}, new int[] {2, 3});
        PermutationSolution<Integer> child = solution(in, true), donor = solution(in, false);
        ParticleOperators.machines(child).set(2, 3); child.setVariableValueworker(2, 2);
        apply(child, donor, in, triggers(0), 5, 2, 5, 2, 2, 0, 2, 1);
        require(child.getVariableValueid(2) == 0 && ParticleOperators.machines(child).get(2) == 0
                && child.getVariableValueworker(2) == 1, "FA segment did not randomly redraw both invalid resources");

        child = solution(in, true); // Both old values remain legal after moving from factory 1 to 0.
        apply(child, donor, in, triggers(0), 5, 2, 5, 2);
        require(ParticleOperators.machines(child).get(2) == 1 && child.getVariableValueworker(2) == 1,
                "FA crossover redrew resources that were already legal");

        child = solution(in, false); donor = solution(in, true);
        ParticleOperators.machines(donor).set(1, 3); donor.setVariableValueworker(1, 2);
        apply(child, donor, in, triggers(1), 5, 1, 5, 1, 2, 0);
        require(ParticleOperators.machines(child).get(1) == 0 && child.getVariableValueworker(1) == 0,
                "MA crossover random repair affected WA or used an invalid machine");
        apply(child, donor, in, triggers(2), 5, 1, 5, 1, 2, 1);
        require(child.getVariableValueworker(1) == 1, "WA crossover filtered a different-FA donor or skipped random repair");
        System.out.println("PASS random legal repairs after FA/MA/WA segments and no FA-equality filter for WA");
    }

    private static void checkIndependentTriggers() {
        Instance in = instance(4, 5, new int[] {3, 3}, new int[] {3, 3});
        for (int trigger = 0; trigger < 6; trigger++) {
            PermutationSolution<Integer> child = solution(in, false), donor = solution(in, true);
            int[] draws = trigger < 3 ? new int[] {5, 2, 5, 2}
                    : trigger == 3 ? new int[] {5, 2, 2, 1, 3, 2, 3, 2} : new int[] {5, 2, 3, 2};
            apply(child, donor, in, triggers(trigger), draws);
            for (int vector = 0; vector < 3; vector++) {
                int expected = trigger == vector ? 1 : trigger == 3 ? (vector == 0 ? 1 : 2)
                        : trigger == vector + 3 ? 2 : 0;
                require(resourceVector(child, vector).get(2) == expected, "Six independent trigger mapping mismatch");
            }
        }
        double[] none = {.9, .9, .9, .9, .9, .9};
        PermutationSolution<Integer> child = solution(in, false), donor = solution(in, true);
        String original = fingerprint(child);
        apply(child, donor, in, none);
        require(original.equals(fingerprint(child)), "Disabled triggers changed the particle");
        System.out.println("PASS six separately controlled triggers drawn before operation arguments, plus no-event case");
    }

    private static void checkFactoryMutationEvents() {
        Instance in = instance(4, 5, new int[] {3, 3}, new int[] {3, 3});
        for (int factory = 0; factory < 2; factory++) {
            PermutationSolution<Integer> child = solution(in, false), donor = solution(in, true);
            apply(child, donor, in, triggers(3), 5, 2, 2, factory, 3, 1, 3, 2);
            require(child.getVariableValueid(2) == factory && ParticleOperators.machines(child).get(2) == 1
                    && child.getVariableValueworker(2) == 2, "FA event did not redraw previously legal MA/WA");
        }
        for (int trigger = 3; trigger < 6; trigger++) {
            PermutationSolution<Integer> child = solution(in, false), donor = solution(in, true);
            int[] draws = trigger == 3 ? new int[] {5, 2, 2, 0, 3, 0, 3, 0} : new int[] {5, 2, 3, 0};
            String original = fingerprint(child);
            apply(child, donor, in, triggers(trigger), draws);
            require(original.equals(fingerprint(child)), "A legal self draw was rejected or changed another value");
        }
        System.out.println("PASS FA events redraw MA/WA for unchanged/new factories; all three mutations permit original values");
    }

    private static void checkTeachersAndChapterGuard() {
        Instance in = instance(4, 5, new int[] {2, 4}, new int[] {2, 3});
        PermutationSolution<Integer> parent = solution(in, false), personal = solution(in, true), global = solution(in, false);
        parent.setVariableValueid(4, 1); personal.setVariableValueid(4, 0); global.setVariableValueid(4, 1);
        String original = fingerprint(parent) + fingerprint(personal) + fingerprint(global);
        SearchConfig enabled = config(); enabled.paperResourceOperators = true;
        enabled.factoryCrossover = enabled.machineCrossover = enabled.workerCrossover = 1;
        enabled.factoryMutation = enabled.machineMutation = enabled.workerMutation = 1;
        ParticleOperators operators = new ParticleOperators(in, enabled.resolved(4));
        for (int i = 0; i < 50; i++) {
            PermutationSolution<Integer> child = operators.update(parent, personal, global);
            require(SchedulingEncoding.repair(child, in) == 0, "Final common repair left an infeasible resource/factory");
            require(original.equals(fingerprint(parent) + fingerprint(personal) + fingerprint(global)),
                    "An update changed the current/pbest/gbest parent");
        }

        Instance chapter3 = instance(3, 6, new int[] {3, 3}, new int[] {3, 3});
        parent = solution(chapter3, false); personal = solution(chapter3, true); global = solution(chapter3, false);
        SearchConfig disabled = config().resolved(3); enabled = config().resolved(3); enabled.paperResourceOperators = true;
        try {
            enabled.resolved(3);
            throw new AssertionError("Chapter 3 config accepted the O flag");
        } catch (IllegalArgumentException expected) { }
        SeededRandom.reset(741);
        String oldPath = fingerprint(new ParticleOperators(chapter3, disabled).update(parent, personal, global))
                + ";next=" + SeededRandom.current().nextDouble();
        SeededRandom.reset(741);
        String flaggedPath = fingerprint(new ParticleOperators(chapter3, enabled).update(parent, personal, global))
                + ";next=" + SeededRandom.current().nextDouble();
        require(oldPath.equals(flaggedPath), "The O flag changed the chapter 3 path or random calls");
        try {
            PaperResourceOperators.apply(parent, personal, chapter3, config(), new Random(1));
            throw new AssertionError("Direct chapter 3 resource-kernel call was accepted");
        } catch (IllegalArgumentException expected) { }
        System.out.println("PASS 50 updates preserve all parents/final feasibility; chapter 3 flag is inert and direct misuse is rejected");
    }

    private static void checkSingleJob() {
        Instance in = instance(4, 1, new int[] {1}, new int[] {1});
        PermutationSolution<Integer> child = solution(in, false), donor = solution(in, false);
        double[] all = {.1, .1, .1, .1, .1, .1};
        apply(child, donor, in, all, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0,
                1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0);
        require(SchedulingEncoding.repair(child, in) == 0, "N=1 operator result is infeasible");
        SearchConfig enabled = config(); enabled.paperResourceOperators = true;
        require(SchedulingEncoding.repair(new ParticleOperators(in, enabled.resolved(4)).update(child, donor, donor), in) == 0,
                "N=1 full update failed");
        System.out.println("PASS N=1/F=1/single-resource full and fixed-random updates");
    }

    private static void printLegacyFixtures() {
        for (int chapter : new int[] {3, 4}) for (long seed : new long[] {1, 271828, 314159}) {
            Instance in = instance(chapter, chapter == 3 ? 6 : 5, new int[] {2, 4},
                    chapter == 3 ? new int[] {2, 4} : new int[] {1, 3});
            SeededRandom.reset(seed);
            ToyProblem problem = new ToyProblem(in);
            PermutationSolution<Integer> parent = problem.createSolution(), personal = problem.createSolution(), global = problem.createSolution();
            ParticleOperators operators = new ParticleOperators(in, new SearchConfig().resolved(chapter));
            for (int i = 0; i < 20; i++) parent = operators.update(parent, personal, global);
            System.out.println("chapter=" + chapter + ";seed=" + seed + ";" + fingerprint(parent)
                    + ";next=" + SeededRandom.current().nextDouble());
        }
    }

    private static SearchConfig config() {
        SearchConfig config = new SearchConfig();
        config.factoryCrossover = config.machineCrossover = config.workerCrossover = .5;
        config.factoryMutation = config.machineMutation = config.workerMutation = .5;
        return config;
    }

    private static double[] triggers(int selected) {
        double[] values = {.9, .9, .9, .9, .9, .9}; values[selected] = .1; return values;
    }

    private static void apply(PermutationSolution<Integer> child, PermutationSolution<Integer> donor,
            Instance in, double[] triggers, int... draws) {
        ScriptedRandom random = new ScriptedRandom(triggers, draws);
        PaperResourceOperators.apply(child, donor, in, config(), random);
        random.finished();
    }

    private static List<Integer> resourceVector(PermutationSolution<Integer> solution, int vector) {
        return vector == 0 ? solution.getVariablesid() : vector == 1 ? ParticleOperators.machines(solution)
                : solution.getVariablesworker();
    }

    private static String fingerprint(PermutationSolution<Integer> solution) {
        return solution.getVariables() + ";FA=" + solution.getVariablesid() + ";MA="
                + ParticleOperators.machines(solution) + ";WA=" + solution.getVariablesworker();
    }

    private static PermutationSolution<Integer> solution(Instance in, boolean donor) {
        PermutationSolution<Integer> solution = new ToyProblem(in).createSolution();
        for (int p = 0; p < in.jobs(); p++) {
            solution.setVariableValue(p, p);
            solution.setVariableValueid(p, donor ? 1 : 0);
            ParticleOperators.machines(solution).set(p, donor ? 1 : 0);
        }
        if (in.kind() == ModelKind.CHAPTER3_FIXED_WORKER) {
            int offset = 0;
            for (int f = 0; f < in.factories(); f++) for (int w = 0; w < in.workers(f, 0); w++) {
                solution.setVariableValueworker(offset++, donor ? in.workers(f, 0) - w - 1 : w);
            }
        } else for (int p = 0; p < in.jobs(); p++) solution.setVariableValueworker(p, donor ? 1 : 0);
        return solution;
    }

    private static Instance instance(int chapter, int jobs, int[] machines, int[] workers) {
        double[][] processing = new double[jobs][1], setup = new double[jobs][1];
        for (double[] row : processing) row[0] = 1;
        double[][][] machineValues = resourceValues(machines), workerValues = resourceValues(workers);
        return new Instance("resource-semantics-check", chapter == 3 ? ModelKind.CHAPTER3_FIXED_WORKER
                : ModelKind.CHAPTER4_DUAL_RESOURCE, processing, setup, machineValues, machineValues,
                machineValues, workerValues, workerValues, "independent fixed-random operator check");
    }

    private static double[][][] resourceValues(int[] counts) {
        double[][][] values = new double[counts.length][1][];
        for (int f = 0; f < counts.length; f++) {
            values[f][0] = new double[counts[f]]; Arrays.fill(values[f][0], 1);
        }
        return values;
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static final class ScriptedRandom extends Random {
        private static final long serialVersionUID = 1L;
        private final double[] triggers;
        private final int[] draws;
        private int triggerCursor, drawCursor;
        ScriptedRandom(double[] triggers, int... draws) { this.triggers = triggers; this.draws = draws; }
        @Override public double nextDouble() {
            require(drawCursor == 0 && triggerCursor < 6, "Triggers were not six independent initial draws");
            return triggers[triggerCursor++];
        }
        @Override public int nextInt(int bound) {
            require(triggerCursor == 6 && drawCursor + 1 < draws.length, "Unexpected integer random call");
            int expectedBound = draws[drawCursor++], value = draws[drawCursor++];
            require(bound == expectedBound && value >= 0 && value < bound, "Wrong uniform sampling bound");
            return value;
        }
        void finished() { require(triggerCursor == 6 && drawCursor == draws.length, "Random draws were skipped"); }
    }

    private static final class ToyProblem implements PermutationProblem<PermutationSolution<Integer>>, SchedulingProblemData {
        private static final long serialVersionUID = 1L;
        private final Instance instance;
        ToyProblem(Instance instance) { this.instance = instance; }
        @Override public PermutationSolution<Integer> createSolution() { return new DefaultIntegerPermutationSolution(this); }
        @Override public void evaluate(PermutationSolution<Integer> solution) { throw new AssertionError("No FE allowed in operator checks"); }
        @Override public int getNumberOfVariables() { return instance.jobs(); }
        @Override public int getPermutationLength() { return instance.jobs(); }
        @Override public int getNumberOfFactories() { return instance.factories(); }
        @Override public int getNumberOfObjectives() { return 3; }
        @Override public int getNumberOfConstraints() { return 0; }
        @Override public String getName() { return "ResourceSemanticsChecks"; }
        @Override public Instance getSchedulingInstance() { return instance; }
        @Override public String getInstanceFile() { return "synthetic-resource-check"; }
        @Override public int getWorkerVectorLength() {
            if (instance.kind() == ModelKind.CHAPTER4_DUAL_RESOURCE) return instance.jobs();
            int total = 0;
            for (int f = 0; f < instance.factories(); f++) total += instance.workers(f, 0);
            return total;
        }
    }
}
