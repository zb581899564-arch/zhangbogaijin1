package research.dynamic;

import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.PermutationProblem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.impl.DefaultIntegerPermutationSolution;
import org.uma.jmetal.util.research.SchedulingProblemData;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.model.ModelKind;
import org.uma.jmetal.util.research.runtime.RunContext;

/** Specifically force interruption after FE acquisition and before a complete evaluation. */
public final class DynamicRuntimeChecks {
    private DynamicRuntimeChecks() { }
    public static void main(String[] args) {
        Toy raw = new Toy();
        RunContext<PermutationSolution<Integer>> context = new RunContext<>(raw, 10, 19, .1);
        raw.inside = () -> { while (true) context.checkpoint(); };
        PermutationSolution<Integer> candidate = context.problem().createSolution();
        context.run(new OneCall(() -> context.problem().evaluate(candidate)));
        require(context.stopReason().equals("TIME_LIMIT"), "Wrong stop reason");
        require(context.budget().attempted() == 1 && context.budget().failed() == 1
                && context.budget().successful() == 0 && context.budget().timeInterruptedAttempts() == 1,
                "Interrupted decode accounting");
        require(context.result().isEmpty(), "Incomplete evaluation entered archive");
        double stopped = context.clock().elapsedSeconds();
        for (int i = 0; i < 100; i++) require(context.clock().elapsedSeconds() == stopped, "Clock did not freeze");
        System.out.println("DYNAMIC_RUNTIME_CHECKS_PASS: interrupted attempt counted, no partial archive, stopped clock frozen");
    }
    private static void require(boolean condition, String message) { if (!condition) throw new AssertionError(message); }
    private static final class OneCall implements Algorithm<Object> {
        private static final long serialVersionUID = 1L;
        private final Runnable action;
        OneCall(Runnable action) { this.action = action; }
        public void run() { action.run(); }
        public Object getResult() { return null; }
        public String getName() { return "Deadline contract check"; }
        public String getDescription() { return getName(); }
    }
    private static final class Toy implements PermutationProblem<PermutationSolution<Integer>>, SchedulingProblemData {
        private static final long serialVersionUID = 1L;
        private transient Runnable inside;
        private final Instance instance = new Instance("deadline-check", ModelKind.CHAPTER4_DUAL_RESOURCE,
                new double[][] {{1}}, new double[][] {{0}}, new double[][][] {{{1}}},
                new double[][][] {{{1}}}, new double[][][] {{{1}}}, new double[][][] {{{1}}},
                new double[][][] {{{1}}}, "SYNTHETIC deadline check");
        public void evaluate(PermutationSolution<Integer> s) { inside.run(); for (int i = 0; i < 3; i++) s.setObjective(i, 1); }
        public PermutationSolution<Integer> createSolution() { return new DefaultIntegerPermutationSolution(this); }
        public Instance getSchedulingInstance() { return instance; }
        public String getInstanceFile() { return "synthetic"; }
        public int getWorkerVectorLength() { return 1; }
        public int getNumberOfVariables() { return 1; }
        public int getPermutationLength() { return 1; }
        public int getNumberOfFactories() { return 1; }
        public int getNumberOfObjectives() { return 3; }
        public int getNumberOfConstraints() { return 0; }
        public String getName() { return "Deadline toy"; }
    }
}
