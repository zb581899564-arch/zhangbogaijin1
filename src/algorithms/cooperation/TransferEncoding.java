package org.uma.jmetal.util.research.cooperation;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.LinkedHashMap;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.DynamicSchedule;
import org.uma.jmetal.util.research.model.DynamicStep;
import org.uma.jmetal.util.research.search.Direction;

/** Pure same-context factory encoding operations, separate from sampling and paid observation. */
final class TransferEncoding {
    private TransferEncoding() { }
    static int target(DynamicSchedule parent, Direction direction) {
        double[] values = direction == Direction.MAKESPAN ? parent.factoryMakespan()
                : direction == Direction.ENERGY ? parent.factoryEnergy() : parent.factoryCost();
        int best = 0;
        for (int f = 1; f < values.length; f++) if (values[f] > values[best]) best = f;
        return best;
    }
    @SuppressWarnings("unchecked")
    static PermutationSolution<Integer> build(PermutationSolution<Integer> parent, int factory,
            FactoryRecord sequence, FactoryRecord machineSource, FactoryRecord workerSource) {
        PermutationSolution<Integer> child = (PermutationSolution<Integer>) parent.copy();
        int n = parent.getNumberOfVariables(), at = 0;
        int[] machinesByJob = new int[n], workersByJob = new int[n];
        for (int i = 0; i < machineSource.jobs.length; i++) machinesByJob[machineSource.jobs[i]] = machineSource.machines[i];
        for (int i = 0; i < workerSource.jobs.length; i++) workersByJob[workerSource.jobs[i]] = workerSource.workers[i];
        List<Integer> machines = (List<Integer>) child.getAttribute("machine");
        for (int p = 0; p < n; p++) if (parent.getVariableValueid(p) == factory) {
            int job = sequence.jobs[at++]; child.setVariableValue(p, job); child.setVariableValueid(p, factory);
            machines.set(p, machinesByJob[job]); child.setVariableValueworker(p, workersByJob[job]);
        }
        if (at != sequence.jobs.length) throw new IllegalStateException("Transfer changed a factory job set");
        child.setAttribute("worker", child.getVariablesworker()); return child;
    }
    static boolean othersPreserved(DynamicSchedule parent, DynamicSchedule child, int changedFactory) {
        for (int f = 0; f < parent.factoryMakespan().length; f++) if (f != changedFactory
                && !new FactoryRecord(parent, f).same(new FactoryRecord(child, f))) return false;
        return true;
    }
    static boolean timelineMatches(DynamicSchedule source, DynamicSchedule actual, int factory) {
        if (source == null) throw new IllegalStateException("Missing paid source schedule");
        List<DynamicStep> left = factorySteps(source, factory), right = factorySteps(actual, factory);
        if (left.size() != right.size()) return false;
        for (int i = 0; i < left.size(); i++) {
            DynamicStep a = left.get(i), b = right.get(i);
            if (a.job() != b.job() || a.stage() != b.stage() || a.machine() != b.machine() || a.worker() != b.worker()) return false;
            double[] x = {a.start(), a.duration(), a.setupDuration(), a.u(), a.v(), a.energy(), a.labor(), a.exposure()};
            double[] y = {b.start(), b.duration(), b.setupDuration(), b.u(), b.v(), b.energy(), b.labor(), b.exposure()};
            for (int k = 0; k < x.length; k++) if (Math.abs(x[k] - y[k]) > 1e-9 * Math.max(1., Math.abs(x[k]))) return false;
        }
        return true;
    }
    private static List<DynamicStep> factorySteps(DynamicSchedule schedule, int factory) {
        List<DynamicStep> result = new ArrayList<>();
        for (DynamicStep step : schedule.steps()) if (step.factory() == factory) result.add(step);
        return result;
    }
    static Map<String, Object> record(FactoryRecord value) {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("jobs", value.jobs.clone()); out.put("machines", value.machines.clone()); out.put("workers", value.workers.clone());
        out.put("objectives", value.objectives.clone()); out.put("paidFE", value.paidFE);
        out.put("generation", value.generation); out.put("producer", value.producer); out.put("stage", value.stage); return out;
    }
    @SuppressWarnings("unchecked")
    static Map<String, Object> encoding(PermutationSolution<Integer> value, int factory) {
        List<Integer> jobs = new ArrayList<>(), machines = new ArrayList<>(), workers = new ArrayList<>();
        List<Integer> ma = (List<Integer>) value.getAttribute("machine");
        for (int p = 0; p < value.getNumberOfVariables(); p++) if (value.getVariableValueid(p) == factory) {
            jobs.add(value.getVariableValue(p)); machines.add(ma.get(p)); workers.add(value.getVariableValueworker(p));
        }
        Map<String, Object> out = new LinkedHashMap<>(); out.put("jobs", jobs); out.put("machines", machines); out.put("workers", workers); return out;
    }
}
