package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Random;
import org.uma.jmetal.problem.PermutationProblem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.impl.DefaultIntegerPermutationSolution;
import org.uma.jmetal.util.research.SchedulingProblemData;
import org.uma.jmetal.util.research.cooperation.CooperationSupport;
import org.uma.jmetal.util.research.model.DynamicParameters;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.model.ModelKind;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Bounded S checks on actual jMetal solutions and independently assigned synthetic objective triples. */
public final class SelectionSemanticsChecks {
    private SelectionSemanticsChecks() { }

    public static void main(String[] args) {
        CountingProblem raw = new CountingProblem();
        RunContext<PermutationSolution<Integer>> context = new RunContext<>(raw, 1000, 271828);
        List<Particle> pool = mergedPool(context);
        checkCompletePool(pool, raw, context);
        checkSnapshotsAndBranches(raw, context);
        checkDuplicateTies(raw, context);
        checkCooperationQuotas(raw, context);
        checkInvalidInputs(pool, raw, context);
        checkCheckpointAndRandom(pool, raw, context);
        System.out.println("SELECTION_SEMANTICS_CHECKS_PASS candidates=200 survivors=100 addedSelectionFE=0"
                + " (engineering evidence only; no optimizer performance experiment)");
    }

    private static List<Particle> mergedPool(RunContext<PermutationSolution<Integer>> context) {
        List<Particle> global = new ArrayList<>(), local = new ArrayList<>();
        for (int i = 0; i < 100; i++) {
            Particle g = new Particle(paid(context, i + 100, i + 100, i + 100));
            global.add(g.snapshot());
            local.add(g.descend(paidCopy(context, g.current, i, i, i)));
        }
        global.addAll(local);
        return global;
    }

    private static void checkCompletePool(List<Particle> pool, CountingProblem raw,
            RunContext<PermutationSolution<Integer>> context) {
        long before = context.budget().attempted(); int calls = raw.calls;
        SurvivorSelection.Result result = SurvivorSelection.select(pool, 100, null, context.problem()::checkpoint);
        int[] indices = result.indices(); double[] score = result.fitness();
        require(pool.size() == 200 && result.survivors().size() == 100, "200-to-100 selection was not executed");
        for (int i = 0; i < 100; i++) {
            require(indices[i] == i + 100, "Local improvement not selected from the complete pool");
            require(result.survivors().get(i) == pool.get(indices[i]), "Survivor/index association changed");
            close(score[i], 100 + i + 1.0 / (100 - i));
            close(score[i + 100], i + 1.0 / (200 - i));
        }
        require(result.categories() == null && result.quotas() == null, "Unconstrained selection gained categories");
        indices[0] = -1; score[0] = -1; result.survivors().clear();
        require(result.indices()[0] == 100 && result.fitness()[0] > 0 && result.survivors().size() == 100,
                "Selection diagnostics expose mutable containers");
        noEvaluation(raw, context, calls, before);
        System.out.println("PASS actual G100+L100 selection; all 200 hand-derived PDDR scores and original indices; added FE=0");
    }

