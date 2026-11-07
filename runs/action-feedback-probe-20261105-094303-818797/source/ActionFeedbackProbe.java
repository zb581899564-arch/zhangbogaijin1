package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
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
import org.uma.jmetal.util.research.runtime.SeededRandom;
import org.uma.jmetal.util.research.search.IntraNeighborhoods;

/** Balanced, fully charged action outcomes. No learned policy participates in search. */
public final class ActionFeedbackProbe {
    private static final int REPLICATES = 4;
    private final Path output;
    private final Instance instance;
    private final DynamicParameters parameters;
    private final RunContext<PermutationSolution<Integer>> context;
    private final IntraNeighborhoods neighborhoods;
    private final double[] scale;
    private long qaCalls;

    private ActionFeedbackProbe(Path out, Instance in, DynamicParameters params,
            RunContext<PermutationSolution<Integer>> run, double[] scales) {
        output = out;
        instance = in;
        parameters = params;
        context = run;
        scale = scales;
        neighborhoods = new IntraNeighborhoods(in);
    }

    public static void main(String[] args) throws Exception {
        Path input = Paths.get(args[0]), out = Paths.get(args[4]);
        Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir", input.getParent().toString());
        System.setProperty("dhfsp.setupFile", args[1]);
        System.setProperty("dhfsp.standbyPower", "1.0");
        String[] dimensions = input.getFileName().toString().replace(".txt", "").split("_");
        EDHHFSPW raw = new EDHHFSPW(Integer.parseInt(dimensions[0]), Integer.parseInt(dimensions[1]),
                Integer.parseInt(dimensions[2]), Integer.parseInt(dimensions[3]));
        Instance in = raw.getSchedulingInstance();
        DynamicParameters params = DynamicInputs.fatigue(in, Paths.get(args[2]));
        DynamicEvaluation evaluator = new DynamicEvaluation(raw, in, params, true);
        List<String> cases = Files.readAllLines(Paths.get(args[3]), StandardCharsets.UTF_8);
        long expected = (long) cases.size() * (1 + REPLICATES * IntraNeighborhoods.COUNT);
        RunContext<PermutationSolution<Integer>> run = new RunContext<>(evaluator, expected, 12860003L);
        evaluator.setCheckpoint(run::checkpoint);
        ActionFeedbackProbe probe = new ActionFeedbackProbe(out, in, params, run, numbers(args[5]));
        boolean completed = false;
        try {
            run.run(new Algorithm<Object>() {
                private static final long serialVersionUID = 1L;
                public void run() { for (String line : cases) probe.caseOutcomes(line); }
                public Object getResult() { return null; }
                public String getName() { return "PAID_ACTION_FEEDBACK_PROBE"; }
                public String getDescription() { return getName(); }
            });
            if (run.budget().successful() != expected || run.budget().failed() != 0)
                throw new AssertionError("Dataset budget did not complete exactly");
            completed = true;
        } finally {
            List<Map<String,Object>> valid = new ArrayList<>();
            for (PermutationSolution<Integer> point : run.result()) valid.add(encoding(point));
            NeutralProbeSupport.append(out.resolve("receipt.jsonl"), NeutralProbeSupport.row(
                    "status", completed ? "COMPLETE" : "INCOMPLETE_RETAINED",
                    "successfulFE", run.budget().successful(), "attemptedFE", run.budget().attempted(),
                    "failedFE", run.budget().failed(), "expectedFE", expected,
                    "fullDecoderQA", probe.qaCalls, "decoder", evaluator.diagnostics(),
                    "basicFeatureNames", ActionStateFeatures.BASIC_NAMES,
                    "fatigueFeatureNames", ActionStateFeatures.FATIGUE_NAMES,
                    "lastValidFront", valid));
        }
    }

