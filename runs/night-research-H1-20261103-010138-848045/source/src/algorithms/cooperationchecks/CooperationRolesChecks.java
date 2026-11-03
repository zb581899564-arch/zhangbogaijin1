package org.uma.jmetal.util.research.cooperation;

import java.util.ArrayList;
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

/** Targeted checks for physical groups, uniform preference, bounded pool evidence and RNG neutrality. */
public final class CooperationRolesChecks {
    private CooperationRolesChecks() { }
    public static void main(String[] args) {
        SeededRandom.reset(112); JointCheckProblem raw = new JointCheckProblem(12);
        FamilyContexts contexts = new FamilyContexts(raw.instance);
        List<PermutationSolution<Integer>> population = new ArrayList<>();
        for (int i = 0; i < 100; i++) {
            PermutationSolution<Integer> s = raw.createSolution(); contexts.initialize(s, i);
            for (int k = 0; k < 3; k++) s.setObjective(k, i + 1);
            population.add(s);
        }
        CooperationSupport uniform = new CooperationSupport(raw.instance, raw.parameters, false, false, true, null, false);
        for (Direction d : Direction.values()) require(uniform.preference(d) == Direction.CENTER, "Uniform preference leaked a boundary objective");
        Map<Direction, List<Integer>> groups = contexts.grouping(population, 15, true);
        boolean[] seen = new boolean[100];
        for (Direction d : Direction.values()) {
            require(groups.get(d).size() == (d == Direction.CENTER ? 55 : 15), "Physical group size changed");
            int[] families = new int[4];
            for (int i : groups.get(d)) { require(!seen[i], "Overlapping group"); seen[i] = true;
                int family = FamilyContexts.family(population.get(i)); if (family >= 0) families[family]++;
            }
            for (int n : families) require(n == (d == Direction.CENTER ? 2 : 1), "Physical family quota changed");
        }
        for (boolean present : seen) require(present, "Group coverage lost");
        require(groups.get(Direction.MAKESPAN).contains(20) && groups.get(Direction.ENERGY).contains(31)
                && groups.get(Direction.WORKER_COST).contains(42), "Uniform grouping did not use CENTER ranking");
        PermutationSolution<Integer> parent = population.get(0);
        DynamicSchedule schedule = DynamicDecoder.full(raw.instance, raw.parameters,
                SchedulingEncoding.integers(parent.getVariables()), SchedulingEncoding.integers(parent.getVariablesid()),
                SchedulingEncoding.machineIntegers(parent), SchedulingEncoding.integers(parent.getVariablesworker()), () -> { });
        for (int k = 0; k < 3; k++) parent.setObjective(k, schedule.objectives()[k]);
        FactoryPool[] pools = new FactoryPool[raw.instance.factories()];
        for (int f = 0; f < pools.length; f++) {
            pools[f] = new FactoryPool(); pools[f].offer(new FactoryRecord(schedule, f, 1, 0, "initialization", "INITIALIZATION"));
        }
        double[] seconds = {1}; CooperationEvidence evidence = new CooperationEvidence(new SemanticAudit(() -> seconds[0], 10, true));
        SeededRandom.reset(321);
        for (int i = 0; i < 30; i++) evidence.request(pools, parent, schedule, 0, 0, 0, 0, 1, 1, 1, i + 1, "INFEASIBLE");
        require(((Number) evidence.summary().get("requests")).longValue() == 30, "Request counters wrong");
        require(evidence.export().size() == 17, "Unbounded pool request snapshots");
        require(((Number) evidence.summary().get("tightRequestsMissingFactory")).longValue() == 30, "Missing-factory deficit lost");
        seconds[0] = 11;
        evidence.request(pools, parent, schedule, 0, 0, 0, 0, 1, 1, 1, 31, "INFEASIBLE");
        require(((Number) evidence.summary().get("requests")).longValue() == 30, "Late request credited");
        require(SeededRandom.current().nextLong() == new Random(321).nextLong(), "Observer consumed RNG");
        System.out.println("COOPERATION_ROLES_CHECKS_PASS optimizerFE=0 syntheticFullDecodes=1 physical quotas;CENTER preference;bounded evidence;late guard;RNG=0");
    }
    private static void require(boolean value, String message) { if (!value) throw new AssertionError(message); }
}
