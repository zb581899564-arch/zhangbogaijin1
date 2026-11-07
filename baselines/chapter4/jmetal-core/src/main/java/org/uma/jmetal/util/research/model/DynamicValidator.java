package org.uma.jmetal.util.research.model;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

/** Independent dynamic timeline audit; deliberately does not call the transition kernel. */
public final class DynamicValidator {
    private static final double TOLERANCE = 1e-9;
    private DynamicValidator() { }

    public static void validate(Instance in, DynamicParameters p, DynamicSchedule schedule) {
        if (p == null || schedule == null) fail("Parameters and schedule are required");
        p.validateFor(in); schedule.validateContext(in, p);
        int[] js = schedule.js(), fa = schedule.fa(), ma = schedule.ma(), wa = schedule.wa();
        Encoding.validate(in, js, fa, ma, wa);
        if (schedule.steps().size() != in.jobs() * in.stages()) fail("Missing or extra operations");
        Audit audit = new Audit(in, p);
        int cursor = 0;
        for (int f = 0; f < in.factories(); f++) {
            List<Integer> positions = new ArrayList<Integer>();
            for (int pos = 0; pos < js.length; pos++) if (fa[pos] == f) positions.add(pos);
            final double[] completion = new double[in.jobs()];
            for (int k = 0; k < in.stages(); k++) {
                if (k > 0) stableSort(positions, js, completion);
                ResourceAudit resources = new ResourceAudit(in, p, f, k);
                for (int pos : positions) {
                    DynamicStep step = schedule.steps().get(cursor++);
                    int m = k == 0 ? ma[pos] : earliest(resources.machineEnd);
                    int w = k == 0 ? wa[pos] : earliest(resources.workerEnd);
                    auditOperation(in, p, step, js[pos], f, k, m, w, completion[js[pos]], resources);
                    completion[js[pos]] = step.completion();
                    audit.add(step);
                }
            }
        }
        audit.check(schedule);
        if (schedule.reusedOperations() < 0 || schedule.recomputedOperations() < 0
                || schedule.reusedOperations() + schedule.recomputedOperations() != schedule.steps().size()) {
            fail("Invalid operation work counters");
        }
    }

    private static void auditOperation(Instance in, DynamicParameters p, DynamicStep op,
            int j, int f, int k, int m, int w, double jobReady, ResourceAudit state) {
        if (op.job() != j || op.factory() != f || op.stage() != k
                || op.machine() != m || op.worker() != w) fail("Wrong operation order or resource binding");
        double start = Math.max(Math.max(jobReady, state.machineEnd[m]), state.workerEnd[w]);
        double u = state.fatigue[w] * Math.exp(-p.mu(f, k, w) * (start - state.workerEnd[w]));
        double base = (in.processing(j, k) / in.speed(f, k, m) + in.setup(j, k)) / in.efficiency(f, k, w);
        double duration = base * (1 + p.beta(f, k, w) * u);
        double v = 1 - (1 - u) * Math.exp(-p.alpha(f, k, w) * duration);
        double energy = in.power(f, k, m) * duration;
        if (state.used[m]) energy += in.standby(f, k, m) * (start - state.machineEnd[m]);
        if (op.start() < 0 || op.duration() <= 0 || op.u() < 0 || op.u() > 1
                || op.v() < 0 || op.v() > 1 || op.exposure() < 0) fail("Invalid transition range");
        close(op.start(), start, "start/resource/precedence");
        close(op.base(), base, "base"); close(op.duration(), duration, "duration");
        close(op.completion(), start + duration, "completion");
        close(op.setupDuration(), in.setup(j, k) / in.efficiency(f, k, w) * (1 + p.beta(f, k, w) * u), "setup");
        close(op.u(), u, "recovery continuity"); close(op.v(), v, "fatigue continuity");
        close(op.energy(), energy, "operation energy");
        close(op.labor(), in.cost(f, k, w) * duration, "operation labor");
        close(op.exposure(), independentIntegral(u, p.alpha(f, k, w), duration), "work exposure");
        state.machineEnd[m] = op.completion(); state.used[m] = true;
        state.workerEnd[w] = op.completion(); state.fatigue[w] = op.v();
    }