    private void caseOutcomes(String line) {
        String[] fields = line.split("\t");
        String id = fields[0], contextId = fields[1], role = fields[3];
        long sourceSeed = Long.parseLong(fields[2]);
        int factory = Integer.parseInt(fields[4]), ordinal = Integer.parseInt(fields[5]);
        PermutationSolution<Integer> parent = context.problem().createSolution();
        fill(parent, fields);
        if (SchedulingEncoding.repair(parent, instance) != 0)
            throw new AssertionError("Stored parent needs repair: " + id);
        context.problem().evaluate(parent);
        if (!Arrays.equals(numbers(fields[6]), parent.getObjectives()))
            throw new AssertionError("Stored parent objectives differ: " + id);
        validate(parent);
        long started = System.nanoTime();
        double[] features = ActionStateFeatures.extract(instance, parent, factory, scale);
        long featureNanos = System.nanoTime() - started;
        for (double value : features) if (!Double.isFinite(value))
            throw new AssertionError("Nonfinite candidate-free feature");
        NeutralProbeSupport.append(output.resolve("parents.jsonl"), NeutralProbeSupport.row(
                "id", id, "context", contextId, "sourceSeed", sourceSeed, "role", role,
                "factory", factory, "features", features, "featureNanos", featureNanos,
                "parent", encoding(parent)));
        DynamicSchedule original = (DynamicSchedule) parent.getAttribute(DynamicEvaluation.KEY);
        for (int action = 0; action < IntraNeighborhoods.COUNT; action++) {
            for (int rep = 0; rep < REPLICATES; rep++) {
                long seed = 12860003L + ordinal * 1009L + action * 37L + rep;
                SeededRandom.reset(seed);
                started = System.nanoTime();
                PermutationSolution<Integer> child = neighborhoods.propose(parent, factory, action);
                long generationNanos = System.nanoTime() - started;
                started = System.nanoTime();
                context.problem().evaluate(child);
                long evaluationNanos = System.nanoTime() - started;
                validate(child);
                requireUnchanged(parent, original);
                NeutralProbeSupport.append(output.resolve("outcomes.jsonl"), NeutralProbeSupport.row(
                        "id", id, "action", action, "rep", rep, "seed", seed,
                        "generationNanos", generationNanos, "evaluationNanos", evaluationNanos,
                        "candidate", encoding(child)));
            }
        }
    }

    private void validate(PermutationSolution<Integer> point) {
        qaCalls++;
        DynamicSchedule cached = (DynamicSchedule) point.getAttribute(DynamicEvaluation.KEY);
        DynamicSchedule full = NeutralProbeSupport.full(instance, parameters, point);
        NeutralProbeSupport.sameTimeline(cached, full);
        if (!Arrays.equals(point.getObjectives(), full.objectives()))
            throw new AssertionError("Paid objectives differ from full QA");
    }

    private static void requireUnchanged(PermutationSolution<Integer> parent, DynamicSchedule original) {
        if (parent.getAttribute(DynamicEvaluation.KEY) != original
                || !Arrays.equals(original.js(), SchedulingEncoding.integers(parent.getVariables()))
                || !Arrays.equals(original.fa(), SchedulingEncoding.integers(parent.getVariablesid()))
                || !Arrays.equals(original.ma(), SchedulingEncoding.machineIntegers(parent))
                || !Arrays.equals(original.wa(), SchedulingEncoding.integers(parent.getVariablesworker())))
            throw new AssertionError("Original neighborhood mutated its paid parent");
    }

    @SuppressWarnings("unchecked")
    private static void fill(PermutationSolution<Integer> point, String[] fields) {
        List<Integer> machines = (List<Integer>) point.getAttribute("machine");
        for (int vector = 0; vector < 4; vector++) {
            int[] values = Arrays.stream(fields[7 + vector].split(","))
                    .mapToInt(Integer::parseInt).toArray();
            if (values.length != point.getNumberOfVariables()) throw new AssertionError("Bad genome length");
            for (int index = 0; index < values.length; index++) {
                if (vector == 0) point.setVariableValue(index, values[index]);
                else if (vector == 1) point.setVariableValueid(index, values[index]);
                else if (vector == 2) machines.set(index, values[index]);
                else point.setVariableValueworker(index, values[index]);
            }
        }
    }

    private static double[] numbers(String text) {
        return Arrays.stream(text.split(",")).mapToDouble(Double::parseDouble).toArray();
    }

    private static Map<String,Object> encoding(PermutationSolution<Integer> point) {
        return NeutralProbeSupport.row("JS", point.getVariables(), "FA", point.getVariablesid(),
                "MA", point.getAttribute("machine"), "WA", point.getVariablesworker(),
                "objectives", point.getObjectives().clone());
    }
}
