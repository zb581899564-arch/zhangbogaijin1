package org.uma.jmetal.util.research.runtime;

/** Cooperative wall-clock limit. Input loading/compilation precede the measured search. */
public final class RunClock {
    private final double limitSeconds;
    private long startedAt;
    private boolean started;
    private long finishedAt;
    RunClock(double seconds) {
        if (Double.isNaN(seconds) || seconds < 0) throw new IllegalArgumentException("Nonnegative time limit required");
        limitSeconds = seconds;
    }
    void start() { startedAt = System.nanoTime(); started = true; }
    void stop() { finishedAt = System.nanoTime(); }
    public void checkpoint() {
        if (started && elapsedSeconds() >= limitSeconds) throw new TimeBudgetExceededException(this);
    }
    public double elapsedSeconds() {
        return started ? ((finishedAt == 0 ? System.nanoTime() : finishedAt) - startedAt) / 1e9 : 0;
    }
    public double limitSeconds() { return limitSeconds; }
}
