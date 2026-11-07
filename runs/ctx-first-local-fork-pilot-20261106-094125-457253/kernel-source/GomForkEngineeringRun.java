package research.dynamic;

import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.util.research.search.GomForkInputs;

/** Unchanged heavy timeline/trace entry plus ancestry-fork evidence, retained even on failure. */
public final class GomForkEngineeringRun {
    private GomForkEngineeringRun() { }
    public static void main(String[] args) throws Exception {
        try {GomEngineeringRun.main(args);}
        finally {
            Map<String,Object> row=new LinkedHashMap<>();row.put("fork",GomForkInputs.diagnostics());
            row.put("identity",ClassResolutionProbe.capture("research.dynamic.GomForkEngineeringRun",
                "org.uma.jmetal.util.research.search.GomForkInputs","org.uma.jmetal.util.research.search.CanonicalHmopso",
                "org.uma.jmetal.util.research.search.Particle"));
            Files.write(Paths.get(args[3]).resolve("fork-input.json"),DynamicJson.encode(row).getBytes(java.nio.charset.StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
        }
    }
}
