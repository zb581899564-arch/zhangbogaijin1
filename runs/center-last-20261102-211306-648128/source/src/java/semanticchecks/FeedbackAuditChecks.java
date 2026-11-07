package org.uma.jmetal.util.research.search;

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

/** Hand-counted delays, copied provenance, rejection/dedup, deadline guard, FE/RNG zero. */
public final class FeedbackAuditChecks {
    private FeedbackAuditChecks() { }
    @SuppressWarnings("unchecked")
    public static void main(String[] args) {
        SeededRandom.reset(17); Fixture fixture = new Fixture();
        PermutationSolution<Integer> initial = fixture.createSolution(), later = fixture.createSolution();
        double[] now = {1}; FeedbackAudit audit = new FeedbackAudit(() -> now[0], 10);
        audit.paid(initial, 1, true); audit.internalOffer(initial, true, true); audit.initialized(); audit.begin();
        audit.paid(later, 20, true); audit.qgs(Direction.MAKESPAN, 0, 2, initial);
        PermutationSolution<Integer> copy = ParetoTools.copy(later);
        audit.paid(fixture.createSolution(), 120, false);
        SeededRandom.reset(33);
        audit.internalOffer(copy, true, false); audit.internalOffer(later, false, false); audit.end();
        Map<String, Object> summary = audit.summary();
        require(n(summary, "distinctSnapshotsInserted") == 2, "Repeated paid snapshot counted twice");
        require(n((Map<String, Object>) summary.get("firstInsertionDelayFE"), "sum") == 100, "Wrong insertion lag");
        require(n((Map<String, Object>) summary.get("action2TeacherAgeFE"), "sum") == 19, "Wrong teacher age");
        require(n(summary, "externalAdmissionSnapshotsInsertedByCutoff") == 2, "Lost external admission lineage");
        List<Map<String, Object>> frames = audit.export();
        Map<String, Object> step = ((List<Map<String, Object>>) frames.get(1).get("steps")).get(0);
        require(n(step, "archiveRefreshLagFE") == 19 && n(step, "archiveRefreshFE") == 1, "Refresh age confused with teacher age");
        audit.paid(copy, 200, false); audit.internalOffer(copy, false, false);
        require(n(audit.summary(), "distinctSnapshotsInserted") == 2, "Rejected snapshot inserted");
        now[0] = 11; audit.internalOffer(later, true, false); audit.qgs(Direction.CENTER, 0, 2, initial);
        require(n(audit.summary(), "lateEventsExcluded") == 2, "Late feedback events included");
        now[0] = 1;
        for (int i = 0; i < 4; i++) { audit.begin(); audit.qgs(Direction.CENTER, 0, 2, initial); audit.end(); }
        frames = audit.export();
        require(frames.size() == 4 && n(frames.get(3), "generation") == 5, "Trace is not first2+last bounded");
        require(SeededRandom.current().nextLong() == new Random(33).nextLong(), "Observer consumed RNG");
        System.out.println("FEEDBACK_AUDIT_CHECKS_PASS FE=0 RNG=0;copied paid provenance;delays;reject/dedup;late guard;capture bound");
    }
    private static long n(Map<String, Object> row, String key) { return ((Number) row.get(key)).longValue(); }
    private static void require(boolean value, String message) { if (!value) throw new AssertionError(message); }
    private static final class Fixture implements PermutationProblem<PermutationSolution<Integer>>, SchedulingProblemData {
        private static final long serialVersionUID = 1L;
        private final Instance in = new Instance("feedback-FE0", ModelKind.CHAPTER4_DUAL_RESOURCE,
                new double[][] {{1}, {1}}, new double[2][1], new double[][][] {{{1, 1}}},
                new double[][][] {{{1, 1}}}, new double[][][] {{{1, 1}}},
                new double[][][] {{{1}}}, new double[][][] {{{1}}}, "FE0 observation fixture");
        public void evaluate(PermutationSolution<Integer> s) { throw new AssertionError("Unexpected FE"); }
        public PermutationSolution<Integer> createSolution() { return new DefaultIntegerPermutationSolution(this); }
        public int getNumberOfVariables() { return 2; } public int getPermutationLength() { return 2; }
        public int getNumberOfFactories() { return 1; } public int getNumberOfObjectives() { return 3; }
        public int getNumberOfConstraints() { return 0; } public int getWorkerVectorLength() { return 2; }
        public String getName() { return "feedback-FE0"; } public Instance getSchedulingInstance() { return in; }
        public String getInstanceFile() { return "synthetic"; }
    }
}
