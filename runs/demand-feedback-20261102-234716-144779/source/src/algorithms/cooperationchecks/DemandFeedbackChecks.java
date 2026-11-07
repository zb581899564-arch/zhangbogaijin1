package org.uma.jmetal.util.research.cooperation;

import java.util.Random;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.joint.JointCheckProblem;
import org.uma.jmetal.util.research.model.DynamicDecoder;
import org.uma.jmetal.util.research.model.DynamicSchedule;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import org.uma.jmetal.util.research.search.Direction;
import org.uma.jmetal.util.research.search.SemanticAudit;

/** Fixed-rule and matched-SHAM checks, independent of performance outcomes. */
public final class DemandFeedbackChecks {
    private DemandFeedbackChecks() { }
    public static void main(String[] args) {
        require(DemandFeedback.target(new double[] {110, 130, 130}, 100) == 1, "Largest deficit/tie rule");
        require(DemandFeedback.target(new double[] {90, 100}, 100) == -1, "Satisfied cap should fall back");
        SeededRandom.reset(17); JointCheckProblem raw = new JointCheckProblem(12);
        PermutationSolution<Integer> parent = raw.createSolution();
        DynamicSchedule schedule = DynamicDecoder.full(raw.instance, raw.parameters,
                SchedulingEncoding.integers(parent.getVariables()), SchedulingEncoding.integers(parent.getVariablesid()),
                SchedulingEncoding.machineIntegers(parent), SchedulingEncoding.integers(parent.getVariablesworker()), () -> { });
        FactoryPool[] pools = new FactoryPool[raw.instance.factories()];
        double min = Double.POSITIVE_INFINITY, max = 0; int target = -1;
        for (int f = 0; f < pools.length; f++) {
            pools[f] = new FactoryPool(); FactoryRecord record = new FactoryRecord(schedule, f);
            pools[f].offer(record); min = Math.min(min, record.objectives[0]);
            if (record.objectives[0] > max) { max = record.objectives[0]; target = f; }
        }
        int random = (target + 1) % pools.length;
        double[] now = {1}; SemanticAudit audit = new SemanticAudit(() -> now[0], 10, true);
        DemandFeedback demand = new DemandFeedback("DEMAND", audit), sham = new DemandFeedback("SHAM", audit);
        demand.request(0, min * .5, 1, 1); sham.request(0, min * .5, 1, 1);
        SeededRandom.reset(553);
        for (int i = 0; i < 40; i++) {
            require(demand.route(pools, 0, Direction.MAKESPAN, random, i + 2, 1) == target, "Demand did not route to missing supply");
            require(sham.route(pools, 0, Direction.MAKESPAN, random, i + 2, 1) == random, "SHAM changed routing");
        }
        require(demand.route(null, -1, Direction.MAKESPAN, random, 42, 1) == random, "Free particle was routed");
        require(demand.route(pools, 0, Direction.ENERGY, random, 42, 1) == random, "Non-makespan group was routed");
        require(demand.export().size() == 17 && sham.export().size() == 17, "Unbounded demand observations");
        demand.request(0, max * 2, 43, 1);
        require(demand.route(pools, 0, Direction.MAKESPAN, random, 44, 1) == random, "Resolved gap did not fall back");
        now[0] = 11;
        require(demand.route(pools, 0, Direction.MAKESPAN, random, 44, 1) == random, "Late routing did not fall back");
        require(SeededRandom.current().nextLong() == new Random(553).nextLong(), "Demand consumed extra RNG");
        System.out.println("DEMAND_FEEDBACK_CHECKS_PASS optimizerFE=0 syntheticFullDecodes=1 target;SHAM;resolved;physical scope;bounds;RNG=0");
    }
    private static void require(boolean value, String message) { if (!value) throw new AssertionError(message); }
}
