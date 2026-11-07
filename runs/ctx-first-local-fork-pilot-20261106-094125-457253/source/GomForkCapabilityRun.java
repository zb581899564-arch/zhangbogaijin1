package research.dynamic;

import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.util.research.search.GomForkInputs;

/** Common frozen light entry, followed by read-only ancestry records. */
public final class GomForkCapabilityRun {
    private GomForkCapabilityRun() { }
    public static void main(String[] args) throws Exception {
        try {GomCapabilityRun.main(args);}
        finally {
            Map<String,Object> row=new LinkedHashMap<>();row.put("fork",GomForkInputs.diagnostics());
            row.put("identity",ClassResolutionProbe.capture("research.dynamic.GomForkCapabilityRun",
                "org.uma.jmetal.util.research.search.GomForkInputs","org.uma.jmetal.util.research.search.CanonicalHmopso"));
            Files.write(Paths.get(args[3]).resolve("fork-input.json"),DynamicJson.encode(row).getBytes(java.nio.charset.StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
        }
    }
}
