package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.Solution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.EvaluationObserver;
import org.uma.jmetal.util.research.runtime.ThreeObjectiveArchive;

/** Optional immutable paid-admission genomes, independent of the final live archive. */
public final class CheckpointGenomes implements EvaluationObserver {
    private final AnytimeRecorder recorder;
    private final double timeLimit;
    private final Map<ObjectiveKey, Genome> paid = new LinkedHashMap<>();
    private long captureNanos, admissions, excludedLate;

    public CheckpointGenomes(AnytimeRecorder recorder, double timeLimit) {
        if (recorder == null || Double.isNaN(timeLimit) || timeLimit < 0)
            throw new IllegalArgumentException("Recorder and nonnegative time limit required");
        this.recorder = recorder; this.timeLimit = timeLimit;
    }

    @Override public void completed(long fe, double seconds, boolean changed, ThreeObjectiveArchive<?> archive) {
        recorder.completed(fe, seconds, changed, archive);
    }

    @Override public void completedSolution(Solution<?> solution, long fe, double seconds,
            boolean changed, ThreeObjectiveArchive<?> archive) {
        long start = System.nanoTime();
        try {
            if (changed && seconds <= timeLimit) {
                if (fe < 1 || !Double.isFinite(seconds) || seconds < 0)
                    throw new IllegalArgumentException("Checkpoint genome must have paid finite provenance");
                admissions++;
                ObjectiveKey key = new ObjectiveKey(solution.getObjectives());
                if (!paid.containsKey(key)) paid.putIfAbsent(key, new Genome(solution, fe, seconds));
            } else if (changed) excludedLate++;
        } finally { captureNanos += System.nanoTime() - start; }
        // The original completion timestamp is retained; capture cost still advances RunClock.
        recorder.completed(fe, seconds, changed, archive);
    }

    /** Read-only rows for all reached fronts; no fabrication for empty/censored rows. */
    public List<Map<String, Object>> checkpointSolutions() {
        List<Map<String, Object>> rows = new ArrayList<>();
        for (Map<String, Object> point : recorder.finish()) {
            double[][] front = (double[][]) point.get("front");
            if (!Boolean.TRUE.equals(point.get("reached"))) {
                if (front.length != 0) throw new IllegalStateException("Censored checkpoint has objectives");
                continue;
            }
            for (double[] objectives : front) {
                Genome genome = paid.get(new ObjectiveKey(objectives));
                if (genome == null) throw new IllegalStateException("Reached checkpoint lacks a paid genome");
                checkBirth(genome, point);
                rows.add(genome.record(point));
            }
        }
        return Collections.unmodifiableList(rows);
    }

    private void checkBirth(Genome genome, Map<String, Object> point) {
        long fe = ((Number) point.get("fe")).longValue();
        double seconds = ((Number) point.get("elapsedSeconds")).doubleValue();
        double checkpoint = ((Number) point.get("checkpoint")).doubleValue();
        if (genome.fe > fe || genome.seconds > seconds || genome.seconds > timeLimit)
            throw new IllegalStateException("Future/unpaid genome entered checkpoint");
        if ("TIME".equals(point.get("checkpointKind")) && genome.seconds > checkpoint
                || "FE".equals(point.get("checkpointKind")) && genome.fe > checkpoint)
            throw new IllegalStateException("Genome was born beyond the checkpoint budget");
    }

