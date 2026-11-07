package org.uma.jmetal.util.research.cooperation;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.search.*;

/** Four FA contexts, fixed by default; optional explicit renewal starts a fresh context epoch. */
final class FamilyContexts {
    static final String FAMILY = "cooperation.family";
    static final String FIXED = "cooperation.fixedFactoryByJob";
    private final Instance in;
    private final int[][] assignments = new int[4][];
    private final long[] epochs = new long[4];
    FamilyContexts(Instance in) { this.in = in; }
    static int family(PermutationSolution<Integer> s) {
        Object value = s.getAttribute(FAMILY); return value == null ? -1 : (Integer) value;
    }
    void initialize(PermutationSolution<Integer> s, int index) {
        if (index >= 20) return;
        int family = index / 5;
        if (index % 5 == 0) {
            assignments[family] = new int[in.jobs()];
            for (int p = 0; p < in.jobs(); p++) assignments[family][s.getVariableValue(p)] = s.getVariableValueid(p);
        }
        s.setAttribute(FAMILY, family); s.setAttribute(FIXED, assignments[family].clone()); restore(s);
    }
    @SuppressWarnings("unchecked")
    void restore(PermutationSolution<Integer> s) {
        ContextRelease.normalize(s); int family = family(s); if (family < 0) return;
        int[] fixed = assignments[family];
        List<Integer> machines = (List<Integer>) s.getAttribute("machine");
        for (int p = 0; p < in.jobs(); p++) {
            int f = fixed[s.getVariableValue(p)]; s.setVariableValueid(p, f);
            machines.set(p, Math.floorMod(machines.get(p), in.machines(f, 0)));
            s.setVariableValueworker(p, Math.floorMod(s.getVariableValueworker(p), in.workers(f, 0)));
        }
    }
    void validate(PermutationSolution<Integer> s) {
        ContextRelease.normalize(s); int family = family(s); if (family < 0) return;
        for (int p = 0; p < in.jobs(); p++) if (s.getVariableValueid(p) != assignments[family][s.getVariableValue(p)])
            throw new IllegalStateException("FA family context changed");
    }
    int[] assignment(int family) { return assignments[family].clone(); }
    boolean matchesAny(PermutationSolution<Integer> solution) {
        int[] assignment = byJob(solution);
        for (int[] known : assignments) if (java.util.Arrays.equals(assignment, known)) return true;
        return false;
    }
    long replace(int family, int[] assignment) {
        if (assignment.length != in.jobs()) throw new IllegalArgumentException("Renewed FA length mismatch");
        int[] counts = new int[in.factories()];
        for (int f : assignment) {
            if (f < 0 || f >= counts.length) throw new IllegalArgumentException("Renewed FA factory mismatch");
            counts[f]++;
        }
        for (int count : counts) if (count == 0) throw new IllegalArgumentException("Renewed FA empties a factory");
        assignments[family] = assignment.clone(); return ++epochs[family];
    }
    void attachRenewed(PermutationSolution<Integer> solution, int family) {
        solution.setAttribute(FAMILY, family); solution.setAttribute(FIXED, assignment(family));
        solution.setAttribute("cooperation.contextEpoch", epochs[family]); restore(solution);
    }
    static int[] byJob(PermutationSolution<Integer> solution) {
        int[] assignment = new int[solution.getNumberOfVariables()];
        for (int p = 0; p < assignment.length; p++) assignment[solution.getVariableValue(p)] = solution.getVariableValueid(p);
        return assignment;
    }
    Map<Direction, List<Integer>> grouping(List<PermutationSolution<Integer>> pop, int boundary) {
        return grouping(pop, boundary, false);
    }
    Map<Direction, List<Integer>> grouping(List<PermutationSolution<Integer>> pop, int boundary, boolean uniform) {
        if (pop.size() != 100 || boundary != 15) throw new IllegalArgumentException("Cooperation pilot requires default 100/15 search");
        Map<Direction, List<Integer>> out = new EnumMap<>(Direction.class);
        for (Direction d : Direction.values()) out.put(d, new ArrayList<>());
        for (PermutationSolution<Integer> s : pop) ContextRelease.normalize(s);
        int protectedCount = ContextRelease.protectedCount();
        for (int f = -1; f < 4; f++) {
            List<Integer> ids = new ArrayList<>();
            for (int i = 0; i < pop.size(); i++) if (family(pop.get(i)) == f) ids.add(i);
            int expected = f < 0 ? 100 - 5 * protectedCount : ContextRelease.released(f) ? 0 : 5;
            if (ids.size() != expected) throw new IllegalStateException("Family population lost");
            if (ids.isEmpty()) continue;
            for (Direction d : new Direction[] {Direction.MAKESPAN, Direction.ENERGY, Direction.WORKER_COST}) {
                if (uniform) {
                    List<PermutationSolution<Integer>> values = new ArrayList<>();
                    for (int i : ids) values.add(pop.get(i));
                    List<Integer> ordered = new ArrayList<>();
                    for (int i : ParetoTools.order(values, Direction.CENTER)) ordered.add(ids.get(i));
                    ids = ordered;
                } else {
                    final int obj = d.objective(); ids.sort((a,b) -> Double.compare(pop.get(a).getObjective(obj), pop.get(b).getObjective(obj)));
                }
                int count = f < 0 ? 15 - protectedCount : 1;
                out.get(d).addAll(new ArrayList<>(ids.subList(0, count))); ids.subList(0, count).clear();
            }
            List<PermutationSolution<Integer>> rest = new ArrayList<>(); for (int i : ids) rest.add(pop.get(i));
            for (int i : ParetoTools.order(rest, Direction.CENTER)) out.get(Direction.CENTER).add(ids.get(i));
        }
        return out;
    }
}
