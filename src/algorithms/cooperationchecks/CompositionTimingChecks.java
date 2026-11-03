package org.uma.jmetal.util.research.cooperation;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Random;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.joint.JointCheckProblem;
import org.uma.jmetal.util.research.model.DynamicDecoder;
import org.uma.jmetal.util.research.model.DynamicSchedule;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import org.uma.jmetal.util.research.search.Direction;
import org.uma.jmetal.util.research.search.SemanticAudit;

/** Synthetic fixture decode only; no optimizer evaluation, timestamp-biased choice, or RNG use. */
public final class CompositionTimingChecks {
    private CompositionTimingChecks() { }
    public static void main(String[] args) {
        SeededRandom.reset(17); JointCheckProblem raw = new JointCheckProblem(12);
        PermutationSolution<Integer> first = raw.createSolution(), child = raw.createSolution();
        DynamicSchedule schedule = DynamicDecoder.full(raw.instance, raw.parameters,
                SchedulingEncoding.integers(first.getVariables()), SchedulingEncoding.integers(first.getVariablesid()),
                SchedulingEncoding.machineIntegers(first), SchedulingEncoding.integers(first.getVariablesworker()), () -> { });
        FactoryRecord plain = new FactoryRecord(schedule, 0);
        FactoryRecord stamped = new FactoryRecord(schedule, 0, 7, 1, "global", "ENERGY");
        FactoryRecord duplicate = new FactoryRecord(schedule, 0, 99, 9, "global", "WORKER_COST");
        require(plain.same(stamped) && stamped.same(duplicate), "Metadata changed encoding equality");
        require(!plain.dominates(stamped) && !stamped.dominates(plain), "Metadata changed dominance");
        FactoryPool pool = new FactoryPool(); pool.offer(stamped); pool.offer(duplicate);
        require(pool.choose(Double.POSITIVE_INFINITY, 0, 1, 1).paidFE == 7, "Duplicate refreshed retained provenance");
        CooperationSupport original = new CooperationSupport(raw.instance, raw.parameters, false);
        CooperationSupport last = new CooperationSupport(raw.instance, raw.parameters, false, true, null);
        require(Arrays.equals(original.globalUpdateOrder(), Direction.values()), "Original global order changed");
        require(Arrays.equals(last.globalUpdateOrder(), new Direction[] {Direction.MAKESPAN, Direction.ENERGY, Direction.WORKER_COST, Direction.CENTER}), "Wrong alternate order");
        FactoryRecord[] records = new FactoryRecord[raw.instance.factories()]; records[0] = stamped;
        for (int f = 1; f < records.length; f++) records[f] = new FactoryRecord(schedule, f, 2, 0, "initialization", "INITIALIZATION");
        double[] now = {1}; SemanticAudit audit = new SemanticAudit(() -> now[0], 10, true);
        CompositionTiming timing = new CompositionTiming(audit);
        audit.proposal(first, "global"); audit.completed(first, 10, 1, false); timing.observed(first); timing.begin();
        SeededRandom.reset(33);
        for (int i = 0; i < 40; i++) {
            timing.opportunity(); timing.proposed(child, records, 0);
            audit.proposal(child, "global"); audit.completed(child, 11 + i, 1, i == 0); timing.observed(child);
        }
        Map<String, Object> summary = timing.summary();
        require(n(summary, "deadlineValidPaidAssemblies") == 40 && n(summary, "sameGenerationLateGroupFragments") == 40, "Fresh source aggregation wrong");
        require(n(summary, "deadlineValidArchiveAdmissions") == 1, "Admission event lost");
        List<Map<String, Object>> trace = timing.export(); require(trace.size() == 33, "Unbounded paid examples");
        require(n(trace.get(1), "paidFE") == 11 && n(trace.get(32), "paidFE") == 50, "First/last samples or detachment wrong");
        now[0] = 11; timing.proposed(child, records, 0);
        audit.proposal(child, "global"); audit.completed(child, 51, 11, true); timing.observed(child);
        require(n(timing.summary(), "deadlineValidPaidAssemblies") == 40, "Late sample entered valid counters");
        require(SeededRandom.current().nextLong() == new Random(33).nextLong(), "Observation consumed RNG");
        System.out.println("COMPOSITION_TIMING_CHECKS_PASS optimizerFE=0;syntheticFullDecodes=1;metadata-neutral pool;paid provenance;bound;late guard;RNG=0");
    }
    private static long n(Map<String, Object> value, String key) { return ((Number) value.get(key)).longValue(); }
    private static void require(boolean value, String message) { if (!value) throw new AssertionError(message); }
}
