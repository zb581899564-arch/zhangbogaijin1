package org.uma.jmetal.util.research.model;

import java.io.Serializable;

/** One immutable append-only transition; exposure integrates fatigue during work only. */
public final class DynamicStep implements Serializable {
    private static final long serialVersionUID = 1L;
    private final int job, factory, stage, machine, worker;
    private final double start, base, duration, setupDuration, completion;
    private final double u, v, energy, labor, exposure;

    DynamicStep(int job, int factory, int stage, int machine, int worker,
            double start, double base, double duration, double setupDuration,
            double u, double v, double energy, double labor, double exposure) {
        this.job = job; this.factory = factory; this.stage = stage;
        this.machine = machine; this.worker = worker;
        this.start = start; this.base = base; this.duration = duration;
        this.setupDuration = setupDuration; this.completion = start + duration;
        this.u = u; this.v = v; this.energy = energy; this.labor = labor;
        this.exposure = exposure;
    }

    public int job() { return job; }
    public int factory() { return factory; }
    public int stage() { return stage; }
    public int machine() { return machine; }
    public int worker() { return worker; }
    public double start() { return start; }
    public double base() { return base; }
    public double duration() { return duration; }
    public double setupDuration() { return setupDuration; }
    public double completion() { return completion; }
    public double u() { return u; }
    public double v() { return v; }
    public double energy() { return energy; }
    public double labor() { return labor; }
    public double exposure() { return exposure; }
}
