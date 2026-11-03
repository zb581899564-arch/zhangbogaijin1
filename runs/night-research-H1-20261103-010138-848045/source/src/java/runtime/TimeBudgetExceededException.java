package org.uma.jmetal.util.research.runtime;

/** A normal stop only for the run that owns this clock. */
public final class TimeBudgetExceededException extends RuntimeException {
    private static final long serialVersionUID = 1L;
    private final RunClock clock;
    TimeBudgetExceededException(RunClock clock) { super("Wall-clock budget exhausted"); this.clock = clock; }
    boolean belongsTo(RunClock expected) { return clock == expected; }
}
