package org.uma.jmetal.util.research;

import java.io.Serializable;
import org.uma.jmetal.solution.Solution;

/** Immutable factory statistics; these are search metadata, never objectives. */
public final class SchedulingMetadata implements Serializable {
    public static final String KEY = "dhfsp.factoryMetrics";
    public static final String SCHEDULE_KEY = "dhfsp.schedule";
    private final double[][] values;

    public SchedulingMetadata(double[] makespan, double[] energy, double[] cost) {
        if (makespan.length == 0 || makespan.length != energy.length || energy.length != cost.length) {
            throw new IllegalArgumentException("Factory statistics have incompatible dimensions");
        }
        values = new double[][] {makespan.clone(), energy.clone(), cost.clone()};
    }

    public int extremum(int objective, boolean maximum) {
        int best = 0;
        for (int i = 1; i < values[objective].length; i++) {
            if (maximum ? values[objective][i] > values[objective][best]
                        : values[objective][i] < values[objective][best]) { best = i; }
        }
        return best;
    }

    public double[] values(int objective) { return values[objective].clone(); }

    public static SchedulingMetadata of(Solution<?> solution) {
        Object metadata = solution.getAttribute(KEY);
        if (!(metadata instanceof SchedulingMetadata)) {
            throw new IllegalStateException("Evaluate the solution before selecting critical factories");
        }
        return (SchedulingMetadata) metadata;
    }
}
