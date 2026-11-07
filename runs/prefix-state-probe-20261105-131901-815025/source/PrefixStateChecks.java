package research.dynamic;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.uma.jmetal.util.research.model.DynamicSchedule;
import org.uma.jmetal.util.research.model.DynamicStep;

/** Only the copied first-stage leading block is state invariant; later stages are unconstrained. */
final class PrefixStateChecks {
    private static String teacherCase;
    private static DynamicSchedule teacher;
    private PrefixStateChecks() { }

    static void observe(String[] fields, DynamicSchedule schedule, Path output) {
        if (fields[1].equals("TEACHER")) { teacherCase = fields[0];teacher = schedule;return; }
        if (!fields[1].equals("PREFIX")) return;
        if (!fields[0].equals(teacherCase) || teacher == null) throw new AssertionError("Missing same-case paid teacher");
        boolean eligible = fields[9].equals("ELIGIBLE");int checked = 0;
        if (eligible) {
            int factory = Integer.parseInt(fields[7]);int[] block = Arrays.stream(fields[8].split(",")).mapToInt(Integer::parseInt).toArray();
            List<DynamicStep> before = firstStage(teacher, factory), after = firstStage(schedule, factory);
            if (block.length < 2 || before.size() < block.length || after.size() < block.length)
                throw new AssertionError("Invalid first-worker-reuse prefix length");
            for (int i = 0; i < block.length; i++) {
                DynamicStep a = before.get(i), b = after.get(i);
                if (a.job() != block[i] || b.job() != block[i] || a.factory() != b.factory()
                        || a.stage() != b.stage() || a.machine() != b.machine() || a.worker() != b.worker()
                        || !Arrays.equals(values(a), values(b))) throw new AssertionError("Copied prefix physical state differs");
                checked++;
            }
        }
        NeutralProbeSupport.append(output.resolve("prefix-state-checks.jsonl"), NeutralProbeSupport.row(
            "case", fields[0], "eligible", eligible, "reason", fields[9], "checkedFirstStageOperations", checked,
            "exactPrefixTimeline", eligible, "laterStagesNotAsserted", true));
    }

    private static List<DynamicStep> firstStage(DynamicSchedule value, int factory) {
        List<DynamicStep> result = new ArrayList<>();
        for (DynamicStep step : value.steps()) if (step.factory() == factory && step.stage() == 0) result.add(step);
        return result;
    }

    private static double[] values(DynamicStep step) {
        return new double[]{step.start(), step.base(), step.duration(), step.setupDuration(), step.completion(),
            step.u(), step.v(), step.energy(), step.labor(), step.exposure()};
    }
}
