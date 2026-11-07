package research.dynamic;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import org.uma.jmetal.util.research.modelglobal.PaRoleSchedule;

/** Frozen light entries with an independent role/receiver-order observation stream. */
public final class PaRoleCapabilityRun {
    private PaRoleCapabilityRun() { }
    public static void main(String[] args) throws Exception {
        Path out=Paths.get(args[3]);Files.createDirectories(out);
        try(BufferedWriter writer=Files.newBufferedWriter(out.resolve("role-events.jsonl"),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW)) {
            PaRoleSchedule.observe(event->{try{writer.write(DynamicJson.encode(event));writer.newLine();writer.flush();}
                catch(IOException error){throw new UncheckedIOException(error);}});
            if(args[4].equals("QPA_DIRECT"))QpaCapabilityRun.main(args);
            else GomCapabilityRun.main(args);
        } finally {
            Files.write(out.resolve("role-identity.json"),DynamicJson.encode(ClassResolutionProbe.capture(
                "research.dynamic.PaRoleCapabilityRun","org.uma.jmetal.util.research.modelglobal.PaRoleSchedule",
                "org.uma.jmetal.util.research.modelglobal.PaPopulation")).getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
        }
    }
}
