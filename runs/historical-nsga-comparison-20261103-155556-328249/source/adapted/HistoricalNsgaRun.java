package research.dynamic;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.algorithm.multiobjective.nsgaii.NSGAII;
import org.uma.jmetal.operator.impl.crossover.PMXCrossover;
import org.uma.jmetal.operator.impl.mutation.PermutationSwapMutation;
import org.uma.jmetal.operator.impl.selection.BinaryTournamentSelection;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.comparator.RankingAndCrowdingDistanceComparator;
import org.uma.jmetal.util.evaluator.impl.SequentialSolutionListEvaluator;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.runtime.RunContext;
import research.normalized.RunOutput;

/** Isolated adapter for the supplied legacy NSGA-II; original stop counter remains observable. */
public final class HistoricalNsgaRun {
    private HistoricalNsgaRun() { }

    public static void main(String[] args) throws Exception {
        Path input = Paths.get(args[0]).toAbsolutePath(), out = Paths.get(args[2]);
        System.setProperty("dhfsp.dataDir", input.getParent().toString());
        System.setProperty("dhfsp.setupFile", Paths.get(args[1]).toAbsolutePath().toString());
        System.setProperty("dhfsp.standbyPower", "1.0");
        boolean nominalStop = args[3].equals("NOMINAL");
        if (!nominalStop && !args[3].equals("ACTUAL")) throw new IllegalArgumentException("Unknown stop rule");
        int cap = Integer.parseInt(args[4]);
        long seed = Long.parseLong(args[5]);
        String[] n = input.getFileName().toString().replace(".txt", "").split("_");
        CountingProblem raw = new CountingProblem(n);
        Instance in = raw.getSchedulingInstance();
        if (!in.satisfiesDualResourceCondition()) throw new IllegalArgumentException("ESWA Eq(8) failure");
        RunContext<PermutationSolution<Integer>> context = new RunContext<>(raw, cap, seed);
        HistoricalSearch search = new HistoricalSearch(context, raw, cap, nominalStop);
        long[] points = new long[args.length - 6];
        for (int i = 0; i < points.length; i++) points[i] = Long.parseLong(args[i + 6]);
        AnytimeRecorder recorder = new AnytimeRecorder(cap, Double.POSITIVE_INFINITY, new double[0], points);
        context.problem().setObserver((fe, seconds, changed, archive) -> {
            recorder.completed(fe, seconds, changed, archive);
            if (java.util.Arrays.binarySearch(points, fe) >= 0) {
                System.out.println("CHECKPOINT FE=" + fe + " seconds=" + seconds);
            }
        });
        context.run(search);
        export(out, context, raw, search, recorder);
    }

    private static void export(Path out, RunContext<PermutationSolution<Integer>> context,
            CountingProblem raw, HistoricalSearch search, AnytimeRecorder recorder) throws Exception {
        if (raw.calls != context.budget().attempted() || raw.successes != context.budget().successful()
                || raw.calls != raw.successes || context.budget().failed() != 0)
            throw new IllegalStateException("Independent physical-entry and budget counts disagree");
        List<PermutationSolution<Integer>> results = context.result();
        double seconds = context.clock().elapsedSeconds();
        RunOutput.write(out, raw.getSchedulingInstance(), context, results, seconds, false,
                "historical-snapshot-static; original batch rates; seed adapter; shared canonical decoder");
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("mode", "NSGA2_HISTORICAL_ADAPTED"); row.put("seed", context.seed());
        row.put("stopReason", context.stopReason()); row.put("stopRule", search.nominalStop ? "NOMINAL" : "ACTUAL");
        row.put("feLimit", context.budget().limit()); row.put("attempted", context.budget().attempted());
        row.put("successful", context.budget().successful()); row.put("failed", context.budget().failed());
        row.put("physicalCalls", raw.calls); row.put("physicalSuccesses", raw.successes);
        row.put("nominalCounter", search.nominalCount()); row.put("generationsCompleted", search.generations);
        row.put("searchSeconds", seconds);
        writeLine(out.resolve("run-receipt.jsonl"), row);
        for (Map<String, Object> point : recorder.finish()) writeLine(out.resolve("anytime.jsonl"), point);
    }

    private static void writeLine(Path path, Map<String, Object> row) throws IOException {
        Files.write(path, (DynamicJson.encode(row) + "\n").getBytes(StandardCharsets.UTF_8),
                StandardOpenOption.CREATE, StandardOpenOption.APPEND);
    }

    private static final class CountingProblem extends EDHHFSPW {
        private long calls, successes;
        CountingProblem(String[] n) throws IOException {
            super(Integer.parseInt(n[0]), Integer.parseInt(n[1]), Integer.parseInt(n[2]), Integer.parseInt(n[3]));
        }
        @Override public void evaluate(PermutationSolution<Integer> candidate) {
            calls++;
            super.evaluate(candidate);
            successes++;
        }
    }

    private static final class HistoricalSearch extends NSGAII<PermutationSolution<Integer>> {
        private final CountingProblem raw;
        private final boolean nominalStop;
        private int generations, beforeReproduction;

        HistoricalSearch(RunContext<PermutationSolution<Integer>> context, CountingProblem raw,
                int limit, boolean nominalStop) {
            super(context.problem(), limit, 100, 100, 100, new PMXCrossover(.4),
                    new PermutationSwapMutation<Integer>(.2),
                    new BinaryTournamentSelection<>(new RankingAndCrowdingDistanceComparator<>()),
                    new SequentialSolutionListEvaluator<>(), .2, .04, .3, .4, .1, .15);
            this.raw = raw; this.nominalStop = nominalStop;
        }
        @Override protected boolean isStoppingConditionReached() {
            return nominalStop && super.isStoppingConditionReached();
        }
        @Override protected List<PermutationSolution<Integer>> reproduction(List<PermutationSolution<Integer>> parents) {
            beforeReproduction = evaluations;
            return super.reproduction(parents);
        }
        @Override protected void updateProgress() {
            int extra = evaluations - beforeReproduction;
            super.updateProgress();
            generations++;
            if (nominalStop) System.out.printf("AUDIT generation=%d nominal=%d physical=%d reproductionIncrement=%d%n",
                    generations, evaluations, raw.calls, extra);
        }
        int nominalCount() { return evaluations; }
    }
}
