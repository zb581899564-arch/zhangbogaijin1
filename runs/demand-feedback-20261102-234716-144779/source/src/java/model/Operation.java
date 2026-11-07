package org.uma.jmetal.util.research.model;

/** One uninterrupted machine and worker reservation, including setup. */
public final class Operation implements java.io.Serializable {
    private static final long serialVersionUID = 1L;
    private final int job, factory, stage, machine, worker;
    private final double start, duration, setupDuration;
    public Operation(int job, int factory, int stage, int machine, int worker,
            double start, double duration, double setupDuration) {
        this.job = job; this.factory = factory; this.stage = stage;
        this.machine = machine; this.worker = worker;
        this.start = start; this.duration = duration; this.setupDuration = setupDuration;
    }
    public int job() { return job; }
    public int factory() { return factory; }
    public int stage() { return stage; }
    public int machine() { return machine; }
    public int worker() { return worker; }
    public double start() { return start; }
    public double end() { return start + duration; }
    public double duration() { return duration; }
    public double setupDuration() { return setupDuration; }
    public double processingStart() { return start + setupDuration; }
    Operation shifted(double newStart) {
        return new Operation(job, factory, stage, machine, worker, newStart, duration, setupDuration);
    }
}
