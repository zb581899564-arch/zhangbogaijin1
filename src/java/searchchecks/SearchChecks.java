package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.problem.PermutationProblem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.impl.DefaultIntegerPermutationSolution;
import org.uma.jmetal.util.research.SchedulingEvaluation;
import org.uma.jmetal.util.research.SchedulingMetadata;
import org.uma.jmetal.util.research.SchedulingProblemData;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.model.ModelKind;
import org.uma.jmetal.util.research.model.Schedule;
import org.uma.jmetal.util.research.model.Validator;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Checks real four-vector solution objects with a small independent scheduling instance. */
public final class SearchChecks {
    private SearchChecks() { }
    public static void main(String[] args) {
        int chapter = Integer.parseInt(args[0]);
        checkQAndDirections(chapter);
        checkParentsAndNeighborhoods(chapter);
        checkAllPhases(chapter);
        String first = runFingerprint(chapter, 271828);
        require(first.equals(runFingerprint(chapter, 271828)), "Same seed did not reproduce all archive encodings/objectives");
        require(!first.equals(runFingerprint(chapter, 314159)), "Different seeds unexpectedly produced identical archive");
        System.out.println("SEARCH_CHECKS_PASS chapter=" + chapter
                + " (engineering/contract evidence only; no performance comparison)");
    }

    private static void checkQAndDirections(int chapter) {
        SeededRandom.reset(11);
        QTable first = new QTable(3, .25, .8), other = new QTable(3, .25, .8);
        first.update(0, 0, 2, 1); close(first.value(0, 0), .5);
        first.update(1, 1, 4, 0); close(first.value(1, 1), 1.1);
        first.update(0, 0, -1, 1); close(first.value(0, 0), .345);
        close(other.value(0, 0), 0); close(other.value(1, 1), 0);
        require(first.choose(1, 0) == 1, "Exploitation ignored the best Q value");
        ToyProblem problem = new ToyProblem(chapter, false);
        PermutationSolution<Integer> before = problem.createSolution(), after = problem.createSolution();
        setObjectives(before, 100, 1000, 10); setObjectives(after, 99, 990, 11);
        close(Direction.MAKESPAN.reward(before, after), 1);
        close(Direction.ENERGY.reward(before, after), 10);
        close(Direction.WORKER_COST.reward(before, after), -1);
        close(Direction.CENTER.reward(before, after), -.08);
        require(Direction.CENTER.state(-.08, chapter) == 1, "Center state uses any-objective improvement");
        require(Direction.MAKESPAN.state(0, 3) == 1 && Direction.MAKESPAN.state(0, 4) == 0,
                "Chapter-specific zero-change state boundary");
        PermutationSolution<Integer> a = problem.createSolution(), b = problem.createSolution(), same = problem.createSolution();
        setObjectives(a, 1, 1, 1); setObjectives(b, 2, 2, 2); setObjectives(same, 1, 1, 1);
        double[] pddr = ParetoTools.fitness(Arrays.asList(a, b, same));
        close(pddr[0], .5); close(pddr[1], 3); close(pddr[2], .5);
        System.out.println("PASS Bellman alpha/bootstrap, isolated Q tables, group reward/state, strict PDDR-FF");
    }

