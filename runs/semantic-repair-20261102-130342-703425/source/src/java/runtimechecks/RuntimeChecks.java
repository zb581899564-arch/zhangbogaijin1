package research;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.Solution;
import org.uma.jmetal.util.pseudorandom.JMetalRandom;
import org.uma.jmetal.util.research.runtime.BudgetExhaustedException;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Small adversarial checks of the runtime contract, not an optimizer benchmark. */
public final class RuntimeChecks {
    private RuntimeChecks() { }

    public static void main(String[] args) throws Exception {
        checkBudgetBoundaries();
        checkExactEndAndRepeatEvaluation();
        checkEvaluationFailures();
        checkIndependentArchive();
        checkUnifiedRandomStream();
        checkSingleThreadBoundary();
        System.out.println("PASS runtime: FE boundaries, failure accounting, three-objective archive, RNG, sole-thread rule");
    }

    private static void checkBudgetBoundaries() {
        for (long limit : new long[] {0, 1, 3, 5, 7, 10}) {
            CountingProblem raw = new CountingProblem();
            RunContext<TestSolution> context = new RunContext<>(raw, limit, 17L);
            context.run(new TestAlgorithm(() -> {
                // A swarm of five followed by three generations of global and local evaluations.
                for (int i = 0; i < 5; i++) { context.problem().evaluate(raw.createSolution()); }
                for (int generation = 0; generation < 3; generation++) {
                    for (int i = 0; i < 5; i++) {
                        context.problem().evaluate(raw.createSolution());
                        context.problem().evaluate(raw.createSolution());
                    }
                }
                throw new AssertionError("Budget should interrupt this synthetic algorithm");
            }));
            require(raw.calls == limit, "Decoder called beyond or before FE limit " + limit);
            require(context.budget().attempted() == limit, "Incorrect attempt count");
            require(context.budget().successful() == limit, "Incorrect success count");
            require(context.budget().failed() == 0, "Unexpected failure count");
            require(context.budget().remaining() == 0, "Budget not exhausted");
            require(context.result().size() == (limit == 0 ? 0 : 1), "Unexpected partial-run archive");
            for (TestSolution solution : context.result()) {
                require(solution.getVariableValue(0) < limit, "Unevaluated solution escaped");
                require(solution.getObjective(0) == solution.getVariableValue(0), "Stale objectives escaped");
            }
        }
        System.out.println("PASS FE=0,1,<swarm,=swarm and partial initialization/global/local batch");
    }

    private static void checkExactEndAndRepeatEvaluation() {
        CountingProblem raw = new CountingProblem();
        RunContext<TestSolution> context = new RunContext<>(raw, 2, 5L);
        TestSolution solution = raw.createSolution();
        context.run(new TestAlgorithm(() -> {
            context.problem().evaluate(solution);
            context.problem().evaluate(solution);
        }));
        require(raw.calls == 2 && context.budget().attempted() == 2, "Repeated solution needs another FE");
        boolean rejected = false;
        try { context.problem().evaluate(solution); } catch (BudgetExhaustedException expected) { rejected = true; }
        require(rejected && raw.calls == 2, "Guard must reject before decode");
        require(context.budget().failed() == 0, "Exhaustion is not a failed decoder attempt");
    }

    private static void checkEvaluationFailures() {
        CountingProblem raw = new CountingProblem();
        RunContext<TestSolution> context = new RunContext<>(raw, 4, 3L);
        context.problem().evaluate(raw.createSolution());
        raw.fail = true;
        boolean propagated = false;
        try { context.run(new TestAlgorithm(() -> context.problem().evaluate(raw.createSolution()))); }
        catch (IllegalStateException expected) { propagated = true; }
        require(propagated, "Ordinary decoder exception must propagate");
        require(raw.calls == 2 && context.budget().attempted() == 2, "Failed decode still consumes FE");
        require(context.budget().successful() == 1 && context.budget().failed() == 1, "Failed FE accounting");
        require(context.result().size() == 1, "Failed solution entered archive");
        raw.fail = false;
        raw.invalid = true;
        try { context.problem().evaluate(raw.createSolution()); throw new AssertionError("NaN accepted"); }
        catch (IllegalStateException expected) { /* invalid physical objective */ }
        require(context.budget().attempted() == 3 && context.budget().failed() == 2, "NaN must consume one failed FE");
        require(context.result().size() == 1, "Invalid solution entered archive");
        raw.invalid = false;
        raw.preserveObjectives = true;
        TestSolution unserializable = vector(10, -1, -1, -1);
        unserializable.setAttribute("resource", new Object());
        try { context.problem().evaluate(unserializable); throw new AssertionError("Unsupported snapshot accepted"); }
        catch (IllegalStateException expected) { /* Must preserve the old archive when copying fails. */ }
        require(context.budget().attempted() == 4 && context.budget().failed() == 3, "Snapshot error FE accounting");
        require(context.result().size() == 1 && context.result().get(0).getObjective(0) == 0,
                "Failed snapshot discarded a prior valid entry");
        boolean secondRunRejected = false;
        try { context.run(new TestAlgorithm(() -> { })); }
        catch (IllegalStateException expected) { secondRunRejected = true; }
        require(secondRunRejected, "Run context reused");
        System.out.println("PASS throwing/invalid evaluations consume FE, propagate, and never enter archive");
    }