    private static double independentIntegral(double u, double a, double d) {
        if (a == 0.0) return u * d;
        double x = a * d;
        if (x < 1e-4) {
            double rising = x / 2 - x * x / 6 + x * x * x / 24
                    - x * x * x * x / 120 + x * x * x * x * x / 720;
            return u * d + (1 - u) * d * rising;
        }
        return d + (1 - u) * Math.expm1(-x) / a;
    }

    private static void stableSort(List<Integer> positions, final int[] js, final double[] completion) {
        Collections.sort(positions, new Comparator<Integer>() {
            public int compare(Integer a, Integer b) { return Double.compare(completion[js[a]], completion[js[b]]); }
        });
    }

    private static int earliest(double[] values) {
        int first = 0;
        for (int i = 1; i < values.length; i++) if (values[i] < values[first]) first = i;
        return first;
    }

    private static void close(double actual, double expected, String field) {
        if (!Double.isFinite(actual) || !Double.isFinite(expected)
                || Math.abs(actual - expected) > TOLERANCE * Math.max(1.0, Math.abs(expected))) {
            fail("Dynamic schedule has wrong " + field + ": " + actual + " != " + expected);
        }
    }

    private static void checkArray(double[] actual, double[] expected, String field) {
        if (actual.length != expected.length) fail("Wrong " + field + " count");
        for (int i = 0; i < actual.length; i++) close(actual[i], expected[i], field);
    }

    private static void fail(String message) { throw new IllegalStateException(message); }

    private static final class ResourceAudit {
        final double[] machineEnd, workerEnd, fatigue;
        final boolean[] used;
        ResourceAudit(Instance in, DynamicParameters p, int f, int k) {
            machineEnd = new double[in.machines(f, k)]; used = new boolean[machineEnd.length];
            workerEnd = new double[in.workers(f, k)]; fatigue = new double[workerEnd.length];
            for (int w = 0; w < fatigue.length; w++) fatigue[w] = p.h0(f, k, w);
        }
    }

    private static final class Audit {
        final double[] objectives = new double[3], makespan, energy, labor;
        final double[][][] exposure;
        double totalExposure, peak;
        Audit(Instance in, DynamicParameters p) {
            makespan = new double[in.factories()]; energy = new double[in.factories()]; labor = new double[in.factories()];
            exposure = new double[in.factories()][in.stages()][];
            for (int f = 0; f < in.factories(); f++) for (int k = 0; k < in.stages(); k++) {
                exposure[f][k] = new double[in.workers(f, k)];
                for (int w = 0; w < in.workers(f, k); w++) peak = Math.max(peak, p.h0(f, k, w));
            }
        }
        void add(DynamicStep op) {
            int f = op.factory();
            makespan[f] = Math.max(makespan[f], op.completion());
            energy[f] += op.energy(); labor[f] += op.labor();
            objectives[0] = Math.max(objectives[0], op.completion());
            objectives[1] += op.energy(); objectives[2] += op.labor();
            exposure[f][op.stage()][op.worker()] += op.exposure(); totalExposure += op.exposure();
            peak = Math.max(peak, Math.max(op.u(), op.v()));
        }
        void check(DynamicSchedule schedule) {
            checkArray(schedule.objectives(), objectives, "objectives");
            checkArray(schedule.factoryMakespan(), makespan, "factory makespan");
            checkArray(schedule.factoryEnergy(), energy, "factory energy");
            checkArray(schedule.factoryCost(), labor, "factory labor");
            double max = 0;
            for (double[][] factory : exposure) for (double[] stage : factory) for (double worker : stage) max = Math.max(max, worker);
            close(schedule.totalExposure(), totalExposure, "total exposure");
            close(schedule.maxExposure(), max, "maximum worker exposure");
            close(schedule.peakFatigue(), peak, "peak fatigue");
        }
    }
}
