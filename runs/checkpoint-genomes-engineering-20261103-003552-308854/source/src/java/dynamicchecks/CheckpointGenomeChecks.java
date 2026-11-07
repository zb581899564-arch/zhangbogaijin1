package org.uma.jmetal.util.research.runtime;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingProblemData;
import org.uma.jmetal.util.research.joint.JointCheckProblem;
import org.uma.jmetal.util.research.model.*;
import research.dynamic.AnytimeRecorder;
import research.dynamic.CheckpointGenomes;
import research.dynamic.DynamicInputs;
import research.dynamic.DynamicJson;

/** Forced late-admission and real paid-genome replay; no optimizer evaluation. */
public final class CheckpointGenomeChecks {
    private CheckpointGenomeChecks() { }

    public static void main(String[] args) throws Exception {
        Path out = Paths.get(args[0]); Files.createDirectories(out);
        SeededRandom.reset(713);
        forcedLateAdmission(out); legacyDefaultCallback(); emptyAndCensored(out);
        if (args.length == 5) realPaidGenome(out, Paths.get(args[1]), Paths.get(args[2]), Paths.get(args[3]), Paths.get(args[4]));
        System.out.println("CHECKPOINT_GENOMES_PASS late final archive cannot erase T genomes; immutable earliest paid copy; default callback; empty/censored; RNG unchanged; optimizerFE=0");
    }

