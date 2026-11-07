package org.uma.jmetal.util.research.search;

import java.util.LinkedHashMap;
import java.util.Map;

/** Parallel totals and mutually interpretable strata, with no acceptance or search feedback. */
final class CandidateRedundancyStats {
    private final Map<String,Long> total = new LinkedHashMap<>();
    private final Map<String,Map<String,Long>> strata = new LinkedHashMap<>();
    void record(String stage, String role, int operator, int jobs, boolean duplicate,
            boolean identity, boolean empty, boolean changed) {
        String[] keys = {"stage:" + stage, "role:" + role, "operator:" + operator,
                        "stageRoleOperator:" + stage + ":" + role + ":" + operator,
                        "factoryJobs:" + jobs};
        update(total, duplicate, identity, empty, changed);
        for (String key : keys) update(strata.computeIfAbsent(key, ignored -> new LinkedHashMap<>()),
                                      duplicate, identity, empty, changed);
    }
    private static void update(Map<String,Long> m, boolean duplicate, boolean identity, boolean empty, boolean changed) {
        add(m, "paid"); if (duplicate) add(m, "historyDuplicate");
        if (identity) add(m, "parentIdentity"); if (empty) add(m, "certifiedEmptyNeighborhood");
        if (duplicate && changed) add(m, "duplicateArchiveChanged");
    }
    private static void add(Map<String,Long> m, String key) { m.put(key, m.getOrDefault(key, 0L) + 1); }
    Map<String,Object> snapshot() {
        Map<String,Object> out = new LinkedHashMap<>();
        out.put("totals", new LinkedHashMap<>(total)); out.put("strata", strata); return out;
    }
}
