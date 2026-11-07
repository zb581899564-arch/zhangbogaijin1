package research.dynamic;

import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.util.research.modelglobal.QpaCompletedDonors;

/** Preserve the full engineering entry, adding loaded helper identity and actual read counters. */
public final class QpaFeedbackRun {
    private QpaFeedbackRun() { }
    public static void main(String[] args) throws Exception {
        QpaPopulationRun.main(args);
        Map<String,Object> result=new LinkedHashMap<>();result.put("reads",QpaCompletedDonors.diagnostics());
        result.put("identity",ClassResolutionProbe.capture("research.dynamic.QpaFeedbackRun",
            "org.uma.jmetal.util.research.modelglobal.QpaCompletedDonors","org.uma.jmetal.util.research.modelglobal.QpaPopulation"));
        Files.write(Paths.get(args[3]).resolve("completed-donor-identity.jsonl"),
            (DynamicJson.encode(result)+"\n").getBytes(java.nio.charset.StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
    }
}
