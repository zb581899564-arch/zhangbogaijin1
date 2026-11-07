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
import org.uma.jmetal.util.research.modelglobal.*;
import org.uma.jmetal.util.research.runtime.RunContext;

/** Finish only a frozen receiver's existing program; no model learning, RNG decisions or new generation. */
public final class PaFixedSuffixRun {
    private PaFixedSuffixRun() { }
    private static final class Program implements Algorithm<Object> {
        private static final long serialVersionUID = 1L;
        final RunContext<PermutationSolution<Integer>> run;
        final Instance instance; final PaRunChecks checks; final FirstStageCatalog catalog;
        final PaInternalArchive archive = new PaInternalArchive();
        final List<String> lines; final Path out; final boolean actual;
        TypedScheduleGenome working; PermutationSolution<Integer> point;
        Program(RunContext<PermutationSolution<Integer>> context, Instance value, PaRunChecks qa, List<String> records,
                List<String> prior, Path folder, boolean original) {
            run = context; instance = value; checks = qa; lines = records; out = folder; actual = original;
            catalog = new FirstStageCatalog(instance);
            for (String row : prior) archive.offer(doubles(row));
        }
        public void run() {
            for (int i = 0; i < lines.size(); i++) {
                run.problem().checkpoint(); String[] f = lines.get(i).split("\t");
                TypedScheduleGenome incoming = TypedScheduleGenome.of(catalog, ProbeData.integers(f[1]), doubles(f[2]));
                TypedScheduleGenome candidate = f[0].equals("MOVE") ? PaMixingMove.apply(catalog, working, incoming, ProbeData.integers(f[3])).genome : incoming;
                PermutationSolution<Integer> evaluated = evaluate(candidate);
                if (i < 2 || actual) checkExpected(evaluated, f);
                PaInternalArchive.Flags flags = archive.offer(evaluated.getObjectives());
                boolean keep = i == 0 || PaInternalArchive.weaklyDominates(evaluated.getObjectives(), point.getObjectives()) || !flags.dominated;
                if (keep) { working = candidate; point = evaluated; }
                Map<String,Object> record = ProbeData.encoding(evaluated);
                record.putAll(NeutralProbeSupport.row("index", i, "kind", f[0], "accepted", keep, "rawPaidHash", checks.lastRawHash,
                    "resources", candidate.allocations(), "keys", candidate.priorities()));
                try { NeutralProbeSupport.append(out.resolve("candidates.jsonl"), record); }
                catch (Exception error) { throw new IllegalStateException(error); }
            }
        }
        @SuppressWarnings("unchecked")
        private PermutationSolution<Integer> evaluate(TypedScheduleGenome genome) {
            PermutationSolution<Integer> child = point == null ? run.problem().createSolution() : (PermutationSolution<Integer>)point.copy();
            FourVectors v = genome.toVectors(); int[][] values = {v.jobs(), v.factories(), v.machines(), v.workers()};
            List<Integer> machines = (List<Integer>)child.getAttribute("machine");
            for (int p = 0; p < values[0].length; p++) {
                child.setVariableValue(p, values[0][p]); child.setVariableValueid(p, values[1][p]);
                machines.set(p, values[2][p]); child.setVariableValueworker(p, values[3][p]);
            }
            if (SchedulingEncoding.repair(child, instance) != 0) throw new AssertionError("Suffix required repair");
            run.problem().evaluate(child); checks.paid(child, run.budget().successful()); return child;
        }
        private void checkExpected(PermutationSolution<Integer> child, String[] f) {
            if (!Arrays.equals(child.getObjectives(), doubles(f[4]))) throw new AssertionError("Frozen objective mismatch");
            if (!f[5].equals("-") && !f[5].equals(checks.lastRawHash)) throw new AssertionError("Frozen paid raw point mismatch");
        }
        public Object getResult() { return null; }
        public String getName() { return "FIXED_RECEIVER_SUFFIX_CAUSAL_CLOSURE"; }
        public String getDescription() { return "No new mechanism; only fixed natural program suffix"; }
    }
    public static void main(String[] args) throws Exception {
        Path input = Paths.get(args[0]), out = Paths.get(args[5]); Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir", input.getParent().toString()); System.setProperty("dhfsp.setupFile", args[1]);
        System.setProperty("dhfsp.standbyPower", "1"); String[] d = input.getFileName().toString().replace(".txt", "").split("_");
        EDHHFSPW raw = new EDHHFSPW(Integer.parseInt(d[0]), Integer.parseInt(d[1]), Integer.parseInt(d[2]), Integer.parseInt(d[3]));
        Instance instance = raw.getSchedulingInstance();
        if (!instance.satisfiesDualResourceCondition()) throw new IllegalArgumentException("Unqualified instance");
        DynamicParameters fatigue = DynamicInputs.fatigue(instance, Paths.get(args[2]));
        DynamicEvaluation decoder = new DynamicEvaluation(raw, instance, fatigue, true);
        List<String> lines = Files.readAllLines(Paths.get(args[3]), StandardCharsets.UTF_8);
        RunContext<PermutationSolution<Integer>> run = new RunContext<>(decoder, lines.size(), 14750029);
        decoder.setCheckpoint(run::checkpoint); PaRunChecks checks = new PaRunChecks(instance, fatigue);
        Program program = new Program(run, instance, checks, lines, Files.readAllLines(Paths.get(args[4]), StandardCharsets.UTF_8), out, args[6].equals("ACTUAL"));
        Throwable failure = null;
        try {
            run.run(program);
            if (!run.stopReason().equals("ALGORITHM_RETURNED") || run.budget().successful() != lines.size() || run.budget().failed() != 0)
                throw new AssertionError("Natural suffix incomplete");
        } catch (RuntimeException | Error error) { failure = error; }
        finally {
            NeutralProbeSupport.append(out.resolve("receipt.jsonl"), NeutralProbeSupport.row("status", failure == null ? "COMPLETE" : "INCOMPLETE_RETAINED",
                "error", failure == null ? null : failure.toString(), "attemptedFE", run.budget().attempted(), "successfulFE", run.budget().successful(),
                "failedFE", run.budget().failed(), "paidFullTimelineQA", checks.paidQA, "paidSHA256", checks.paidDigest.finish(), "stopReason", run.stopReason(),
                "internalArchive", program.archive.snapshot(), "lastWorking", program.point == null ? null : ProbeData.encoding(program.point),
                "lastResources", program.working == null ? null : program.working.allocations(),
                "lastKeys", program.working == null ? null : program.working.priorities(), "decoder", decoder.diagnostics(), "goalAchieved", false));
            decoder.clearPrepared();
        }
        if (failure != null) throw new IllegalStateException("Suffix evidence retained", failure);
        NeutralProbeSupport.append(out.resolve("loaded-identity.jsonl"), ClassResolutionProbe.capture("research.dynamic.PaFixedSuffixRun",
            "org.uma.jmetal.util.research.modelglobal.PaMixingMove", "org.uma.jmetal.util.research.modelglobal.TypedScheduleGenome",
            "org.uma.jmetal.util.research.modelglobal.PaInternalArchive", "org.uma.jmetal.util.research.DynamicEvaluation",
            "org.uma.jmetal.util.research.model.DynamicDecoder", "org.uma.jmetal.util.research.runtime.BudgetedProblem"));
    }
    private static double[] doubles(String text) {
        String[] values = text.split(","); double[] result = new double[values.length];
        for (int i = 0; i < result.length; i++) result[i] = Double.parseDouble(values[i]); return result;
    }
}
