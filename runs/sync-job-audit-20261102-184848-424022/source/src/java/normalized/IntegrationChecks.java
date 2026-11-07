package research.normalized;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
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

/** Real-encoding checks at partial initialization, generation and local-search boundaries. */
public final class IntegrationChecks {
    private IntegrationChecks() { }

    private static List<String> fingerprints(List<PermutationSolution<Integer>> result) {
        List<String> rows = new ArrayList<>();
        for (PermutationSolution<Integer> solution : result) {
            rows.add(java.util.Arrays.toString(solution.getObjectives()) + solution.getVariables()
                    + solution.getVariablesid() + solution.getAttribute("machine") + solution.getVariablesworker());
        }
        java.util.Collections.sort(rows);
        return rows;
    }

    public static void main(String[] args) throws Exception {
        int chapter = Integer.parseInt(args[0]);
        Path output = Paths.get(args[2]); Files.createDirectories(output);
        System.setProperty("dhfsp.dataDir", args[1]);
        System.setProperty("dhfsp.standbyPower", "1");
        System.setProperty("dhfsp.validateEveryEvaluation", "true");
        if (chapter == 4) {
            Path setup = output.resolve("RECONSTRUCTED-setup.txt");
            SetupTimes.generatedSupplement(20,2,314159).write(setup);
            System.setProperty("dhfsp.setupFile", setup.toString());
        }
        for (long fe : new long[] {0,1,99,100,101,200,701,6500}) {
            List<String> first = run(chapter, fe, output.resolve("fe-" + fe + "-a"));
            List<String> repeated = run(chapter, fe, output.resolve("fe-" + fe + "-b"));
            if (!first.equals(repeated)) throw new AssertionError("Same seed is not reproducible at FE=" + fe);
            System.out.println("PASS chapter=" + chapter + " FE=" + fe + " exact budget and same-seed full archive");
        }
        SeededRandom.reset(271828);
        Problem<PermutationSolution<Integer>> raw = NormalizedRun.problem(chapter,"20_2_3_1.txt");
        RunContext<PermutationSolution<Integer>> failed = new RunContext<>(raw,1,271828);
        PermutationSolution<Integer> invalid = raw.createSolution();
        invalid.setVariableValue(1, invalid.getVariableValue(0));
        try { failed.problem().evaluate(invalid); throw new AssertionError("Invalid permutation was accepted"); }
        catch (IllegalArgumentException expected) { }
        if (failed.budget().attempted()!=1 || failed.budget().failed()!=1 || !failed.result().isEmpty()) {
            throw new AssertionError("A failed real decode escaped the FE contract");
        }
        System.out.println("INTEGRATION_CHECKS_PASS chapter=" + chapter);
    }

    private static List<String> run(int chapter,long limit,Path output) throws Exception {
        Files.createDirectories(output);
        SeededRandom.reset(271828);
        Problem<PermutationSolution<Integer>> raw = NormalizedRun.problem(chapter,"20_2_3_1.txt");
        Instance instance = ((SchedulingProblemData) raw).getSchedulingInstance();
        RunContext<PermutationSolution<Integer>> context = new RunContext<>(raw,limit,271828);
        SearchConfig config = new SearchConfig();
        CanonicalHmopso search = new CanonicalHmopso(context.problem(),instance,chapter,config);
        long start = System.nanoTime(); context.run(search); double seconds=(System.nanoTime()-start)/1e9;
        if(context.budget().attempted()!=limit || context.budget().failed()!=0) throw new AssertionError("Wrong FE accounting");
        List<PermutationSolution<Integer>> result=context.result();
        if((limit==0) != result.isEmpty()) throw new AssertionError("Incorrect empty archive behavior");
        RunOutput.write(output,instance,context,result,seconds,false,config.describe(chapter));
        RunOutput.diagnostics(output,search.diagnostics());
        if (limit==6500) System.out.println("PHASE_DIAGNOSTICS " + search.diagnostics());
        return fingerprints(result);
    }
}
