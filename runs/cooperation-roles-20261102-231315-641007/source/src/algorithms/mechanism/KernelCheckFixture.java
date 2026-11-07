package org.uma.jmetal.util.research.mechanism;

import java.util.Arrays;
import org.uma.jmetal.problem.PermutationProblem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.impl.DefaultIntegerPermutationSolution;
import org.uma.jmetal.util.research.SchedulingProblemData;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.model.ModelKind;

/** Small four-vector fixtures; evaluation is forbidden so these checks consume zero FE. */
final class KernelCheckFixture implements PermutationProblem<PermutationSolution<Integer>>, SchedulingProblemData {
    private static final long serialVersionUID = 1L;
    final Instance instance;

    KernelCheckFixture(boolean heterogeneous) {
        double[][] processing = {{2}, {3}, {4}, {5}};
        double[][][] machine = values(4, heterogeneous ? 5 : 4);
        double[][][] worker = values(heterogeneous ? 3 : 4, 4);
        instance = new Instance("kernel-contract-fixture", ModelKind.CHAPTER4_DUAL_RESOURCE,
                processing, new double[4][1], machine, machine, machine, worker, worker,
                "independent FE0 same-parent generation contract checks");
    }

    PermutationSolution<Integer> solution(int[] js, int offset) {
        PermutationSolution<Integer> solution = createSolution();
        for (int p = 0; p < js.length; p++) {
            int job = js[p], factory = (job + offset) % instance.factories();
            solution.setVariableValue(p, job);
            solution.setVariableValueid(p, factory);
            JobAlignedResources.vector(solution, true).set(p, (job + offset) % instance.machines(factory, 0));
            solution.setVariableValueworker(p, (job + offset + 1) % instance.workers(factory, 0));
        }
        for (int objective = 0; objective < 3; objective++) solution.setObjective(objective, 100 + offset + objective);
        return solution;
    }

    static String fingerprint(PermutationSolution<Integer> solution) {
        return solution.getVariables() + ";" + solution.getVariablesid() + ";"
                + JobAlignedResources.vector(solution, true) + ";" + solution.getVariablesworker()
                + ";" + solution.getObjective(0) + ";" + solution.getObjective(1) + ";" + solution.getObjective(2);
    }

    static int[][] byJob(PermutationSolution<Integer> solution) {
        int[][] values = new int[solution.getNumberOfVariables()][3];
        for (int p = 0; p < values.length; p++) {
            int job = solution.getVariableValue(p);
            values[job][0] = solution.getVariableValueid(p);
            values[job][1] = JobAlignedResources.vector(solution, true).get(p);
            values[job][2] = solution.getVariableValueworker(p);
        }
        return values;
    }

    private static double[][][] values(int... lengths) {
        double[][][] values = new double[lengths.length][1][];
        for (int f = 0; f < lengths.length; f++) {
            values[f][0] = new double[lengths[f]]; Arrays.fill(values[f][0], 1);
        }
        return values;
    }

    @Override public void evaluate(PermutationSolution<Integer> solution) {
        throw new AssertionError("FE0 generation checks must never evaluate a schedule");
    }
    @Override public PermutationSolution<Integer> createSolution() { return new DefaultIntegerPermutationSolution(this); }
    @Override public int getNumberOfVariables() { return instance.jobs(); }
    @Override public int getPermutationLength() { return instance.jobs(); }
    @Override public int getNumberOfFactories() { return instance.factories(); }
    @Override public int getNumberOfObjectives() { return 3; }
    @Override public int getNumberOfConstraints() { return 0; }
    @Override public String getName() { return "KernelFE0Checks"; }
    @Override public Instance getSchedulingInstance() { return instance; }
    @Override public String getInstanceFile() { return "synthetic-FE0-kernel-check"; }
    @Override public int getWorkerVectorLength() { return instance.jobs(); }
}
