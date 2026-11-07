package org.uma.jmetal.util.research.model;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

/** Independent physical/formula audit; never calls either decoder or the shared transition kernel. */
public final class ExplicitResourceValidator {
    private ExplicitResourceValidator() { }

    public static void validate(Instance instance, DynamicParameters params, ExplicitSchedule schedule) {
        schedule.validateContext(instance, params);
        int[] js = schedule.js(), fa = schedule.fa(), ma = schedule.ma(), wa = schedule.wa();
        Encoding.validate(instance, js, fa, ma, wa);
        if (schedule.steps().size() != instance.jobs() * instance.stages()) fail("Operation count");
        double[] total = new double[3], makespan = new double[instance.factories()];
        double[] energy = new double[instance.factories()], labor = new double[instance.factories()];
        int cursor = 0;
        for (int f = 0; f < instance.factories(); f++) {
            List<Integer> positions = new ArrayList<>();
            for (int pos = 0; pos < js.length; pos++) if (fa[pos] == f) positions.add(pos);
            final double[] ready = new double[instance.jobs()];
            for (int k = 0; k < instance.stages(); k++) {
                if (k > 0) Collections.sort(positions, new Comparator<Integer>() {
                    public int compare(Integer a, Integer b) { return Double.compare(ready[js[a]], ready[js[b]]); }
                });
                Resources resources = new Resources(instance, params, f, k);
                for (int pos : positions) {
                    int job = js[pos];
                    StageResourcePlan plan = schedule.plan();
                    int machine = k == 0 ? ma[pos] : plan.specified(job, k)
                            ? plan.machine(job, k) : earliest(resources.machineEnd);
                    int worker = k == 0 ? wa[pos] : plan.specified(job, k)
                            ? plan.worker(job, k) : earliest(resources.workerEnd);
                    DynamicStep operation = schedule.steps().get(cursor++);
                    operation(instance, params, operation, job, f, k, machine, worker, ready[job], resources);
                    ready[job] = operation.completion();
                    total[0] = Math.max(total[0], operation.completion());
                    total[1] += operation.energy(); total[2] += operation.labor();
                    makespan[f] = Math.max(makespan[f], operation.completion());
                    energy[f] += operation.energy(); labor[f] += operation.labor();
                }
            }
        }
        array(schedule.objectives(), total); array(schedule.factoryMakespan(), makespan);
        array(schedule.factoryEnergy(), energy); array(schedule.factoryCost(), labor);
    }

    private static void operation(Instance in, DynamicParameters p, DynamicStep op,
            int job, int factory, int stage, int machine, int worker, double ready, Resources state) {
        if (op.job() != job || op.factory() != factory || op.stage() != stage
                || op.machine() != machine || op.worker() != worker) fail("Order or binding");
        double start = Math.max(ready, Math.max(state.machineEnd[machine], state.workerEnd[worker]));
        double u = state.fatigue[worker] * Math.exp(-p.mu(factory, stage, worker)
                * (start - state.workerEnd[worker]));
        double base = (in.processing(job, stage) / in.speed(factory, stage, machine) + in.setup(job, stage))
                / in.efficiency(factory, stage, worker);
        double factor = 1 + p.beta(factory, stage, worker) * u, duration = base * factor;
        double v = 1 - (1 - u) * Math.exp(-p.alpha(factory, stage, worker) * duration);
        double energy = in.power(factory, stage, machine) * duration;
        if (state.used[machine]) energy += in.standby(factory, stage, machine) * (start - state.machineEnd[machine]);
        if (op.start() < 0 || op.duration() <= 0 || op.u() < 0 || op.u() > 1
                || op.v() < 0 || op.v() > 1 || op.exposure() < 0) fail("Physical ranges");
        close(op.start(), start); close(op.base(), base); close(op.duration(), duration);
        close(op.completion(), start + duration);
        close(op.setupDuration(), in.setup(job, stage) / in.efficiency(factory, stage, worker) * factor);
        close(op.u(), u); close(op.v(), v); close(op.energy(), energy);
        close(op.labor(), in.cost(factory, stage, worker) * duration);
        close(op.exposure(), integral(u, p.alpha(factory, stage, worker), duration));
        state.machineEnd[machine] = op.completion(); state.used[machine] = true;
        state.workerEnd[worker] = op.completion(); state.fatigue[worker] = op.v();
    }

    private static double integral(double u, double alpha, double duration) {
        if (alpha == 0) return u * duration;
        double x = alpha * duration;
        if (x < 1e-4) {
            double rising = x / 2 - x * x / 6 + x * x * x / 24 - x * x * x * x / 120
                    + x * x * x * x * x / 720;
            return u * duration + (1 - u) * duration * rising;
        }
        return duration + (1 - u) * Math.expm1(-x) / alpha;
    }

    private static int earliest(double[] values) {
        int best = 0;
        for (int i = 1; i < values.length; i++) if (values[i] < values[best]) best = i;
        return best;
    }

    private static void array(double[] actual, double[] expected) {
        if (actual.length != expected.length) fail("Summary dimensions");
        for (int i = 0; i < actual.length; i++) close(actual[i], expected[i]);
    }

    private static void close(double actual, double expected) {
        if (!Double.isFinite(actual) || !Double.isFinite(expected)
                || Math.abs(actual - expected) > 1e-9 * Math.max(1, Math.abs(expected)))
            fail("Transition or objective formula: " + actual + " != " + expected);
    }

    private static void fail(String reason) { throw new IllegalStateException(reason); }

    private static final class Resources {
        final double[] machineEnd, workerEnd, fatigue;
        final boolean[] used;
        Resources(Instance instance, DynamicParameters parameters, int factory, int stage) {
            machineEnd = new double[instance.machines(factory, stage)]; used = new boolean[machineEnd.length];
            workerEnd = new double[instance.workers(factory, stage)]; fatigue = new double[workerEnd.length];
            for (int worker = 0; worker < fatigue.length; worker++) fatigue[worker] = parameters.h0(factory, stage, worker);
        }
    }
}
