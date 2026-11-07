package org.uma.jmetal.util.research.search;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;
import research.dynamic.DynamicJson;

/** Change only the CENTER outer VNS exit comparison, retaining original inner PDDR descent. */
public final class ProgramExitPolicy {
    private static final boolean ENABLED = Boolean.getBoolean("research.programExit.enabled");
    private static final boolean AUDIT = Boolean.getBoolean("research.programExit.audit");
    private static final double EPSILON = 1e-10, REFERENCE = 1.5;
    private static final double[] SCALE = vector("research.programExit.scale", true);
    private static final double[] LOWER = vector("research.programExit.lower", false);
    private static final List<Map<String,Object>> COMPARISONS = new ArrayList<>(), REFERENCES = new ArrayList<>();
    private static Reference current;
    private static long decisions, accepts, cacheHits, dominanceHits, referenceBuilds, metricNanos;
    private ProgramExitPolicy() { }
    public static void initialize() { }

    static boolean better(Direction direction, PermutationSolution<Integer> candidate,
            PermutationSolution<Integer> incumbent, List<PermutationSolution<Integer>> reference) {
        if (!ENABLED || direction != Direction.CENTER) return LocalPddrKernel.better(direction, candidate, incumbent, reference);
        long started = System.nanoTime();
        if (current == null || current.identity != reference) current = new Reference(reference, ++referenceBuilds);
        double c = current.score(candidate.getObjectives()), i = current.score(incumbent.getObjectives());
        boolean accepted = c > i + EPSILON;decisions++;if (accepted) accepts++;
        metricNanos += System.nanoTime() - started;
        if (AUDIT) {
            current.verifyUnchanged(reference);
            COMPARISONS.add(row("comparison", decisions, "reference", current.id,
                "candidate", candidate.getObjectives().clone(), "incumbent", incumbent.getObjectives().clone(),
                "candidateReferenceHV", c, "incumbentReferenceHV", i, "accepted", accepted,
                "originalPddrWouldAccept", LocalPddrKernel.better(direction, candidate, incumbent, reference)));
        }
        return accepted;
    }

    private static final class Reference {
        final List<PermutationSolution<Integer>> identity;
        final long id;final double[][] raw, points;final double base;
        final Map<String,Double> scores = new HashMap<>();
        Reference(List<PermutationSolution<Integer>> source, long value) {
            identity = source;id = value;raw = new double[source.size()][];
            double[][] normalized = new double[source.size()][];
            for (int j = 0; j < raw.length; j++) { raw[j] = source.get(j).getObjectives().clone();normalized[j] = normalize(raw[j]); }
            points = ProgramExitHv3D.nondominated(normalized);base = ProgramExitHv3D.volume(points, REFERENCE);
            if (AUDIT) REFERENCES.add(row("reference", id, "points", raw, "normalizedNondominatedCount", points.length));
        }
        double score(double[] objective) {
            String key = Arrays.toString(objective);Double old = scores.get(key);
            if (old != null) { cacheHits++;return old; }
            double[] point = normalize(objective);
            for (double[] other : points) if (other[0] <= point[0] && other[1] <= point[1] && other[2] <= point[2]) {
                dominanceHits++;scores.put(key, base);return base;
            }
            double[][] union = Arrays.copyOf(points, points.length + 1);union[points.length] = point;
            double result = ProgramExitHv3D.volume(union, REFERENCE);scores.put(key, result);return result;
        }
        void verifyUnchanged(List<PermutationSolution<Integer>> values) {
            if (values.size() != raw.length) throw new AssertionError("Reference size changed inside local phase");
            for (int j = 0; j < raw.length; j++) if (!Arrays.equals(raw[j], values.get(j).getObjectives()))
                throw new AssertionError("Cached local reference mutated");
        }
    }

    private static double[] normalize(double[] point) {
        double[] result = new double[3];
        for (int d = 0; d < 3; d++) {
            result[d] = (point[d] - LOWER[d]) / SCALE[d];
            if (!Double.isFinite(result[d]) || result[d] < 0) throw new IllegalArgumentException("Objective outside lower bound");
        }
        return result;
    }
    private static double[] vector(String name, boolean positive) {
        String input = System.getProperty(name, positive ? "1,1,1" : "0,0,0");
        double[] result = Arrays.stream(input.split(",")).mapToDouble(Double::parseDouble).toArray();
        if (result.length != 3) throw new IllegalArgumentException("Three normalization constants required");
        for (double value : result) if (!Double.isFinite(value) || positive && value <= 0) throw new IllegalArgumentException("Invalid normalization");
        return result;
    }
    public static void write(Path output) throws Exception {
        lines(output.resolve("program-exit-policy.jsonl"), java.util.Collections.singletonList(row(
            "enabled", ENABLED, "audit", AUDIT, "centerOuterDecisions", decisions, "centerOuterAccepts", accepts,
            "referenceBuilds", referenceBuilds, "cacheHits", cacheHits, "dominatedReferenceShortcuts", dominanceHits,
            "metricNanos", metricNanos, "scale", SCALE, "lower", LOWER, "referencePoint", REFERENCE,
            "strictThreshold", EPSILON, "innerPddrUnchanged", true, "objectiveEvaluationsInMetric", 0)));
        if (AUDIT) { lines(output.resolve("program-exit-references.jsonl"), REFERENCES);lines(output.resolve("program-exit-comparisons.jsonl"), COMPARISONS); }
    }
    private static Map<String,Object> row(Object... fields) {
        Map<String,Object> result = new LinkedHashMap<>();for (int j = 0; j < fields.length; j += 2) result.put((String)fields[j], fields[j + 1]);return result;
    }
    private static void lines(Path path, List<Map<String,Object>> values) throws Exception {
        List<String> result = new ArrayList<>();for (Map<String,Object> value : values) result.add(DynamicJson.encode(value));
        Files.write(path, result, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
    }
}
