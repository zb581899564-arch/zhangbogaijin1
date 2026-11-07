package org.uma.jmetal.util.research.cooperation;

import java.util.Arrays;
import org.uma.jmetal.util.research.model.DynamicSchedule;

/** Immutable first-stage local encoding plus exact paid factory objectives. */
final class FactoryRecord {
    final int[] jobs, machines, workers;
    final double[] objectives;
    FactoryRecord(DynamicSchedule schedule, int factory) {
        int[] js = schedule.js(), fa = schedule.fa(), ma = schedule.ma(), wa = schedule.wa();
        int count = 0; for (int f : fa) if (f == factory) count++;
        jobs = new int[count]; machines = new int[count]; workers = new int[count];
        int at = 0;
        for (int p = 0; p < js.length; p++) if (fa[p] == factory) {
            jobs[at] = js[p]; machines[at] = ma[p]; workers[at++] = wa[p];
        }
        objectives = new double[] {schedule.factoryMakespan()[factory], schedule.factoryEnergy()[factory], schedule.factoryCost()[factory]};
    }
    boolean same(FactoryRecord other) {
        return Arrays.equals(jobs, other.jobs) && Arrays.equals(machines, other.machines) && Arrays.equals(workers, other.workers);
    }
    boolean dominates(FactoryRecord other) {
        boolean strict = false;
        for (int k = 0; k < 3; k++) {
            if (objectives[k] > other.objectives[k]) return false;
            strict |= objectives[k] < other.objectives[k];
        }
        return strict;
    }
}
