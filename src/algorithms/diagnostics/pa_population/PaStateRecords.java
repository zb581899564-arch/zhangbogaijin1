package research.dynamic;

import java.util.*;
import org.uma.jmetal.util.research.modelglobal.*;

/** Numeric descriptors permit streaming reconstruction without saving every copied solution graph. */
final class PaStateRecords {
    private PaStateRecords() { }
    static Map<String,Object> state(PaIndividual value, boolean genome) {
        Map<String,Object> result = NeutralProbeSupport.row("id", value.id, "paidFE", value.paidFE,
            "role", value.role.name(), "hash", value.hash, "objectives", value.objectives());
        if (genome) { result.put("resources", value.genome.allocations()); result.put("keys", value.genome.priorities()); }
        return result;
    }
    static List<Map<String,Object>> population(List<PaIndividual> values) {
        List<Map<String,Object>> result = new ArrayList<>(); for (PaIndividual value : values) result.add(state(value, false)); return result;
    }
}
