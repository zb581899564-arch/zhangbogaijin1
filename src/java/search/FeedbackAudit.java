package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.DoubleSupplier;
import org.uma.jmetal.solution.PermutationSolution;

/** Paid-snapshot timing metadata only. No extra decode, RNG, archive offer or selection. */
final class FeedbackAudit {
    private static final String BIRTH = "feedbackAudit.paidFE";
    private static final String ADMITTED = "feedbackAudit.externalAdmission";
    private final DoubleSupplier elapsed;
    private final double limit;
    private final Set<Long> offered = new HashSet<>(), inserted = new HashSet<>();
    private final DelayStats offerDelay = new DelayStats(), insertDelay = new DelayStats();
    private final DelayStats externalInsertDelay = new DelayStats(), archiveTeacherAge = new DelayStats();
    private final List<Frame> first = new ArrayList<>();
    private Frame active, last;
    private long successful, admissions, externalOffered, externalInserted, refreshFE, generation;
    private long rememberCalls, initialInsertions, invalidLateEvents;

    FeedbackAudit(DoubleSupplier elapsed, double limit) { this.elapsed = elapsed; this.limit = limit; }
    void paid(PermutationSolution<Integer> value, long fe, boolean admission) {
        paid(value, fe, admission, valid());
    }
    void paid(PermutationSolution<Integer> value, long fe, boolean admission, boolean deadlineValid) {
        successful = fe;
        value.setAttribute(BIRTH, fe); value.setAttribute(ADMITTED, admission && deadlineValid);
        if (admission && deadlineValid) admissions++;
    }
    void internalOffer(PermutationSolution<Integer> value, boolean accepted, boolean initialization) {
        if (!valid()) { invalidLateEvents++; return; }
        long birth = birth(value);
        if (birth < 1 || birth > successful) throw new IllegalStateException("Missing paid snapshot provenance");
        boolean external = Boolean.TRUE.equals(value.getAttribute(ADMITTED));
        rememberCalls++;
        if (offered.add(birth)) {
            if (!initialization) offerDelay.add(successful - birth);
            if (external) externalOffered++;
        }
        if (accepted && inserted.add(birth)) {
            if (initialization) initialInsertions++;
            else {
                insertDelay.add(successful - birth);
                if (external) externalInsertDelay.add(successful - birth);
            }
            if (external) externalInserted++;
        }
    }
    void initialized() { refreshFE = successful; }
    void begin() { active = new Frame(++generation, successful, refreshFE); }
    void qgs(Direction direction, int zeroStep, int action, PermutationSolution<Integer> teacher) {
        if (!valid()) { invalidLateEvents++; return; }
        long born = birth(teacher);
        if (born < 1 || born > successful) throw new IllegalStateException("Teacher is not a paid snapshot");
        if (action == 2) archiveTeacherAge.add(successful - born);
        if (zeroStep != 0 && zeroStep != 9 && zeroStep != 24 && zeroStep != 49) return;
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("direction", direction.name()); row.put("step", zeroStep + 1); row.put("action", action);
        row.put("successfulFE", successful); row.put("elapsedSeconds", elapsed.getAsDouble());
        row.put("archiveRefreshFE", refreshFE); row.put("archiveRefreshLagFE", successful - refreshFE);
        row.put("teacherPaidFE", born); row.put("teacherAgeFE", successful - born);
        row.put("teacherWasExternalAdmission", Boolean.TRUE.equals(teacher.getAttribute(ADMITTED)));
        active.steps.add(row);
    }
    void end() {
        refreshFE = successful;
        active.endFE = successful; active.seconds = elapsed.getAsDouble(); active.complete = true;
        active.valid = valid();
        if (first.size() < 2) first.add(active);
        last = active; active = null;
    }
    private boolean valid() { return elapsed.getAsDouble() <= limit; }
    static long birth(PermutationSolution<Integer> value) {
        Object result = value.getAttribute(BIRTH); return result instanceof Long ? (Long) result : -1;
    }
    static boolean admission(PermutationSolution<Integer> value) { return Boolean.TRUE.equals(value.getAttribute(ADMITTED)); }
    Map<String, Object> summary() {
        Map<String, Object> row = new LinkedHashMap<>(); row.put("enabled", true);
        row.put("observationOnly", true); row.put("successfulFE", successful); row.put("generationsStarted", generation);
        row.put("externalArchiveAdmissions", admissions); row.put("distinctSnapshotsOffered", offered.size());
        row.put("distinctSnapshotsInserted", inserted.size()); row.put("initialInsertions", initialInsertions);
        row.put("externalAdmissionSnapshotsOfferedByCutoff", externalOffered);
        row.put("externalAdmissionSnapshotsInsertedByCutoff", externalInserted);
        row.put("rememberCalls", rememberCalls); row.put("lateEventsExcluded", invalidLateEvents);
        row.put("firstOfferDelayFE", offerDelay.record()); row.put("firstInsertionDelayFE", insertDelay.record());
        row.put("externalAdmissionFirstInsertionDelayFE", externalInsertDelay.record());
        row.put("action2TeacherAgeFE", archiveTeacherAge.record());
        row.put("snapshotProvenance", "Last paid evaluation of the retained snapshot, preserved by copy; not first global discovery of a genotype");
        row.put("capturePolicy", "first2+last complete generations plus partial; steps1/10/25/50");
        return row;
    }
    List<Map<String, Object>> export() {
        List<Map<String, Object>> out = new ArrayList<>();
        Map<String, Object> head = summary(); head.put("type", "feedback-summary"); out.add(head);
        for (Frame frame : first) out.add(frame.record());
        if (last != null && !first.contains(last)) out.add(last.record());
        if (active != null) out.add(active.record());
        return out;
    }
    private static final class DelayStats {
        long count, sum, max;
        void add(long value) { if (value < 0) throw new IllegalStateException("Negative feedback age"); count++; sum += value; max = Math.max(max, value); }
        Map<String, Object> record() {
            Map<String, Object> row = new LinkedHashMap<>(); row.put("count", count); row.put("sum", sum); row.put("max", max);
            row.put("mean", count == 0 ? null : (double) sum / count); return row;
        }
    }
    private static final class Frame {
        final long id, startFE, refreshAtStart;
        final List<Map<String, Object>> steps = new ArrayList<>();
        long endFE; double seconds; boolean complete, valid;
        Frame(long id, long startFE, long refreshAtStart) { this.id = id; this.startFE = startFE; this.refreshAtStart = refreshAtStart; }
        Map<String, Object> record() {
            Map<String, Object> row = new LinkedHashMap<>(); row.put("type", "feedback-generation"); row.put("generation", id);
            row.put("startFE", startFE); row.put("refreshAtStartFE", refreshAtStart); row.put("endFE", endFE);
            row.put("elapsedSeconds", seconds); row.put("complete", complete); row.put("deadlineValid", valid);
            row.put("steps", new ArrayList<>(steps)); return row;
        }
    }
}
