package research.normalized;

import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.SchedulingMetadata;
import org.uma.jmetal.util.research.model.Decoder;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.model.Operation;
import org.uma.jmetal.util.research.model.Schedule;
import org.uma.jmetal.util.research.model.Validator;
import org.uma.jmetal.util.research.runtime.RunContext;

/** Saves every feasible archive encoding and its complete independently checked timeline. */
public final class RunOutput {
    private RunOutput() { }

    @SuppressWarnings("unchecked")
    public static void write(Path output, Instance instance, RunContext<PermutationSolution<Integer>> context,
            List<PermutationSolution<Integer>> source, double seconds, boolean diagnostic, String config) throws Exception {
        List<PermutationSolution<Integer>> result = new ArrayList<>(source);
        result.sort(new Comparator<PermutationSolution<Integer>>() {
            public int compare(PermutationSolution<Integer> a, PermutationSolution<Integer> b) {
                for (int i = 0; i < 3; i++) {
                    int order = Double.compare(a.getObjective(i), b.getObjective(i));
                    if (order != 0) return order;
                }
                return 0;
            }
        });
        try (BufferedWriter front = create(output.resolve("front.tsv"));
             BufferedWriter solutions = create(output.resolve("solutions.jsonl"));
             BufferedWriter timeline = create(output.resolve("schedule.tsv"))) {
            front.write("Cmax\tTEC\tTWC\n");
            timeline.write("solution\tjob\tfactory\tstage\tmachine\tworker\tstart\tsetup_end\tend\n");
            int index = 0;
            for (PermutationSolution<Integer> solution : result) {
                Schedule archived = (Schedule) solution.getAttribute(SchedulingMetadata.SCHEDULE_KEY);
                Validator.validate(instance, archived);
                Schedule repeated = Decoder.decode(instance, SchedulingEncoding.integers(solution.getVariables()),
                        SchedulingEncoding.integers(solution.getVariablesid()),
                        SchedulingEncoding.integers((List<Integer>) solution.getAttribute("machine")),
                        SchedulingEncoding.integers(solution.getVariablesworker()));
                Validator.validate(instance, repeated);
                if (!Arrays.equals(solution.getObjectives(), repeated.objectives())) {
                    throw new AssertionError("Archive genotype and physical objectives disagree");
                }
                double[] objectives = solution.getObjectives();
                front.write(objectives[0] + "\t" + objectives[1] + "\t" + objectives[2] + "\n");
                solutions.write("{\"objectives\":" + Arrays.toString(objectives)
                        + ",\"JS\":" + solution.getVariables() + ",\"FA\":" + solution.getVariablesid()
                        + ",\"MA\":" + solution.getAttribute("machine") + ",\"WA\":" + solution.getVariablesworker() + "}\n");
                for (Operation op : repeated.operations()) {
                    timeline.write(index + "\t" + op.job() + "\t" + op.factory() + "\t" + op.stage() + "\t"
                            + op.machine() + "\t" + op.worker() + "\t" + op.start() + "\t"
                            + op.processingStart() + "\t" + op.end() + "\n");
                }
                index++;
            }
        }
        try (BufferedWriter summary = create(output.resolve("summary.json"))) {
            summary.write("{\n\"baseline\":\"A0-sourced-reconstruction-v2\",\n\"modelProvenance\":" + quote(instance.provenance())
                    + ",\n\"seed\":" + context.seed() + ",\n\"searchFeLimit\":" + context.budget().limit()
                    + ",\n\"searchDecoderAttempts\":" + context.budget().attempted()
                    + ",\n\"successfulSearchEvaluations\":" + context.budget().successful()
                    + ",\n\"failedSearchEvaluations\":" + context.budget().failed()
                    + ",\n\"offlineValidationDecodes\":" + result.size()
                    + ",\n\"archiveSize\":" + result.size() + ",\n\"searchSecondsIncludingArchive\":" + seconds
                    + ",\n\"diagnosticOnly\":" + diagnostic + ",\n\"searchConfig\":" + quote(config) + "\n}\n");
        }
    }

    private static BufferedWriter create(Path path) throws Exception {
        return Files.newBufferedWriter(path, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
    }
    public static void diagnostics(Path output, Map<String, Long> counts) throws Exception {
        try (BufferedWriter writer = create(output.resolve("diagnostics.json"))) {
            writer.write("{\n");
            int index = 0;
            for (Map.Entry<String, Long> entry : counts.entrySet()) {
                if (index++ > 0) writer.write(",\n");
                writer.write(quote(entry.getKey()) + ":" + entry.getValue());
            }
            writer.write("\n}\n");
        }
    }
    private static String quote(String value) {
        return "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"").replace("\r", "\\r").replace("\n", "\\n") + "\"";
    }
}
