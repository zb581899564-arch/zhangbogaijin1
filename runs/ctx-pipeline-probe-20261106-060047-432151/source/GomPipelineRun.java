package research.dynamic;

import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.util.research.search.GomPipelineProbe;

/** Frozen complete light entry, plus guaranteed close of the isolated read-only observer. */
public final class GomPipelineRun {
    private GomPipelineRun() { }
    public static void main(String[] args) throws Exception {
        try { GomCapabilityRun.main(args); }
        finally { GomPipelineProbe.finish(); }
        PaLightEvidence.writeRows(Paths.get(args[3]).resolve("loaded-probe-identity.jsonl"),Collections.singletonList(
            ClassResolutionProbe.capture("research.dynamic.GomPipelineRun","org.uma.jmetal.util.research.search.GomPipelineProbe")));
    }
}
