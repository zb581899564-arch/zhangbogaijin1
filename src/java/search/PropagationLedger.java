package org.uma.jmetal.util.research.search;

import java.util.LinkedHashMap;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;

/** Bounded direct shared-genotype provenance; no attribution to changed descendants. */
final class PropagationLedger {
    static final String STAGE = "semantic.stage", SAMPLE = "semantic.sampleParent";
    private static final String ID = "semantic.sharedOrigin", KEY = "semantic.sharedEncoding";
    private static final int CAP = 4096, PERIOD = 256;
    private final Map<Long, Integer> flags = new LinkedHashMap<>();
    private final Map<String, Long> counts = new LinkedHashMap<>();
    private long generated, origins;
    private void count(String key) { counts.put(key, counts.getOrDefault(key, 0L) + 1); }

    void generated(PermutationSolution<Integer> child, PermutationSolution<Integer> parent, boolean shared) {
        generated++;
        child.getAttributes().remove(ID); child.getAttributes().remove(KEY);
        if (shared) {
            long id = ++origins;
            if (flags.size() < CAP) {
                child.setAttribute(ID, id); child.setAttribute(KEY, AuditEncoding.key(child)); flags.put(id, 0);
            } else count("sharedOriginsOverCap");
        }
        if ((generated - 1) % PERIOD == 0)
            child.setAttribute(SAMPLE, AuditEncoding.key(parent));
        else child.getAttributes().remove(SAMPLE);
    }
    void proposal(PermutationSolution<Integer> candidate, String stage) {
        candidate.setAttribute(STAGE, stage);
        if (!"global".equals(stage)) candidate.getAttributes().remove(SAMPLE);
    }
    long exactId(PermutationSolution<Integer> s) {
        Object id = s.getAttribute(ID), key = s.getAttribute(KEY);
        return id instanceof Long && key instanceof String && key.equals(AuditEncoding.key(s)) ? (Long) id : 0;
    }
    private void mark(PermutationSolution<Integer> s, int bit) {
        long id = exactId(s); Integer old = flags.get(id);
        if (old != null) flags.put(id, old | bit);
    }
    void paid(PermutationSolution<Integer> s, boolean changed, boolean deadlineValid) {
        count("paidEvaluationsObserved");
        String stage = String.valueOf(s.getAttribute(STAGE)); count("paid." + stage);
        if (changed && deadlineValid) { count("paidArchiveAdmissions"); count("admissions." + stage); }
        Object sample = s.getAttribute(SAMPLE);
        if (sample instanceof String) {
            count("globalSampledPaid");
            if (!sample.equals(AuditEncoding.key(s))) count("globalSampledDifferent");
        }
        mark(s, 1);
        if (changed && deadlineValid) mark(s, 2);
    }
    void population(PermutationSolution<Integer> s) { mark(s, 4); }
    void teacher(PermutationSolution<Integer> s, boolean consumed) { mark(s, consumed ? 16 : 8); }
    Map<String, Object> summary() {
        Map<String, Object> out = new LinkedHashMap<>(); out.putAll(counts);
        for (String key : new String[] {"paidEvaluationsObserved", "paidArchiveAdmissions", "globalSampledPaid", "globalSampledDifferent", "sharedOriginsOverCap"})
            if (!out.containsKey(key)) out.put(key, 0L);
        out.put("globalSamplePeriod", PERIOD); out.put("originsCap", CAP);
        out.put("sharedOriginsProposed", origins); out.put("sharedOriginsTracked", flags.size());
        String[] labels = {"Paid", "Archive", "Population", "TeacherSelected", "TeacherConsumed"};
        for (int i = 0; i < labels.length; i++) {
            int bit = 1 << i; long n = 0;
            for (int flag : flags.values()) if ((flag & bit) != 0) n++;
            out.put("sharedOrigins" + labels[i], n);
        }
        out.put("propagationScope", "unique tracked exact shared genotypes; direct teacher use; no causal descendant attribution");
        return out;
    }
}