    private static void forcedLateAdmission(Path out) throws Exception {
        JointCheckProblem raw = new JointCheckProblem(6);
        ThreeObjectiveArchive<PermutationSolution<Integer>> archive = new ThreeObjectiveArchive<>();
        AnytimeRecorder recorder = new AnytimeRecorder(15000, 10, new double[] {.5, 1}, new long[] {2, 3, 15000});
        CheckpointGenomes capture = new CheckpointGenomes(recorder, 10);
        PermutationSolution<Integer> first = raw.createSolution(); setObjectives(first, 9);
        int firstJob = first.getVariableValue(0);
        SeededRandom.reset(911);
        boolean changed = archive.addEvaluated(first); capture.completedSolution(first, 1, 1, changed, archive);
        // Duplicate observer notification must retain the earliest provenance and immutable vectors.
        capture.completedSolution(first, 1, 2, true, archive);
        first.setVariableValue(0, -999);
        PermutationSolution<Integer> second = archive.snapshot().get(0); setObjectives(second, 8);
        changed = archive.addEvaluated(second); capture.completedSolution(second, 2, 6, changed, archive);
        PermutationSolution<Integer> late = archive.snapshot().get(0); setObjectives(late, 1);
        changed = archive.addEvaluated(late); capture.completedSolution(late, 3, 11, changed, archive);
        require(archive.size() == 1 && archive.objectiveSnapshot()[0][0] == 1, "Late point did not evict old final archive");
        List<Map<String, Object>> rows = capture.checkpointSolutions();
        require(rows.size() == 3, "Censored/empty points fabricated checkpoint genomes");
        require(((double[]) rows.get(0).get("objectives"))[0] == 9, "Old halfT genome lost");
        require(((double[]) rows.get(1).get("objectives"))[0] == 8, "Old T genome lost");
        require(((Number) rows.get(0).get("bornFE")).longValue() == 1
                && ((Number) rows.get(0).get("bornSeconds")).doubleValue() == 1, "First paid provenance overwritten");
        require(((int[]) rows.get(0).get("JS"))[0] == firstJob, "Source mutation reached cached genome");
        ((int[]) rows.get(0).get("JS"))[0] = -123;
        require(((int[]) capture.checkpointSolutions().get(0).get("JS"))[0] == firstJob, "Export mutation reached cache");
        require(SeededRandom.current().nextLong() == new Random(911).nextLong(), "Capture consumed RNG");
        List<String> lines = new ArrayList<>();
        for (Map<String, Object> row : capture.checkpointSolutions()) lines.add(DynamicJson.encode(row));
        Files.write(out.resolve("late-recovered-checkpoints.jsonl"), lines, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        Map<String, Object> proof = new LinkedHashMap<>();
        proof.put("forcedLateFinalObjective", archive.objectiveSnapshot()[0]); proof.put("recoveredReachedPoints", rows.size());
        proof.put("TObjectiveRecovered", 8); proof.put("halfTObjectiveRecovered", 9); proof.put("latePointAbsentFromCheckpoints", true);
        proof.put("scope", "Synthetic observer timestamps/objectives; no schedule evaluation or optimizer FE");
        Files.write(out.resolve("late-admission-proof.json"), Collections.singletonList(DynamicJson.encode(proof)),
                StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
    }

    private static void legacyDefaultCallback() {
        final long[] observedFE = {-1}; final double[] observedSeconds = {-1}; final boolean[] observedChanged = {false};
        EvaluationObserver legacy = (fe, seconds, changed, archive) -> {
            observedFE[0] = fe; observedSeconds[0] = seconds; observedChanged[0] = changed;
        };
        legacy.completedSolution(null, 42, 7.25, true, new ThreeObjectiveArchive<>());
        require(observedFE[0] == 42 && observedSeconds[0] == 7.25 && observedChanged[0], "Default callback altered old observer arguments");
    }

    private static void emptyAndCensored(Path out) throws Exception {
        AnytimeRecorder recorder = new AnytimeRecorder(0, 10, new double[] {.5, 1}, new long[] {0, 1});
        CheckpointGenomes capture = new CheckpointGenomes(recorder, 10);
        require(capture.checkpointSolutions().isEmpty(), "Unreached FE or empty front fabricated genomes");
        JointCheckProblem raw = new JointCheckProblem(6);
        Map<String, Object> result = capture.validateAndWrite(out.resolve("empty"), raw.instance, raw.parameters);
        require(((Number) result.get("checkpointPoints")).intValue() == 0
                && ((Number) result.get("uniqueOfflineDecodes")).intValue() == 0
                && Boolean.TRUE.equals(result.get("allReachedPointsCovered")), "Empty checkpoint coverage/QA count wrong");
    }

    @SuppressWarnings("unchecked")
    private static void realPaidGenome(Path out, Path input, Path setup, Path fatigue, Path vectors) throws Exception {
        System.setProperty("dhfsp.dataDir", input.toAbsolutePath().getParent().toString());
        System.setProperty("dhfsp.standbyPower", "1.0"); System.setProperty("dhfsp.setupFile", setup.toAbsolutePath().toString());
        String[] name = input.getFileName().toString().replace(".txt", "").split("_");
        Problem<PermutationSolution<Integer>> problem = (Problem<PermutationSolution<Integer>>) Class
                .forName("org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW").getConstructor(int.class, int.class, int.class, int.class)
                .newInstance(Integer.parseInt(name[0]), Integer.parseInt(name[1]), Integer.parseInt(name[2]), Integer.parseInt(name[3]));
        Instance in = ((SchedulingProblemData) problem).getSchedulingInstance();
        DynamicParameters parameters = DynamicInputs.fatigue(in, fatigue);
        List<String> data = Files.readAllLines(vectors, StandardCharsets.UTF_8);
        PermutationSolution<Integer> solution = problem.createSolution();
        double[] objectives = doubles(data.get(0));
        int[][] genome = new int[4][]; for (int k = 0; k < 4; k++) genome[k] = integers(data.get(k + 1));
        for (int p = 0; p < in.jobs(); p++) {
            solution.setVariableValue(p, genome[0][p]); solution.setVariableValueid(p, genome[1][p]);
            solution.setVariableValuemachine(p, genome[2][p]); solution.setVariableValueworker(p, genome[3][p]);
        }
        for (int k = 0; k < 3; k++) solution.setObjective(k, objectives[k]);
        ThreeObjectiveArchive<PermutationSolution<Integer>> archive = new ThreeObjectiveArchive<>();
        AnytimeRecorder recorder = new AnytimeRecorder(2, 10, new double[] {.5, 1}, new long[] {1, 2});
        CheckpointGenomes capture = new CheckpointGenomes(recorder, 10);
        SeededRandom.reset(1217);
        boolean changed = archive.addEvaluated(solution); capture.completedSolution(solution, 1, 1, changed, archive);
        Map<String, Object> result = capture.validateAndWrite(out.resolve("real-paid-replay"), in, parameters);
        require(((Number) result.get("checkpointPoints")).intValue() == 3
                && ((Number) result.get("uniqueOfflineDecodes")).intValue() == 1, "Unique offline replay was not deduplicated");
        require(SeededRandom.current().nextLong() == new Random(1217).nextLong(), "Offline validation consumed RNG");
        System.out.println("CHECKPOINT_REAL_PAID_REPLAY_PASS uniqueOfflineDecodes=1 checkpointPoints=3 optimizerFE=0");
    }

    private static double[] doubles(String line) { return Arrays.stream(line.trim().split(",")).mapToDouble(Double::parseDouble).toArray(); }
    private static int[] integers(String line) { return Arrays.stream(line.trim().split(",")).mapToInt(Integer::parseInt).toArray(); }
    private static void setObjectives(PermutationSolution<Integer> solution, double value) {
        for (int k = 0; k < 3; k++) solution.setObjective(k, value);
    }
    private static void require(boolean condition, String message) { if (!condition) throw new AssertionError(message); }
}
