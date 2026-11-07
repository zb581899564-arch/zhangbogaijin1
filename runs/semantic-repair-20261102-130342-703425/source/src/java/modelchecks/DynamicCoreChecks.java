package org.uma.jmetal.util.research.modelchecks;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.util.List;
import java.util.Random;
import org.uma.jmetal.util.research.model.DynamicDecoder;
import org.uma.jmetal.util.research.model.DynamicParameters;
import org.uma.jmetal.util.research.model.DynamicPrefix;
import org.uma.jmetal.util.research.model.DynamicSchedule;
import org.uma.jmetal.util.research.model.DynamicStep;
import org.uma.jmetal.util.research.model.DynamicValidator;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.model.ModelKind;

/** Focused dynamic-core checks, without running an optimizer or changing frozen evidence. */
public final class DynamicCoreChecks {
    private DynamicCoreChecks() { }

    public static void main(String[] args) throws Exception {
        handAnchor(); recoveryAnchor(); stableTieAnchor();
        Instance in = fixture(); DynamicParameters p = DynamicParameters.uniform(in, .02, .03, .9, .2);
        int[][] genome = initialGenome(in); Random random = new Random(20261101L);
        DynamicSchedule previous = DynamicDecoder.full(in, p, genome[0], genome[1], genome[2], genome[3], null);
        for (int trial = 0; trial < 240; trial++) {
            mutate(in, genome, random, trial % 3);
            DynamicSchedule full = DynamicDecoder.full(in, p, genome[0], genome[1], genome[2], genome[3], null);
            DynamicSchedule inc = DynamicDecoder.incremental(in, p, genome[0], genome[1], genome[2], genome[3], previous, null, null);
            DynamicValidator.validate(in, p, full); DynamicValidator.validate(in, p, inc);
            same(full, inc);
            DynamicPrefix prefix = new DynamicPrefix(in, p);
            int prefixLength = trial % (in.jobs() + 1);
            for (int pos = 0; pos < prefixLength; pos++) {
                DynamicStep preview = prefix.preview(genome[0][pos], genome[1][pos], genome[2][pos], genome[3][pos]);
                require(prefix.size() == pos, "Preview mutated prefix");
                sameStep(preview, prefix.append(genome[0][pos], genome[1][pos], genome[2][pos], genome[3][pos]));
            }
            DynamicPrefix copy = prefix.copy();
            double[] before = prefix.partialObjectives();
            if (prefixLength < in.jobs()) copy.append(genome[0][prefixLength], genome[1][prefixLength], genome[2][prefixLength], genome[3][prefixLength]);
            require(prefix.size() == prefixLength, "Copy mutated parent size"); bits(before, prefix.partialObjectives());
            DynamicSchedule constructed = DynamicDecoder.incremental(in, p, genome[0], genome[1], genome[2], genome[3], previous, prefix, null);
            same(full, constructed); require(constructed.reusedOperations() >= prefixLength, "Chosen steps were redone");
            previous = full;
        }
        reuseAndContext(in, p, genome, previous);
        System.out.println("DYNAMIC_CORE_CHECKS_PASS: hand/recovery/stable-tie anchors; 240 changed-FA/resource/order full-incremental checks; prefix replay/copy; immutable serialization/context; checkpoints/cancellation");
    }

    private static void handAnchor() {
        double[][][] speed = {{{2, 2}}}, power = {{{5, 5}}}, standby = {{{7, 7}}};
        Instance in = new Instance("dynamic-hand", ModelKind.CHAPTER4_DUAL_RESOURCE,
                new double[][] {{12}}, new double[][] {{2}}, speed, power, standby,
                new double[][][] {{{2}}}, new double[][][] {{{20}}}, "synthetic-hand");
        DynamicParameters p = DynamicParameters.uniform(in, 0, 0, 2, .5);
        DynamicSchedule schedule = DynamicDecoder.full(in, p, new int[] {0}, new int[] {0}, new int[] {0}, new int[] {0}, null);
        bits(schedule.objectives(), new double[] {8, 40, 160});
        DynamicStep op = schedule.steps().get(0);
        bits(new double[] {op.base(), op.setupDuration(), op.exposure()}, new double[] {4, 2, 4});
        DynamicValidator.validate(in, p, schedule);
        DynamicParameters tiny = DynamicParameters.uniform(in, 1e-20, 0, 0, 0);
        DynamicSchedule tinySchedule = DynamicDecoder.full(in, tiny, new int[] {0}, new int[] {0}, new int[] {0}, new int[] {0}, null);
        require(tinySchedule.totalExposure() > 0, "Tiny-alpha integral lost all significant digits");
        DynamicValidator.validate(in, tiny, tinySchedule);
    }

