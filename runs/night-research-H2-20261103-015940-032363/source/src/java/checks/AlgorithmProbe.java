package research;

import java.util.List;
import org.uma.jmetal.algorithm.multiobjective.mypso.MOPSODivSubDE;
import org.uma.jmetal.algorithm.multiobjective.mypso.MOPSODivSubDEBuilder;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;

/** One short generation, with every evaluator call counted independently. */
public final class AlgorithmProbe {
    private AlgorithmProbe() { }

    private static final class CountingProblem implements Problem<PermutationSolution<Integer>> {
        private final Problem<PermutationSolution<Integer>> delegate;
        private int evaluations;
        CountingProblem(Problem<PermutationSolution<Integer>> delegate) { this.delegate = delegate; }
        public int getNumberOfVariables() { return delegate.getNumberOfVariables(); }
        public int getNumberOfObjectives() { return delegate.getNumberOfObjectives(); }
        public int getNumberOfConstraints() { return delegate.getNumberOfConstraints(); }
        public String getName() { return delegate.getName(); }
        public PermutationSolution<Integer> createSolution() { return delegate.createSolution(); }
        public void evaluate(PermutationSolution<Integer> solution) {
            evaluations++;
            delegate.evaluate(solution);
        }
    }

    public static void main(String[] args) throws Exception {
        int chapter = Integer.parseInt(args[0]);
        System.setProperty("dhfsp.dataDir", args[1]);
        CountingProblem problem = new CountingProblem(BaselineChecks.problem(chapter, 20, 2, 3));
        MOPSODivSubDE algorithm = new MOPSODivSubDEBuilder(problem, 100, 3, 0.4, 0.8, 0.9, 2)
                .setSwarmSize(100).setMaxIterations(200).setLocalSearch(1)
                .setRand_k(0.4).setCrossoverRate(0.2).setMutationRate(0.06)
                .setCrossoverRates4worker(0.4).setCrossoverRates4machine(0.3)
                .setMutationRate4worker(0.1).setMutationRate4machine(0.25).build();
        // The old mutation wrote at machineCount instead of the selected locus.
        PermutationSolution<Integer> singleton = problem.createSolution();
        singleton.setAttribute("machine", java.util.Collections.singletonList(0));
        java.lang.reflect.Method mutation = MOPSODivSubDE.class
                .getDeclaredMethod("mutation4machine", PermutationSolution.class);
        mutation.setAccessible(true);
        mutation.invoke(algorithm, singleton);
        System.out.println("PASS machine mutation selected-locus regression");
        algorithm.run();
        List<PermutationSolution<Integer>> result = algorithm.getResult();
        BaselineChecks.require(result != null && !result.isEmpty(), "Empty search result");
        for (PermutationSolution<Integer> solution : result) { BaselineChecks.finiteObjectives(solution); }
        System.out.println("PROBE result_size=" + result.size() + " actual_evaluations=" + problem.evaluations
                + " configured_counter_limit=200; not a performance comparison");
    }
}
