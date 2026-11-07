package org.uma.jmetal.util.research.classic;

import java.util.ArrayList;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.joint.JointCheckProblem;
import org.uma.jmetal.util.research.model.DynamicDecoder;
import org.uma.jmetal.util.research.model.DynamicSchedule;
import org.uma.jmetal.util.research.runtime.RunContext;

final class ClassicRuntimeChecks {
    private static final String[] MODES = {"NSGA2_4V", "SPEA2_4V", "MOEAD_4V", "NSGA2_VNS_4V"};
    private ClassicRuntimeChecks() { }
    static void run() {
        rejectBareProblem();
        for (String mode : MODES) {
            for (int cap : new int[] {0,1,99,100,101,149,150,151,251,351}) budget(mode, cap);
            String first = replay(mode), second = replay(mode);
            ClassicChecks.require(first.equals(second), mode + " fixed seed complete archive/diagnostic mismatch");
            failure(mode); time(mode);
            System.out.println("CLASSIC_RUNTIME_PASS " + mode + " FE-boundaries=0,1,99,100,101,149,150,151,251,351 seed=7319 replayFE=333 failure-at=102 time-limit=0.02s");
        }
    }
    private static void rejectBareProblem() {
        Fixture fixture = new Fixture();
        for (String mode : MODES) {
            try {
                new ClassicAlgorithm(fixture, fixture.problem.instance, new ClassicConfig(mode,0), () -> { });
                throw new AssertionError("Classic constructor accepted a bare Problem");
            } catch (IllegalArgumentException expected) {
                ClassicChecks.require(expected.getMessage().contains("BudgetedProblem"), "Wrong bare-Problem rejection");
            }
        }
        System.out.println("CLASSIC_ENTRY_GUARD_PASS four-modes-reject-bare-Problem");
    }
    private static void budget(String mode, int cap) {
        Fixture fixture = new Fixture();
        RunContext<PermutationSolution<Integer>> context = new RunContext<>(fixture, cap, 20261101);
        fixture.raw.setCheckpoint(context::checkpoint);
        ClassicAlgorithm algorithm = new ClassicAlgorithm(context.problem(), fixture.problem.instance, new ClassicConfig(mode, 0), context::checkpoint);
        context.run(algorithm);
        ClassicChecks.require("FE_LIMIT".equals(context.stopReason()), mode + " budget stop reason");
        ClassicChecks.require(context.budget().attempted() == cap && context.budget().successful() == cap
                && context.budget().failed() == 0 && fixture.evaluations == cap, mode + " exact paid FE");
        ClassicChecks.require(fixture.raw.diagnostics().get("dynamic.evaluations") == cap, mode + " decoder/guard FE mismatch");
        ClassicChecks.require(fixture.created == Math.min(100, cap), mode + " initialization must use guarded creation only");
        Map<String,Object> diagnostic = algorithm.diagnostics();
        long global = number(diagnostic, "global.evaluations"), initialized = number(diagnostic, "initialization.evaluations");
        long local = 0;
        if (diagnostic.containsKey("ordinaryVns")) {
            @SuppressWarnings("unchecked") Map<String,Long> vns = (Map<String,Long>) diagnostic.get("ordinaryVns");
            local = vns.getOrDefault("inter.evaluations",0L) + vns.getOrDefault("intra.evaluations",0L);
            ClassicChecks.require(vns.get("calls") == global / 50, "VNS cadence must count only global offspring");
            ClassicChecks.require(vns.getOrDefault("intra.evaluations",0L) <= 30 * vns.get("calls"), "VNS intra cap");
        }
        ClassicChecks.require(initialized + global + local == cap, mode + " hidden/unaccounted evaluations");
        if ("MOEAD_4V".equals(mode) && cap > 100) {
            ClassicChecks.require(number(diagnostic, "idealPaidUpdates") == global, "MOEAD ideal updated only by own paid offspring");
            ClassicChecks.require(number(diagnostic, "maximumReplacementsPerChild") <= 2, "MOEAD replacement cap");
        }
        fixture.verifyUnchanged();
        verifyResults(context.result(), fixture);
        if (!algorithm.getResult().isEmpty()) {
            List<PermutationSolution<Integer>> copy = algorithm.getResult(); String original = signature(algorithm.getResult().get(0));
            copy.get(0).setVariableValue(0, -100);
            ClassicChecks.require(signature(algorithm.getResult().get(0)).equals(original), "Returned population aliases internal storage");
        }
    }
    private static String replay(String mode) {
        Fixture fixture = new Fixture(); RunContext<PermutationSolution<Integer>> context = new RunContext<>(fixture, 333, 7319);
        fixture.raw.setCheckpoint(context::checkpoint);
        ClassicAlgorithm algorithm = new ClassicAlgorithm(context.problem(), fixture.problem.instance, new ClassicConfig(mode, 0), context::checkpoint);
        context.run(algorithm); List<String> signatures = new ArrayList<>();
        for (PermutationSolution<Integer> solution : context.result()) signatures.add(signature(solution));
        Collections.sort(signatures); verifyResults(context.result(), fixture);
        return signatures.toString() + algorithm.diagnostics().toString();
    }
    private static void failure(String mode) {
        Fixture fixture = new Fixture(); RuntimeException expected = new IllegalStateException("expected decoder failure");
        fixture.failure = expected; fixture.failAt = 102;
        RunContext<PermutationSolution<Integer>> context = new RunContext<>(fixture, 500, 9201);
        fixture.raw.setCheckpoint(context::checkpoint);
        ClassicAlgorithm algorithm = new ClassicAlgorithm(context.problem(), fixture.problem.instance, new ClassicConfig(mode,0), context::checkpoint);
        try { context.run(algorithm); throw new AssertionError("Decoder failure swallowed"); }
        catch (RuntimeException actual) { ClassicChecks.require(actual == expected, "Decoder exception identity changed"); }
        ClassicChecks.require(context.budget().attempted() == 102 && context.budget().successful() == 101
                && context.budget().failed() == 1 && "FAILED".equals(context.stopReason()), "Failed evaluation billing");
    }
    private static void time(String mode) {
        Fixture fixture = new Fixture(); RunContext<PermutationSolution<Integer>> context = new RunContext<>(fixture, 1000000, 881, .02);
        fixture.raw.setCheckpoint(context::checkpoint);
        ClassicAlgorithm algorithm = new ClassicAlgorithm(context.problem(), fixture.problem.instance, new ClassicConfig(mode,0), context::checkpoint);
        context.run(algorithm);
        ClassicChecks.require("TIME_LIMIT".equals(context.stopReason()), mode + " wall-clock interruption");
        ClassicChecks.require(context.budget().attempted() == context.budget().successful() + context.budget().failed(), "Interrupted accounting");
        verifyResults(context.result(), fixture);
    }
    private static long number(Map<String,Object> values, String key) {
        Object result = values.get(key); return result == null ? 0 : ((Number) result).longValue();
    }
    private static void verifyResults(List<PermutationSolution<Integer>> result, Fixture fixture) {
        for (PermutationSolution<Integer> solution : result) {
            legal(solution, fixture.problem);
            DynamicSchedule full = DynamicDecoder.full(fixture.problem.instance, fixture.problem.parameters,
                    SchedulingEncoding.integers(solution.getVariables()), SchedulingEncoding.integers(solution.getVariablesid()),
                    SchedulingEncoding.machineIntegers(solution), SchedulingEncoding.integers(solution.getVariablesworker()), null);
            for (int m = 0; m < 3; m++) ClassicChecks.close(solution.getObjective(m), full.objectives()[m]);
        }
    }
    static void legal(PermutationSolution<Integer> solution, JointCheckProblem fixture) {
        boolean[] seen = new boolean[fixture.instance.jobs()], used = new boolean[fixture.instance.factories()];
        int[] machines = SchedulingEncoding.machineIntegers(solution);
        for (int p = 0; p < seen.length; p++) {
            int j = solution.getVariableValue(p), f = solution.getVariableValueid(p), w = solution.getVariableValueworker(p);
            ClassicChecks.require(j >= 0 && j < seen.length && !seen[j], "Invalid job permutation"); seen[j] = true;
            ClassicChecks.require(f >= 0 && f < used.length, "Invalid FA"); used[f] = true;
            ClassicChecks.require(machines[p] >= 0 && machines[p] < fixture.instance.machines(f,0), "Invalid local MA");
            ClassicChecks.require(w >= 0 && w < fixture.instance.workers(f,0), "Invalid local WA");
        }
        for (boolean present : used) ClassicChecks.require(present, "Empty factory after common repair");
    }
    static String signature(PermutationSolution<Integer> solution) {
        StringBuilder result = new StringBuilder();
        result.append(solution.getVariables()).append(solution.getVariablesid())
                .append(java.util.Arrays.toString(SchedulingEncoding.machineIntegers(solution))).append(solution.getVariablesworker());
        for (int m = 0; m < 3; m++) result.append('/').append(Double.toHexString(solution.getObjective(m)));
        return result.toString();
    }
    private static final class Fixture implements Problem<PermutationSolution<Integer>> {
        private static final long serialVersionUID = 1L;
        final JointCheckProblem problem = new JointCheckProblem(6);
        final DynamicEvaluation raw = new DynamicEvaluation(problem, problem.instance, problem.parameters, true);
        final IdentityHashMap<PermutationSolution<Integer>,String> evaluated = new IdentityHashMap<>();
        int created, evaluations, failAt = -1;
        RuntimeException failure;
        @Override public void evaluate(PermutationSolution<Integer> solution) {
            verifyUnchanged(); legal(solution, problem);
            ClassicChecks.require(!evaluated.containsKey(solution), "An evaluated parent was evaluated in place again");
            evaluations++; if (evaluations == failAt) throw failure;
            raw.evaluate(solution); evaluated.put(solution, signature(solution));
        }
        void verifyUnchanged() {
            for (Map.Entry<PermutationSolution<Integer>,String> item : evaluated.entrySet())
                ClassicChecks.require(item.getValue().equals(signature(item.getKey())), "An earlier paid parent was modified");
        }
        @Override public PermutationSolution<Integer> createSolution() { created++; return raw.createSolution(); }
        @Override public int getNumberOfVariables() { return raw.getNumberOfVariables(); }
        @Override public int getNumberOfObjectives() { return 3; }
        @Override public int getNumberOfConstraints() { return 0; }
        @Override public String getName() { return "classic-engineering-fixture"; }
    }
}
