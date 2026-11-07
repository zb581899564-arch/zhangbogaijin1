package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.DoubleSupplier;
import java.util.function.LongSupplier;
import org.uma.jmetal.solution.PermutationSolution;

/** Bounded paid-state observations; does not evaluate schedules or consume random numbers. */
public final class MechanismCapture {
    private final DoubleSupplier elapsed;
    private final LongSupplier successful;
    private final double limit;
    private final boolean retainParents;
    private final List<Generation> first = new ArrayList<>();
    private final List<Case> cases = new ArrayList<>();
    private Generation active, last;
    private long generations, proposals, nanos;
    private final String origin;

    public MechanismCapture(DoubleSupplier elapsed, LongSupplier successful, double limit,
            boolean retainParents, String origin) {
        this.elapsed = elapsed; this.successful = successful; this.limit = limit;
        this.retainParents = retainParents; this.origin = origin;
    }
    public boolean retainParents() { return retainParents; }
    public void begin(List<PermutationSolution<Integer>> parents) {
        long start = System.nanoTime();
        active = new Generation(++generations, parents, successful.getAsLong());
        nanos += System.nanoTime() - start;
    }
    void globalPost(List<Particle> values) { active.global = values(values); }
    void end(List<Particle> local, List<Particle> selected, SwarmSupport support) {
        long start = System.nanoTime();
        active.local = values(local); active.selected = values(selected);
        active.seconds = elapsed.getAsDouble(); active.fe = successful.getAsLong();
        active.valid = active.seconds <= limit; active.complete = true;
        if (support != null) active.quotas = support.selectionQuotas();
        keep(); nanos += System.nanoTime() - start;
    }
    public void classicEnd(List<PermutationSolution<Integer>> offspring,
            List<PermutationSolution<Integer>> selected) {
        long start = System.nanoTime();
        active.global = new ArrayList<>(offspring); active.local = new ArrayList<>(offspring);
        active.selected = new ArrayList<>(selected); active.seconds = elapsed.getAsDouble();
        active.fe = successful.getAsLong(); active.valid = active.seconds <= limit; active.complete = true;
        keep(); nanos += System.nanoTime() - start;
    }
    private void keep() {
        if (first.size() < 2) first.add(active);
        last = active; active = null;
    }
    void batch(Direction direction, int step, List<Particle> current) {
        if (step != 0 && step != 9 && step != 24 && step != 49) return;
        long start = System.nanoTime();
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("direction", direction.name()); row.put("step", step + 1);
        row.put("successfulFE", successful.getAsLong()); row.put("elapsedSeconds", elapsed.getAsDouble());
        List<double[]> points = new ArrayList<>();
        for (Particle p : current) points.add(p.current.getObjectives().clone());
        row.put("objectives", points); active.batches.add(row);
        nanos += System.nanoTime() - start;
    }
    public void proposal(PermutationSolution<Integer> parent, PermutationSolution<Integer> personal,
            PermutationSolution<Integer> global, boolean composed) {
        long index = ++proposals;
        if (retainParents) return;
        int phase = -1;
        long[] anchors = {200, 1500, 3750, 4500};
        for (int p = 0; p < anchors.length; p++) if (index >= anchors[p] && index < anchors[p] + 8) { phase = p; break; }
        if (phase < 0 || elapsed.getAsDouble() > limit) return;
        long start = System.nanoTime();
        cases.add(new Case(origin + "-" + index, new String[] {"MAKESPAN", "CENTER", "ENERGY", "WORKER_COST"}[phase],
                parent, personal, global, active.parents, successful.getAsLong(), composed));
        nanos += System.nanoTime() - start;
    }
    public List<Map<String, Object>> finish() {
        List<Map<String, Object>> out = new ArrayList<>();
        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("type", "mechanism-summary"); summary.put("generationsStarted", generations);
        summary.put("globalProposals", proposals); summary.put("kernelCases", cases.size());
        summary.put("captureSeconds", nanos / 1e9); summary.put("retainParents", retainParents);
        out.add(summary);
        for (Generation g : first) out.add(g.record());
        if (last != null && !first.contains(last)) out.add(last.record());
        if (active != null) out.add(active.record());
        for (Case c : cases) out.add(c.record());
        return out;
    }
    private static List<PermutationSolution<Integer>> values(List<Particle> particles) {
        List<PermutationSolution<Integer>> out = new ArrayList<>();
        for (Particle p : particles) out.add(p.current);
        return out;
    }
    private static List<Map<String, Object>> records(List<PermutationSolution<Integer>> values) {
        if (values == null) return null;
        List<Map<String, Object>> out = new ArrayList<>();
        for (PermutationSolution<Integer> value : values) out.add(encoding(value));
        return out;
    }
    public static Map<String, Object> encoding(PermutationSolution<Integer> s) {
        Map<String, Object> out = AuditEncoding.record(s, 0, "paid", -1, -1, -1, -1);
        out.put("family", s.getAttribute("cooperation.family"));
        Object fixed = s.getAttribute("cooperation.fixedFactoryByJob");
        out.put("fixedFactoryByJob", fixed == null ? null : ((int[]) fixed).clone());
        return out;
    }
    private static final class Generation {
        final long id, startFE;
        final List<PermutationSolution<Integer>> parents;
        List<PermutationSolution<Integer>> global, local, selected;
        final List<Map<String, Object>> batches = new ArrayList<>();
        long fe; double seconds; boolean valid, complete; int[] quotas;
        Generation(long id, List<PermutationSolution<Integer>> parents, long startFE) {
            this.id = id; this.parents = new ArrayList<>(parents); this.startFE = startFE;
        }
        Map<String, Object> record() {
            Map<String, Object> row = new LinkedHashMap<>(); row.put("type", "generation");
            row.put("generation", id); row.put("startSuccessfulFE", startFE);
            row.put("successfulFE", fe); row.put("elapsedSeconds", seconds);
            row.put("deadlineValid", valid); row.put("complete", complete);
            row.put("parents", records(parents)); row.put("global", records(global));
            row.put("local", records(local)); row.put("selected", records(selected));
            row.put("quotas", quotas); row.put("batches", batches); return row;
        }
    }
    private static final class Case {
        final String id, phase;
        final PermutationSolution<Integer> parent, personal, global;
        final List<PermutationSolution<Integer>> reference;
        final long fe; final boolean composed;
        Case(String id, String phase, PermutationSolution<Integer> parent,
                PermutationSolution<Integer> personal, PermutationSolution<Integer> global,
                List<PermutationSolution<Integer>> reference, long fe, boolean composed) {
            this.id = id; this.phase = phase; this.parent = parent; this.personal = personal;
            this.global = global; this.reference = reference; this.fe = fe; this.composed = composed;
        }
        Map<String, Object> record() {
            Map<String, Object> row = new LinkedHashMap<>(); row.put("type", "kernel-case");
            row.put("caseId", id); row.put("phase", phase); row.put("successfulFE", fe);
            row.put("parent", encoding(parent)); row.put("personal", encoding(personal));
            row.put("global", encoding(global)); row.put("composedSource", composed);
            List<double[]> points = new ArrayList<>();
            for (PermutationSolution<Integer> value : reference) points.add(value.getObjectives().clone());
            points.add(parent.getObjectives().clone()); points.add(personal.getObjectives().clone());
            points.add(global.getObjectives().clone()); row.put("reference", points); return row;
        }
    }
}