    /** Offline full replay is separate QA and never calls a search evaluator. */
    public Map<String, Object> validateAndWrite(Path out, Instance in, DynamicParameters parameters) throws Exception {
        long start = System.nanoTime();
        List<Map<String, Object>> rows = checkpointSolutions();
        Map<ObjectiveKey, Genome> unique = new LinkedHashMap<>();
        for (Map<String, Object> row : rows) {
            ObjectiveKey key = new ObjectiveKey((double[]) row.get("objectives"));
            unique.putIfAbsent(key, paid.get(key));
        }
        for (Genome genome : unique.values()) {
            DynamicSchedule replay = DynamicDecoder.full(in, parameters,
                    genome.js, genome.fa, genome.ma, genome.wa, () -> { });
            DynamicValidator.validate(in, parameters, replay);
            if (!Arrays.equals(genome.objectives, replay.objectives()))
                throw new AssertionError("Checkpoint paid genome replay changed objectives");
        }
        Map<String, Object> result = validation(rows.size(), unique.size(), (System.nanoTime() - start) / 1e9);
        List<String> lines = new ArrayList<>();
        for (Map<String, Object> row : rows) lines.add(DynamicJson.encode(row));
        Files.createDirectories(out);
        Files.write(out.resolve("checkpoint-solutions.jsonl"), lines, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        Files.write(out.resolve("checkpoint-validation.json"), Collections.singletonList(DynamicJson.encode(result)),
                StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        return result;
    }

    private Map<String, Object> validation(int covered, int unique, double offlineSeconds) {
        int reached = 0, censored = 0, points = 0;
        for (Map<String, Object> row : recorder.finish()) {
            if (Boolean.TRUE.equals(row.get("reached"))) {
                reached++; points += ((double[][]) row.get("front")).length;
            } else censored++;
        }
        if (points != covered) throw new IllegalStateException("Incomplete checkpoint genome coverage");
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("status", "passed"); result.put("enabled", true); result.put("policy", "SNAPSHOT_GENOMES-v1");
        result.put("checkpointRows", recorder.finish().size()); result.put("reachedCheckpoints", reached);
        result.put("censoredCheckpoints", censored); result.put("checkpointPoints", points); result.put("coveredPoints", covered);
        result.put("allReachedPointsCovered", true); result.put("uniqueOfflineDecodes", unique);
        result.put("cachedAcceptedObjectiveRepresentatives", paid.size()); result.put("deadlineValidAdmissionEvents", admissions);
        result.put("lateAdmissionsExcluded", excludedLate); result.put("searchCaptureSeconds", captureNanos / 1e9);
        result.put("offlineValidationSeconds", offlineSeconds); result.put("extraSearchFE", 0); result.put("consumesRNG", false);
        result.put("offlineCostBoundary", "Checkpoint lookup and unique full replay; JSON export remains in process/campaign wall");
        result.put("provenance", "Earliest paid admitted objective representative at or before T; no search feedback");
        return result;
    }

    private static final class ObjectiveKey {
        private final double[] values;
        ObjectiveKey(double[] values) {
            if (values.length != 3) throw new IllegalArgumentException("Three physical objectives required");
            this.values = values.clone();
            for (double value : values) if (!Double.isFinite(value)) throw new IllegalArgumentException("Nonfinite objective");
        }
        @Override public int hashCode() { return Arrays.hashCode(values); }
        @Override public boolean equals(Object other) { return other instanceof ObjectiveKey && Arrays.equals(values, ((ObjectiveKey) other).values); }
    }

    private static final class Genome {
        final double[] objectives; final int[] js, fa, ma, wa; final long fe; final double seconds;
        @SuppressWarnings("unchecked")
        Genome(Solution<?> value, long fe, double seconds) {
            if (!(value instanceof PermutationSolution<?>)) throw new IllegalArgumentException("Four-vector solution required");
            PermutationSolution<Integer> solution = (PermutationSolution<Integer>) value;
            objectives = solution.getObjectives().clone(); js = SchedulingEncoding.integers(solution.getVariables());
            fa = SchedulingEncoding.integers(solution.getVariablesid()); ma = SchedulingEncoding.machineIntegers(solution);
            wa = SchedulingEncoding.integers(solution.getVariablesworker()); this.fe = fe; this.seconds = seconds;
            if (js.length == 0 || fa.length != js.length || ma.length != js.length || wa.length != js.length)
                throw new IllegalArgumentException("Unaligned checkpoint four vectors");
        }
        Map<String, Object> record(Map<String, Object> checkpoint) {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("checkpointKind", checkpoint.get("checkpointKind")); row.put("checkpoint", checkpoint.get("checkpoint"));
            row.put("objectives", objectives.clone()); row.put("JS", js.clone()); row.put("FA", fa.clone());
            row.put("MA", ma.clone()); row.put("WA", wa.clone()); row.put("bornFE", fe); row.put("bornSeconds", seconds);
            row.put("checkpointFE", checkpoint.get("fe")); row.put("checkpointElapsedSeconds", checkpoint.get("elapsedSeconds"));
            return Collections.unmodifiableMap(row);
        }
    }
}
