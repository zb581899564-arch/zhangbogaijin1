package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.DynamicParameters;
import org.uma.jmetal.util.research.model.DynamicSchedule;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.runtime.RunContext;

/** Fully paid source replay and matched complete programs, no evolving source pool or mainline changes. */
public final class LinkageMixingRun {
    private LinkageMixingRun() { }
    static final class Probe {
        final Instance in;final DynamicParameters params;final RunContext<PermutationSolution<Integer>> context;
        final Path out;final long noiseSeed;final PddrPaidDigest digest = new PddrPaidDigest();
        final Map<Integer,PermutationSolution<Integer>> sources = new LinkedHashMap<>();
        final Map<String,List<Integer>> groups = new LinkedHashMap<>();
        final List<PermutationSolution<Integer>> reference = new ArrayList<>();
        final List<int[]> subsets = new ArrayList<>(), relabeled = new ArrayList<>();
        long qa, contracts;
        Probe(Instance instance, DynamicParameters parameters, RunContext<PermutationSolution<Integer>> run, Path output, long seed) {
            in = instance;params = parameters;context = run;out = output;noiseSeed = seed;
        }
        void check(PermutationSolution<Integer> point) {
            qa++;DynamicSchedule full = NeutralProbeSupport.full(in, params, point);
            NeutralProbeSupport.sameTimeline((DynamicSchedule)point.getAttribute(DynamicEvaluation.KEY), full);
        }
        void replay(Path input) throws Exception {
            for (String line : Files.readAllLines(input, StandardCharsets.UTF_8)) {
                String[] f = line.split("\t");int index = Integer.parseInt(f[0]);
                PermutationSolution<Integer> point = context.problem().createSolution();ProbeData.fill(point, f, 4, -1, null);
                if (SchedulingEncoding.repair(point, in) != 0) throw new AssertionError("Source repair differs");
                context.problem().evaluate(point);digest.update(context.budget().successful(), point);ProbeData.expected(point, f[3]);check(point);
                if (sources.put(index, point) != null) throw new AssertionError("Repeated source index");reference.add(point);
                if (Integer.parseInt(f[2]) == 0) groups.computeIfAbsent(f[1], key -> new ArrayList<>()).add(index);
            }
            if (sources.size() != 100 || groups.values().stream().mapToInt(List::size).sum() != 80) throw new AssertionError("Wrong source supply");
        }
        void subsetFile(Path path) throws Exception {
            for (String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
                String[] fields = line.split("\t");int[] a = ProbeData.integers(fields[0]), b = ProbeData.integers(fields[1]);
                if (a.length != b.length) throw new AssertionError("Random control changed subset size");
                for (int[] subset : new int[][]{a, b}) {
                    boolean[] seen = new boolean[in.jobs()];for (int j : subset) {
                        if (j < 0 || j >= in.jobs() || seen[j]) throw new AssertionError("Invalid linkage subset");seen[j] = true;
                    }
                }
                subsets.add(a);relabeled.add(b);
            }
            if (subsets.size() != 2 * in.jobs() - 1) throw new AssertionError("Wrong full tree size");
        }
        void execute(Path folder) throws Exception {
            replay(folder.resolve("sources.tsv"));subsetFile(folder.resolve("subsets.tsv"));
            List<String> originals = new ArrayList<>();for (PermutationSolution<Integer> point : reference) originals.add(ProbeData.key(point));
            LinkageMixingProgram program = new LinkageMixingProgram(this);int ordinal = 0;
            for (String line : Files.readAllLines(folder.resolve("parents.tsv"), StandardCharsets.UTF_8)) {
                String[] p = line.split("\t");int index = Integer.parseInt(p[2]);List<Integer> group = groups.get(p[0]);
                if (!group.contains(index)) throw new AssertionError("Receiver is not free in its declared role");
                contracts += LinkageGenomeChecks.check(in, sources.get(index), sources.get(group.get((ordinal + 1) % group.size())));
                program.run(p[0], Integer.parseInt(p[1]), ordinal, index, ordinal % LinkageMixingProgram.METHODS.length);ordinal++;
            }
            if (ordinal != 32) throw new AssertionError("Wrong fixed receiver count");
            for (int i = 0; i < reference.size(); i++) if (!originals.get(i).equals(ProbeData.key(reference.get(i)))) throw new AssertionError("Paid source mutated");
        }
    }

    public static void main(String[] args) throws Exception {
        Path input = Paths.get(args[0]), folder = Paths.get(args[3]), out = Paths.get(args[4]);Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir", input.getParent().toString());System.setProperty("dhfsp.setupFile", args[1]);
        System.setProperty("dhfsp.standbyPower", "1");System.setProperty("research.pddr.mode", "LINEAR");
        System.setProperty("research.makespan.tie", "STRICT");
        String[] d = input.getFileName().toString().replace(".txt", "").split("_");
        EDHHFSPW raw = new EDHHFSPW(Integer.parseInt(d[0]), Integer.parseInt(d[1]), Integer.parseInt(d[2]), Integer.parseInt(d[3]));
        Instance in = raw.getSchedulingInstance();DynamicParameters params = DynamicInputs.fatigue(in, Paths.get(args[2]));
        DynamicEvaluation decoder = new DynamicEvaluation(raw, in, params, true);
        long limit = 100 + 32L * 4 * (2 * in.jobs() - 1), seed = Long.parseLong(args[5]);
        RunContext<PermutationSolution<Integer>> run = new RunContext<>(decoder, limit, seed);decoder.setCheckpoint(run::checkpoint);
        Probe probe = new Probe(in, params, run, out, seed);boolean complete = false;
        NeutralProbeSupport.append(out.resolve("loaded-identity.jsonl"), ClassResolutionProbe.capture(
            "research.dynamic.LinkageMixingRun", "research.dynamic.LinkageGenome", "org.uma.jmetal.util.research.classic.ClassicKernelBridge",
            "org.uma.jmetal.util.research.search.LocalPddrKernel", "org.uma.jmetal.util.research.DynamicEvaluation",
            "org.uma.jmetal.util.research.model.DynamicDecoder", "org.uma.jmetal.util.research.model.DynamicValidator"));
        try {
            run.run(new Algorithm<Object>() {
                private static final long serialVersionUID = 1L;
                public void run() { try { probe.execute(folder); } catch (java.io.IOException e) { throw new java.io.UncheckedIOException(e); }
                    catch (Exception e) { throw new IllegalStateException(e); } }
                public Object getResult() { return null; }public String getName() { return "FA_LINKAGE_FULL_PROGRAM_PROBE"; }
                public String getDescription() { return getName(); }
            });
            if (run.budget().successful() != limit || run.budget().failed() != 0 || probe.qa != limit || probe.contracts != 192)
                throw new AssertionError("Incomplete linkage program accounting/QA");
            complete = true;
        } finally {
            List<Map<String,Object>> front = new ArrayList<>();for (PermutationSolution<Integer> point : run.result()) front.add(ProbeData.encoding(point));
            NeutralProbeSupport.append(out.resolve("receipt.jsonl"), NeutralProbeSupport.row("status", complete ? "COMPLETE" : "INCOMPLETE_RETAINED",
                "expectedFE", limit, "successfulFE", run.budget().successful(), "attemptedFE", run.budget().attempted(),
                "failedFE", run.budget().failed(), "fullDecoderQA", probe.qa, "pureGenomeContractChecks", probe.contracts,
                "paidSHA256", probe.digest.finish(), "jobs", in.jobs(), "stages", in.stages(), "factories", in.factories(),
                "decoder", decoder.diagnostics(), "lastValidFront", front));decoder.clearPrepared();
        }
    }
}
