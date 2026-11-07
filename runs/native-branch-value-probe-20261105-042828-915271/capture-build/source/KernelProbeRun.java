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
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.SchedulingProblemData;
import org.uma.jmetal.util.research.mechanism.KernelVariants;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;
import org.uma.jmetal.util.research.search.SearchConfig;

/** One fixed-triple experiment; all parent replays and candidate evaluations are charged. */
public final class KernelProbeRun {
    private KernelProbeRun() { }
    @SuppressWarnings("unchecked")
    public static void main(String[] args) throws Exception {
        Path input = Paths.get(args[0]), setup = Paths.get(args[1]), fatigue = Paths.get(args[2]);
        Path tsv = Paths.get(args[3]), output = Paths.get(args[4]);
        int reps = Integer.parseInt(args[5]); long baseSeed = Long.parseLong(args[6]);
        System.setProperty("dhfsp.dataDir", input.toAbsolutePath().getParent().toString());
        System.setProperty("dhfsp.standbyPower", "1.0"); System.setProperty("dhfsp.setupFile", setup.toAbsolutePath().toString());
        String[] parts = input.getFileName().toString().replace(".txt", "").split("_");
        Problem<PermutationSolution<Integer>> source = (Problem<PermutationSolution<Integer>>) Class.forName("org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW")
                .getConstructor(int.class, int.class, int.class, int.class).newInstance(Integer.parseInt(parts[0]), Integer.parseInt(parts[1]), Integer.parseInt(parts[2]), Integer.parseInt(parts[3]));
        Instance in = ((SchedulingProblemData) source).getSchedulingInstance();
        DynamicParameters params = DynamicInputs.fatigue(in, fatigue);
        DynamicEvaluation raw = new DynamicEvaluation(source, in, params, true);
        List<String> inputs = Files.readAllLines(tsv, StandardCharsets.UTF_8);
        long planned = inputs.size() * (3L + 4L * reps);
        RunContext<PermutationSolution<Integer>> ctx = new RunContext<>(raw, planned, baseSeed, 120);
        raw.setCheckpoint(ctx::checkpoint);
        Probe probe = new Probe(ctx, in, inputs, reps, baseSeed); ctx.run(probe);
        if (ctx.budget().successful() != planned || ctx.budget().failed() != 0) throw new AssertionError("Incomplete paid probe");
        long qaStart = System.nanoTime();
        for (PermutationSolution<Integer> s : probe.children) {
            DynamicSchedule full = DynamicDecoder.full(in, params, SchedulingEncoding.integers(s.getVariables()), SchedulingEncoding.integers(s.getVariablesid()),
                    SchedulingEncoding.machineIntegers(s), SchedulingEncoding.integers(s.getVariablesworker()), () -> { });
            DynamicValidator.validate(in, params, full);
            if (!Arrays.equals(full.objectives(), s.getObjectives())) throw new AssertionError("Candidate full replay differs");
        }
        Files.createDirectories(output);
        List<String> lines = new ArrayList<>(); for (Map<String, Object> row : probe.rows) lines.add(DynamicJson.encode(row));
        Files.write(output.resolve("kernel-raw.jsonl"), lines, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        Map<String, Object> receipt = new LinkedHashMap<>(); receipt.put("status", "passed");
        receipt.put("successfulFE", ctx.budget().successful()); receipt.put("failedFE", ctx.budget().failed());
        receipt.put("cases", inputs.size()); receipt.put("candidateFE", probe.children.size()); receipt.put("parentReplayFE", inputs.size() * 3);
        receipt.put("searchSeconds", ctx.clock().elapsedSeconds()); receipt.put("offlineCandidateReplays", probe.children.size());
        receipt.put("offlineQASeconds", (System.nanoTime() - qaStart) / 1e9);
        Files.write(output.resolve("kernel-receipt.json"), Arrays.asList(DynamicJson.encode(receipt)), StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        System.out.println("KERNEL_PROBE_PASS cases=" + inputs.size() + " paidFE=" + planned);
    }
    private static long mixed(long value) {
        value = (value ^ (value >>> 30)) * 0xbf58476d1ce4e5b9L;
        value = (value ^ (value >>> 27)) * 0x94d049bb133111ebL;
        return value ^ (value >>> 31);
    }
    private static final class Probe implements Algorithm<Object> {
        private static final long serialVersionUID = 1L;
        final RunContext<PermutationSolution<Integer>> ctx; final Instance in;
        final List<String> inputs; final int reps; final long baseSeed;
        final List<Map<String, Object>> rows = new ArrayList<>();
        final List<PermutationSolution<Integer>> children = new ArrayList<>();
        Probe(RunContext<PermutationSolution<Integer>> ctx, Instance in, List<String> inputs, int reps, long baseSeed) {
            this.ctx = ctx; this.in = in; this.inputs = inputs; this.reps = reps; this.baseSeed = baseSeed;
        }
        public void run() {
            SearchConfig cfg = new SearchConfig(); cfg.paperResourceOperators = true; cfg.mergeGlobalLocal = true;
            KernelVariants variants = new KernelVariants(in, cfg.resolved(4), ctx::checkpoint);
            String[] names = {"PAPER", "JOB_ALIGNED", "CLASSIC_GLOBAL", "CLASSIC_PERSONAL"};
            int caseIndex = 0;
            for (String line : inputs) {
                String[] fields = line.split("\t", -1); if (fields.length != 18) throw new IllegalArgumentException("Expected18 TSV fields");
                int family = Integer.parseInt(fields[1]); int[] fixed = ProbeData.integers(fields[2]);
                List<PermutationSolution<Integer>> parents = new ArrayList<>();
                for (int k = 0; k < 3; k++) {
                    PermutationSolution<Integer> p = ctx.problem().createSolution();
                    ProbeData.fill(p, fields, 3 + 5 * k, k == 0 ? family : -1, k == 0 ? fixed : null);
                    ctx.problem().evaluate(p); ProbeData.expected(p, fields[7 + 5 * k]); parents.add(p);
                }
                String[] keys = {ProbeData.key(parents.get(0)), ProbeData.key(parents.get(1)), ProbeData.key(parents.get(2))};
                for (int rep = 0; rep < reps; rep++) for (int turn = 0; turn < names.length; turn++) {
                    String kernel = names[(turn + rep + caseIndex) % names.length]; long seed = mixed(baseSeed + (caseIndex / 16) * 1009L + rep);
                    SeededRandom.reset(seed); long start = System.nanoTime();
                    PermutationSolution<Integer> child = variants.child(kernel, parents.get(0), parents.get(1), parents.get(2));
                    int restored = ProbeData.restore(child, in, fixed); int repaired = SchedulingEncoding.repair(child, in);
                    long generationNanos = System.nanoTime() - start; start = System.nanoTime(); ctx.problem().evaluate(child);
                    long evaluationNanos = System.nanoTime() - start;
                    Map<String, Object> row = new LinkedHashMap<>(); row.put("caseId", fields[0]); row.put("kernel", kernel);
                    row.put("rep", rep); row.put("seed", seed); row.put("child", ProbeData.encoding(child));
                    row.put("successfulFE", ctx.budget().successful());
                    row.put("generationNanos", generationNanos); row.put("evaluationNanos", evaluationNanos);
                    row.put("repairChanged", repaired > 0); row.put("finalCommonRepairEdits", repaired);
                    row.put("familyRestoreEdits", restored);
                    row.put("repairScope", "Final common repair only; family restore separate; internal kernel repairs not observable here");
                    row.put("changesByJob", ProbeData.changes(parents.get(0), child)); rows.add(row); children.add(child);
                    for (int k = 0; k < 3; k++) if (!keys[k].equals(ProbeData.key(parents.get(k)))) throw new AssertionError("Kernel mutated parent");
                }
                caseIndex++;
            }
        }
        public Object getResult() { return null; }
        public String getName() { return "fixed-parent-kernel-probe"; }
        public String getDescription() { return getName(); }
    }
}
