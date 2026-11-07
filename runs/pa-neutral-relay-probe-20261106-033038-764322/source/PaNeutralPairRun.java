package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.RunContext;

/** Fixed already-selected actual/rollback pairs; both are charged, never fed back to the source search. */
public final class PaNeutralPairRun {
    private PaNeutralPairRun() { }
    public static void main(String[] args) throws Exception {
        Path input = Paths.get(args[0]), out = Paths.get(args[4]); Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir", input.getParent().toString()); System.setProperty("dhfsp.setupFile", args[1]);
        System.setProperty("dhfsp.standbyPower", "1"); String[] d = input.getFileName().toString().replace(".txt", "").split("_");
        EDHHFSPW raw = new EDHHFSPW(Integer.parseInt(d[0]), Integer.parseInt(d[1]), Integer.parseInt(d[2]), Integer.parseInt(d[3]));
        Instance instance = raw.getSchedulingInstance();
        if (!instance.satisfiesDualResourceCondition()) throw new IllegalArgumentException("Unqualified instance");
        DynamicParameters fatigue = DynamicInputs.fatigue(instance, Paths.get(args[2]));
        DynamicEvaluation decoder = new DynamicEvaluation(raw, instance, fatigue, true);
        List<String> lines = Files.readAllLines(Paths.get(args[3]), StandardCharsets.UTF_8);
        RunContext<PermutationSolution<Integer>> run = new RunContext<>(decoder, lines.size(), Long.parseLong(args[5]));
        decoder.setCheckpoint(run::checkpoint); PaRunChecks checks = new PaRunChecks(instance, fatigue); Throwable failure = null;
        try {
            run.run(new Algorithm<Object>() {
                private static final long serialVersionUID = 1L;
                public void run() {
                    for (String line : lines) {
                        String[] fields = line.split("\t"); PermutationSolution<Integer> value = run.problem().createSolution();
                        write(value, fields); if (SchedulingEncoding.repair(value, instance) != 0) throw new AssertionError("Pair required repair");
                        run.problem().evaluate(value); checks.paid(value, run.budget().successful());
                        if (fields[1].equals("ACTUAL")) {
                            String[] expected = fields[2].split(",");
                            for (int i = 0; i < 3; i++) if (Double.doubleToLongBits(Double.parseDouble(expected[i])) != Double.doubleToLongBits(value.getObjective(i)))
                                throw new AssertionError("Actual child objective differs from paid source");
                        }
                        Map<String,Object> record = ProbeData.encoding(value);
                        record.putAll(NeutralProbeSupport.row("case", Integer.parseInt(fields[0]), "branch", fields[1], "paidFE", run.budget().successful()));
                        try { NeutralProbeSupport.append(out.resolve("candidates.jsonl"), record); }
                        catch (Exception error) { throw new IllegalStateException(error); }
                    }
                }
                public Object getResult() { return null; }
                public String getName() { return "PA_NEUTRAL_PAIR_DIAGNOSTIC"; }
                public String getDescription() { return "No search feedback or new selector"; }
            });
            if (!run.stopReason().equals("ALGORITHM_RETURNED") || run.budget().successful() != lines.size() || run.budget().failed() != 0)
                throw new AssertionError("Fixed pair fees incomplete");
        } catch (RuntimeException | Error error) { failure = error; }
        finally {
            List<Map<String,Object>> front = new ArrayList<>();
            for (PermutationSolution<Integer> point : run.result()) front.add(ProbeData.encoding(point));
            NeutralProbeSupport.append(out.resolve("receipt.jsonl"), NeutralProbeSupport.row("status", failure == null ? "COMPLETE" : "INCOMPLETE_RETAINED",
                "error", failure == null ? null : failure.toString(), "successfulFE", run.budget().successful(), "attemptedFE", run.budget().attempted(),
                "failedFE", run.budget().failed(), "paidFullTimelineQA", checks.paidQA, "paidSHA256", checks.paidDigest.finish(),
                "stopReason", run.stopReason(), "decoder", decoder.diagnostics(), "lastValidFront", front, "goalAchieved", false));
            decoder.clearPrepared();
        }
        if (failure != null) throw new IllegalStateException("Paid pair failure retained", failure);
        NeutralProbeSupport.append(out.resolve("loaded-identity.jsonl"), ClassResolutionProbe.capture("research.dynamic.PaNeutralPairRun",
            "research.dynamic.PaRunChecks", "org.uma.jmetal.util.research.DynamicEvaluation", "org.uma.jmetal.util.research.model.DynamicDecoder",
            "org.uma.jmetal.util.research.model.DynamicValidator", "org.uma.jmetal.util.research.runtime.BudgetedProblem"));
    }
    @SuppressWarnings("unchecked")
    private static void write(PermutationSolution<Integer> point, String[] fields) {
        int[][] vectors = new int[4][]; for (int k = 0; k < 4; k++) vectors[k] = ProbeData.integers(fields[k + 3]);
        List<Integer> machines = (List<Integer>)point.getAttribute("machine");
        for (int p = 0; p < vectors[0].length; p++) {
            point.setVariableValue(p, vectors[0][p]); point.setVariableValueid(p, vectors[1][p]);
            machines.set(p, vectors[2][p]); point.setVariableValueworker(p, vectors[3][p]);
        }
    }
}
