package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.DoubleSupplier;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.EvaluationAudit;

/** Bounded diagnostics shared by controls and repairs; never consumes RNG or evaluates a schedule. */
public final class SemanticAudit implements EvaluationAudit<PermutationSolution<Integer>> {
    private final DoubleSupplier elapsed;
    private final double limit;
    private final PropagationLedger ledger = new PropagationLedger();
    private final SelectionCapture pools = new SelectionCapture();
    private final FeedbackAudit feedback;
    private long nanos, exportNanos;
    private List<Map<String, Object>> finished;
    public SemanticAudit(DoubleSupplier elapsed, double limit) { this(elapsed, limit, false); }
    public SemanticAudit(DoubleSupplier elapsed, double limit, boolean feedbackEnabled) {
        this.elapsed = elapsed; this.limit = limit;
        feedback = feedbackEnabled ? new FeedbackAudit(elapsed, limit) : null;
    }
    private void addTime(long start) { nanos += System.nanoTime() - start; }
    public void generated(PermutationSolution<Integer> child, PermutationSolution<Integer> parent, boolean shared) {
        long start = System.nanoTime(); try { ledger.generated(child, parent, shared); } finally { addTime(start); }
    }
    public void proposal(PermutationSolution<Integer> child, String stage) {
        long start = System.nanoTime(); try { ledger.proposal(child, stage); } finally { addTime(start); }
    }
    public void teacherSelected(PermutationSolution<Integer> s) {
        long start = System.nanoTime(); try { if (elapsed.getAsDouble() <= limit) ledger.teacher(s, false); } finally { addTime(start); }
    }
    public void teacherConsumed(PermutationSolution<Integer> s) {
        long start = System.nanoTime(); try { if (elapsed.getAsDouble() <= limit) ledger.teacher(s, true); } finally { addTime(start); }
    }
    @Override public void completed(PermutationSolution<Integer> s, long successful, double seconds, boolean changed) {
        long start = System.nanoTime();
        try { ledger.paid(s, changed, seconds <= limit); if (feedback != null) feedback.paid(s, successful, changed, seconds <= limit); }
        finally { addTime(start); }
    }
    void feedbackOffer(PermutationSolution<Integer> s, boolean accepted, boolean initial) {
        if (feedback == null) return;
        long start = System.nanoTime(); try { feedback.internalOffer(s, accepted, initial); } finally { addTime(start); }
    }
    void feedbackInitialized() { if (feedback != null) feedback.initialized(); }
    void feedbackBegin() { if (feedback != null) feedback.begin(); }
    void feedbackEnd() { if (feedback != null) feedback.end(); }
    void feedbackQgs(Direction d, int step, int action, PermutationSolution<Integer> teacher) {
        if (feedback == null) return;
        long start = System.nanoTime(); try { feedback.qgs(d, step, action, teacher); } finally { addTime(start); }
    }
    public List<Map<String, Object>> feedbackTrace() { return feedback == null ? null : feedback.export(); }
    public boolean feedbackEnabled() { return feedback != null; }
    public boolean withinDeadline() { return elapsed.getAsDouble() <= limit; }
    public double elapsedSeconds() { return elapsed.getAsDouble(); }
    public static long paidSnapshotFE(PermutationSolution<Integer> value) { return FeedbackAudit.birth(value); }
    public static boolean wasExternalAdmission(PermutationSolution<Integer> value) { return FeedbackAudit.admission(value); }
    void pool(List<Particle> candidates, SurvivorSelection.Result result, int globalCount) {
        long start = System.nanoTime();
        try {
            List<PermutationSolution<Integer>> values = new ArrayList<>(); long[][] ids = new long[candidates.size()][2];
            for (int i = 0; i < candidates.size(); i++) {
                Particle p = candidates.get(i); values.add(p.current); ids[i][0] = p.lineageId(); ids[i][1] = p.branchId();
            }
            double seconds = elapsed.getAsDouble();
            if (seconds <= limit) for (Particle p : result.survivors()) ledger.population(p.current);
            pools.observe(values, result.indices(), result.fitness(), result.categories(), result.quotas(), ids,
                    globalCount, "G", "L", "PDDR", seconds, seconds <= limit);
        } finally { addTime(start); }
    }
    public void classicPool(List<PermutationSolution<Integer>> candidates, List<PermutationSolution<Integer>> selected, int parents) {
        long start = System.nanoTime();
        try {
            boolean[] used = new boolean[candidates.size()]; int[] indices = new int[selected.size()];
            for (int j = 0; j < selected.size(); j++) {
                int found = -1;
                for (int i = 0; i < candidates.size(); i++) if (!used[i] && candidates.get(i) == selected.get(j)) { found = i; break; }
                if (found < 0) throw new IllegalStateException("Selected classic candidate absent from paid pool");
                indices[j] = found; used[found] = true;
            }
            double seconds = elapsed.getAsDouble();
            pools.observe(candidates, indices, null, null, null, null, parents, "P", "O", "rank-crowding", seconds, seconds <= limit);
        } finally { addTime(start); }
    }
    public Map<String, Object> diagnostics() {
        Map<String, Object> out = new LinkedHashMap<>(); out.putAll(ledger.summary()); out.putAll(pools.summary());
        out.put("auditSeconds", nanos / 1e9); out.put("poolExportSeconds", exportNanos / 1e9);
        if (feedback != null) out.put("feedbackTiming", feedback.summary());
        return out;
    }
    public List<Map<String, Object>> finish() {
        if (finished == null) {
            long start = System.nanoTime(); finished = pools.export(ledger); exportNanos = System.nanoTime() - start;
            Map<String, Object> summary = new LinkedHashMap<>(); summary.put("type", "audit-summary"); summary.putAll(diagnostics());
            finished.add(0, summary);
        }
        return new ArrayList<>(finished);
    }
}