    private static void checkParentsAndNeighborhoods(int chapter) {
        ToyProblem raw = new ToyProblem(chapter, false);
        RunContext<PermutationSolution<Integer>> context = new RunContext<>(raw, 150, 271828);
        PermutationSolution<Integer> parent = context.problem().createSolution(); context.problem().evaluate(parent);
        PermutationSolution<Integer> personal = context.problem().createSolution(); context.problem().evaluate(personal);
        PermutationSolution<Integer> global = context.problem().createSolution(); context.problem().evaluate(global);
        List<String> original = Arrays.asList(fingerprint(parent), fingerprint(personal), fingerprint(global));
        SearchConfig config = new SearchConfig();
        config.factoryCrossover = config.machineCrossover = config.workerCrossover = 1;
        config.factoryMutation = config.machineMutation = config.workerMutation = 1;
        ParticleOperators operators = new ParticleOperators(raw.instance, config.resolved(chapter));
        for (int i = 0; i < 100; i++) {
            PermutationSolution<Integer> child = operators.update(parent, personal, global);
            context.problem().evaluate(child);
            Validator.validate(raw.instance, (Schedule) child.getAttribute(SchedulingMetadata.SCHEDULE_KEY));
            require(original.equals(Arrays.asList(fingerprint(parent), fingerprint(personal), fingerprint(global))),
                    "Global operator mutated current/pbest/gbest parent");
        }
        IntraNeighborhoods neighborhoods = new IntraNeighborhoods(raw.instance);
        for (int operator = 0; operator < IntraNeighborhoods.COUNT; operator++) for (int factory = 0; factory < 2; factory++) {
            PermutationSolution<Integer> child = neighborhoods.propose(parent, factory, operator);
            context.problem().evaluate(child);
            Validator.validate(raw.instance, (Schedule) child.getAttribute(SchedulingMetadata.SCHEDULE_KEY));
            require(original.get(0).equals(fingerprint(parent)), "Local neighborhood mutated its parent");
        }
        require(context.budget().attempted() == 121 && context.budget().failed() == 0, "Operator evaluation accounting");
        System.out.println("PASS 100 forced crossover/mutation updates + all nine neighborhoods; parents immutable and schedules valid");
    }

    private static void checkAllPhases(int chapter) {
        ToyProblem raw = new ToyProblem(chapter, true);
        RunContext<PermutationSolution<Integer>> context = new RunContext<>(raw, 800, 77531);
        SearchConfig config = smallConfig();
        CanonicalHmopso search = new CanonicalHmopso(context.problem(), raw.instance, chapter, config);
        context.run(search);
        require(context.budget().attempted() == 800 && context.budget().failed() == 0, "Search exceeded or under-consumed budget");
        Map<String, Long> diagnostics = search.diagnostics();
        long total = 0;
        for (String stage : Arrays.asList("initialization", "global", "inter", "intra")) {
            long count = diagnostics.getOrDefault(stage + ".evaluations", 0L);
            require(count > 0, "Stage not executed: " + stage); total += count;
        }
        require(total == 800, "Phase counters do not account for every decoder call");
        for (Direction direction : Direction.values()) {
            for (String stage : Arrays.asList("global", "inter", "intra")) {
                require(diagnostics.getOrDefault(stage + ".g" + direction.id() + ".evaluations", 0L) > 0,
                        "Missing phase/direction " + stage + "/" + direction);
            }
            require(diagnostics.getOrDefault((chapter == 3 ? "qls" : "qgs") + ".g" + direction.id() + ".updates", 0L) > 0,
                    "Q learning not executed for " + direction);
        }
        for (int operator = 0; operator < IntraNeighborhoods.COUNT; operator++) {
            require(diagnostics.getOrDefault("intra.neighborhood" + operator + ".proposals", 0L) > 0,
                    "Neighborhood not enabled: " + operator);
        }
        require(context.result().size() == 1, "Equal objectives must still yield a nonempty ND archive");
        System.out.println("PASS all four directions, global/inter/intra, nine neighborhoods and chapter-specific Q path; FE=800");
    }

