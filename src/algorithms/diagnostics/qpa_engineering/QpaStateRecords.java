package research.dynamic;

import java.util.*;
import org.uma.jmetal.util.research.modelglobal.*;

/** Read-only numeric evidence; full genomes are needed only for the100 initial states. */
final class QpaStateRecords {
    private QpaStateRecords() { }
    static Map<String,Object> state(QpaIndividual value, boolean genome) {
        if (value == null) return null;
        Map<String,Object> record = NeutralProbeSupport.row("id", value.id, "paidFE", value.paidFE,
            "role", value.role.name(), "hash", value.hash, "objectives", value.objectives());
        if (genome) { record.put("resources", value.genome.resources()); record.put("positions", value.genome.positions()); }
        return record;
    }
    static List<Map<String,Object>> population(List<QpaIndividual> values) {
        List<Map<String,Object>> records = new ArrayList<>();
        for (QpaIndividual value : values) records.add(state(value, false)); return records;
    }
    static Map<String,Object> raw(QpaIndividual value) {
        FourVectors vectors = value.genome.toVectors();
        return NeutralProbeSupport.row("JS", vectors.jobs(), "FA", vectors.factories(), "MA", vectors.machines(),
            "WA", vectors.workers(), "objectives", value.objectives(), "fe", value.paidFE);
    }
    static void flags(Map<String,Object> record, PaInternalArchive.Flags flags) {
        record.putAll(NeutralProbeSupport.row("archiveDominated", flags.dominated, "archiveEqual", flags.equal,
            "archiveFresh", flags.fresh, "archiveSizeBefore", flags.before, "archiveSizeAfter", flags.after));
    }
}