    @SuppressWarnings("unchecked")
    private static void checkIndependentArchive() {
        CountingProblem raw = new CountingProblem();
        raw.preserveObjectives = true;
        RunContext<TestSolution> context = new RunContext<>(raw, 8, 9L);
        TestSolution first = vector(1, 1, 4, 4);
        first.setAttribute("nested", new ArrayList<>(Arrays.asList(new ArrayList<>(Arrays.asList(7, 8)))));
        context.problem().evaluate(first);
        context.problem().evaluate(vector(2, 4, 1, 4));
        context.problem().evaluate(vector(3, 4, 4, 1));
        context.problem().evaluate(vector(4, 5, 5, 5)); // Dominated in all three objectives.
        context.problem().evaluate(vector(5, 1, 4, 4)); // Exact objective duplicate keeps the first.
        first.setObjective(0, -999);
        first.setVariableValue(0, 999);
        ((List<List<Integer>>) first.getAttribute("nested")).get(0).set(0, 999);
        List<TestSolution> result = context.result();
        require(result.size() == 3, "Archive dominance must use all three minimization objectives");
        TestSolution saved = result.get(0);
        require(saved.getVariableValue(0) == 1 && saved.getObjective(0) == 1, "Archive aliases candidate");
        require(((List<List<Integer>>) saved.getAttribute("nested")).get(0).get(0) == 7, "Archive aliases nested attributes");
        saved.setObjective(0, -888);
        ((List<List<Integer>>) saved.getAttribute("nested")).get(0).set(0, 888);
        require(context.result().get(0).getObjective(0) == 1, "Archive aliases returned snapshot");
        require(((List<List<Integer>>) context.result().get(0).getAttribute("nested")).get(0).get(0) == 7,
                "Returned attributes alias archive");
        context.problem().evaluate(vector(6, 0, 0, 0));
        require(context.result().size() == 1 && context.result().get(0).getVariableValue(0) == 6,
                "Dominating candidate must remove older entries");
        System.out.println("PASS independent solution/objective/nested-attribute snapshots and exact three-objective Pareto archive");
    }

    private static void checkUnifiedRandomStream() {
        long seed = 77531L;
        SeededRandom.reset(seed);
        Random reference = new Random(seed);
        require(SeededRandom.current().nextLong() == reference.nextLong(), "Java Random not seeded");
        require(JMetalRandom.getInstance().nextDouble() == reference.nextDouble(), "jMetal is not the same stream");
        require(JMetalRandom.getInstance().nextInt(2, 15) == 2 + reference.nextInt(14), "Inclusive jMetal integer bounds");
        List<Integer> actual = new ArrayList<>(Arrays.asList(0, 1, 2, 3, 4, 5));
        List<Integer> expected = new ArrayList<>(actual);
        SeededRandom.shuffle(actual);
        java.util.Collections.shuffle(expected, reference);
        require(actual.equals(expected), "Shuffle uses a separate source");
        String first = randomTrace(seed);
        require(first.equals(randomTrace(seed)), "Same seed produces different trace");
        require(!first.equals(randomTrace(seed + 1)), "Distinct test seeds produce identical trace");
        JMetalRandom.getInstance().setSeed(seed);
        require(SeededRandom.current().nextDouble() == new Random(seed).nextDouble(), "jMetal seed does not reset shared stream");
        require(SeededRandom.seed() == seed, "Seed metadata stale");
        System.out.println("PASS one seeded stream shared by java.util.Random, Collections.shuffle and JMetalRandom");
    }

    private static String randomTrace(long seed) {
        SeededRandom.reset(seed);
        StringBuilder trace = new StringBuilder();
        for (int i = 0; i < 15; i++) {
            trace.append(SeededRandom.current().nextInt(100)).append(':');
            trace.append(Double.doubleToLongBits(JMetalRandom.getInstance().nextDouble())).append(';');
        }
        return trace.toString();
    }

