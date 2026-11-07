package research.normalized;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingProblemData;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.model.SetupTimes;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import org.uma.jmetal.util.research.search.CanonicalHmopso;
import org.uma.jmetal.util.research.search.SearchConfig;

/** The supported, guarded entry point for both reconstructed paper baselines. */
public final class NormalizedRun {
    private NormalizedRun() { }

    @SuppressWarnings("unchecked")
    public static Problem<PermutationSolution<Integer>> problem(int chapter, String name) throws Exception {
        String[] dimensions = name.replace(".txt", "").split("_");
        if (dimensions.length != 4) throw new IllegalArgumentException("Expected jobs_stages_factories_id.txt");
        return (Problem<PermutationSolution<Integer>>) Class.forName("org.uma.jmetal.problem.multiobjective.dfsp."
                + (chapter == 3 ? "DHFSP" : "EDHHFSPW"))
                .getConstructor(int.class, int.class, int.class, int.class)
                .newInstance(Integer.parseInt(dimensions[0]), Integer.parseInt(dimensions[1]),
                        Integer.parseInt(dimensions[2]), Integer.parseInt(dimensions[3]));
    }

    public static void main(String[] args) throws Exception {
        int chapter = Integer.parseInt(args[0]);
        String name = args[1]; long fe = Long.parseLong(args[2]), seed = Long.parseLong(args[3]);
        Path output = Paths.get(args[4]);
        System.setProperty("dhfsp.dataDir", args[5]);
        System.setProperty("dhfsp.standbyPower", args[6]);
        String[] dimensions = name.replace(".txt", "").split("_");
        if (chapter == 4 && args[7].startsWith("generate:")) {
            Path setup = output.resolve("RECONSTRUCTED-setup.txt");
            SetupTimes.generatedSupplement(Integer.parseInt(dimensions[0]), Integer.parseInt(dimensions[1]),
                    Long.parseLong(args[7].substring(9))).write(setup);
            System.setProperty("dhfsp.setupFile", setup.toString());
        } else if (chapter == 4) {
            System.setProperty("dhfsp.setupFile", args[7]);
        }
        SeededRandom.reset(seed);
        Problem<PermutationSolution<Integer>> raw = problem(chapter, name);
        Instance instance = ((SchedulingProblemData) raw).getSchedulingInstance();
        boolean diagnostic = Boolean.parseBoolean(args[8]);
        if (chapter == 4 && !instance.satisfiesDualResourceCondition() && !diagnostic) {
            throw new IllegalArgumentException("Instance violates ESWA Eq(8); only an explicitly diagnostic run is allowed");
        }
        RunContext<PermutationSolution<Integer>> context = new RunContext<>(raw, fe, seed);
        SearchConfig config = new SearchConfig();
        CanonicalHmopso algorithm = new CanonicalHmopso(context.problem(), instance, chapter, config);
        long start = System.nanoTime();
        context.run(algorithm);
        double seconds = (System.nanoTime() - start) / 1e9;
        List<PermutationSolution<Integer>> result = context.result();
        RunOutput.write(output, instance, context, result, seconds, diagnostic, config.describe(chapter));
        RunOutput.diagnostics(output, algorithm.diagnostics());
        System.out.println("NORMALIZED_RUN_PASS chapter=" + chapter + " seed=" + seed
                + " search_FE=" + context.budget().attempted() + "/" + fe + " archive=" + result.size());
    }
}