    private static String runFingerprint(int chapter, long seed) {
        ToyProblem raw = new ToyProblem(chapter, false);
        RunContext<PermutationSolution<Integer>> context = new RunContext<>(raw, 900, seed);
        CanonicalHmopso search = new CanonicalHmopso(context.problem(), raw.instance, chapter, smallConfig());
        context.run(search);
        List<String> rows = new ArrayList<>();
        for (PermutationSolution<Integer> solution : context.result()) {
            Validator.validate(raw.instance, (Schedule) solution.getAttribute(SchedulingMetadata.SCHEDULE_KEY));
            rows.add(fingerprint(solution));
        }
        Collections.sort(rows);
        return rows.toString();
    }
    private static SearchConfig smallConfig() {
        SearchConfig config = new SearchConfig();
        config.populationSize = 8; config.boundarySize = 1; config.qIterations = 1; config.localProposalCap = 12;
        return config;
    }
    private static String fingerprint(PermutationSolution<Integer> solution) {
        return Arrays.toString(solution.getObjectives()) + solution.getVariables() + solution.getVariablesid()
                + solution.getAttribute("machine") + solution.getVariablesworker();
    }
    private static void setObjectives(PermutationSolution<Integer> solution, double a, double b, double c) {
        solution.setObjective(0, a); solution.setObjective(1, b); solution.setObjective(2, c);
    }
    private static void close(double actual, double expected) {
        require(Math.abs(actual - expected) <= 1e-12 * Math.max(1, Math.abs(expected)), "Expected " + expected + ", got " + actual);
    }
    private static void require(boolean condition, String message) { if (!condition) throw new AssertionError(message); }

    private static final class ToyProblem implements PermutationProblem<PermutationSolution<Integer>>, SchedulingProblemData {
        private static final long serialVersionUID = 1L;
        final Instance instance;
        private final boolean constantObjectives;
        ToyProblem(int chapter, boolean constantObjectives) {
            this.constantObjectives = constantObjectives;
            double[][][] speed = {{{1, 1.5, 2}}, {{1.2, 1.4, 1.8}}};
            double[][][] power = {{{4, 5, 6}}, {{4.5, 5.5, 6.5}}};
            double[][][] standby = {{{1, 1, 1}}, {{1, 1, 1}}};
            double[][][] efficiency = chapter == 3 ? new double[][][] {{{.8, 1, 1.2}}, {{.9, 1.1, 1.3}}}
                    : new double[][][] {{{.8, 1.2}}, {{.9, 1.3}}};
            double[][][] cost = chapter == 3 ? new double[][][] {{{8, 10, 12}}, {{9, 11, 13}}}
                    : new double[][][] {{{8, 12}}, {{9, 13}}};
            instance = new Instance("search-checks", chapter == 3 ? ModelKind.CHAPTER3_FIXED_WORKER : ModelKind.CHAPTER4_DUAL_RESOURCE,
                    new double[][] {{4}, {5}, {6}, {7}, {8}, {9}},
                    chapter == 3 ? new double[6][1] : new double[][] {{1}, {2}, {1}, {2}, {1}, {2}},
                    speed, power, standby, efficiency, cost, "independent synthetic search contract check");
        }
        @Override public void evaluate(PermutationSolution<Integer> solution) {
            SchedulingEvaluation.evaluate(solution, instance);
            if (constantObjectives) setObjectives(solution, 1, 1, 1);
        }
        @Override public PermutationSolution<Integer> createSolution() { return new DefaultIntegerPermutationSolution(this); }
        @Override public int getNumberOfVariables() { return instance.jobs(); }
        @Override public int getPermutationLength() { return instance.jobs(); }
        @Override public int getNumberOfFactories() { return instance.factories(); }
        @Override public int getNumberOfObjectives() { return 3; }
        @Override public int getNumberOfConstraints() { return 0; }
        @Override public String getName() { return "SearchCheckProblem"; }
        @Override public Instance getSchedulingInstance() { return instance; }
        @Override public String getInstanceFile() { return "synthetic-search-check"; }
        @Override public int getWorkerVectorLength() {
            if (instance.kind() == ModelKind.CHAPTER4_DUAL_RESOURCE) return instance.jobs();
            int total = 0;
            for (int f = 0; f < instance.factories(); f++) total += instance.workers(f, 0);
            return total;
        }
    }
}
