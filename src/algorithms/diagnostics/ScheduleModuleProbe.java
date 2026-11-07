package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.algorithm.Algorithm;

/** Paid counterfactual encoding probe; oracle donor material never enters an optimizer. */
public final class ScheduleModuleProbe {
    private ScheduleModuleProbe() {}
    @SuppressWarnings("unchecked")
    private static List<Integer> machines(PermutationSolution<Integer> s) {
        return (List<Integer>) s.getAttribute("machine");
    }
    public static void main(String[] args) throws Exception {
        Path input = Paths.get(args[0]), out = Paths.get(args[4]);
        System.setProperty("dhfsp.dataDir", input.getParent().toString());
        System.setProperty("dhfsp.setupFile", args[1]);
        System.setProperty("dhfsp.standbyPower", "1.0");
        EDHHFSPW raw = new EDHHFSPW(20, 2, 3, 1);
        Instance in = raw.getSchedulingInstance();
        DynamicParameters p = DynamicInputs.fatigue(in, Paths.get(args[2]));
        List<String> cases = Files.readAllLines(Paths.get(args[3]), StandardCharsets.UTF_8);
        DynamicEvaluation eval = new DynamicEvaluation(raw, in, p, false);
        RunContext<PermutationSolution<Integer>> context = new RunContext<>(eval, cases.size(), 8111009);
        List<Map<String,Object>> results = new ArrayList<>();
        context.run(new Algorithm<Object>() {
            private static final long serialVersionUID = 1L;
            public void run() {
                for (String line : cases) {
                    String[] parts = line.split("\t");
                    PermutationSolution<Integer> s = context.problem().createSolution();
                    int at = 1;
                    for (int v = 0; v < 4; v++) for (int i = 0; i < in.jobs(); i++) {
                        int value = Integer.parseInt(parts[at++]);
                        if (v == 0) s.setVariableValue(i, value);
                        else if (v == 1) s.setVariableValueid(i, value);
                        else if (v == 2) machines(s).set(i, value);
                        else s.setVariableValueworker(i, value);
                    }
                    int edits = SchedulingEncoding.repair(s, in);
                    context.problem().evaluate(s);
                    DynamicSchedule schedule = (DynamicSchedule) s.getAttribute(DynamicEvaluation.KEY);
                    DynamicValidator.validate(in, p, schedule);
                    Map<String,Object> row = new LinkedHashMap<>();
                    row.put("case", parts[0]); row.put("objectives", s.getObjectives().clone()); row.put("repairEdits", edits);
                    row.put("factoryMakespan", schedule.factoryMakespan()); row.put("factoryEnergy", schedule.factoryEnergy());
                    row.put("factoryCost", schedule.factoryCost()); row.put("exposure", schedule.totalExposure());
                    row.put("peakFatigue", schedule.peakFatigue());
                    results.add(row);
                }
                context.problem().checkpoint();
            }
            public Object getResult() { return null; }
            public String getName() { return "PAID_MODULE_PROBE"; }
            public String getDescription() { return getName(); }
        });
        if (context.budget().successful() != cases.size() || context.budget().failed() != 0
                || !"FE_LIMIT".equals(context.stopReason())) throw new AssertionError("Incomplete module probe");
        List<String> lines = new ArrayList<>();
        for (Map<String,Object> row : results) lines.add(DynamicJson.encode(row));
        Files.write(out.resolve("results.jsonl"), lines, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        Map<String,Object> receipt = new LinkedHashMap<>();
        receipt.put("attempted", context.budget().attempted()); receipt.put("successful", context.budget().successful());
        receipt.put("failed", context.budget().failed()); receipt.put("stopReason", context.stopReason());
        receipt.put("decoder", eval.diagnostics()); receipt.put("searchSeconds", context.clock().elapsedSeconds());
        Files.write(out.resolve("receipt.json"), DynamicJson.encode(receipt).getBytes(StandardCharsets.UTF_8));
    }
}
