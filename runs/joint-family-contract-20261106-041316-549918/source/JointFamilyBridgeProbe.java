package org.uma.jmetal.util.research.cooperation;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.modelglobal.*;
import org.uma.jmetal.util.research.search.Direction;

/** Calls the actual frozen family guard on unscored structural fixtures; never evaluates a child. */
public final class JointFamilyBridgeProbe {
    private final Instance instance;
    private final FirstStageCatalog catalog;
    private final FamilyContexts contexts;
    private final List<PermutationSolution<Integer>> points;
    private final List<TypedScheduleGenome> genomes = new ArrayList<>();
    private final Map<String,long[]> cells = new LinkedHashMap<>();
    private final List<Map<String,Object>> witnesses = new ArrayList<>();
    private long compatible, donorPairs;

    public JointFamilyBridgeProbe(Instance value, List<PermutationSolution<Integer>> sources) {
        instance = value; points = sources; catalog = new FirstStageCatalog(instance); contexts = new FamilyContexts(instance);
        if (points.size() != 100) throw new IllegalArgumentException("100 known initial states required");
        for (int i = 0; i < points.size(); i++) {
            String before = raw(points.get(i)); contexts.initialize(points.get(i), i); contexts.validate(points.get(i));
            if (!before.equals(raw(points.get(i)))) throw new AssertionError("Imported common initialization differs");
            genomes.add(TypedScheduleGenome.fromVectors(catalog, vectors(points.get(i))));
        }
    }
    public Map<String,Object> run() {
        List<String> before = new ArrayList<>(); for (PermutationSolution<Integer> value : points) before.add(raw(value));
        for (int parent = 0; parent < 100; parent++) {
            @SuppressWarnings("unchecked") PermutationSolution<Integer> scratch = (PermutationSolution<Integer>)points.get(parent).copy();
            for (int donor = 0; donor < 100; donor++) {
                if (parent < 20) {
                    donorPairs++; if (sameFA(genomes.get(parent), genomes.get(donor))) compatible++;
                    for (int job = 0; job < catalog.jobs(); job++) fixture(parent, donor, new int[]{job}, "SINGLE", scratch);
                }
                int[] full = new int[catalog.jobs()]; for (int j = 0; j < full.length; j++) full[j] = j;
                fixture(parent, donor, full, "FULL", scratch);
            }
            for (int i = 0; i < points.size(); i++) if (!before.get(i).equals(raw(points.get(i)))) throw new AssertionError("Fixture mutated source");
        }
        Map<Direction,List<Integer>> groups = contexts.grouping(points, 15);
        for (Direction role : Direction.values()) if (groups.get(role).size() != (role == Direction.CENTER ? 55 : 15)) throw new AssertionError("Role allocation changed");
        Map<String,Object> result = new LinkedHashMap<>(); result.put("cells", cells); result.put("witnesses", witnesses);
        result.put("fixedParentDonorPairs", donorPairs); result.put("fullFACompatiblePairs", compatible);
        result.put("jobs", catalog.jobs()); result.put("factories", catalog.factories()); result.put("sourceMutation", false);
        int[] machines = new int[catalog.factories()], workers = new int[catalog.factories()];
        for (int f = 0; f < machines.length; f++) { machines[f] = instance.machines(f, 0); workers[f] = instance.workers(f, 0); }
        result.put("machineCounts", machines); result.put("workerCounts", workers);
        result.put("counterColumns", Arrays.asList("fixtures", "nativeFallbacks", "projectionChangedCandidates", "changedFAJobs", "changedMAJobs", "changedWAJobs", "projectedThirdTupleJobs"));
        return result;
    }
    private void fixture(int parent, int donor, int[] mask, String kind, PermutationSolution<Integer> scratch) {
        TypedScheduleGenome p = genomes.get(parent), d = genomes.get(donor);
        PaMixingMove move = PaMixingMove.apply(catalog, p, d, mask); write(scratch, move.genome.toVectors());
        int[] before = move.genome.allocations(), original = p.allocations(), incoming = d.allocations();
        int[] sequence = SchedulingEncoding.integers(scratch.getVariables()); contexts.restore(scratch); contexts.validate(scratch);
        if (SchedulingEncoding.repair(scratch, instance) != 0) throw new AssertionError("Projected fixture illegal");
        if (!Arrays.equals(sequence, SchedulingEncoding.integers(scratch.getVariables()))) throw new AssertionError("Guard changed sequence");
        int[] after = TypedScheduleGenome.fromVectors(catalog, vectors(scratch)).allocations();
        String cell = (parent < 20 ? "FIXED" : "FREE")+"/"+(donor < 20 ? "FIXED" : "FREE")+"/"+kind;
        long[] count = cells.computeIfAbsent(cell, unused -> new long[7]); count[0]++; if (move.fallback) count[1]++;
        boolean changed = false;
        for (int job = 0; job < before.length; job++) {
            int[] a = catalog.tuple(before[job]), b = catalog.tuple(after[job]);
            if (parent >= 20 && !Arrays.equals(a, b)) throw new AssertionError("Free domain unexpectedly projected");
            if (a[0] != b[0]) count[3]++; if (a[1] != b[1]) count[4]++; if (a[2] != b[2]) count[5]++;
            if (!Arrays.equals(a, b)) {
                changed = true;
                if (after[job] != original[job] && after[job] != incoming[job]) count[6]++;
                if (witnesses.size() < 12 && kind.equals("FULL") && parent % 5 == 0) {
                    Map<String,Object> item = new LinkedHashMap<>(); item.put("parent", parent); item.put("donor", donor); item.put("job", job);
                    item.put("parentTuple", catalog.tuple(original[job])); item.put("donorTuple", catalog.tuple(incoming[job]));
                    item.put("nativeTuple", a); item.put("afterGuard", b); witnesses.add(item);
                }
            }
        }
        if (changed) count[2]++;
    }
    private boolean sameFA(TypedScheduleGenome a, TypedScheduleGenome b) {
        int[] x = a.allocations(), y = b.allocations();
        for (int j = 0; j < x.length; j++) if (catalog.factory(x[j]) != catalog.factory(y[j])) return false; return true;
    }
    private static FourVectors vectors(PermutationSolution<Integer> s) {
        return new FourVectors(SchedulingEncoding.integers(s.getVariables()), SchedulingEncoding.integers(s.getVariablesid()),
            SchedulingEncoding.machineIntegers(s), SchedulingEncoding.integers(s.getVariablesworker()));
    }
    @SuppressWarnings("unchecked")
    private static void write(PermutationSolution<Integer> s, FourVectors v) {
        int[] js = v.jobs(), fa = v.factories(), ma = v.machines(), wa = v.workers(); List<Integer> machines = (List<Integer>)s.getAttribute("machine");
        for (int p = 0; p < js.length; p++) { s.setVariableValue(p, js[p]); s.setVariableValueid(p, fa[p]); machines.set(p, ma[p]); s.setVariableValueworker(p, wa[p]); }
    }
    private static String raw(PermutationSolution<Integer> value) {
        return value.getVariables()+"|"+value.getVariablesid()+"|"+value.getAttribute("machine")+"|"+value.getVariablesworker()+"|"+Arrays.toString(value.getObjectives());
    }
}
