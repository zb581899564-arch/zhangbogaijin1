package org.uma.jmetal.util.research.cooperation;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.joint.*;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import org.uma.jmetal.util.research.search.*;

/** Tests context isolation, finite-pool selection, constrained generation, and paid assembly replay. */
public final class CooperationChecks {
    private CooperationChecks() { }
    public static void main(String[] args) {
        SeededRandom.reset(564324);
        JointCheckProblem raw = new JointCheckProblem(12);
        CooperationSupport support = new CooperationSupport(raw.instance, raw.parameters, true);
        List<PermutationSolution<Integer>> pop = new ArrayList<>();
        for (int i = 0; i < 100; i++) {
            PermutationSolution<Integer> s = raw.createSolution(); support.prepareInitialization(s, i);
            support.beforeEvaluation(s, "initialization", null); raw.evaluate(s); support.evaluated(s, "initialization", null); pop.add(s);
        }
        support.initialized(pop);
        Map<Direction,List<Integer>> groups = support.grouping(pop, 15);
        for (Direction d : Direction.values()) require(groups.get(d).size() == (d == Direction.CENTER ? 55 : 15), "Group quota");
        for (int f = 0; f < 4; f++) for (Direction d : Direction.values()) {
            int count = 0; for (int i : groups.get(d)) if (FamilyContexts.family(pop.get(i)) == f) count++;
            require(count == (d == Direction.CENTER ? 2 : 1), "Family role coverage");
        }
        JointPolicy joint = new JointPolicy(raw.instance, raw.parameters, new ParticleOperators(raw.instance, new SearchConfig().resolved(4)),
                JointPolicy.Mode.VALUE, raw::prepare, () -> { });
        joint.initialized(pop); joint.beginBatch(Direction.CENTER);
        for (int round = 0; round < 1200; round++) {
            int at = round % 20; PermutationSolution<Integer> parent = pop.get(at);
            PermutationSolution<Integer> child = joint.propose(parent, pop.get((at + 5) % 20), pop.get(25), Direction.CENTER);
            support.beforeEvaluation(child, "rejected-local-diagnostic", Direction.CENTER); raw.evaluate(child);
            support.evaluated(child, "rejected-local-diagnostic", Direction.CENTER); joint.evaluated(child, Direction.CENTER);
            int[] fixed = (int[]) child.getAttribute(FamilyContexts.FIXED);
            for (int p = 0; p < raw.instance.jobs(); p++) require(child.getVariableValueid(p) == fixed[child.getVariableValue(p)], "Joint FA constraint");
            PermutationSolution<Integer> assembled = support.compose(parent, Direction.CENTER);
            if (assembled != null) { support.beforeEvaluation(assembled, "global", Direction.CENTER); raw.evaluate(assembled); support.evaluated(assembled, "global", Direction.CENTER); }
            pop.set(at, child);
        }
        joint.endBatch(Direction.CENTER);
        require(((Number) support.diagnostics().get("assembliesValidated")).longValue() > 0, "No paid assembly replayed");
        DynamicSchedule schedule = (DynamicSchedule) pop.get(0).getAttribute("dynamic.schedule");
        boolean mismatch = false;
        try { schedule.validateContext(raw.instance, DynamicParameters.uniform(raw.instance, .07, .05, 1.5, .2)); }
        catch (IllegalArgumentException expected) { mismatch = true; }
        require(mismatch, "Initial-state context mismatch accepted");
        checkPool(pop, raw);
        System.out.println("COOPERATION_CHECKS_PASS quotas; fixed FA; rejected paid observations; strict contexts; exact pool selection; cap; assembly replay");
        System.out.println(support.diagnostics());
    }
    private static void checkPool(List<PermutationSolution<Integer>> pop, JointCheckProblem raw) {
        FactoryPool pool = new FactoryPool();
        for (int i = 0; i < 5; i++) pool.offer(new FactoryRecord((DynamicSchedule) pop.get(i).getAttribute("dynamic.schedule"), 0));
        require(pool.size() <= 8, "Pool cap");
        for (double cap : new double[] {0, 20, 10000}) for (double eta : new double[] {0, 1, 4}) {
            FactoryRecord selected = pool.choose(cap, eta, 10, 20); double score = Double.POSITIVE_INFINITY;
            for (FactoryRecord r : pool.records()) if (r.objectives[0] <= cap) score = Math.min(score, r.objectives[1]/10 + eta*r.objectives[2]/20);
            require(selected == null ? Double.isInfinite(score) : selected.objectives[1]/10 + eta*selected.objectives[2]/20 == score, "Finite pool minimization");
        }
        boolean mismatch = false;
        try { pool.offer(new FactoryRecord((DynamicSchedule) pop.get(5).getAttribute("dynamic.schedule"), 0)); }
        catch (IllegalArgumentException expected) { mismatch = true; }
        require(mismatch, "Wrong job set accepted");
    }
    private static void require(boolean ok, String message) { if (!ok) throw new AssertionError(message); }
}
