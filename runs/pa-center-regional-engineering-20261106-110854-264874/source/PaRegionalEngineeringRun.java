package research.dynamic;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.util.research.modelglobal.PaRegionalPolicy;

/** Frozen paid full-timeline entry with a separate policy-only trace. */
public final class PaRegionalEngineeringRun {
    private PaRegionalEngineeringRun(){ }
    public static void main(String[] args) throws Exception {
        Path out=Paths.get(args[4]);Files.createDirectories(out);
        try(BufferedWriter writer=Files.newBufferedWriter(out.resolve("regional-events.jsonl"),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW)) {
            PaRegionalPolicy.observe(event->{try{writer.write(DynamicJson.encode(event));writer.newLine();writer.flush();}
                catch(IOException error){throw new UncheckedIOException(error);}});
            PaPopulationRun.main(args);
        } finally {
            Map<String,Object> row=new LinkedHashMap<>();row.put("policy",PaRegionalPolicy.diagnostics());
            row.put("identity",ClassResolutionProbe.capture("research.dynamic.PaRegionalEngineeringRun",
                "org.uma.jmetal.util.research.modelglobal.PaRegionalPolicy","org.uma.jmetal.util.research.modelglobal.CenterTargets",
                "org.uma.jmetal.util.research.modelglobal.CenterAssignment"));
            Files.write(out.resolve("regional-policy.json"),DynamicJson.encode(row).getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
        }
    }
}
