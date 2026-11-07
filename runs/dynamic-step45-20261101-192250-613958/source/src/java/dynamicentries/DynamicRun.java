package research.dynamic;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.Files;
import java.nio.charset.StandardCharsets;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.*;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;
import org.uma.jmetal.util.research.search.*;
import org.uma.jmetal.util.research.joint.JointPolicy;
import org.uma.jmetal.util.research.cooperation.CooperationSupport;

/** One independent JVM/instance/seed. Numerical input preparation is outside search time. */
public final class DynamicRun {
    private DynamicRun() { }
    @SuppressWarnings("unchecked")
    public static void main(String[] args) throws Exception {
        Path input = Paths.get(args[0]), setup = Paths.get(args[1]), fatigue = Paths.get(args[2]);
        Path output = Paths.get(args[3]);
        String mode = args[4]; long fe = Long.parseLong(args[5]), seed = Long.parseLong(args[6]);
        double seconds = Double.parseDouble(args[7]), standby = Double.parseDouble(args[8]);
        boolean incremental = Boolean.parseBoolean(args[9]), small = Boolean.parseBoolean(args[10]);
        int traceLimit = args.length > 11 ? Integer.parseInt(args[11]) : 0;
        System.setProperty("dhfsp.dataDir", input.toAbsolutePath().getParent().toString());
        System.setProperty("dhfsp.standbyPower", Double.toString(standby));
        System.setProperty("dhfsp.setupFile", setup.toAbsolutePath().toString());
        Class<?> entry = Class.forName("org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW");
        String[] parts = input.getFileName().toString().replace(".txt", "").split("_");
        Problem<PermutationSolution<Integer>> source = (Problem<PermutationSolution<Integer>>) entry
                .getConstructor(int.class, int.class, int.class, int.class)
                .newInstance(Integer.parseInt(parts[0]), Integer.parseInt(parts[1]),
                        Integer.parseInt(parts[2]), Integer.parseInt(parts[3]));
        Instance in = ((SchedulingProblemData) source).getSchedulingInstance();
        if (!in.satisfiesDualResourceCondition()) throw new IllegalArgumentException("ESWA Eq8 failure");
        DynamicParameters parameters = DynamicInputs.fatigue(in, fatigue);
        DynamicEvaluation raw = new DynamicEvaluation(source, in, parameters, incremental);
        RunContext<PermutationSolution<Integer>> context = new RunContext<>(raw, fe, seed, seconds);
        raw.setCheckpoint(context::checkpoint);
        SearchConfig cfg = new SearchConfig();
        if (small) { cfg.populationSize = 8; cfg.boundarySize = 1; cfg.qIterations = 1; cfg.localProposalCap = 12; }
        boolean cooperative = mode.contains("SHARE") || mode.contains("SYNC");
        String jointMode = mode.startsWith("VALUE_") ? "VALUE" : mode;
        JointPolicy policy = (mode.equals("BASELINE") || mode.equals("SYNC") || mode.equals("SHARE")) ? null : new JointPolicy(in, parameters,
                new ParticleOperators(in, cfg.resolved(4)), JointPolicy.Mode.valueOf(jointMode), raw::prepare, context::checkpoint, traceLimit);
        CooperationSupport support = cooperative ? new CooperationSupport(in, parameters, mode.contains("SHARE")) : null;
        AnytimeRecorder recorder = new AnytimeRecorder(fe, seconds);
        context.problem().setObserver(recorder);
        CanonicalHmopso algorithm = new CanonicalHmopso(context.problem(), in, 4, cfg, policy, support);
        Map<String, Object> summary = new LinkedHashMap<>();
        Throwable failure = null;
        try { context.run(algorithm); }
        catch (RuntimeException | Error ex) { failure = ex; }
        finally { raw.clearPrepared(); }
        summary.put("status", failure == null ? "passed" : "failed");
        summary.put("mode", mode); summary.put("model", "dynamic-append-v1");
        summary.put("instance", input.toAbsolutePath().toString()); summary.put("provenance", in.provenance());
        summary.put("fatigueSource", parameters.source()); summary.put("seed", seed);
        summary.put("stopReason", context.stopReason()); summary.put("feLimit", fe);
        summary.put("attempted", context.budget().attempted()); summary.put("successful", context.budget().successful());
        summary.put("failed", context.budget().failed()); summary.put("searchSeconds", context.clock().elapsedSeconds());
        summary.put("timeInterruptedAttempts", context.budget().timeInterruptedAttempts());
        summary.put("timeLimitSeconds", Double.isFinite(seconds) ? seconds : null);
        summary.put("deadlineOvershootSeconds", Double.isFinite(seconds) ? Math.max(0, context.clock().elapsedSeconds() - seconds) : 0);
        summary.put("incremental", incremental); summary.put("diagnosticSmallSearchConfig", small);
        summary.put("searchConfiguration", cfg.describe(4)); summary.put("search", algorithm.diagnostics());
        summary.put("decoder", raw.diagnostics());
        if (policy != null) summary.put("joint", policy.diagnostics());
        if (support != null) summary.put("cooperation", support.diagnostics());
        if (failure != null) summary.put("error", failure.toString());
        List<PermutationSolution<Integer>> result = context.result();
        DynamicOutput.write(output, in, parameters, result, summary, args.length <= 12 || !Boolean.parseBoolean(args[12]));
        List<String> curves = new ArrayList<>();
        for (Map<String, Object> row : recorder.finish()) curves.add(DynamicJson.encode(row));
        Files.write(output.resolve("anytime.jsonl"), curves, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        if (policy != null && traceLimit > 0) DynamicMechanismDiagnostic.write(output, in, parameters, policy.trajectories());
        if (failure != null) throw new IllegalStateException("Dynamic run failed; partial evidence saved", failure);
        System.out.println("DYNAMIC_RUN_PASS mode=" + mode + " FE=" + context.budget().attempted()
                + " stop=" + context.stopReason() + " archive=" + result.size());
    }
}
