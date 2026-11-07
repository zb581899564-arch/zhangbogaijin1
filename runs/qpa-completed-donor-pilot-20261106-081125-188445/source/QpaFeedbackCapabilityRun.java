package research.dynamic;

import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.util.research.modelglobal.QpaCompletedDonors;

/** The frozen light capability entry, followed by read-only helper identity and counters. */
public final class QpaFeedbackCapabilityRun {
    private QpaFeedbackCapabilityRun() { }
    public static void main(String[] args) throws Exception {
        QpaCapabilityRun.main(args);
        Map<String,Object> record=new LinkedHashMap<>();record.put("reads",QpaCompletedDonors.diagnostics());
        record.put("identity",ClassResolutionProbe.capture("research.dynamic.QpaFeedbackCapabilityRun",
            "org.uma.jmetal.util.research.modelglobal.QpaCompletedDonors","org.uma.jmetal.util.research.modelglobal.QpaPopulation"));
        Files.write(Paths.get(args[3]).resolve("completed-donor-identity.jsonl"),
            (DynamicJson.encode(record)+"\n").getBytes(java.nio.charset.StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
    }
}
