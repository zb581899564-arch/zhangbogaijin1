package research.dynamic;

import java.util.Arrays;
import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.DynamicSchedule;
import org.uma.jmetal.util.research.model.DynamicStep;
import org.uma.jmetal.util.research.model.Instance;

/** Candidate-free features from one already-paid parent and the selected factory. */
final class ActionStateFeatures {
    static final List<String> BASIC_NAMES = Arrays.asList(
            "normalizedC", "normalizedE", "normalizedW", "factoryJobShare",
            "factoryCShare", "factoryEShare", "factoryWShare",
            "machineLoadCV", "workerLoadCV", "usedMachineShare", "usedWorkerShare");
    static final List<String> FATIGUE_NAMES = Arrays.asList(
            "meanStartFatigue", "maxStartFatigue", "meanEndFatigue",
            "workExposurePerDuration", "durationOverBase");

    private ActionStateFeatures() { }

    static double[] extract(Instance instance, PermutationSolution<Integer> parent,
            int factory, double[] scale) {
        DynamicSchedule schedule = (DynamicSchedule) parent.getAttribute(DynamicEvaluation.KEY);
        int[] machines = new int[instance.machines(factory, 0)];
        int[] workers = new int[instance.workers(factory, 0)];
        int count = 0;
        double start = 0, maxStart = 0, end = 0, exposure = 0, duration = 0, base = 0;
        // No candidate construction, random draw, new decoder call or unobserved suffix.
        for (DynamicStep step : schedule.steps()) {
            if (step.factory() != factory || step.stage() != 0) continue;
            count++;
            machines[step.machine()]++;
            workers[step.worker()]++;
            start += step.u();
            maxStart = Math.max(maxStart, step.u());
            end += step.v();
            exposure += step.exposure();
            duration += step.duration();
            base += step.base();
        }
        if (count == 0) throw new AssertionError("Selected factory has no jobs");
        double[] objective = parent.getObjectives();
        return new double[] {
            objective[0] / scale[0], objective[1] / scale[1], objective[2] / scale[2],
            (double) count / instance.jobs(),
            schedule.factoryMakespan()[factory] / objective[0],
            schedule.factoryEnergy()[factory] / objective[1],
            schedule.factoryCost()[factory] / objective[2],
            coefficientOfVariation(machines), coefficientOfVariation(workers),
            usedShare(machines), usedShare(workers), start / count, maxStart, end / count,
            exposure / duration, duration / base
        };
    }

    private static double coefficientOfVariation(int[] counts) {
        double mean = 0, variance = 0;
        for (int value : counts) mean += value;
        mean /= counts.length;
        for (int value : counts) variance += (value - mean) * (value - mean);
        return Math.sqrt(variance / counts.length) / mean;
    }

    private static double usedShare(int[] counts) {
        int used = 0;
        for (int value : counts) if (value > 0) used++;
        return (double) used / counts.length;
    }
}
