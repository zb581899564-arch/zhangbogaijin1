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

/** Fully paid legal counterfactual schedules; no optimizer, teacher policy or repair-based attribution. */
public final class PrefixStateProbe {
    private final Path output;
    private final Instance instance;
    private final DynamicParameters parameters;
    private final RunContext<PermutationSolution<Integer>> context;
    private long qa;
    private PrefixStateProbe(Path out, Instance in, DynamicParameters params, RunContext<PermutationSolution<Integer>> run) {
        output = out;instance = in;parameters = params;context = run;
    }
    public static void main(String[] args) throws Exception {
        Path input = Paths.get(args[0]), out = Paths.get(args[4]);Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir", input.getParent().toString());System.setProperty("dhfsp.setupFile", args[1]);
        System.setProperty("dhfsp.standbyPower", "1");
        String[] d = input.getFileName().toString().replace(".txt", "").split("_");
        EDHHFSPW raw = new EDHHFSPW(Integer.parseInt(d[0]), Integer.parseInt(d[1]), Integer.parseInt(d[2]), Integer.parseInt(d[3]));
        Instance in = raw.getSchedulingInstance();DynamicParameters originalParameters = DynamicInputs.fatigue(in, Paths.get(args[2]));
        DynamicParameters params = Boolean.parseBoolean(args[5]) ? FactorBeta0Parameters.make(in, originalParameters) : originalParameters;
        if (Boolean.parseBoolean(args[5])) NeutralProbeSupport.append(out.resolve("parameter-contract.jsonl"),
            FactorBeta0Parameters.contract(in, originalParameters, params));
        DynamicEvaluation decoder = new DynamicEvaluation(raw, in, params, true);
        List<String> lines = Files.readAllLines(Paths.get(args[3]), StandardCharsets.UTF_8);
        RunContext<PermutationSolution<Integer>> run = new RunContext<>(decoder, lines.size(), 13310003L);
        decoder.setCheckpoint(run::checkpoint);PrefixStateProbe probe = new PrefixStateProbe(out, in, params, run);
        boolean complete = false;
        try {
            run.run(new Algorithm<Object>() {
                private static final long serialVersionUID = 1L;
                public void run() { for (String line : lines) probe.evaluate(line); }
                public Object getResult() { return null; }
                public String getName() { return "PAID_PREFIX_STATE_COUNTERFACTUAL"; }
                public String getDescription() { return getName(); }
            });
            if (run.budget().successful() != lines.size() || run.budget().failed() != 0 || probe.qa != lines.size())
                throw new AssertionError("Counterfactual fee/QA mismatch");
            complete = true;
        } finally {
            List<Map<String,Object>> front = new ArrayList<>();
            for (PermutationSolution<Integer> point : run.result()) front.add(encoding(point));
            NeutralProbeSupport.append(out.resolve("receipt.jsonl"), NeutralProbeSupport.row("status", complete ? "COMPLETE" : "INCOMPLETE_RETAINED",
                "expectedFE", lines.size(), "successfulFE", run.budget().successful(), "attemptedFE", run.budget().attempted(),
                "failedFE", run.budget().failed(), "fullDecoderQA", probe.qa, "decoder", decoder.diagnostics(), "lastValidFront", front));
            decoder.clearPrepared();
        }
    }
    private void evaluate(String line) {
        String[] fields = line.split("\t");PermutationSolution<Integer> point = context.problem().createSolution();
        fill(point, fields);
        if (SchedulingEncoding.repair(point, instance) != 0) throw new AssertionError("Legal source-bundle splice unexpectedly needs repair");
        context.problem().evaluate(point);
        if (!fields[2].equals("-") && !Arrays.equals(point.getObjectives(), numbers(fields[2])))
            throw new AssertionError("Source endpoint objective replay differs");
        qa++;
        DynamicSchedule full = NeutralProbeSupport.full(instance, parameters, point);
        NeutralProbeSupport.sameTimeline((DynamicSchedule)point.getAttribute(DynamicEvaluation.KEY), full);
        if (!Arrays.equals(point.getObjectives(), full.objectives())) throw new AssertionError("Counterfactual full objectives differ");
        PrefixStateChecks.observe(fields, full, output);
        NeutralProbeSupport.append(output.resolve("outcomes.jsonl"), NeutralProbeSupport.row("case", fields[0], "method", fields[1],
            "paidFE", context.budget().successful(), "repairEdits", 0, "genome", encoding(point)));
    }
    private static void fill(PermutationSolution<Integer> point, String[] fields) {
        @SuppressWarnings("unchecked") List<Integer> machines = (List<Integer>)point.getAttribute("machine");
        for (int vector = 0; vector < 4; vector++) {
            int[] values = Arrays.stream(fields[3 + vector].split(",")).mapToInt(Integer::parseInt).toArray();
            if (values.length != point.getNumberOfVariables()) throw new AssertionError("Source vector length differs");
            for (int i = 0; i < values.length; i++) {
                if (vector == 0) point.setVariableValue(i, values[i]);
                else if (vector == 1) point.setVariableValueid(i, values[i]);
                else if (vector == 2) machines.set(i, values[i]);
                else point.setVariableValueworker(i, values[i]);
            }
        }
    }
    private static double[] numbers(String value) { return Arrays.stream(value.split(",")).mapToDouble(Double::parseDouble).toArray(); }
    private static Map<String,Object> encoding(PermutationSolution<Integer> p) {
        return NeutralProbeSupport.row("JS", new ArrayList<>(p.getVariables()), "FA", new ArrayList<>(p.getVariablesid()),
            "MA", new ArrayList<>((List<?>)p.getAttribute("machine")), "WA", new ArrayList<>(p.getVariablesworker()), "objectives", p.getObjectives().clone());
    }
}
