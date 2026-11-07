package org.uma.jmetal.util.research.model;

import java.util.List;

/** Independent timeline constraints; throws on invalid schedules rather than repairing silently. */
public final class Validator {
    private static final double EPS = 1e-7;
    private Validator() { }
    public static void validate(Instance in, Schedule schedule) {
        List<Operation> ops = schedule.operations();
        if (ops.size() != in.jobs() * in.stages()) fail("Missing or extra operations");
        Operation[][] byJob = new Operation[in.jobs()][in.stages()];
        for (Operation op : ops) {
            if (byJob[op.job()][op.stage()] != null) fail("Duplicate operation");
            byJob[op.job()][op.stage()] = op;
            if (!Double.isFinite(op.start()) || op.start() < -EPS || !Double.isFinite(op.end())
                    || !Double.isFinite(op.duration()) || op.duration() <= 0) fail("Invalid interval");
            if (Math.abs(op.duration() - in.duration(op.job(), op.factory(), op.stage(), op.machine(), op.worker())) > EPS) fail("Wrong duration");
            double setup = in.setup(op.job(), op.stage()) / in.efficiency(op.factory(), op.stage(), op.worker());
            if (!Double.isFinite(op.setupDuration()) || Math.abs(op.setupDuration() - setup) > EPS) fail("Wrong setup interval");
        }
        for (int j = 0; j < in.jobs(); j++) for (int k = 1; k < in.stages(); k++) {
            Operation before = byJob[j][k - 1], after = byJob[j][k];
            if (before == null || after == null || before.factory() != after.factory()) fail("Missing stage or factory transfer");
            if (before.end() > after.start() + EPS) fail("Stage precedence violation");
        }
        for (int i = 0; i < ops.size(); i++) for (int j = i + 1; j < ops.size(); j++) {
            Operation a = ops.get(i), b = ops.get(j);
            if (a.factory() != b.factory()) continue;
            boolean sameStage = a.stage() == b.stage();
            boolean sameMachine = sameStage && a.machine() == b.machine();
            boolean sameWorker = a.worker() == b.worker()
                    && (sameStage || in.kind() == ModelKind.CHAPTER3_FIXED_WORKER);
            if (in.kind() == ModelKind.CHAPTER3_FIXED_WORKER && sameMachine != sameWorker) fail("Fixed worker binding violated");
            if ((sameMachine || sameWorker) && a.start() < b.end() - EPS && b.start() < a.end() - EPS) fail("Resource overlap");
        }
        for (double value : schedule.objectives()) if (!Double.isFinite(value) || value < -EPS) fail("Invalid objective");
    }
    private static void fail(String message) { throw new IllegalStateException(message); }
}
