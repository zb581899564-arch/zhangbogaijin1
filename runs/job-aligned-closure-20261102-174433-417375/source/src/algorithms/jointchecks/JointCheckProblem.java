package org.uma.jmetal.util.research.joint;

import java.util.IdentityHashMap;
import java.util.List;
import org.uma.jmetal.problem.PermutationProblem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.impl.DefaultIntegerPermutationSolution;
import org.uma.jmetal.util.research.SchedulingProblemData;
import org.uma.jmetal.util.research.model.DynamicDecoder;
import org.uma.jmetal.util.research.model.DynamicParameters;
import org.uma.jmetal.util.research.model.DynamicPrefix;
import org.uma.jmetal.util.research.model.DynamicSchedule;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.model.ModelKind;

/** Heterogeneous local resource pools and a nonzero later-stage return. */
public final class JointCheckProblem implements PermutationProblem<PermutationSolution<Integer>>, SchedulingProblemData {
    private static final long serialVersionUID = 1L;
    public final Instance instance;
    public final DynamicParameters parameters;
    final IdentityHashMap<PermutationSolution<Integer>, DynamicPrefix> prepared = new IdentityHashMap<>();
    public JointCheckProblem(int jobs) {
        double[][] processing = new double[jobs][2], setup = new double[jobs][2];
        for (int j = 0; j < jobs; j++) {
            processing[j] = new double[] {4 + j, 11 - j / 2.0}; setup[j] = new double[] {1, 2};
        }
        instance = new Instance("joint-check", ModelKind.CHAPTER4_DUAL_RESOURCE, processing, setup,
                new double[][][] {{{1, 2}, {1, 1.2}}, {{1.5, 2, 2.5}, {1}}, {{.8}, {1, 1.5}}},
                new double[][][] {{{4, 6}, {4, 5}}, {{5, 6, 7}, {4}}, {{3}, {4, 6}}},
                new double[][][] {{{1, 1}, {1, 1}}, {{1, 1, 1}, {1}}, {{1}, {1, 1}}},
                new double[][][] {{{1}, {1}}, {{.8, 1.2}, {1}}, {{1}, {1}}},
                new double[][][] {{{8}, {8}}, {{6, 9}, {8}}, {{7}, {9}}}, "synthetic contract check, not performance data");
        parameters = DynamicParameters.uniform(instance, .07, .05, 1.5, .1);
    }
    public void prepare(PermutationSolution<Integer> solution, DynamicPrefix prefix) { prepared.put(solution, prefix); }
    @Override public void evaluate(PermutationSolution<Integer> solution) {
        int[] js = integers(solution.getVariables()), fa = integers(solution.getVariablesid());
        int[] ma = integers(machines(solution)), wa = integers(solution.getVariablesworker());
        DynamicSchedule full = DynamicDecoder.full(instance, parameters, js, fa, ma, wa, null);
        DynamicPrefix prefix = prepared.remove(solution);
        if (prefix != null) {
            DynamicSchedule replay = DynamicDecoder.incremental(instance, parameters, js, fa, ma, wa, null, prefix, null);
            for (int q = 0; q < 3; q++) JointChecks.close(replay.objectives()[q], full.objectives()[q], 1e-11);
            JointChecks.require(prefix.size() >= Math.min(4, instance.jobs()), "Prepared prefix omitted block actions");
        }
        for (int q = 0; q < 3; q++) solution.setObjective(q, full.objectives()[q]);
        solution.setAttribute("dynamic.schedule", full);
    }
    @SuppressWarnings("unchecked")
    static List<Integer> machines(PermutationSolution<Integer> solution) { return (List<Integer>) solution.getAttribute("machine"); }
    private static int[] integers(List<Integer> list) {
        int[] result = new int[list.size()]; for (int i = 0; i < result.length; i++) result[i] = list.get(i); return result;
    }
    @Override public PermutationSolution<Integer> createSolution() { return new DefaultIntegerPermutationSolution(this); }
    @Override public int getNumberOfVariables() { return instance.jobs(); }
    @Override public int getPermutationLength() { return instance.jobs(); }
    @Override public int getNumberOfFactories() { return instance.factories(); }
    @Override public int getNumberOfObjectives() { return 3; }
    @Override public int getNumberOfConstraints() { return 0; }
    @Override public String getName() { return "JointCheckProblem"; }
    @Override public Instance getSchedulingInstance() { return instance; }
    @Override public String getInstanceFile() { return "synthetic-joint-check"; }
    @Override public int getWorkerVectorLength() { return instance.jobs(); }
}
