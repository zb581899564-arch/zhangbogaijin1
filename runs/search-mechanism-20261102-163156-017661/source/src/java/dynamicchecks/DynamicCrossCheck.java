package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;
import org.uma.jmetal.util.research.model.*;

/** Compare Java full/incremental schedules against independently materialized Python results. */
public final class DynamicCrossCheck {
    private DynamicCrossCheck() { }
    public static void main(String[] args) throws Exception {
        Path root = Paths.get(args[0]); int cases = 0, operations = 0;
        for (String line : Files.readAllLines(root.resolve("manifest.tsv"), StandardCharsets.UTF_8)) {
            String[] names = line.split("\t"); Path folder = root.resolve(names[1]);
            int[] dims = Arrays.stream(names[0].replace(".txt", "").split("_")).mapToInt(Integer::parseInt).toArray();
            Instance in = InstanceLoader.loadChapter4(Paths.get(args[1]).resolve(names[0]),
                    SetupTimes.fromFile(folder.resolve("RECONSTRUCTED-setup.txt"), dims[0], dims[1]), 1.0);
            DynamicParameters parameters = DynamicInputs.fatigue(in, folder.resolve("fatigue-input.txt"));
            DynamicSchedule prior = null;
            for (String row : Files.readAllLines(folder.resolve("reference.tsv"), StandardCharsets.UTF_8)) {
                String[] columns = row.split("\t");
                int[] js = integers(columns[0]), fa = integers(columns[1]), ma = integers(columns[2]), wa = integers(columns[3]);
                DynamicSchedule actual = DynamicDecoder.full(in, parameters, js, fa, ma, wa, () -> { });
                DynamicSchedule incremental = DynamicDecoder.incremental(in, parameters, js, fa, ma, wa, prior, null, () -> { });
                DynamicValidator.validate(in, parameters, actual);
                DynamicValidator.validate(in, parameters, incremental);
                if (!Arrays.equals(actual.objectives(), incremental.objectives())) throw new AssertionError("Incremental objectives differ");
                doubles(actual.objectives(), numbers(columns[4]));
                double[] expectedC = numbers(columns[5]), expectedV = numbers(columns[6]);
                int[] machines = integers(columns[7]), workers = integers(columns[8]);
                for (DynamicStep step : actual.steps()) {
                    int id = step.stage() * in.jobs() + step.job();
                    close(step.completion(), expectedC[id]); close(step.v(), expectedV[id]);
                    if (step.machine() != machines[id] || step.worker() != workers[id]) throw new AssertionError("Resource binding differs");
                    operations++;
                }
                for (int i = 0; i < actual.steps().size(); i++) {
                    DynamicStep a = actual.steps().get(i), b = incremental.steps().get(i);
                    if (a.completion() != b.completion() || a.v() != b.v() || a.machine() != b.machine()
                            || a.worker() != b.worker() || a.factory() != b.factory()) throw new AssertionError("Incremental timeline differs");
                }
                prior = actual; cases++;
            }
        }
        Files.write(root.resolve("crosscheck.json"), Arrays.asList("{\"status\":\"passed\",\"cases\":" + cases
                + ",\"operations\":" + operations + ",\"relativeTolerance\":1e-9}"), StandardCharsets.UTF_8);
        System.out.println("CROSSCHECK_PASS cases=" + cases + " operations=" + operations);
    }
    private static double[] numbers(String text) { return Arrays.stream(text.split(",")).mapToDouble(Double::parseDouble).toArray(); }
    private static int[] integers(String text) { return Arrays.stream(text.split(",")).mapToInt(Integer::parseInt).toArray(); }
    private static void doubles(double[] actual, double[] expected) {
        for (int i = 0; i < actual.length; i++) close(actual[i], expected[i]);
    }
    private static void close(double actual, double expected) {
        if (Math.abs(actual - expected) > 1e-9 * Math.max(1, Math.abs(expected))) {
            throw new AssertionError("Cross-language mismatch: " + actual + " vs " + expected);
        }
    }
}
