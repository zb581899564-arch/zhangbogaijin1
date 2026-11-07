package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.Solution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.DynamicParameters;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.runtime.EvaluationObserver;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import org.uma.jmetal.util.research.runtime.ThreeObjectiveArchive;
import org.uma.jmetal.util.research.search.LocalPddrKernel;
import org.uma.jmetal.util.research.search.QgsLocalLedger;
import org.uma.jmetal.util.research.search.SearchConfig;

/** Same strict FE search for all arms. Two recorder views give exact FE and common real-time cuts. */
public final class PddrIsolationRun {
    private PddrIsolationRun() {}

    public static void main(String[] args) throws Exception {
        Path input = Paths.get(args[0]).toAbsolutePath(), setup = Paths.get(args[1]).toAbsolutePath();
        Path out = Paths.get(args[3]);
        String mode = args[4], pddr = args[5];
        long limit = Long.parseLong(args[7]), seed = Long.parseLong(args[8]);
        boolean audit = pddr.equals("AUDIT");
        System.setProperty("research.pddr.mode", pddr);
        System.setProperty("research.qgsAudit.mode", "replay");
        System.setProperty("research.qgsAudit.ledger", args[6]);
        EDHHFSPW source = load(input, setup);
        Instance in = source.getSchedulingInstance();
        if (!in.satisfiesDualResourceCondition()) throw new IllegalArgumentException("ESWA Eq(8) failure");
        DynamicParameters params = DynamicInputs.fatigue(in, Paths.get(args[2]));
        DynamicEvaluation dynamic = new DynamicEvaluation(source, in, params, true);
        if (audit) {
            SeededRandom.reset(seed);
            LocalPddrKernel.selfCheck(source.createSolution());
        }
        RunContext<PermutationSolution<Integer>> context = new RunContext<>(dynamic, limit, seed);
        dynamic.setCheckpoint(context::checkpoint);
        SearchConfig cfg = new SearchConfig();
        cfg.mergeGlobalLocal = cfg.paperResourceOperators = !DynamicSearch.isClassic(mode);
        DynamicSearch search = DynamicSearch.create(mode, in, params, dynamic, context, cfg, false, 0, 0);
        long[] checkpoints = Arrays.stream(Arrays.copyOfRange(args, 9, args.length)).mapToLong(Long::parseLong).toArray();
        if (checkpoints[checkpoints.length - 1] != limit) throw new IllegalArgumentException("Missing terminal FE");
        Observations obs = new Observations(audit, limit, checkpoints);
        context.problem().setObserver(obs);
        try { context.run(search.algorithm); }
        catch (RuntimeException | Error failure) {
            append(out.resolve("failure.jsonl"), row("error", failure.toString(), "attempted", context.budget().attempted(),
                    "successful", context.budget().successful(), "failed", context.budget().failed()));
            throw failure;
        } finally { dynamic.clearPrepared(); }
        if (context.budget().attempted() != limit || context.budget().successful() != limit
                || context.budget().failed() != 0 || !"FE_LIMIT".equals(context.stopReason()))
            throw new IllegalStateException("Invalid fixed-FE receipt");
        QgsLocalLedger.finish(out);
        Map<String, Object> receipt = row("mode", mode, "seed", seed, "feLimit", limit,
                "attempted", context.budget().attempted(), "successful", context.budget().successful(),
                "failed", context.budget().failed(), "stopReason", context.stopReason(),
                "searchSeconds", context.clock().elapsedSeconds(), "configuration", search.configuration,
                "search", search.diagnostics(), "decoder", dynamic.diagnostics(), "pddr", LocalPddrKernel.diagnostics(),
                "paidSHA256", audit ? obs.digest.finish() : null);
        append(out.resolve("run-receipt.jsonl"), receipt);
        obs.write(out);
        append(out.resolve("launch.jsonl"), org.uma.jmetal.util.research.search.LocalLaunch.diagnostics());
        DynamicOutput.write(out, in, params, context.result(), receipt, false);
    }

    private static final class Observations implements EvaluationObserver {
        final AnytimeRecorder fe, time;
        final PddrPaidDigest digest;
        final List<String> initial = new ArrayList<>(), admissions = new ArrayList<>();

        Observations(boolean audit, long limit, long[] checkpoints) throws Exception {
            fe = new AnytimeRecorder(limit, Double.POSITIVE_INFINITY, new double[0], checkpoints);
            time = audit ? null : new AnytimeRecorder(limit, 12.0, new double[] {1.0/12, 2.0/12, 4.0/12, 6.0/12, 8.0/12, 10.0/12, 1}, new long[0]);
            digest = audit ? new PddrPaidDigest() : null;
            admissions.add("fe,cmax,tec,twc");
        }
        @Override public void completed(long paid, double seconds, boolean changed, ThreeObjectiveArchive<?> archive) {
            fe.completed(paid, seconds, changed, archive);
            if (time != null) time.completed(paid, seconds, changed, archive);
        }
        @Override public void completedSolution(Solution<?> value, long paid, double seconds,
                boolean changed, ThreeObjectiveArchive<?> archive) {
            PermutationSolution<?> s = (PermutationSolution<?>) value;
            if (digest != null) digest.update(paid, s);
            if (digest != null && changed)
                admissions.add(paid + "," + s.getObjective(0) + "," + s.getObjective(1) + "," + s.getObjective(2));
            if (paid <= 100)
                initial.add(DynamicJson.encode(row("fe", paid, "JS", s.getVariables(), "FA", s.getVariablesid(),
                        "MA", s.getAttribute("machine"), "WA", s.getVariablesworker(), "objectives", s.getObjectives())));
            completed(paid, seconds, changed, archive);
        }
        void write(Path out) throws Exception {
            for (Map<String, Object> r : fe.finish()) append(out.resolve("anytime.jsonl"), r);
            if (time != null) for (Map<String, Object> r : time.finish()) append(out.resolve("time.jsonl"), r);
            Files.write(out.resolve("initial-population.jsonl"), initial, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
            if (digest != null)
                Files.write(out.resolve("archive-admissions.csv"), admissions, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        }
    }

    private static EDHHFSPW load(Path input, Path setup) throws Exception {
        System.setProperty("dhfsp.dataDir", input.getParent().toString());
        System.setProperty("dhfsp.setupFile", setup.toString());
        System.setProperty("dhfsp.standbyPower", "1.0");
        String[] n = input.getFileName().toString().replace(".txt", "").split("_");
        return new EDHHFSPW(Integer.parseInt(n[0]), Integer.parseInt(n[1]), Integer.parseInt(n[2]), Integer.parseInt(n[3]));
    }
    private static Map<String, Object> row(Object... pairs) {
        Map<String, Object> map = new LinkedHashMap<>();
        for (int i = 0; i < pairs.length; i += 2) map.put((String) pairs[i], pairs[i + 1]);
        return map;
    }
    private static void append(Path file, Map<String, Object> value) throws Exception {
        Files.write(file, (DynamicJson.encode(value) + "\n").getBytes(StandardCharsets.UTF_8),
                StandardOpenOption.CREATE, StandardOpenOption.APPEND);
    }
}
