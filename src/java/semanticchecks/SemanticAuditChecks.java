package org.uma.jmetal.util.research.search;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Random;
import org.uma.jmetal.problem.PermutationProblem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.impl.DefaultIntegerPermutationSolution;
import org.uma.jmetal.util.research.SchedulingProblemData;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.model.ModelKind;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Actual direct-origin propagation, capture bounds, detached export and zero evaluation/RNG checks. */
public final class SemanticAuditChecks {
    private SemanticAuditChecks() { }
    @SuppressWarnings("unchecked")
    public static void main(String[] args) {
        Fixture fixture = new Fixture(); SeededRandom.reset(17);
        PermutationSolution<Integer> parent = fixture.createSolution();
        for (int k = 0; k < 3; k++) parent.setObjective(k, k + 1);
        PermutationSolution<Integer> shared = ParetoTools.copy(parent), changed = ParetoTools.copy(parent);
        SeededRandom.reset(33);
        SemanticAudit audit = new SemanticAudit(() -> 1.0, 10);
        audit.generated(shared, parent, true); audit.proposal(shared, "global");
        audit.completed(shared, 1, 1.0, true);
        audit.teacherSelected(ParetoTools.copy(shared)); audit.teacherConsumed(ParetoTools.copy(shared));
        audit.generated(changed, parent, true); audit.proposal(changed, "global");
        audit.completed(changed, 2, 11.0, true); // Paid success may finish diagnostics after the deadline.
        int first = changed.getVariableValue(0); changed.setVariableValue(0, changed.getVariableValue(1)); changed.setVariableValue(1, first);
        audit.teacherSelected(changed); audit.teacherConsumed(changed); // Changed descendants must not count.
        Particle particle = new Particle(shared);
        for (int i = 0; i < 5; i++) {
            List<Particle> pool = Arrays.asList(particle.snapshot());
            audit.pool(pool, SurvivorSelection.select(pool, 1, null, () -> { }), 1);
        }
        List<Map<String, Object>> rows = audit.finish(); Map<String, Object> summary = audit.diagnostics();
        require(number(summary, "paidEvaluationsObserved") == 2, "Missed successful evaluation observer");
        require(number(summary, "paidArchiveAdmissions") == 1, "Late archive event treated as deadline-valid");
        require(number(summary, "sharedOriginsPaid") == 2 && number(summary, "sharedOriginsArchive") == 1, "Paid/archive direct origins wrong");
        require(number(summary, "sharedOriginsPopulation") == 1 && number(summary, "sharedOriginsTeacherSelected") == 1
                && number(summary, "sharedOriginsTeacherConsumed") == 1, "Exact direct-origin propagation broken");
        require(number(summary, "poolsObserved") == 5 && rows.size() == 4, "Pool capture not bounded to first2+last");
        require(number(rows.get(1), "generation") == 1 && number(rows.get(2), "generation") == 2
                && number(rows.get(3), "generation") == 5, "Wrong pool capture identities");
        Map<String, Object> encoded = ((List<Map<String, Object>>) rows.get(1).get("candidates")).get(0);
        int[] saved = ((int[]) encoded.get("JS")).clone(); shared.setVariableValue(0, -999);
        require(Arrays.equals((int[]) encoded.get("JS"), saved), "Export aliases live encoding");
        require(SeededRandom.current().nextLong() == new Random(33).nextLong(), "Audit consumed search RNG");
        checkRepairTiming(parent);
        require(fixture.evaluations == 0, "Audit evaluated a candidate");
        System.out.println("SEMANTIC_AUDIT_CHECKS_PASS exact propagation, late-event guard, first2+last, detached export, FE=0 RNG=0");
    }
    private static long number(Map<String, Object> m, String key) { return ((Number) m.get(key)).longValue(); }
    private static void checkRepairTiming(PermutationSolution<Integer> parent) {
        PermutationSolution<Integer> child = ParetoTools.copy(parent);
        int a = child.getVariableValue(0), b = child.getVariableValue(1);
        child.setVariableValue(0, b); child.setVariableValue(1, a);
        SemanticAudit audit = new SemanticAudit(() -> 1, 10);
        audit.generated(child, parent, false);
        child.setVariableValue(0, a); child.setVariableValue(1, b); // Common restore/repair can undo a proposal.
        audit.proposal(child, "global"); audit.completed(child, 1, 1, true);
        require(number(audit.diagnostics(), "globalSampledDifferent") == 0, "Differentness measured before repair");
        SemanticAudit late = new SemanticAudit(() -> 11, 10);
        late.generated(child, parent, true); late.proposal(child, "global"); late.completed(child, 1, 9, true);
        late.teacherSelected(child); late.teacherConsumed(child);
        List<Particle> pool = Arrays.asList(new Particle(child));
        late.pool(pool, SurvivorSelection.select(pool, 1, null, () -> { }), 1);
        require(number(late.diagnostics(), "sharedOriginsPopulation") == 0
                && number(late.diagnostics(), "sharedOriginsTeacherConsumed") == 0, "Late propagation counted as valid");
    }
    private static void require(boolean ok, String message) { if (!ok) throw new AssertionError(message); }
    private static final class Fixture implements PermutationProblem<PermutationSolution<Integer>>, SchedulingProblemData {
        private static final long serialVersionUID = 1L;
        private int evaluations;
        private final Instance in = new Instance("audit", ModelKind.CHAPTER4_DUAL_RESOURCE,
                new double[][] {{1}, {1}, {1}, {1}}, new double[4][1],
                new double[][][] {{{1, 1}}, {{1, 1}}}, new double[][][] {{{1, 1}}, {{1, 1}}},
                new double[][][] {{{1, 1}}, {{1, 1}}}, new double[][][] {{{1, 1}}, {{1, 1}}},
                new double[][][] {{{1, 1}}, {{1, 1}}}, "synthetic observer check");
        public void evaluate(PermutationSolution<Integer> s) { evaluations++; }
        public PermutationSolution<Integer> createSolution() { return new DefaultIntegerPermutationSolution(this); }
        public int getNumberOfVariables() { return 4; }
        public int getPermutationLength() { return 4; }
        public int getNumberOfFactories() { return 2; }
        public int getNumberOfObjectives() { return 3; }
        public int getNumberOfConstraints() { return 0; }
        public String getName() { return "audit-fixture"; }
        public Instance getSchedulingInstance() { return in; }
        public String getInstanceFile() { return "synthetic"; }
        public int getWorkerVectorLength() { return 4; }
    }
}