    private static void checkSnapshotsAndBranches(CountingProblem raw,
            RunContext<PermutationSolution<Integer>> context) {
        Particle root = new Particle(paid(context, 1, 9, 9));
        Particle global = root.descend(paidCopy(context, root.current, 9, 1, 9));
        Particle frozen = global.snapshot(); String saved = fingerprint(frozen.current);
        PermutationSolution<Integer> changed = paidCopy(context, global.current, 9, 9, 1);
        changeEncoding(changed);
        long before = context.budget().attempted(); int calls = raw.calls;
        Particle local = global.descend(changed);
        changeEncoding(global.current); global.current.setObjective(0, 999);
        require(saved.equals(fingerprint(frozen.current)), "G snapshot aliases the pre-local-search current solution");
        require(root.lineageId() == global.lineageId() && root.lineageId() == local.lineageId(), "Descendant lost root identity");
        require(global.branchId() == frozen.branchId() && global.lineageId() == frozen.lineageId(), "Snapshot changed branch identity");
        require(root.branchId() != global.branchId() && global.branchId() != local.branchId(), "Descend reused a branch identity");
        require(root.personalArchive().size() == 1 && frozen.personalArchive().size() == 2 && local.personalArchive().size() == 3,
                "G/L branches did not retain their respective personal ND histories");
        List<PermutationSolution<Integer>> exposed = local.personalArchive();
        exposed.get(0).setObjective(0, -1000); exposed.clear();
        PermutationSolution<Integer> teacher = frozen.personalBest(Direction.MAKESPAN);
        teacher.setVariableValue(0, 999); teacher.setObjective(0, -1000);
        require(local.personalArchive().size() == 3 && frozen.personalBest(Direction.MAKESPAN).getObjective(0) == 1,
                "Personal history or teacher copies alias branch state");
        SurvivorSelection.Result both = SurvivorSelection.select(Arrays.asList(frozen, local), 2, null, context.problem()::checkpoint);
        require(both.survivors().contains(frozen) && both.survivors().contains(local), "Same-lineage branches were deduplicated");
        require(both.survivors().get(0).personalArchive().size() == 2 && both.survivors().get(1).personalArchive().size() == 3,
                "Selection attached histories by an old array index");
        noEvaluation(raw, context, calls, before);
        System.out.println("PASS independent four-vector/objective G snapshot; root/branch identities, G/L history isolation, both branches survive");
    }

    private static void checkDuplicateTies(CountingProblem raw, RunContext<PermutationSolution<Integer>> context) {
        Particle root = new Particle(paid(context, 1, 1, 1));
        List<Particle> copies = new ArrayList<>();
        for (int i = 0; i < 200; i++) copies.add(root.descend(ParetoTools.copy(root.current)));
        long before = context.budget().attempted(); int calls = raw.calls;
        SurvivorSelection.Result tied = SurvivorSelection.select(copies, 100, new SwarmSupport() {
            @Override public int selectionCategory(PermutationSolution<Integer> solution) {
                throw new AssertionError("Category hook must not run without quotas");
            }
        }, context.problem()::checkpoint);
        for (int i = 0; i < 100; i++) require(tied.indices()[i] == i, "Equal PDDR score changed stable input order");
        for (double value : tied.fitness()) close(value, 1);
        require(tied.survivors().get(0).lineageId() == tied.survivors().get(99).lineageId(), "Duplicate lineage records were removed");
        noEvaluation(raw, context, calls, before);
        System.out.println("PASS 200 identical genotypes retained as records; equal-score truncation keeps first 100 input records");
    }

    private static void checkCooperationQuotas(CountingProblem raw,
            RunContext<PermutationSolution<Integer>> context) {
        List<Particle> pool = quotaPool(context);
        long before = context.budget().attempted(); int calls = raw.calls;
        SurvivorSelection.Result unrestricted = SurvivorSelection.select(pool, 100, null, context.problem()::checkpoint);
        for (Particle survivor : unrestricted.survivors()) require(survivor.current.getAttribute("cooperation.family") == null,
                "Quota check must first demonstrate that unconstrained truncation loses all fixed families");
        for (boolean sharing : new boolean[] {false, true}) {
            CooperationSupport support = new CooperationSupport(raw.instance,
                    DynamicParameters.uniform(raw.instance, .1, .1, .1, 0), sharing);
            SurvivorSelection.Result result = SurvivorSelection.select(pool, 100, support, context.problem()::checkpoint);
            int[] counts = new int[5], categories = result.categories();
            for (int index : result.indices()) counts[categories[index]]++;
            require(Arrays.equals(counts, new int[] {80, 5, 5, 5, 5}), "Cooperation quotas were not preserved");
            require(Arrays.equals(result.quotas(), counts), "Quota diagnostics changed order");
            double[] score = result.fitness(); int[] indices = result.indices();
            for (int i = 0; i < pool.size(); i++) {
                int rank = (int) pool.get(i).current.getObjective(0);
                close(score[i], rank + 1.0 / (200 - rank));
            }
            for (int i = 0; i < 100; i++) {
                require(indices[i] == (i < 80 ? i + 120 : i + 20), "Quota truncation ignored common-pool scores");
            }
            List<PermutationSolution<Integer>> survivors = new ArrayList<>();
            for (Particle p : result.survivors()) survivors.add(p.current);
            Map<Direction, List<Integer>> groups = support.grouping(survivors, 15);
            int grouped = 0; for (List<Integer> group : groups.values()) grouped += group.size();
            require(grouped == 100, "Post-selection cooperation grouping lost particles");
        }
        noEvaluation(raw, context, calls, before);
        System.out.println("PASS quotas restore families lost by unconstrained selection: SYNC/SHARE 80 free + four x5; full-pool scores and next grouping");
    }

