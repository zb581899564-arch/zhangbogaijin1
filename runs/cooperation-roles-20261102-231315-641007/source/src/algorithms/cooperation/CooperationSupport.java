package org.uma.jmetal.util.research.cooperation;

import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.search.*;

/** Fixed-context sharing pilot; all assemblies are charged as ordinary complete evaluations. */
public final class CooperationSupport implements SwarmSupport {
    private final Instance in;
    private final DynamicParameters parameters;
    private final boolean sharing;
    private final boolean centerLast;
    private final boolean uniform;
    private final CooperationEvidence evidence;
    private final CompositionTiming timing;
    private final FamilyContexts contexts;
    private final FactoryPool[][] pools;
    private final long[] opportunities = new long[4], cycles = new long[4];
    private final Map<PermutationSolution<Integer>, double[]> predictions = new IdentityHashMap<>();
    private final Map<String, Long> counts = new LinkedHashMap<>();
    private double energyScale = 1, wageScale = 1;
    private long nanos;
    public CooperationSupport(Instance in, DynamicParameters parameters, boolean sharing) {
        this(in, parameters, sharing, false, null);
    }
    public CooperationSupport(Instance in, DynamicParameters parameters, boolean sharing,
            boolean centerLast, SemanticAudit audit) {
        this(in, parameters, sharing, centerLast, false, audit, false);
    }
    public CooperationSupport(Instance in, DynamicParameters parameters, boolean sharing,
            boolean centerLast, boolean uniform, SemanticAudit audit, boolean captureEvidence) {
        this.in = in; this.parameters = parameters; this.sharing = sharing; contexts = new FamilyContexts(in);
        this.centerLast = centerLast;
        this.uniform = uniform;
        timing = audit != null && audit.feedbackEnabled() ? new CompositionTiming(audit) : null;
        if (captureEvidence && timing == null) throw new IllegalArgumentException("Pool evidence requires paid feedback audit");
        evidence = captureEvidence ? new CooperationEvidence(audit) : null;
        pools = new FactoryPool[4][in.factories()];
        for (int g = 0; g < 4; g++) for (int f = 0; f < in.factories(); f++) pools[g][f] = new FactoryPool();
    }
    @Override public void beginGeneration() { if (timing != null) timing.begin(); }
    @Override public Direction preference(Direction group) { return uniform ? Direction.CENTER : group; }
    @Override public Direction[] globalUpdateOrder() {
        return centerLast ? new Direction[] {Direction.MAKESPAN, Direction.ENERGY, Direction.WORKER_COST, Direction.CENTER}
                : Direction.values();
    }
    private void count(String key) { counts.put(key, counts.getOrDefault(key, 0L) + 1); }
    @Override public void prepareInitialization(PermutationSolution<Integer> s, int index) { contexts.initialize(s, index); }
    @Override public void beforeEvaluation(PermutationSolution<Integer> s, String stage, Direction d) {
        long start = System.nanoTime(); contexts.restore(s); nanos += System.nanoTime() - start;
    }
    @Override public void evaluated(PermutationSolution<Integer> s, String stage, Direction d) {
        long start = System.nanoTime(); contexts.validate(s);
        double[] expected = predictions.remove(s);
        if (expected != null) {
            for (int k = 0; k < 3; k++) if (Math.abs(expected[k] - s.getObjective(k)) > 1e-9 * Math.max(1, Math.abs(expected[k])))
                throw new IllegalStateException("Composed factory objectives disagree with actual decode");
            count("assembliesValidated");
        }
        if (timing != null) timing.observed(s);
        int family = FamilyContexts.family(s);
        if (sharing && family >= 0) {
            DynamicSchedule schedule = (DynamicSchedule) s.getAttribute(DynamicEvaluation.KEY);
            schedule.validateContext(in, parameters); count("paidObservations"); count("observed." + stage);
            for (int f = 0; f < in.factories(); f++) {
                FactoryRecord record = timing == null ? new FactoryRecord(schedule, f)
                        : new FactoryRecord(schedule, f, SemanticAudit.paidSnapshotFE(s), timing.generation(),
                                stage, d == null ? "INITIALIZATION" : d.name());
                pools[family][f].offer(record);
            }
        }
        nanos += System.nanoTime() - start;
    }
    @Override public void initialized(List<PermutationSolution<Integer>> pop) {
        energyScale = 0; wageScale = 0;
        for (PermutationSolution<Integer> s : pop) { energyScale += s.getObjective(1) / pop.size(); wageScale += s.getObjective(2) / pop.size(); }
        if (energyScale == 0) energyScale = 1; if (wageScale == 0) wageScale = 1;
    }
    @Override public Map<Direction, List<Integer>> grouping(List<PermutationSolution<Integer>> pop, int boundary) {
        long start = System.nanoTime(); Map<Direction, List<Integer>> result = contexts.grouping(pop, boundary, uniform);
        count("groupings"); nanos += System.nanoTime() - start; return result;
    }
    @Override public int[] selectionQuotas() { return new int[] {80, 5, 5, 5, 5}; }
    @Override public int selectionCategory(PermutationSolution<Integer> solution) { return FamilyContexts.family(solution) + 1; }
    @SuppressWarnings("unchecked")
    @Override public PermutationSolution<Integer> compose(PermutationSolution<Integer> parent, Direction direction) {
        int family = FamilyContexts.family(parent);
        if (!sharing || family < 0 || direction != Direction.CENTER) return null;
        if (timing != null) timing.opportunity();
        if (++opportunities[family] % 4 != 0) return null;
        long start = System.nanoTime(); count("assemblyRequests");
        int cycle = (int) (cycles[family]++ % 9);
        double cap = parent.getObjective(0) * new double[] {.9, 1, 1.1}[cycle / 3];
        double eta = new double[] {0, 1, 4}[cycle % 3];
        FactoryRecord[] chosen = new FactoryRecord[in.factories()];
        for (int f = 0; f < in.factories(); f++) {
            chosen[f] = pools[family][f].choose(cap, eta, energyScale, wageScale);
            if (chosen[f] == null) {
                count("infeasibleCap"); observeRequest(parent, family, cycle, cap, eta, "INFEASIBLE");
                nanos += System.nanoTime() - start; return null;
            }
        }
        count("feasibleAssemblies");
        PermutationSolution<Integer> child = (PermutationSolution<Integer>) parent.copy();
        List<Integer> machines = (List<Integer>) child.getAttribute("machine");
        double[] predicted = new double[3]; int at = 0;
        for (int f = 0; f < in.factories(); f++) {
            FactoryRecord r = chosen[f]; predicted[0] = Math.max(predicted[0], r.objectives[0]);
            predicted[1] += r.objectives[1]; predicted[2] += r.objectives[2];
            for (int i = 0; i < r.jobs.length; i++) {
                child.setVariableValue(at, r.jobs[i]); child.setVariableValueid(at, f);
                machines.set(at, r.machines[i]); child.setVariableValueworker(at++, r.workers[i]);
            }
        }
        child.setAttribute("worker", child.getVariablesworker()); contexts.validate(child);
        // Interleavings across independent factories are equivalent; compare local encodings.
        DynamicSchedule old = (DynamicSchedule) parent.getAttribute(DynamicEvaluation.KEY);
        boolean same = true;
        for (int f = 0; f < in.factories(); f++) same &= chosen[f].same(new FactoryRecord(old, f));
        if (same) {
            count("duplicateParent"); observeRequest(parent, family, cycle, cap, eta, "DUPLICATE_PARENT");
            nanos += System.nanoTime() - start; return null;
        }
        predictions.put(child, predicted);
        if (timing != null) timing.proposed(child, chosen, family);
        observeRequest(parent, family, cycle, cap, eta, "PROPOSED");
        count("assembliesProposed"); nanos += System.nanoTime() - start; return child;
    }
    private void observeRequest(PermutationSolution<Integer> parent, int family, int cycle, double cap, double eta, String outcome) {
        if (evidence == null) return;
        evidence.request(pools[family], parent, (DynamicSchedule) parent.getAttribute(DynamicEvaluation.KEY),
                family, cycle, cap, eta, energyScale, wageScale, timing.generation(), timing.currentFE(), outcome);
    }
    public Map<String, Object> diagnostics() {
        Map<String, Object> out = new LinkedHashMap<>(); out.putAll(counts); out.put("sharing", sharing);
        long accepted = 0, rejected = 0, truncated = 0, records = 0;
        for (FactoryPool[] family : pools) for (FactoryPool pool : family) {
            accepted += pool.accepted; rejected += pool.rejected; truncated += pool.truncated; records += pool.size();
        }
        out.put("poolAccepted", accepted); out.put("poolRejected", rejected); out.put("poolTruncated", truncated);
        out.put("poolRecords", records); out.put("cooperationSeconds", nanos / 1e9);
        out.put("contexts", "4 fixed FA families x5; 80 free; no refresh");
        out.put("globalOrder", centerLast ? "MAKESPAN,ENERGY,WORKER_COST,CENTER" : "MAKESPAN,CENTER,ENERGY,WORKER_COST");
        long eligible = 0; for (long value : opportunities) eligible += value;
        out.put("eligibleCenterOpportunities", eligible);
        out.put("targetSpecialization", !uniform);
        Map<String, Object> preferences = new LinkedHashMap<>();
        for (Direction d : Direction.values()) preferences.put(d.name(), preference(d).name());
        out.put("rolePreferenceMap", preferences);
        if (timing != null) out.put("compositionTiming", timing.summary());
        if (evidence != null) out.put("poolEvidence", evidence.summary());
        return out;
    }
    public List<Map<String, Object>> compositionTrace() { return timing == null ? null : timing.export(); }
    public List<Map<String, Object>> poolEvidenceTrace() { return evidence == null ? null : evidence.export(); }
}
