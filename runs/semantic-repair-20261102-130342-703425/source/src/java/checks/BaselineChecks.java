package research;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.impl.DefaultIntegerPermutationSolution;
import org.uma.jmetal.util.comparator.DominanceComparator;
import org.uma.jmetal.util.research.InstanceFileProvider;

/** Structural and repeat-evaluation checks; these do not prove model fidelity. */
public final class BaselineChecks {
    private BaselineChecks() { }

    @SuppressWarnings("unchecked")
    static Problem<PermutationSolution<Integer>> problem(int chapter, int jobs, int stages, int factories)
            throws Exception {
        String name = chapter == 3 ? "DHFSP" : "EDHHFSPW";
        return (Problem<PermutationSolution<Integer>>) Class
                .forName("org.uma.jmetal.problem.multiobjective.dfsp." + name)
                .getConstructor(int.class, int.class, int.class, int.class)
                .newInstance(jobs, stages, factories, 1);
    }

    static void require(boolean condition, String message) {
        if (!condition) { throw new AssertionError(message); }
    }

    @SuppressWarnings("unchecked")
    private static void checkCopy(DefaultIntegerPermutationSolution source) {
        // Operators replace this attribute, so getters must track its actual list.
        source.setAttribute("machine", new ArrayList<>(source.getVariablesmachine()));
        DefaultIntegerPermutationSolution copy = (DefaultIntegerPermutationSolution) source.copy();
        require(copy.getVariables().equals(source.getVariables()), "JS copy mismatch");
        require(copy.getVariablesid().equals(source.getVariablesid()), "FA copy mismatch");
        require(copy.getVariablesworker().equals(source.getVariablesworker()), "WA copy mismatch");
        require(copy.getVariablesmachine().equals(source.getVariablesmachine()), "MA copy mismatch");
        require(copy.getAttribute("machine") == copy.getVariablesmachine(), "MA attribute detached");
        require(copy.getAttribute("worker") == copy.getVariablesworker(), "WA attribute detached");
        int originalMachine = source.getVariableValuemachine(0);
        int originalWorker = source.getVariableValueworker(0);
        ((List<Integer>) copy.getAttribute("machine")).set(0, -99);
        copy.setVariableValueworker(0, -99);
        require(source.getVariableValuemachine(0) == originalMachine, "MA shares storage");
        require(source.getVariableValueworker(0) == originalWorker, "WA shares storage");
    }

    static void finiteObjectives(PermutationSolution<Integer> solution) {
        for (int index : new int[] {0, 1, 2}) {
            require(Double.isFinite(solution.getObjective(index)) && solution.getObjective(index) > 0,
                    "Invalid physical objective " + index);
        }
    }

    private static void checkInstance(int chapter, Path file) throws Exception {
        String[] dimensions = file.getFileName().toString().split("_");
        Problem<PermutationSolution<Integer>> problem = problem(chapter,
                Integer.parseInt(dimensions[0]), Integer.parseInt(dimensions[1]), Integer.parseInt(dimensions[2]));
        DefaultIntegerPermutationSolution source = (DefaultIntegerPermutationSolution) problem.createSolution();
        require(source.getVariablesworker().size() == ((InstanceFileProvider) problem).getWorkerVectorLength(),
                "Worker vector length mismatch");
        require(!source.getVariablesworker().contains(null), "Null WA entry");
        require(!source.getVariablesmachine().contains(null), "Null MA entry");
        checkCopy(source);
        problem.evaluate(source);
        finiteObjectives(source);
        double[] first = source.getObjectives().clone();
        for (int repeat = 0; repeat < 3; repeat++) {
            problem.evaluate(source);
            require(Arrays.equals(first, source.getObjectives()), "Evaluation is not repeatable");
        }
        @SuppressWarnings("unchecked")
        DefaultIntegerPermutationSolution copy = (DefaultIntegerPermutationSolution) source.copy();
        problem.evaluate(copy);
        require(Arrays.equals(first, copy.getObjectives()), "Copied encoding changes objectives");
        System.out.println("PASS " + file.getFileName());
    }

    private static void checkPhysicalDominance(int chapter, Path data, Path output) throws Exception {
        setup(chapter, data.resolve("20_2_3_1.txt"), output);
        Problem<PermutationSolution<Integer>> p = problem(chapter, 20, 2, 3);
        PermutationSolution<Integer> a = p.createSolution(), b = p.createSolution();
        require(a.getNumberOfObjectives() == 3, "Auxiliary factory indices leaked into objectives");
        for (int i = 0; i < 3; i++) { a.setObjective(i, 1); b.setObjective(i, 2); }
        a.setAttribute("dhfsp.factoryMetrics", new org.uma.jmetal.util.research.SchedulingMetadata(
                new double[]{100,0,5}, new double[]{0,100,5}, new double[]{5,0,100}));
        b.setAttribute("dhfsp.factoryMetrics", new org.uma.jmetal.util.research.SchedulingMetadata(
                new double[]{0,100,5}, new double[]{5,0,100}, new double[]{0,100,5}));
        require(new DominanceComparator<PermutationSolution<Integer>>().compare(a, b) == -1,
                "Physical dominance depends on factory metadata");
        System.out.println("PASS three physical objectives ignore all auxiliary factory indices");
    }

    private static void setup(int chapter, Path file, Path output) throws Exception {
        if (chapter != 4) return;
        String[] d = file.getFileName().toString().split("_");
        Path sut = output.resolve(file.getFileName().toString());
        if (!java.nio.file.Files.exists(sut)) org.uma.jmetal.util.research.model.SetupTimes
                .generatedSupplement(Integer.parseInt(d[0]),Integer.parseInt(d[1]),314159).write(sut);
        System.setProperty("dhfsp.setupFile", sut.toString());
    }

    public static void main(String[] args) throws Exception {
        int chapter = Integer.parseInt(args[0]);
        Path data = Paths.get(args[1]).toAbsolutePath();
        System.setProperty("dhfsp.dataDir", data.toString());
        System.setProperty("dhfsp.standbyPower", "1");
        org.uma.jmetal.util.research.runtime.SeededRandom.reset(271828);
        Path output = Paths.get(args[2]).toAbsolutePath();
        java.nio.file.Files.createDirectories(output);
        try (java.util.stream.Stream<Path> files = java.nio.file.Files.list(data)) {
            for (Path file : (Iterable<Path>) files.filter(p -> p.toString().endsWith(".txt")).sorted()::iterator) {
                setup(chapter, file, output);
                checkInstance(chapter, file);
            }
        }
        checkPhysicalDominance(chapter, data, output);
        System.out.println("PASS structural checks; sourced-model structural checks complete");
    }
}
