package org.uma.jmetal.util.research.runtime;

/** Explicit engineering exception injection; never changes the real clock or acquires an FE. */
public final class GomSyntheticStop {
    private GomSyntheticStop() { }
    public static void stop(RunClock owner) { throw new TimeBudgetExceededException(owner); }
}