    private static List<Particle> quotaPool(RunContext<PermutationSolution<Integer>> context) {
        List<Particle> global = new ArrayList<>(), local = new ArrayList<>();
        for (int i = 0; i < 100; i++) {
            // All 160 free records dominate every fixed-family record, forcing quotas to act.
            int globalRank = i < 20 ? 180 + i : 80 + i - 20;
            int localRank = i < 20 ? 160 + i : i - 20;
            PermutationSolution<Integer> evaluated = paid(context, globalRank, globalRank, globalRank);
            if (i < 20) evaluated.setAttribute("cooperation.family", i / 5);
            Particle g = new Particle(evaluated);
            global.add(g.snapshot());
            local.add(g.descend(paidCopy(context, g.current, localRank, localRank, localRank)));
        }
        global.addAll(local); return global;
    }

    private static void checkInvalidInputs(List<Particle> pool, CountingProblem raw,
            RunContext<PermutationSolution<Integer>> context) {
        long before = context.budget().attempted(); int calls = raw.calls;
        reject(() -> SurvivorSelection.select(pool, -1, null, context.problem()::checkpoint));
        reject(() -> SurvivorSelection.select(pool, 201, null, context.problem()::checkpoint));
        reject(() -> SurvivorSelection.select(pool, 100, quotas(new int[] {99}, 0), context.problem()::checkpoint));
        reject(() -> SurvivorSelection.select(pool, 100, quotas(new int[] {-1, 101}, 0), context.problem()::checkpoint));
        reject(() -> SurvivorSelection.select(pool, 100, quotas(new int[0], 0), context.problem()::checkpoint));
        reject(() -> SurvivorSelection.select(pool, 100, quotas(new int[] {100}, -1), context.problem()::checkpoint));
        reject(() -> SurvivorSelection.select(pool, 100, quotas(new int[] {100}, 1), context.problem()::checkpoint));
        reject(() -> SurvivorSelection.select(pool, 100, quotas(new int[] {99, 1}, 0), context.problem()::checkpoint));
        noEvaluation(raw, context, calls, before);
        System.out.println("PASS invalid counts, quota totals/negative/empty values, illegal categories and insufficient category capacity reject without evaluation");
    }

    private static void checkCheckpointAndRandom(List<Particle> pool, CountingProblem raw,
            RunContext<PermutationSolution<Integer>> context) {
        long before = context.budget().attempted(); int calls = raw.calls;
        IllegalStateException stop = new IllegalStateException("selection checkpoint");
        int[] checkpoints = {0};
        try {
            SurvivorSelection.select(pool, 100, null, () -> { if (++checkpoints[0] == 7) throw stop; });
            throw new AssertionError("Selection ignored checkpoint interruption");
        } catch (IllegalStateException expected) { require(expected == stop, "Selection replaced checkpoint exception"); }
        SeededRandom.reset(991);
        Particle snapshot = pool.get(0).snapshot(); snapshot.descend(ParetoTools.copy(snapshot.current));
        SurvivorSelection.select(pool, 100, null, context.problem()::checkpoint);
        require(SeededRandom.current().nextLong() == new Random(991).nextLong(), "Snapshot/selection consumed search RNG");
        noEvaluation(raw, context, calls, before);
        System.out.println("PASS callback interruption propagates; snapshots, branch ids and selection consume neither FE nor RNG");
    }

