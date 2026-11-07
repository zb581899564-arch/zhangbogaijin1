package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.search.Direction;

/** Paid offline witness-continuation diagnostic; never supplies labels or actions to search. */
public final class DynamicMechanismDiagnostic {
    private DynamicMechanismDiagnostic() { }
    @SuppressWarnings("unchecked")
    public static void write(Path out, Instance in, DynamicParameters params, List<Map<String, Object>> traces) throws Exception {
        long start = System.nanoTime(); int decodes = 0, decisions = 0; double regret = 0;
        List<Map<String, Object>> records = new ArrayList<>();
        for (Map<String, Object> trace : traces) {
            List<List<Integer>> parent = (List<List<Integer>>) trace.get("parent");
            int begin = ((Number) trace.get("blockBegin")).intValue(), length = ((Number) trace.get("blockLength")).intValue();
            Direction direction = Direction.valueOf(trace.get("direction").toString());
            List<Number> scales = (List<Number>) trace.get("scales");
            List<List<Integer>> committed = new ArrayList<>();
            for (Map<String, Object> decision : (List<Map<String, Object>>) trace.get("decisions")) {
                List<Map<String, Object>> candidates = (List<Map<String, Object>>) decision.get("candidates");
                int chosen = ((Number) decision.get("chosen")).intValue(); double best = Double.POSITIVE_INFINITY;
                List<Double> truth = new ArrayList<>(), predicted = new ArrayList<>();
                for (Map<String, Object> candidate : candidates) {
                    List<List<Integer>> full = new ArrayList<>(parent.subList(0, begin)); full.addAll(committed);
                    full.add((List<Integer>) candidate.get("action"));
                    full.addAll((List<List<Integer>>) candidate.get("witness"));
                    full.addAll(parent.subList(begin + length, parent.size()));
                    int[][] genes = new int[4][in.jobs()];
                    for (int p = 0; p < full.size(); p++) for (int q = 0; q < 4; q++) genes[q][p] = full.get(p).get(q);
                    DynamicSchedule schedule = DynamicDecoder.full(in, params, genes[0], genes[1], genes[2], genes[3], () -> { });
                    DynamicValidator.validate(in, params, schedule); decodes++;
                    double scalar = scalar(schedule.objectives(), scales, direction);
                    truth.add(scalar); best = Math.min(best, scalar);
                    predicted.add(((Number) candidate.get("score")).doubleValue());
                }
                double r = truth.get(chosen) - best; regret += r; decisions++;
                Map<String, Object> row = new LinkedHashMap<>(); row.put("direction", direction.name());
                row.put("predictedScores", predicted); row.put("trueWitnessContinuationCosts", truth);
                row.put("chosen", chosen); row.put("regret", r); records.add(row);
                committed.add((List<Integer>) candidates.get(chosen).get("action"));
            }
        }
        Map<String, Object> report = new LinkedHashMap<>();
        report.put("scope", "offline fixed-witness continuation; not optimal value or on-policy value accuracy; no feedback to search");
        report.put("trajectories", traces.size()); report.put("decisions", decisions); report.put("fullDecodes", decodes);
        report.put("meanRegret", decisions == 0 ? 0 : regret / decisions);
        report.put("offlineSeconds", (System.nanoTime() - start) / 1e9); report.put("records", records);
        Files.write(out.resolve("mechanism-diagnostic.json"), Arrays.asList(DynamicJson.encode(report)), StandardCharsets.UTF_8);
        List<String> traceLines = new ArrayList<>(); for (Map<String, Object> trace : traces) traceLines.add(DynamicJson.encode(trace));
        Files.write(out.resolve("trajectories.jsonl"), traceLines, StandardCharsets.UTF_8);
    }
    private static double scalar(double[] values, List<Number> scales, Direction direction) {
        if (direction.objective() >= 0) return values[direction.objective()] / scales.get(direction.objective()).doubleValue();
        double total = 0; for (int q = 0; q < 3; q++) total += values[q] / scales.get(q).doubleValue() / 3; return total;
    }
}
