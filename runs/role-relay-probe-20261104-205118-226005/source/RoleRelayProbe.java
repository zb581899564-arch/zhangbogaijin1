package org.uma.jmetal.util.research.search;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;
import research.dynamic.DynamicInputs;
import research.dynamic.DynamicJson;

/** Paid whole-schedule continuations using the unchanged local engine; no inherited particle history. */
public final class RoleRelayProbe {
    private RoleRelayProbe() { }

    public static void main(String[] args) throws Exception {
        Path input = Paths.get(args[0]), out = Paths.get(args[5]);
        System.setProperty("dhfsp.dataDir", input.getParent().toString());
        System.setProperty("dhfsp.setupFile", args[1]);
        System.setProperty("dhfsp.standbyPower", "1.0");
        System.setProperty("research.qgsAudit.mode", "record");
        System.setProperty("research.pddr.mode", "LINEAR");
        EDHHFSPW raw = new EDHHFSPW(20, 2, 3, 1);
        Instance in = raw.getSchedulingInstance();
        DynamicParameters parameters = DynamicInputs.fatigue(in, Paths.get(args[2]));
        SeededRandom.reset(0);
        List<PermutationSolution<Integer>> reference = new ArrayList<>();
        for (String line : Files.readAllLines(Paths.get(args[3]), StandardCharsets.UTF_8)) {
            PermutationSolution<Integer> s = raw.createSolution(); fill(s, line.split("\t"), 0);
            reference.add(s);
        }
        long total = 0, validation = 0;
        for (String line : Files.readAllLines(Paths.get(args[4]), StandardCharsets.UTF_8)) {
            String[] fields = line.split("\t");
            String id = fields[0]; Direction target = Direction.valueOf(fields[1]);
            long seed = Long.parseLong(fields[2]); int limit = Integer.parseInt(fields[3]);
            DynamicEvaluation decoder = new DynamicEvaluation(raw, in, parameters, true);
            RunContext<PermutationSolution<Integer>> context = new RunContext<>(decoder, limit + 1, seed);
            decoder.setCheckpoint(context::checkpoint);
            SearchState state = new SearchState(context.problem(), in, null);
            state.observationGroup(target);
            LocalSearch local = new LocalSearch(in, 4, new SearchConfig().resolved(4), state);
            context.run(new Algorithm<Object>() {
                private static final long serialVersionUID = 1L;
                public void run() {
                    PermutationSolution<Integer> parent = context.problem().createSolution(); fill(parent, fields, 4);
                    if (SchedulingEncoding.repair(parent, in) != 0) throw new AssertionError("Illegal stored parent");
                    context.problem().evaluate(parent);
                    expected(parent, fields[4]);
                    // Initialization is paid; continuation starts with its own common stream.
                    SeededRandom.reset(seed);
                    Particle particle = new Particle(parent);
                    while (true) { context.checkpoint(); particle = local.improve(particle, target, reference); }
                }
                public Object getResult() { return null; }
                public String getName() { return "WHOLE_SCHEDULE_RELAY_PROBE"; }
                public String getDescription() { return getName(); }
            });
            if (context.budget().successful() != limit + 1 || context.budget().failed() != 0
                    || !"FE_LIMIT".equals(context.stopReason())) throw new AssertionError("Invalid continuation receipt");
            decoder.clearPrepared();
            List<Map<String,Object>> points = new ArrayList<>();
            for (PermutationSolution<Integer> solution : context.result()) {
                DynamicSchedule schedule = (DynamicSchedule) solution.getAttribute(DynamicEvaluation.KEY);
                DynamicValidator.validate(in, parameters, schedule);
                DynamicSchedule full = DynamicDecoder.full(in, parameters, SchedulingEncoding.integers(solution.getVariables()),
                        SchedulingEncoding.integers(solution.getVariablesid()), SchedulingEncoding.machineIntegers(solution),
                        SchedulingEncoding.integers(solution.getVariablesworker()), null);
                if (!Arrays.equals(full.objectives(), solution.getObjectives())) throw new AssertionError("QA replay mismatch");
                validation++;
                points.add(row("JS", solution.getVariables(), "FA", solution.getVariablesid(), "MA", solution.getAttribute("machine"),
                               "WA", solution.getVariablesworker(), "objectives", solution.getObjectives().clone()));
            }
            append(out.resolve("trials.jsonl"), row("id", id, "target", target.name(), "seed", seed,
                    "attempted", context.budget().attempted(), "successful", context.budget().successful(),
                    "failed", context.budget().failed(), "searchSeconds", context.clock().elapsedSeconds(),
                    "decoder", decoder.diagnostics(), "search", state.diagnostics(), "front", points));
            total += context.budget().successful();
        }
        append(out.resolve("receipt.jsonl"), row("successful", total, "failed", 0, "offlineFullQADecodes", validation));
    }

    @SuppressWarnings("unchecked")
    private static void fill(PermutationSolution<Integer> s, String[] f, int offset) {
        double[] expected = Arrays.stream(f[offset].split(",")).mapToDouble(Double::parseDouble).toArray();
        int[][] vector = new int[4][];
        for (int k = 0; k < 4; k++) vector[k] = Arrays.stream(f[offset + 1 + k].split(",")).mapToInt(Integer::parseInt).toArray();
        List<Integer> machines = (List<Integer>) s.getAttribute("machine");
        for (int p = 0; p < vector[0].length; p++) {
            s.setVariableValue(p, vector[0][p]); s.setVariableValueid(p, vector[1][p]);
            machines.set(p, vector[2][p]); s.setVariableValueworker(p, vector[3][p]);
        }
        for (int k = 0; k < 3; k++) s.setObjective(k, expected[k]);
    }
    private static void expected(PermutationSolution<Integer> s, String text) {
        double[] values = Arrays.stream(text.split(",")).mapToDouble(Double::parseDouble).toArray();
        if (!Arrays.equals(s.getObjectives(), values)) throw new AssertionError("Parent source replay differs");
    }
    private static Map<String,Object> row(Object... pairs) {
        Map<String,Object> value = new LinkedHashMap<>();
        for (int i = 0; i < pairs.length; i += 2) value.put((String) pairs[i], pairs[i + 1]);
        return value;
    }
    private static void append(Path path, Map<String,Object> value) throws Exception {
        Files.write(path, Collections.singletonList(DynamicJson.encode(value)), StandardCharsets.UTF_8,
                StandardOpenOption.CREATE, StandardOpenOption.APPEND);
    }
}