    private static void checkSingleThreadBoundary() throws InterruptedException {
        CountingProblem raw = new CountingProblem();
        RunContext<TestSolution> context = new RunContext<>(raw, 1, 42L);
        Throwable[] caught = new Throwable[5];
        Thread other = new Thread(() -> {
            try { context.problem().evaluate(raw.createSolution()); } catch (Throwable error) { caught[0] = error; }
            try { SeededRandom.current(); } catch (Throwable error) { caught[1] = error; }
            try { context.problem().createSolution(); } catch (Throwable error) { caught[2] = error; }
            try { context.result(); } catch (Throwable error) { caught[3] = error; }
            try { context.run(new TestAlgorithm(() -> { })); } catch (Throwable error) { caught[4] = error; }
        });
        other.start();
        other.join();
        for (Throwable error : caught) {
            require(error instanceof IllegalStateException, "Unsupported worker threads should fail explicitly");
        }
        require(raw.calls == 0 && context.budget().attempted() == 0, "Worker thread consumed an FE");
        context.run(new TestAlgorithm(() -> context.problem().evaluate(context.problem().createSolution())));
        require(raw.calls == 1, "Rejected cross-thread call damaged the owner context");
    }

    private static TestSolution vector(int id, double a, double b, double c) {
        TestSolution result = new TestSolution(id);
        result.setObjective(0, a);
        result.setObjective(1, b);
        result.setObjective(2, c);
        return result;
    }

    private static void require(boolean condition, String message) {
        if (!condition) { throw new AssertionError(message); }
    }

    private static final class TestAlgorithm implements Algorithm<List<TestSolution>> {
        private static final long serialVersionUID = 1L;
        private final Runnable action;
        TestAlgorithm(Runnable action) { this.action = action; }
        @Override public void run() { action.run(); }
        @Override public List<TestSolution> getResult() { throw new AssertionError("Unsafe original result requested"); }
        @Override public String getName() { return "RuntimeChecks"; }
        @Override public String getDescription() { return "Synthetic FE control-flow check"; }
    }

    private static final class CountingProblem implements Problem<TestSolution> {
        private static final long serialVersionUID = 1L;
        private int nextId;
        private long calls;
        private boolean fail;
        private boolean invalid;
        private boolean preserveObjectives;
        @Override public void evaluate(TestSolution solution) {
            calls++;
            if (fail) { solution.setObjective(0, -1000); throw new IllegalStateException("Expected decoder failure"); }
            if (!preserveObjectives) {
                for (int i = 0; i < 3; i++) { solution.setObjective(i, solution.getVariableValue(0)); }
            }
            if (invalid) { solution.setObjective(2, Double.NaN); }
        }
        @Override public TestSolution createSolution() { return new TestSolution(nextId++); }
        @Override public int getNumberOfVariables() { return 1; }
        @Override public int getNumberOfObjectives() { return 3; }
        @Override public int getNumberOfConstraints() { return 0; }
        @Override public String getName() { return "CountingProblem"; }
    }

    private static final class TestSolution implements Solution<Integer> {
        private static final long serialVersionUID = 1L;
        private final double[] objectives = new double[3];
        private final List<Integer> variables = new ArrayList<>();
        private final Map<Object, Object> attributes = new HashMap<>();
        TestSolution(int id) { variables.add(id); }
        @Override public void setObjective(int index, double value) { objectives[index] = value; }
        @Override public double getObjective(int index) { return objectives[index]; }
        @Override public double[] getObjectives() { return objectives; }
        @Override public Integer getVariableValue(int index) { return variables.get(index); }
        @Override public List<Integer> getVariables() { return variables; }
        @Override public void setVariableValue(int index, Integer value) { variables.set(index, value); }
        @Override public String getVariableValueString(int index) { return String.valueOf(variables.get(index)); }
        @Override public int getNumberOfVariables() { return variables.size(); }
        @Override public int getNumberOfObjectives() { return 3; }
        @Override public Solution<Integer> copy() {
            TestSolution result = vector(getVariableValue(0), objectives[0], objectives[1], objectives[2]);
            result.attributes.putAll(attributes); // Deliberately shallow: runtime must not trust this.
            return result;
        }
        @Override public void setAttribute(Object id, Object value) { attributes.put(id, value); }
        @Override public Object getAttribute(Object id) { return attributes.get(id); }
        @Override public Map<Object, Object> getAttributes() { return attributes; }
    }
}
