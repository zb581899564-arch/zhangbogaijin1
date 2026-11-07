package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.*;

/** Export and independent replay happen after the timed search and never feed search. */
public final class DynamicOutput {
    private DynamicOutput() { }
    public static void write(Path out, Instance in, DynamicParameters params,
            List<PermutationSolution<Integer>> results, Map<String, Object> summary) throws Exception {
        write(out, in, params, results, summary, true);
    }
    public static void write(Path out, Instance in, DynamicParameters params,
            List<PermutationSolution<Integer>> results, Map<String, Object> summary, boolean timelineEnabled) throws Exception {
        results = new ArrayList<>(results);
        results.sort(Comparator.comparingDouble(s -> s.getObjective(0)));
        List<String> fronts = new ArrayList<>(), genomes = new ArrayList<>(), timeline = new ArrayList<>();
        fronts.add("Cmax\tTEC\tTWC");
        timeline.add("solution\tjob\tfactory\tstage\tmachine\tworker\tstart\tsetup_end\tend\tu\tv\texposure");
        int index = 0;
        for (PermutationSolution<Integer> s : results) {
            DynamicSchedule saved = (DynamicSchedule) s.getAttribute(DynamicEvaluation.KEY);
            DynamicValidator.validate(in, params, saved);
            DynamicSchedule replay = DynamicDecoder.full(in, params,
                    SchedulingEncoding.integers(s.getVariables()), SchedulingEncoding.integers(s.getVariablesid()),
                    SchedulingEncoding.machineIntegers(s), SchedulingEncoding.integers(s.getVariablesworker()), () -> { });
            DynamicValidator.validate(in, params, replay);
            if (!Arrays.equals(s.getObjectives(), replay.objectives())) throw new AssertionError("Archive replay changed objectives");
            double[] f = s.getObjectives(); fronts.add(f[0] + "\t" + f[1] + "\t" + f[2]);
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("objectives", f); row.put("JS", s.getVariables()); row.put("FA", s.getVariablesid());
            row.put("MA", SchedulingEncoding.machineIntegers(s)); row.put("WA", s.getVariablesworker());
            row.put("totalWorkExposure", replay.totalExposure()); row.put("maxWorkerWorkExposure", replay.maxExposure());
            row.put("peakFatigue", replay.peakFatigue()); genomes.add(DynamicJson.encode(row));
            if (timelineEnabled) for (DynamicStep op : replay.steps()) timeline.add(index + "\t" + op.job() + "\t" + op.factory()
                    + "\t" + op.stage() + "\t" + op.machine() + "\t" + op.worker() + "\t" + op.start()
                    + "\t" + (op.start() + op.setupDuration()) + "\t" + op.completion()
                    + "\t" + op.u() + "\t" + op.v() + "\t" + op.exposure());
            index++;
        }
        summary.put("archiveSize", index); summary.put("offlineValidationDecodes", index);
        summary.put("timelineExported", timelineEnabled);
        write(out.resolve("front.tsv"), fronts); write(out.resolve("solutions.jsonl"), genomes);
        if (timelineEnabled) write(out.resolve("schedule.tsv"), timeline);
        write(out.resolve("summary.json"), Arrays.asList(DynamicJson.encode(summary)));
    }
    private static void write(Path path, List<String> lines) throws Exception {
        Files.write(path, lines, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
    }
}
