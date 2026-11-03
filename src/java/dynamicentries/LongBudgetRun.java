package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.DynamicParameters;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.util.research.search.SearchConfig;
import research.normalized.RunOutput;

/** Fixed-FE bridge: the frozen algorithms on either the static or append decoder. */
public final class LongBudgetRun {
    private LongBudgetRun() { }

    public static void main(String[] args) throws Exception {
        Path input = Paths.get(args[0]).toAbsolutePath();
        Path setup = Paths.get(args[1]).toAbsolutePath(), out = Paths.get(args[3]);
        boolean useStatic = args[2].equals("STATIC");
        String mode = args[4];
        long fe = Long.parseLong(args[5]), seed = Long.parseLong(args[6]);
        if (!mode.equals("BASELINE") && !mode.equals("NSGA2_4V")
                && !(mode.equals("SHARE_JOB_ALIGNED") && !useStatic))
            throw new IllegalArgumentException("Unsupported model/search pairing");
        if (args.length < 8) throw new IllegalArgumentException("Explicit FE checkpoints required");
        long[] points = new long[args.length - 7];
        for (int i = 0; i < points.length; i++) points[i] = Long.parseLong(args[i + 7]);
        if (points[points.length - 1] != fe) throw new IllegalArgumentException("Final checkpoint must equal budget");
        EDHHFSPW source = load(input, setup);
        Instance in = source.getSchedulingInstance();
        if (!in.satisfiesDualResourceCondition()) throw new IllegalArgumentException("ESWA Eq(8) failure");
        DynamicParameters fatigue = useStatic ? null : DynamicInputs.fatigue(in, Paths.get(args[2]));
        DynamicEvaluation dynamic = useStatic ? null : new DynamicEvaluation(source, in, fatigue, true);
        Problem<PermutationSolution<Integer>> problem = useStatic ? source : dynamic;
        RunContext<PermutationSolution<Integer>> context = new RunContext<>(problem, fe, seed);
        if (dynamic != null) dynamic.setCheckpoint(context::checkpoint);

        SearchConfig cfg = new SearchConfig();
        boolean classic = DynamicSearch.isClassic(mode);
        cfg.mergeGlobalLocal = !classic;
        cfg.paperResourceOperators = !classic;
        DynamicSearch search = DynamicSearch.create(mode, in, fatigue, dynamic, context, cfg, false, 0, 0);
        AnytimeRecorder recorder = new AnytimeRecorder(fe, Double.POSITIVE_INFINITY, new double[0], points);
        context.problem().setObserver((paid, seconds, changed, archive) -> {
            recorder.completed(paid, seconds, changed, archive);
            if (java.util.Arrays.binarySearch(points, paid) >= 0) {
                System.out.println("CHECKPOINT FE=" + paid + " seconds=" + seconds);
            }
        });
        try { context.run(search.algorithm); }
        finally { if (dynamic != null) dynamic.clearPrepared(); }
        Map<String, Object> receipt = receipt(context, useStatic, mode, search);
        List<PermutationSolution<Integer>> results = context.result();
        if (useStatic) {
            RunOutput.write(out, in, context, results, context.clock().elapsedSeconds(), false, search.configuration);
        } else {
            receipt.put("fatigueSource", fatigue.source());
            receipt.put("decoder", dynamic.diagnostics());
            DynamicOutput.write(out, in, fatigue, results, receipt, false);
        }
        for (Map<String, Object> row : recorder.finish()) append(out.resolve("anytime.jsonl"), row);
        append(out.resolve("run-receipt.jsonl"), receipt);
        if (!"FE_LIMIT".equals(context.stopReason()) || context.budget().successful() != fe
                || context.budget().attempted() != fe || context.budget().failed() != 0)
            throw new IllegalStateException("Incomplete fixed-FE budget; evidence retained");
    }

    private static EDHHFSPW load(Path input, Path setup) throws Exception {
        System.setProperty("dhfsp.dataDir", input.getParent().toString());
        System.setProperty("dhfsp.setupFile", setup.toString());
        System.setProperty("dhfsp.standbyPower", "1.0");
        String[] n = input.getFileName().toString().replace(".txt", "").split("_");
        return new EDHHFSPW(Integer.parseInt(n[0]), Integer.parseInt(n[1]),
                Integer.parseInt(n[2]), Integer.parseInt(n[3]));
    }

    private static Map<String, Object> receipt(RunContext<?> context, boolean useStatic, String mode, DynamicSearch search) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("mode", mode);
        result.put("model", useStatic ? "canonical-v1" : "dynamic-append-v1");
        result.put("seed", context.seed());
        result.put("feLimit", context.budget().limit());
        result.put("attempted", context.budget().attempted());
        result.put("successful", context.budget().successful());
        result.put("failed", context.budget().failed());
        result.put("stopReason", context.stopReason());
        result.put("searchSeconds", context.clock().elapsedSeconds());
        result.put("configuration", search.configuration);
        result.put("search", search.diagnostics());
        return result;
    }

    private static void append(Path path, Map<String, Object> value) throws Exception {
        Files.write(path, (DynamicJson.encode(value) + "\n").getBytes(StandardCharsets.UTF_8),
                StandardOpenOption.CREATE, StandardOpenOption.APPEND);
    }
}