    private static void recoveryAnchor() {
        Instance in = new Instance("dynamic-recovery", ModelKind.CHAPTER4_DUAL_RESOURCE,
                new double[][] {{4}, {10}, {2}}, new double[][] {{0}, {0}, {0}},
                new double[][][] {{{1, 1}}}, new double[][][] {{{1, 1}}}, new double[][][] {{{3, 3}}},
                new double[][][] {{{1, 1}}}, new double[][][] {{{1, 1}}}, "synthetic-recovery");
        DynamicParameters p = DynamicParameters.uniform(in, 0, Math.log(2), 1, .5);
        DynamicSchedule schedule = DynamicDecoder.full(in, p, new int[] {0, 1, 2}, new int[] {0, 0, 0}, new int[] {0, 1, 1}, new int[] {0, 1, 0}, null);
        DynamicStep last = schedule.steps().get(2);
        require(Math.abs(last.u() - 1.0 / 1024) < 1e-15, "Wrong recovery interval");
        require(Math.abs(last.exposure() - last.u() * last.duration()) < 1e-15, "Exposure includes idle gap");
        DynamicValidator.validate(in, p, schedule);
    }

    private static void stableTieAnchor() {
        double[][][] resources = {{{1, 1}, {1, 1}, {1, 1}}};
        Instance in = new Instance("dynamic-ties", ModelKind.CHAPTER4_DUAL_RESOURCE,
                new double[][] {{2, 2, 1}, {1, 3, 1}}, new double[][] {{0, 0, 0}, {0, 0, 0}},
                resources, resources, resources, resources, resources, "synthetic-stable-ties");
        DynamicParameters p = DynamicParameters.uniform(in, 0, 0, 0, 0);
        DynamicSchedule result = DynamicDecoder.full(in, p, new int[] {0, 1}, new int[] {0, 0},
                new int[] {0, 1}, new int[] {0, 1}, null);
        require(result.steps().get(2).job() == 1 && result.steps().get(3).job() == 0, "Wrong completion FIFO");
        require(result.steps().get(4).job() == 1 && result.steps().get(5).job() == 0, "Tie lost preceding-stage order");
        require(result.steps().get(4).machine() == 0 && result.steps().get(4).worker() == 0, "Wrong lowest-id resource tie");
        DynamicValidator.validate(in, p, result);
    }

    private static void reuseAndContext(Instance in, DynamicParameters p, int[][] g, DynamicSchedule previous) throws Exception {
        final int[] boundaries = {0};
        Runnable checkpoint = new Runnable() { public void run() { boundaries[0]++; } };
        DynamicSchedule same = DynamicDecoder.incremental(in, p, g[0], g[1], g[2], g[3], previous, null, checkpoint);
        require(same.recomputedOperations() == 0 && same.reusedOperations() == in.jobs() * in.stages(), "Unchanged factories were redone");
        require(boundaries[0] == in.jobs() * in.stages(), "Missing reused-operation checkpoints");
        final RuntimeException cancelled = new RuntimeException("intentional-checkpoint-stop");
        boolean propagated = false;
        try { DynamicDecoder.incremental(in, p, g[0], g[1], g[2], g[3], previous, null,
                new Runnable() { public void run() { throw cancelled; } }); }
        catch (RuntimeException expected) { propagated = expected == cancelled; }
        require(propagated, "Checkpoint cancellation was swallowed");
        DynamicValidator.validate(in, p, previous);
        DynamicSchedule restored = serialized(previous);
        same(previous, DynamicDecoder.incremental(in, p, g[0], g[1], g[2], g[3], restored, null, null));
        double[] objectives = previous.objectives(); objectives[0] = -1;
        int[] js = previous.js(); js[0] = -1; require(previous.js()[0] >= 0, "Mutable genome getter");
        boolean rejected = false;
        try { previous.steps().clear(); } catch (UnsupportedOperationException expected) { rejected = true; }
        require(rejected && previous.objectives()[0] >= 0, "Mutable schedule getter");
        rejected = false;
        try { DynamicDecoder.incremental(in, DynamicParameters.uniform(in, .02, .03, .8, .2), g[0], g[1], g[2], g[3], previous, null, null); }
        catch (IllegalArgumentException expected) { rejected = true; }
        require(rejected, "Incompatible parameter cache accepted");
        DynamicPrefix wrong = new DynamicPrefix(in, p);
        wrong.append(g[0][1], g[1][1], g[2][1], g[3][1]);
        rejected = false;
        try { DynamicDecoder.incremental(in, p, g[0], g[1], g[2], g[3], previous, wrong, null); }
        catch (IllegalArgumentException expected) { rejected = true; }
        require(rejected, "Wrong constructed prefix accepted");
    }

