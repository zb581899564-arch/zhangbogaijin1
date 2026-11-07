package research.dynamic;

import java.nio.file.*;
import java.util.*;

/** Same frozen light run and observer closure; record exact class identities after the search. */
public final class GomPhaseRoleRun {
    private GomPhaseRoleRun() { }
    public static void main(String[] args) throws Exception {
        GomPipelineRun.main(args);
        PaLightEvidence.writeRows(Paths.get(args[3]).resolve("loaded-phase-identity.jsonl"),Collections.singletonList(
            ClassResolutionProbe.capture("research.dynamic.GomPhaseRoleRun","org.uma.jmetal.util.research.search.GomPhasePreferences",
                "org.uma.jmetal.util.research.search.GomPhasePaidDigest")));
    }
}
