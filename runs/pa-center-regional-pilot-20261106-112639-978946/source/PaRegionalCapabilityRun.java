package research.dynamic;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.util.research.modelglobal.PaRegionalPolicy;

/** Same frozen kernel bytes; record the fixed target assignment, not detailed paid steps. */
public final class PaRegionalCapabilityRun {
    private PaRegionalCapabilityRun(){ }
    public static void main(String[] args) throws Exception {
        Path out=Paths.get(args[3]);Files.createDirectories(out);
        try(BufferedWriter writer=Files.newBufferedWriter(out.resolve("regional-targets.jsonl"),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW)) {
            PaRegionalPolicy.observe(event->{if(!event.get("kind").equals("targets"))return;
                try{writer.write(DynamicJson.encode(event));writer.newLine();writer.flush();}catch(IOException error){throw new UncheckedIOException(error);}});
            GomCapabilityRun.main(args);
        } finally {
            Map<String,Object> row=new LinkedHashMap<>();row.put("policy",PaRegionalPolicy.diagnostics());
            row.put("identity",ClassResolutionProbe.capture("research.dynamic.PaRegionalCapabilityRun",
                "org.uma.jmetal.util.research.modelglobal.PaRegionalPolicy","org.uma.jmetal.util.research.modelglobal.PaPopulation",
                "org.uma.jmetal.util.research.modelglobal.CenterTargets","org.uma.jmetal.util.research.modelglobal.CenterAssignment"));
            Files.write(out.resolve("regional-summary.json"),DynamicJson.encode(row).getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
        }
    }
}
