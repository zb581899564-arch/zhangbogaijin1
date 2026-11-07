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
    private final FamilyContexts contexts;
    private final FactoryPool[][] pools;
    private final long[] opportunities = new long[4], cycles = new long[4];
    private final Map<PermutationSolution<Integer>, double[]> predictions = new IdentityHashMap<>();
    private final Map<String, Long> counts = new LinkedHashMap<>();
    private double energyScale = 1, wageScale = 1;
    private long nanos;
    public CooperationSupport(Instance in, DynamicParameters parameters, boolean sharing) {
        this.in = in; this.parameters = parameters; this.sharing = sharing; contexts = new FamilyContexts(in);
        pools = new FactoryPool[4][in.factories()];
        for (int g = 0; g < 4; g++) for (int f = 0; f < in.factories(); f++) pools[g][f] = new FactoryPool();
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
        int family = FamilyContexts.family(s);
        if (sharing && family >= 0) {
            DynamicSchedule schedule = (DynamicSchedule) s.getAttribute(DynamicEvaluation.KEY);
            schedule.validateContext(in, parameters); count("paidObservations"); count("observed." + stage);
            for (int f = 0; f < in.factories(); f++) pools[family][f].offer(new FactoryRecord(schedule, f));
        }
        nanos += System.nanoTime() - start;
    }
    @Override public void initialized(List<PermutationSolution<Integer>> pop) {
        energyScale = 0; wageScale = 0;
        for (PermutationSolution<Integer> s : pop) { energyScale += s.getObjective(1) / pop.size(); wageScale += s.getObjective(2) / pop.size(); }
        if (energyScale == 0) energyScale = 1; if (wageScale == 0) wageScale = 1;
    }
    @Override public Map<Direction, List<Integer>> grouping(List<PermutationSolution<Integer>> pop, int boundary) {
        long start = System.nanoTime(); Map<Direction, List<Integer>> result = contexts.grouping(pop, boundary);
        count("groupings"); nanos += System.nanoTime() - start; return result;
    }
    @SuppressWarnings("unchecked")
    @Override public PermutationSolution<Integer> compose(PermutationSolution<Integer> parent, Direction direction) {
        int family = FamilyContexts.family(parent);
        if (!sharing || family < 0 || direction != Direction.CENTER || ++opportunities[family] % 4 != 0) return null;
        long start = System.nanoTime(); count("assemblyRequests");
        int cycle = (int) (cycles[family]++ % 9);
        double cap = parent.getObjective(0) * new double[] {.9, 1, 1.1}[cycle / 3];
        double eta = new double[] {0, 1, 4}[cycle % 3];
        FactoryRecord[] chosen = new FactoryRecord[in.factories()];
        for (int f = 0; f < in.factories(); f++) {
            chosen[f] = pools[family][f].choose(cap, eta, energyScale, wageScale);
            if (chosen[f] == null) { count("infeasibleCap"); nanos += System.nanoTime() - start; return null; }
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
        if (same) { count("duplicateParent"); nanos += System.nanoTime() - start; return null; }
        predictions.put(child, predicted); count("assembliesProposed"); nanos += System.nanoTime() - start; return child;
    }
    public Map<String, Object> diagnostics() {
        Map<String, Object> out = new LinkedHashMap<>(); out.putAll(counts); out.put("sharing", sharing);
        long accepted = 0, rejected = 0, truncated = 0, records = 0;
        for (FactoryPool[] family : pools) for (FactoryPool pool : family) {
            accepted += pool.accepted; rejected += pool.rejected; truncated += pool.truncated; records += pool.size();
        }
        out.put("poolAccepted", accepted); out.put("poolRejected", rejected); out.put("poolTruncated", truncated);
        out.put("poolRecords", records); out.put("cooperationSeconds", nanos / 1e9);
        out.put("contexts", "4 fixed FA families x5; 80 free; no refresh"); return out;
    }
}
