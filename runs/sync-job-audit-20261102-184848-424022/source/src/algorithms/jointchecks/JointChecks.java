package org.uma.jmetal.util.research.joint;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import org.uma.jmetal.util.research.search.Direction;
import org.uma.jmetal.util.research.search.ParticleOperators;
import org.uma.jmetal.util.research.search.SearchConfig;

/** Focused synthetic engineering checks. These do not establish algorithm quality. */
public final class JointChecks {
    private JointChecks() { }
    public static void main(String[] args) {
        checkRidge(); checkWitness(); checkControlsAndGenotypes(); checkTraining(); checkObjectiveIsolation();
        System.out.println("JOINT_CHECKS_PASS ridge/episode weighting; compatible witnesses; heterogeneous legal tuples; "
                + "outside/parent/copy invariance; exact prefix replay; four controls; 63/64 and second cohort; batch freeze; no incomplete labels");
    }
    private static void checkRidge() {
        List<LinearValueModel.Sample> samples = new ArrayList<>();
        for (int x = -2; x <= 2; x++) samples.add(new LinearValueModel.Sample(new double[] {x}, 3 + 2 * x, 1));
        double[] fit = LinearValueModel.fit(samples, 1, () -> { }); close(fit[0], 3, 1e-12); close(fit[1], 2, .001);
        samples.clear();
        for (int s = 0; s < 4; s++) samples.add(new LinearValueModel.Sample(new double[] {0}, 0, .25));
        samples.add(new LinearValueModel.Sample(new double[] {0}, 10, 1));
        fit = LinearValueModel.fit(samples, 1, () -> { }); close(fit[0], 5, 1e-12); close(fit[1], 0, 1e-12);
        close(LinearValueModel.predict(new double[] {0, -1}, new double[] {2}), 0, 0);
        samples.add(new LinearValueModel.Sample(new double[] {Double.NaN}, 1, 1));
        boolean rejected = false;
        try { LinearValueModel.fit(samples, 1, () -> { }); } catch (IllegalArgumentException expected) { rejected = true; }
        require(rejected, "Non-finite regression feature accepted");
    }
    private static void checkWitness() {
        SeededRandom.reset(901); JointCheckProblem raw = new JointCheckProblem(3);
        PermutationSolution<Integer> parent = raw.createSolution();
        for (int p = 0; p < 3; p++) {
            parent.setVariableValue(p, p); parent.setVariableValueid(p, p);
            JointCheckProblem.machines(parent).set(p, 0); parent.setVariableValueworker(p, 0);
        }
        BlockContext block = new BlockContext(raw.instance, parent, 0, 3);
        JointAction migrated = new JointAction(0, 1, 2, 1);
        require(block.completable(migrated), "Temporary empty factory wrongly rejected");
        List<JointAction> next = block.afterWitness(migrated); block.commit(migrated, next);
        require(!block.completable(new JointAction(1, 1, 0, 0)), "Factory coverage dead-end accepted");
        while (block.remainingCount() > 0) {
            JointAction a = block.witness().get(0); block.commit(a, block.afterWitness(a));
        }
        PermutationSolution<Integer> child = block.child(parent); raw.evaluate(child);
        require(child.getVariableValueid(0) == 1 && child.getVariableValueid(1) == 0, "Compatible witness did not finish the cross-factory exchange");
        @SuppressWarnings("unchecked") PermutationSolution<Integer> copy = (PermutationSolution<Integer>) child.copy();
        require(genome(copy).equals(genome(child)), "Copy lost rewritten machine field/attribute correspondence");
        JointCheckProblem.machines(copy).set(0, 0); require(JointCheckProblem.machines(child).get(0) == 2, "Copy aliases machines");
        raw.evaluate(parent); List<PermutationSolution<Integer>> teachers = Arrays.asList(parent, parent, parent);
        JointPolicy policy = policy(raw, JointPolicy.Mode.RANDOM, 0); policy.initialized(teachers); policy.beginBatch(Direction.CENTER);
        for (int i = 0; i < 12; i++) {
            PermutationSolution<Integer> small = policy.guided(parent, parent, parent, Direction.CENTER);
            raw.evaluate(small); policy.evaluated(small, Direction.CENTER);
        }
        policy.endBatch(Direction.CENTER);
        require(number(policy.diagnostics(), "selectedActions") == 12 * 3, "Small instance block length was not truncated");
    }
    private static void checkControlsAndGenotypes() {
        for (JointPolicy.Mode mode : JointPolicy.Mode.values()) {
            SeededRandom.reset(942 + mode.ordinal()); JointCheckProblem raw = new JointCheckProblem(7);
            List<PermutationSolution<Integer>> teachers = teachers(raw); List<String> original = genomes(teachers);
            JointPolicy policy = policy(raw, mode, 24); policy.initialized(teachers); policy.beginBatch(Direction.CENTER);
            for (int i = 0; i < 24; i++) {
                PermutationSolution<Integer> child = policy.guided(teachers.get(0), teachers.get(1), teachers.get(2), Direction.CENTER);
                raw.evaluate(child); policy.evaluated(child, Direction.CENTER);
                require(original.equals(genomes(teachers)), "Generator modified frozen teachers");
                Map<String, Object> trace = policy.trajectories().get(i);
                int begin = ((Number) trace.get("blockBegin")).intValue();
                for (int p = 0; p < raw.instance.jobs(); p++) if (p < begin || p >= begin + 4) {
                    PermutationSolution<Integer> parent = teachers.get(0);
                    require(child.getVariableValue(p).equals(parent.getVariableValue(p))
                            && child.getVariableValueid(p).equals(parent.getVariableValueid(p))
                            && JointCheckProblem.machines(child).get(p).equals(JointCheckProblem.machines(parent).get(p))
                            && child.getVariableValueworker(p).equals(parent.getVariableValueworker(p)), "Outside block tuple changed");
                }
            }
            policy.endBatch(Direction.CENTER); require(policy.trajectories().size() == 24, "Trace cap/capture changed");
            for (Map<String, Object> trace : policy.trajectories()) checkOutside(trace);
            require(number(policy.diagnostics(), "noLegalFallbacks") == 0, "Witness required an unexplained rollback");
            require(number(head(policy, Direction.CENTER), "updates") == 0, "Control/startup unexpectedly trained");
        }
    }
    @SuppressWarnings("unchecked")
    private static void checkOutside(Map<String, Object> trace) {
        List<List<Integer>> parent = (List<List<Integer>>) trace.get("parent");
        int begin = ((Number) trace.get("blockBegin")).intValue(), length = ((Number) trace.get("blockLength")).intValue();
        boolean[] jobs = new boolean[parent.size()];
        for (int p = begin; p < begin + length; p++) jobs[parent.get(p).get(0)] = true;
        List<Map<String, Object>> steps = (List<Map<String, Object>>) trace.get("decisions");
        require(steps.size() == length, "Trace did not contain all block decisions");
        for (Map<String, Object> step : steps) {
            List<Map<String, Object>> candidates = (List<Map<String, Object>>) step.get("candidates");
            require(candidates.size() >= 1 && candidates.size() <= 6, "Candidate cap/support changed");
            for (Map<String, Object> candidate : candidates) {
                List<Integer> action = (List<Integer>) candidate.get("action"); require(jobs[action.get(0)], "Candidate escaped original block");
                require(((List<?>) candidate.get("afterFeatures")).size() == 20, "Feature contract changed");
            }
            int selected = ((Number) step.get("chosen")).intValue();
            List<Integer> action = (List<Integer>) candidates.get(selected).get("action");
            require(jobs[action.get(0)], "Block duplicated a committed job"); jobs[action.get(0)] = false;
        }
        for (boolean remaining : jobs) require(!remaining, "Original block job was lost");
        Map<String, Object> last = steps.get(steps.size() - 1);
        List<Map<String, Object>> candidates = (List<Map<String, Object>>) last.get("candidates");
        List<Double> tail = (List<Double>) candidates.get(((Number) last.get("chosen")).intValue()).get("tailEstimate");
        require(tail.get(1) > 0 && tail.get(2) > 0, "Block end incorrectly treated as full scheduling terminal");
    }
    private static void checkTraining() {
        SeededRandom.reset(977); JointCheckProblem raw = new JointCheckProblem(7); List<PermutationSolution<Integer>> teachers = teachers(raw);
        JointPolicy policy = policy(raw, JointPolicy.Mode.VALUE, 0); policy.initialized(teachers);
        policy.beginBatch(Direction.MAKESPAN);
        policy.guided(teachers.get(0), teachers.get(1), teachers.get(2), Direction.MAKESPAN);
        policy.evaluated(teachers.get(0), Direction.MAKESPAN); policy.endBatch(Direction.MAKESPAN);
        require(number(policy.diagnostics(), "incompleteTrajectories") == 1, "Incomplete episode was not tracked");
        require(number(head(policy, Direction.MAKESPAN), "labelledTrajectories") == 0, "Missing completion or ordinary operator created labels");
        completeBatch(policy, raw, teachers, 63, 0); require(number(head(policy, Direction.MAKESPAN), "updates") == 0, "Model trained before 64 independent children");
        completeBatch(policy, raw, teachers, 1, 0); require(number(head(policy, Direction.MAKESPAN), "updates") == 1, "First 64-child cohort did not fit");
        close(((Number) head(policy, Direction.MAKESPAN).get("fittedTrajectoryWeight")).doubleValue(), 64, 1e-12);
        completeBatch(policy, raw, teachers, 32, 1); require(number(head(policy, Direction.MAKESPAN), "updates") == 1, "Partial second cohort trained");
        completeBatch(policy, raw, teachers, 32, 1); require(number(head(policy, Direction.MAKESPAN), "updates") == 2, "Second complete cohort did not fit");
        require(number(head(policy, Direction.ENERGY), "updates") == 0, "Counterfactual direction was trained");
        require(number(policy.diagnostics(), "learnedActions") == 64 * 4, "Batch-start frozen head was not used after startup");
    }
    private static void completeBatch(JointPolicy policy, JointCheckProblem raw, List<PermutationSolution<Integer>> teachers, int count, long version) {
        policy.beginBatch(Direction.MAKESPAN);
        for (int i = 0; i < count; i++) {
            PermutationSolution<Integer> child = policy.guided(teachers.get(0), teachers.get(1), teachers.get(2), Direction.MAKESPAN);
            raw.evaluate(child); policy.evaluated(child, Direction.MAKESPAN);
            require(number(head(policy, Direction.MAKESPAN), "modelVersion") == version, "Head changed during batch");
        }
        policy.endBatch(Direction.MAKESPAN);
    }
    private static void checkObjectiveIsolation() {
        SeededRandom.reset(1011); JointCheckProblem raw = new JointCheckProblem(7); List<PermutationSolution<Integer>> teachers = teachers(raw);
        JointPolicy first = policy(raw, JointPolicy.Mode.TAIL, 0), second = policy(raw, JointPolicy.Mode.TAIL, 0);
        first.initialized(teachers); second.initialized(teachers); first.beginBatch(Direction.CENTER); second.beginBatch(Direction.CENTER);
        SeededRandom.reset(1012); String a = genome(first.guided(teachers.get(0), teachers.get(1), teachers.get(2), Direction.CENTER));
        for (PermutationSolution<Integer> teacher : teachers) for (int q = 0; q < 3; q++) teacher.setObjective(q, 1e99);
        SeededRandom.reset(1012); String b = genome(second.guided(teachers.get(0), teachers.get(1), teachers.get(2), Direction.CENTER));
        require(a.equals(b), "Candidate proposal/scoring leaked teacher real objectives after frozen scales");
        first.endBatch(Direction.CENTER); second.endBatch(Direction.CENTER);
    }
    private static JointPolicy policy(JointCheckProblem raw, JointPolicy.Mode mode, int traceLimit) {
        return new JointPolicy(raw.instance, raw.parameters, new ParticleOperators(raw.instance, new SearchConfig().resolved(4)),
                mode, raw::prepare, () -> { }, traceLimit);
    }
    private static List<PermutationSolution<Integer>> teachers(JointCheckProblem raw) {
        List<PermutationSolution<Integer>> result = Arrays.asList(raw.createSolution(), raw.createSolution(), raw.createSolution());
        for (PermutationSolution<Integer> item : result) raw.evaluate(item); return result;
    }
    @SuppressWarnings("unchecked")
    private static Map<String, Object> head(JointPolicy policy, Direction direction) {
        return (Map<String, Object>) ((Map<?, ?>) policy.diagnostics().get("perDirection")).get(direction.name());
    }
    private static long number(Map<String, Object> map, String key) { return ((Number) map.get(key)).longValue(); }
    private static List<String> genomes(List<PermutationSolution<Integer>> values) {
        List<String> result = new ArrayList<>(); for (PermutationSolution<Integer> value : values) result.add(genome(value)); return result;
    }
    private static String genome(PermutationSolution<Integer> value) {
        return value.getVariables() + "/" + value.getVariablesid() + "/" + value.getAttribute("machine") + "/" + value.getVariablesworker();
    }
    static void close(double a, double b, double tolerance) { require(Math.abs(a - b) <= tolerance * Math.max(1, Math.abs(b)), "Expected " + b + ", got " + a); }
    static void require(boolean condition, String message) { if (!condition) throw new AssertionError(message); }
}
