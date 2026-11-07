package org.uma.jmetal.util.research.joint;

import java.util.ArrayList;
import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.DynamicPrefix;
import org.uma.jmetal.util.research.model.Instance;

/** By-job assignments, fixed outside encoding, and a compatible remaining-block witness. */
final class BlockContext {
    final Instance instance;
    final int begin, length;
    final int[] parentSequence;
    final JointAction[] assignments;
    final int[] coverage;
    private List<JointAction> witness;
    private final List<JointAction> committed = new ArrayList<>();
    private final int[] fixedFactory;

    BlockContext(Instance in, PermutationSolution<Integer> parent, int begin, int length) {
        instance = in; this.begin = begin; this.length = length;
        Object fixed = parent.getAttribute("cooperation.fixedFactoryByJob");
        fixedFactory = fixed == null ? null : ((int[]) fixed).clone();
        parentSequence = sequence(parent); assignments = byJob(in, parent, true);
        coverage = new int[in.factories()]; witness = new ArrayList<>();
        for (int p = 0; p < parentSequence.length; p++) {
            JointAction a = assignments[parentSequence[p]];
            if (p >= begin && p < begin + length) witness.add(a); else coverage[a.factory()]++;
        }
    }
    static int[] sequence(PermutationSolution<Integer> solution) {
        int[] result = new int[solution.getNumberOfVariables()];
        for (int p = 0; p < result.length; p++) result[p] = solution.getVariableValue(p);
        return result;
    }
    @SuppressWarnings("unchecked")
    static JointAction[] byJob(Instance in, PermutationSolution<Integer> solution, boolean strict) {
        JointAction[] result = new JointAction[in.jobs()];
        List<Integer> machines = (List<Integer>) solution.getAttribute("machine");
        if (solution.getNumberOfVariables() != in.jobs() || machines == null || machines.size() != in.jobs()
                || solution.getNumberOfVariablesworker() != in.jobs()) {
            throw new IllegalArgumentException("Joint generator requires chapter4 positional four-vectors");
        }
        for (int p = 0; p < in.jobs(); p++) {
            int j = solution.getVariableValue(p);
            if (j < 0 || j >= in.jobs() || result[j] != null) throw new IllegalArgumentException("Invalid teacher job permutation");
            JointAction a = new JointAction(j, solution.getVariableValueid(p), machines.get(p), solution.getVariableValueworker(p));
            if (strict && !legal(in, a)) throw new IllegalArgumentException("Illegal parent tuple " + a);
            result[j] = a;
        }
        return result;
    }
    static boolean legal(Instance in, JointAction a) {
        return a.job() >= 0 && a.job() < in.jobs() && a.factory() >= 0 && a.factory() < in.factories()
                && a.machine() >= 0 && a.machine() < in.machines(a.factory(), 0)
                && a.worker() >= 0 && a.worker() < in.workers(a.factory(), 0);
    }
    boolean remaining(int job) {
        for (JointAction a : witness) if (a.job() == job) return true;
        return false;
    }
    int remainingCount() { return witness.size(); }
    List<JointAction> witness() { return new ArrayList<>(witness); }
    boolean completable(JointAction action) {
        if (!legal(instance, action) || !remaining(action.job())) return false;
        if (fixedFactory != null) return action.factory() == fixedFactory[action.job()];
        int missing = 0;
        for (int f = 0; f < coverage.length; f++) if (coverage[f] == 0 && f != action.factory()) missing++;
        return missing <= witness.size() - 1;
    }
    List<JointAction> afterWitness(JointAction action) {
        if (!completable(action)) throw new IllegalArgumentException("Action has no feasible factory-cover completion");
        List<JointAction> next = new ArrayList<>();
        for (JointAction a : witness) if (a.job() != action.job()) next.add(a);
        if (fixedFactory != null) return next;
        int cursor = 0;
        for (int f = 0; f < coverage.length; f++) if (coverage[f] == 0 && f != action.factory()) {
            JointAction old = next.get(cursor);
            next.set(cursor++, old.factory() == f ? old : new JointAction(old.job(), f, 0, 0));
        }
        return next;
    }
    void commit(JointAction action, List<JointAction> nextWitness) {
        if (!completable(action)) throw new IllegalStateException("Cannot commit infeasible action");
        assignments[action.job()] = action; coverage[action.factory()]++; committed.add(action);
        witness = new ArrayList<>(nextWitness);
    }
    JointAction[] projected(JointAction action, List<JointAction> nextWitness) {
        JointAction[] result = assignments.clone(); result[action.job()] = action;
        for (JointAction a : nextWitness) result[a.job()] = a;
        return result;
    }
    List<JointAction> future(List<JointAction> nextWitness) {
        List<JointAction> future = new ArrayList<>(nextWitness);
        for (int p = begin + length; p < parentSequence.length; p++) future.add(assignments[parentSequence[p]]);
        return future;
    }
    void restorePrefix(DynamicPrefix prefix, Runnable checkpoint) {
        for (int p = 0; p < begin; p++) {
            checkpoint.run(); append(prefix, assignments[parentSequence[p]]);
        }
    }
    @SuppressWarnings("unchecked")
    PermutationSolution<Integer> child(PermutationSolution<Integer> parent) {
        if (!witness.isEmpty()) throw new IllegalStateException("Block not complete");
        for (int count : coverage) if (count == 0) throw new IllegalStateException("Final factory coverage lost");
        PermutationSolution<Integer> result = (PermutationSolution<Integer>) parent.copy();
        List<Integer> machines = (List<Integer>) result.getAttribute("machine");
        if (machines == parent.getAttribute("machine") || result.getVariablesworker() == parent.getVariablesworker()
                || result.getVariables() == parent.getVariables() || result.getVariablesid() == parent.getVariablesid()) {
            throw new IllegalStateException("Solution.copy must provide independent four-vector storage");
        }
        for (int i = 0; i < length; i++) {
            int p = begin + i; JointAction a = committed.get(i);
            result.setVariableValue(p, a.job()); result.setVariableValueid(p, a.factory());
            machines.set(p, a.machine()); result.setVariableValueworker(p, a.worker());
        }
        result.setAttribute("worker", result.getVariablesworker());
        return result;
    }
    static void append(DynamicPrefix prefix, JointAction a) { prefix.append(a.job(), a.factory(), a.machine(), a.worker()); }
}