    private static SwarmSupport quotas(final int[] quotas, final int category) {
        return new SwarmSupport() {
            @Override public int[] selectionQuotas() { return quotas; }
            @Override public int selectionCategory(PermutationSolution<Integer> solution) { return category; }
        };
    }
    private static PermutationSolution<Integer> paid(RunContext<PermutationSolution<Integer>> context, double a, double b, double c) {
        return paidObjectives(context, context.problem().createSolution(), a, b, c);
    }
    private static PermutationSolution<Integer> paidCopy(RunContext<PermutationSolution<Integer>> context,
            PermutationSolution<Integer> original, double a, double b, double c) {
        return paidObjectives(context, ParetoTools.copy(original), a, b, c);
    }
    private static PermutationSolution<Integer> paidObjectives(RunContext<PermutationSolution<Integer>> context,
            PermutationSolution<Integer> solution, double a, double b, double c) {
        solution.setObjective(0, a); solution.setObjective(1, b); solution.setObjective(2, c);
        context.problem().evaluate(solution); return solution;
    }
    @SuppressWarnings("unchecked")
    private static void changeEncoding(PermutationSolution<Integer> s) {
        int first = s.getVariableValue(0); s.setVariableValue(0, s.getVariableValue(1)); s.setVariableValue(1, first);
        s.setVariableValueid(0, 1 - s.getVariableValueid(0));
        List<Integer> machines = (List<Integer>) s.getAttribute("machine");
        machines.set(0, 1 - machines.get(0));
        s.setVariableValueworker(0, 1 - s.getVariableValueworker(0));
    }
    private static String fingerprint(PermutationSolution<Integer> s) {
        return s.getVariables() + "/" + s.getVariablesid() + "/" + s.getAttribute("machine")
                + "/" + s.getVariablesworker() + "/" + Arrays.toString(s.getObjectives());
    }
    private static void noEvaluation(CountingProblem raw, RunContext<PermutationSolution<Integer>> context, int calls, long before) {
        require(raw.calls == calls && context.budget().attempted() == before, "Copy/selection unexpectedly evaluated a candidate");
    }
    private static void reject(Runnable call) {
        try { call.run(); throw new AssertionError("Invalid selection inputs accepted"); }
        catch (IllegalArgumentException expected) { /* No fallback or new candidate is permitted. */ }
    }
    private static void close(double actual, double expected) {
        require(Math.abs(actual - expected) <= 1e-12 * Math.max(1, Math.abs(expected)), "Expected " + expected + ", got " + actual);
    }
    private static void require(boolean condition, String message) { if (!condition) throw new AssertionError(message); }

    private static final class CountingProblem implements PermutationProblem<PermutationSolution<Integer>>, SchedulingProblemData {
        private static final long serialVersionUID = 1L;
        private final Instance instance = new Instance("selection-semantics", ModelKind.CHAPTER4_DUAL_RESOURCE,
                new double[][] {{1}, {1}, {1}, {1}}, new double[4][1],
                new double[][][] {{{1, 1}}, {{1, 1}}}, new double[][][] {{{1, 1}}, {{1, 1}}},
                new double[][][] {{{1, 1}}, {{1, 1}}}, new double[][][] {{{1, 1}}, {{1, 1}}},
                new double[][][] {{{1, 1}}, {{1, 1}}}, "synthetic objective-assignment contract check; no scheduling claim");
        private int calls;
        @Override public void evaluate(PermutationSolution<Integer> solution) { calls++; }
        @Override public PermutationSolution<Integer> createSolution() { return new DefaultIntegerPermutationSolution(this); }
        @Override public int getNumberOfVariables() { return instance.jobs(); }
        @Override public int getPermutationLength() { return instance.jobs(); }
        @Override public int getNumberOfFactories() { return instance.factories(); }
        @Override public int getNumberOfObjectives() { return 3; }
        @Override public int getNumberOfConstraints() { return 0; }
        @Override public String getName() { return "SelectionSemanticsCountingProblem"; }
        @Override public Instance getSchedulingInstance() { return instance; }
        @Override public String getInstanceFile() { return "synthetic-selection-check"; }
        @Override public int getWorkerVectorLength() { return instance.jobs(); }
    }
}
