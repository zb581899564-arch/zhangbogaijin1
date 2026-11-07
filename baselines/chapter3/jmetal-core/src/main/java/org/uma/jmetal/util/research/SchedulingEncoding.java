package org.uma.jmetal.util.research;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.impl.DefaultIntegerPermutationSolution;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.model.ModelKind;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Positional four-vector initialization and shared deterministic feasibility repair. */
public final class SchedulingEncoding {
    private SchedulingEncoding() { }

    public static void initialize(DefaultIntegerPermutationSolution solution, Instance in) {
        Random random = SeededRandom.current();
        List<Integer> jobs = sequence(in.jobs());
        Collections.shuffle(jobs, random);
        List<Integer> factories = new ArrayList<>();
        for (int f = 0; f < in.factories(); f++) factories.add(f);
        while (factories.size() < in.jobs()) factories.add(random.nextInt(in.factories()));
        Collections.shuffle(factories, random);
        for (int p = 0; p < in.jobs(); p++) {
            solution.setVariableValue(p, jobs.get(p));
            solution.setVariableValueid(p, factories.get(p));
            solution.setVariableValuemachine(p, random.nextInt(in.machines(factories.get(p), 0)));
        }
        int cursor = 0;
        if (in.kind() == ModelKind.CHAPTER3_FIXED_WORKER) {
            for (int f = 0; f < in.factories(); f++) {
                List<Integer> workers = sequence(in.workers(f, 0));
                Collections.shuffle(workers, random);
                for (int worker : workers) solution.setVariableValueworker(cursor++, worker);
            }
        } else {
            for (int p = 0; p < in.jobs(); p++) {
                solution.setVariableValueworker(p, random.nextInt(in.workers(factories.get(p), 0)));
            }
        }
    }

    public static int repair(PermutationSolution<Integer> solution, Instance in) {
        int repaired = 0;
        int[] counts = new int[in.factories()];
        for (int p = 0; p < in.jobs(); p++) {
            int f = solution.getVariableValueid(p);
            if (f < 0 || f >= in.factories()) throw new IllegalArgumentException("Invalid factory id");
            counts[f]++;
        }
        // The paper requires a nonempty job set at each factory. Move from the
        // largest donor deterministically; ties use the lowest factory/position.
        for (int f = 0; f < counts.length; f++) if (counts[f] == 0) {
            int donor = 0;
            for (int g = 1; g < counts.length; g++) if (counts[g] > counts[donor]) donor = g;
            for (int p = 0; p < in.jobs(); p++) if (solution.getVariableValueid(p) == donor) {
                solution.setVariableValueid(p, f); counts[donor]--; counts[f]++; repaired++; break;
            }
        }
        @SuppressWarnings("unchecked")
        List<Integer> machines = (List<Integer>) solution.getAttribute("machine");
        for (int p = 0; p < in.jobs(); p++) {
            int f = solution.getVariableValueid(p);
            int machine = machines.get(p), validMachine = Math.floorMod(machine, in.machines(f, 0));
            if (machine != validMachine) { machines.set(p, validMachine); repaired++; }
            if (in.kind() == ModelKind.CHAPTER4_DUAL_RESOURCE) {
                int worker = solution.getVariableValueworker(p);
                int validWorker = Math.floorMod(worker, in.workers(f, 0));
                if (worker != validWorker) { solution.setVariableValueworker(p, validWorker); repaired++; }
            }
        }
        return repaired;
    }

    public static int[] integers(List<Integer> values) {
        int[] result = new int[values.size()];
        for (int i = 0; i < result.length; i++) result[i] = values.get(i);
        return result;
    }

    private static List<Integer> sequence(int count) {
        List<Integer> result = new ArrayList<>();
        for (int i = 0; i < count; i++) result.add(i);
        return result;
    }
}
