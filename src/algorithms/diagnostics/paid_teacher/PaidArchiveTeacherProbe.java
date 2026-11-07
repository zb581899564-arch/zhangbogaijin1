package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.util.research.model.DynamicParameters;

/** Fixed-context single-kernel guide-source diagnostic; all reconstruction and offspring calls charged. */
public final class PaidArchiveTeacherProbe {
    private PaidArchiveTeacherProbe() { }

    public static void main(String[] args) throws Exception {
        Path input = Paths.get(args[0]), out = Paths.get(args[5]); Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir", input.getParent().toString());
        System.setProperty("dhfsp.setupFile", args[1]); System.setProperty("dhfsp.standbyPower", "1.0");
        System.setProperty("research.snapshot.mode", "ANCHOR");
        String[] dimensions = input.getFileName().toString().replace(".txt", "").split("_");
        EDHHFSPW raw = new EDHHFSPW(Integer.parseInt(dimensions[0]), Integer.parseInt(dimensions[1]),
                Integer.parseInt(dimensions[2]), Integer.parseInt(dimensions[3]));
        DynamicParameters params = DynamicInputs.fatigue(raw.getSchedulingInstance(), Paths.get(args[2]));
        Map<String,List<String[]>> inputs = load(Paths.get(args[3])), recipients = load(Paths.get(args[4]));
        if (inputs.size() != 6 || recipients.size() != 6) throw new AssertionError("Missing original windows");
        int index = 0; long paid = 0, qa = 0;
        for (String id : inputs.keySet()) {
            PaidTeacherContext context = new PaidTeacherContext(raw, params, out, Long.parseLong(args[6]),
                    index++, inputs.get(id).size());
            context.run(id, inputs.get(id), recipients.get(id));
            paid += context.context.budget().successful(); qa += context.fullQA;
        }
        NeutralProbeSupport.append(out.resolve("receipt.jsonl"), NeutralProbeSupport.row(
                "status", "COMPLETE", "successfulFE", paid, "attemptedFE", paid, "failedFE", 0,
                "fullDecoderQA", qa, "contexts", inputs.size(), "offspringFE", 6 * 8 * 16 * 5));
    }

    private static Map<String,List<String[]>> load(Path path) throws Exception {
        Map<String,List<String[]>> values = new LinkedHashMap<>();
        for (String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            String[] fields = line.split("\t", -1);
            values.computeIfAbsent(fields[0], ignored -> new ArrayList<>()).add(fields);
        }
        return values;
    }
}
