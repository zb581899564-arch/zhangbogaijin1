package org.uma.jmetal.util.research.classic;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.joint.JointCheckProblem;
import org.uma.jmetal.util.research.runtime.SeededRandom;

final class ClassicMathChecks {
    private ClassicMathChecks() { }
    static void run() {
        SeededRandom.reset(1201);
        nsga(); spea(); normalizedDistances(); decomposition(); variation(); jobAlignment(); interruptions();
        System.out.println("CLASSIC_MATH_PASS NSGA-fronts+crowding+elitism SPEA-strength+raw+density+lex-truncation MOEAD-weights+neighbors+frozen-scale+ideal+Tchebycheff");
    }
    private static void nsga() {
        NsgaSelection selection = new NsgaSelection(() -> { });
        List<PermutationSolution<Integer>> pool = points(new double[][] {
                {0,4,0}, {1,3,0}, {2,2,0}, {3,1,0}, {4,0,0}, {5,5,1}});
        NsgaSelection.Scores score = selection.score(pool);
        for (int i = 0; i < 5; i++) ClassicChecks.require(score.rank[i] == 0, "NSGA nondominated rank");
        ClassicChecks.require(score.rank[5] == 1, "NSGA dominated rank");
        ClassicChecks.close(score.crowding[1], 1); ClassicChecks.close(score.crowding[2], 1);
        List<PermutationSolution<Integer>> selected = selection.select(pool, 2);
        ClassicChecks.require(selected.contains(pool.get(0)) && selected.contains(pool.get(4)), "NSGA boundary elitism");
        NsgaSelection.Selection retained = selection.environmental(pool, 4);
        for (int p = 0; p < retained.population.size(); p++) if (retained.population.get(p) == pool.get(1))
            ClassicChecks.close(retained.scores.crowding[p], 1);
        score = selection.score(points(new double[][] {{1,1,1},{1,1,1},{1,1,1}}));
        for (double distance : score.crowding) ClassicChecks.require(!Double.isNaN(distance), "Constant-objective crowding NaN");
    }
    private static void spea() {
        SpeaSelection selection = new SpeaSelection(() -> { });
        SpeaSelection.Scores score = selection.score(points(new double[][] {{0,0,0},{1,1,1},{2,2,2},{0,2,0}}));
        ClassicChecks.require(Arrays.equals(score.strength, new int[] {3,1,0,1}), "SPEA strength hand calculation");
        ClassicChecks.require(Arrays.equals(score.raw, new int[] {0,3,5,3}), "SPEA raw fitness hand calculation");
        ClassicChecks.close(score.density[0], .25); ClassicChecks.close(score.density[1], 1 / (Math.sqrt(3) + 2));
        ClassicChecks.require(selection.select(score, 2).equals(Arrays.asList(0,3)), "SPEA density-based dominated fill");
        score = selection.score(points(new double[][] {{0,10,0},{1,9,0},{2,8,0},{10,0,0}}));
        ClassicChecks.require(selection.select(score, 3).equals(Arrays.asList(0,2,3)), "SPEA lexicographic second-neighbor tie break");
        score = selection.score(points(new double[][] {{1,1,1},{1,1,1}}));
        ClassicChecks.require(Arrays.equals(score.raw, new int[] {0,0}), "Equal objectives must not dominate");
        ClassicChecks.close(score.density[0], .5);
    }
    private static void decomposition() {
        SeededRandom.reset(3321); long expected = SeededRandom.current().nextLong();
        SeededRandom.reset(3321); double[][] weights = MoeadDecomposition.weights(() -> { });
        ClassicChecks.require(expected == SeededRandom.current().nextLong(), "Weight construction consumed search RNG");
        Set<String> unique = new HashSet<>();
        for (double[] weight : weights) {
            ClassicChecks.close(weight[0] + weight[1] + weight[2], 1);
            for (double value : weight) ClassicChecks.require(value >= 0 && value <= 1, "Simplex bounds");
            unique.add(Arrays.toString(weight));
        }
        ClassicChecks.require(unique.size() == 100, "100 unique fixed weights");
        for (int m = 0; m < 3; m++) ClassicChecks.close(weights[m][m], 1);
        double[][] objective = new double[100][3];
        for (double[] row : objective) { row[0] = 2; row[1] = 4; row[2] = 8; }
        List<PermutationSolution<Integer>> initial = points(objective);
        MoeadDecomposition model = new MoeadDecomposition(initial, 20, () -> { });
        for (int i = 0; i < 100; i++) ClassicChecks.require(model.neighbors[i].length == 20 && model.neighbors[i][0] == i, "Weight neighbors include self");
        PermutationSolution<Integer> child = points(new double[][] {{1,6,10}}).get(0);
        model.updateIdeal(child);
        ClassicChecks.close(model.scale[0], 2); ClassicChecks.close(model.scale[1], 4); ClassicChecks.close(model.scale[2], 8);
        ClassicChecks.close(model.ideal[0], 1); ClassicChecks.close(model.ideal[1], 4); ClassicChecks.close(model.ideal[2], 8);
        ClassicChecks.close(model.scalar(initial.get(0), 0), .5); ClassicChecks.close(model.scalar(child, 1), .5);
    }
    private static void normalizedDistances() {
        double[][] objectives = {{1,6,3},{2,4,6},{3,2,9},{4,1,12}}, converted = new double[4][3];
        double[] units = {100,.01,50};
        for (int i = 0; i < objectives.length; i++) for (int m = 0; m < 3; m++) converted[i][m] = objectives[i][m] * units[m];
        List<PermutationSolution<Integer>> first = points(objectives), second = points(converted);
        double[] frozen = FrozenObjectiveScale.from(first, () -> { });
        SpeaSelection selection = new SpeaSelection(frozen, () -> { });
        SpeaSelection convertedSelection = new SpeaSelection(FrozenObjectiveScale.from(second, () -> { }), () -> { });
        Arrays.fill(frozen, 777); // A caller cannot change the selection's frozen metric.
        SpeaSelection.Scores a = selection.score(first), b = convertedSelection.score(second);
        for (int i = 0; i < 4; i++) {
            ClassicChecks.close(a.fitness[i], b.fitness[i]);
            for (int j = 0; j < 4; j++) ClassicChecks.close(a.distance[i][j], b.distance[i][j]);
        }
        ClassicChecks.require(selection.select(a,2).equals(convertedSelection.select(b,2)), "SPEA normalized truncation changed under unit conversion");
        double[] zero = FrozenObjectiveScale.from(points(new double[][] {{0,2,4},{0,2,4}}), () -> { });
        ClassicChecks.require(Arrays.equals(zero,new double[] {1,2,4}), "Zero-mean scale fallback");
        System.out.println("CLASSIC_SCALE_PASS initial-paid-mean-frozen zero-to-1 SPEA-density+truncation-unit-invariance");
    }
    private static void variation() {
        JointCheckProblem fixture = new JointCheckProblem(6);
        PermutationSolution<Integer> a = fixture.createSolution(), b = fixture.createSolution();
        String first = ClassicRuntimeChecks.signature(a), second = ClassicRuntimeChecks.signature(b);
        for (int setting = 0; setting < 3; setting++) {
            ClassicVariation variation = new ClassicVariation(fixture.instance, new ClassicConfig("NSGA2_4V", setting), () -> { });
            for (int i = 0; i < 120; i++) {
                PermutationSolution<Integer> child = variation.child(a,b); SchedulingEncoding.repair(child, fixture.instance);
                ClassicRuntimeChecks.legal(child, fixture);
            }
        }
        ClassicChecks.require(first.equals(ClassicRuntimeChecks.signature(a)) && second.equals(ClassicRuntimeChecks.signature(b)), "Variation mutated a parent");
    }
    private static void jobAlignment() {
        JointCheckProblem fixture = new JointCheckProblem(6);
        PermutationSolution<Integer> a = fixture.createSolution(), b = fixture.createSolution();
        for (int p = 0; p < 6; p++) { setJobTuple(a,p,p,fixture); setJobTuple(b,p,5-p,fixture); }
        // This fixed fixture seed has a nontrivial OX order and no changed resource
        // bindings. Both parents give each job the same tuple in different positions.
        SeededRandom.reset(4);
        PermutationSolution<Integer> child = new ClassicVariation(fixture.instance, new ClassicConfig("NSGA2_4V",1), () -> { }).child(a,b);
        SchedulingEncoding.repair(child, fixture.instance);
        ClassicChecks.require(child.getVariables().equals(Arrays.asList(5,2,1,3,4,0)), "Fixed OX fixture order");
        int[] ma = SchedulingEncoding.machineIntegers(child);
        for (int p = 0; p < 6; p++) {
            int j = child.getVariableValue(p), f = j % 3;
            ClassicChecks.require(child.getVariableValueid(p) == f && ma[p] == j / 3 % fixture.instance.machines(f,0)
                    && child.getVariableValueworker(p) == j / 3 % fixture.instance.workers(f,0), "Resources did not follow job identity");
        }
    }
    @SuppressWarnings("unchecked")
    private static void setJobTuple(PermutationSolution<Integer> solution, int position, int job, JointCheckProblem fixture) {
        int f = job % 3; solution.setVariableValue(position,job); solution.setVariableValueid(position,f);
        ((List<Integer>) solution.getAttribute("machine")).set(position, job / 3 % fixture.instance.machines(f,0));
        solution.setVariableValueworker(position, job / 3 % fixture.instance.workers(f,0));
    }
    private static void interruptions() {
        double[][] objectives = new double[100][3];
        for (int i = 0; i < 100; i++) { objectives[i][0] = i; objectives[i][1] = 100-i; objectives[i][2] = 1; }
        List<PermutationSolution<Integer>> pool = points(objectives);
        RuntimeException expected = new IllegalStateException("expected checkpoint interruption");
        int[] calls = {0};
        expectInterruption(() -> new NsgaSelection(() -> { if (++calls[0] == 104) throw expected; }).score(pool), expected);
        calls[0] = 0;
        expectInterruption(() -> new MoeadDecomposition(pool,20,() -> { if (++calls[0] == 205) throw expected; }), expected);
        SpeaSelection.Scores dominated = new SpeaSelection(() -> { }).score(points(new double[][] {{0,0,0},{1,1,1},{2,2,2},{3,3,3}}));
        expectInterruption(() -> new SpeaSelection(() -> { throw expected; }).select(dominated,2), expected);
        System.out.println("CLASSIC_PREEMPTION_PASS NSGA-objective-sort SPEA-dominated-fill-sort MOEAD-neighbor-sort preserve-exception-identity");
    }
    private static void expectInterruption(Runnable action, RuntimeException expected) {
        try { action.run(); throw new AssertionError("Checkpoint interruption swallowed"); }
        catch (RuntimeException actual) { ClassicChecks.require(actual == expected, "Checkpoint exception identity changed"); }
    }
    private static List<PermutationSolution<Integer>> points(double[][] objectives) {
        JointCheckProblem problem = new JointCheckProblem(6); List<PermutationSolution<Integer>> result = new ArrayList<>();
        for (double[] values : objectives) {
            PermutationSolution<Integer> solution = problem.createSolution();
            for (int m = 0; m < 3; m++) solution.setObjective(m, values[m]); result.add(solution);
        }
        return result;
    }
}