    private static DynamicSchedule serialized(DynamicSchedule schedule) throws Exception {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        ObjectOutputStream output = new ObjectOutputStream(bytes); output.writeObject(schedule); output.close();
        ObjectInputStream input = new ObjectInputStream(new ByteArrayInputStream(bytes.toByteArray()));
        DynamicSchedule restored = (DynamicSchedule) input.readObject(); input.close(); return restored;
    }

    private static void same(DynamicSchedule a, DynamicSchedule b) {
        bits(a.objectives(), b.objectives()); bits(a.factoryMakespan(), b.factoryMakespan());
        bits(a.factoryEnergy(), b.factoryEnergy()); bits(a.factoryCost(), b.factoryCost());
        bits(new double[] {a.totalExposure(), a.maxExposure(), a.peakFatigue()}, new double[] {b.totalExposure(), b.maxExposure(), b.peakFatigue()});
        List<DynamicStep> x = a.steps(), y = b.steps(); require(x.size() == y.size(), "Different operation count");
        for (int i = 0; i < x.size(); i++) sameStep(x.get(i), y.get(i));
    }

    private static void sameStep(DynamicStep x, DynamicStep y) {
        require(x.job() == y.job() && x.factory() == y.factory() && x.stage() == y.stage()
                && x.machine() == y.machine() && x.worker() == y.worker(), "Different operation bindings");
        bits(new double[] {x.start(), x.base(), x.duration(), x.setupDuration(), x.completion(), x.u(), x.v(), x.energy(), x.labor(), x.exposure()},
                new double[] {y.start(), y.base(), y.duration(), y.setupDuration(), y.completion(), y.u(), y.v(), y.energy(), y.labor(), y.exposure()});
    }

    private static void bits(double[] a, double[] b) {
        require(a.length == b.length, "Different vector length");
        for (int i = 0; i < a.length; i++) require(Double.doubleToLongBits(a[i]) == Double.doubleToLongBits(b[i]), "Different double at " + i);
    }

    private static int[][] initialGenome(Instance in) {
        int[][] result = new int[4][in.jobs()];
        for (int j = 0; j < in.jobs(); j++) { result[0][j] = j; result[1][j] = j % in.factories(); }
        return result;
    }

    private static void mutate(Instance in, int[][] g, Random random, int mode) {
        int a = random.nextInt(in.jobs()), b = random.nextInt(in.jobs());
        if (mode == 0) {
            for (int row = 0; row < 4; row++) { int value = g[row][a]; g[row][a] = g[row][b]; g[row][b] = value; }
        } else if (mode == 1) {
            int f = g[1][a]; g[1][a] = g[1][b]; g[1][b] = f;
            for (int pos : new int[] {a, b}) { g[2][pos] %= in.machines(g[1][pos], 0); g[3][pos] %= in.workers(g[1][pos], 0); }
        } else {
            g[2][a] = random.nextInt(in.machines(g[1][a], 0)); g[3][a] = random.nextInt(in.workers(g[1][a], 0));
        }
    }

    private static Instance fixture() {
        int n = 8, factories = 2, stages = 3;
        double[][] processing = new double[n][stages], setup = new double[n][stages];
        for (int j = 0; j < n; j++) for (int k = 0; k < stages; k++) { processing[j][k] = 2 + (j + k) % 5; setup[j][k] = (j + 2 * k) % 3; }
        double[][][] speed = new double[factories][stages][], power = new double[factories][stages][];
        double[][][] standby = new double[factories][stages][], efficiency = new double[factories][stages][], cost = new double[factories][stages][];
        for (int f = 0; f < factories; f++) for (int k = 0; k < stages; k++) {
            int machines = 2 + (f + k) % 2, workers = 1 + (f + k) % 2;
            speed[f][k] = new double[machines]; power[f][k] = new double[machines]; standby[f][k] = new double[machines];
            for (int m = 0; m < machines; m++) { speed[f][k][m] = 1 + .1 * m; power[f][k][m] = 3 + m; standby[f][k][m] = .5; }
            efficiency[f][k] = new double[workers]; cost[f][k] = new double[workers];
            for (int w = 0; w < workers; w++) { efficiency[f][k][w] = .9 + .2 * w; cost[f][k][w] = 2 + w; }
        }
        return new Instance("dynamic-fixture", ModelKind.CHAPTER4_DUAL_RESOURCE, processing, setup,
                speed, power, standby, efficiency, cost, "synthetic-heterogeneous");
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
}
