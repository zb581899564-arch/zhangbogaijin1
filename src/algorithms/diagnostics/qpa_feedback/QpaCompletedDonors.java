package org.uma.jmetal.util.research.modelglobal;

import java.util.*;
import org.uma.jmetal.util.research.search.Direction;

/** Isolated ordinary lifecycle ablation; only completed paid programs can replace a donor snapshot. */
public final class QpaCompletedDonors {
    private enum Mode { SYNC, OWN, ALL }
    private static final Mode MODE=Mode.valueOf(System.getProperty("research.qpa.completedDonors","SYNC"));
    private static long reads,completedAvailable,freshReads,crossRoleFreshReads;
    private QpaCompletedDonors() { }

    static QpaIndividual choose(List<QpaIndividual> parents,List<QpaIndividual> completed,int slot,Direction receiver) {
        reads++; QpaIndividual frozen=parents.get(slot);
        if (slot>=completed.size()) return frozen;
        completedAvailable++; QpaIndividual latest=completed.get(slot);
        if (latest.role!=frozen.role) throw new AssertionError("Completed donor role changed");
        if (MODE==Mode.SYNC || MODE==Mode.OWN && latest.role!=receiver) return frozen;
        if (latest.id!=frozen.id) {freshReads++; if (latest.role!=receiver) crossRoleFreshReads++;}
        return latest;
    }

    public static Map<String,Object> diagnostics() {
        Map<String,Object> result=new LinkedHashMap<>();result.put("mode",MODE.name());result.put("maskReads",reads);
        result.put("completedDonorAvailable",completedAvailable);result.put("freshMaskReads",freshReads);
        result.put("crossRoleFreshMaskReads",crossRoleFreshReads);return result;
    }
}
