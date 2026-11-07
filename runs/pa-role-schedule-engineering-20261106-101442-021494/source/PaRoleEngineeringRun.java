package research.dynamic;

import java.io.*;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.util.research.modelglobal.PaRoleSchedule;

/** Frozen full-timeline PA entry with a separate, ordered role/receiver mapping trace. */
public final class PaRoleEngineeringRun {
    private PaRoleEngineeringRun() { }
    public static void main(String[] args) throws Exception {
        Path out=Paths.get(args[4]);Files.createDirectories(out);
        try(BufferedWriter writer=Files.newBufferedWriter(out.resolve("role-events.jsonl"),java.nio.charset.StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW)) {
            PaRoleSchedule.observe(event->{try{writer.write(DynamicJson.encode(event));writer.newLine();writer.flush();}catch(IOException e){throw new UncheckedIOException(e);}});
            PaPopulationRun.main(args);
        } finally {
            Files.write(out.resolve("role-identity.json"),DynamicJson.encode(ClassResolutionProbe.capture("research.dynamic.PaRoleEngineeringRun",
                "org.uma.jmetal.util.research.modelglobal.PaRoleSchedule","org.uma.jmetal.util.research.modelglobal.PaPopulation",
                "org.uma.jmetal.util.research.search.ParetoTools")).getBytes(java.nio.charset.StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
        }
    }
}
