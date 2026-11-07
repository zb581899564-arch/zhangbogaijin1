package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.modelglobal.*;

/** Immutable numeric evidence and vector interchange; no physics or search decisions. */
public final class GomRecords {
    private GomRecords() { }
    public static Map<String,Object> row(Object... fields) {
        Map<String,Object> result = new LinkedHashMap<>();
        for (int i = 0; i < fields.length; i += 2) result.put((String)fields[i], fields[i+1]); return result;
    }
    public static FourVectors vectors(PermutationSolution<Integer> p) {
        return new FourVectors(SchedulingEncoding.integers(p.getVariables()), SchedulingEncoding.integers(p.getVariablesid()),
            SchedulingEncoding.machineIntegers(p), SchedulingEncoding.integers(p.getVariablesworker()));
    }
    public static Map<String,Object> raw(PermutationSolution<Integer> p) {
        FourVectors v = vectors(p);
        return row("JS", v.jobs(), "FA", v.factories(), "MA", v.machines(), "WA", v.workers(), "objectives", p.getObjectives().clone());
    }
    @SuppressWarnings("unchecked")
    static PermutationSolution<Integer> copy(PermutationSolution<Integer> p, TypedScheduleGenome genes) {
        PermutationSolution<Integer> child = (PermutationSolution<Integer>)p.copy(); FourVectors v = genes.toVectors();
        int[] js = v.jobs(), fa = v.factories(), ma = v.machines(), wa = v.workers();
        List<Integer> machines = (List<Integer>)child.getAttribute("machine");
        for (int i = 0; i < js.length; i++) { child.setVariableValue(i, js[i]); child.setVariableValueid(i, fa[i]); machines.set(i, ma[i]); child.setVariableValueworker(i, wa[i]); }
        return child;
    }
    static void sameView(PermutationSolution<Integer> p, TypedScheduleGenome genes) {
        FourVectors a = vectors(p), b = genes.toVectors();
        if (!Arrays.equals(a.jobs(), b.jobs()) || !Arrays.equals(a.factories(), b.factories())
                || !Arrays.equals(a.machines(), b.machines()) || !Arrays.equals(a.workers(), b.workers())) throw new AssertionError("Family guard/repair changed GOM candidate");
    }
    static final class State {
        final long id, paidFE;
        final TypedScheduleGenome genes;
        final PermutationSolution<Integer> point;
        final double[] objectives;
        State(long number, long fee, TypedScheduleGenome value, PermutationSolution<Integer> p) {
            id = number; paidFE = fee; genes = value; point = p; objectives = p.getObjectives().clone();
        }
        Map<String,Object> record(boolean full) {
            Map<String,Object> row = GomRecords.row("id", id, "paidFE", paidFE, "objectives", objectives);
            if (full) { row.put("resources", genes.allocations()); row.put("keys", genes.priorities()); }
            return row;
        }
    }
}
