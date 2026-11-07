package org.uma.jmetal.util.research.classic;

/** Focused mechanism/engineering checks, not an algorithm performance benchmark. */
public final class ClassicChecks {
    private ClassicChecks() { }
    public static void main(String[] args) {
        ClassicMathChecks.run();
        ClassicRuntimeChecks.run();
        System.out.println("CLASSIC_CHECKS_PASS mathematical-selection,job-aligned-variation,legal-genomes,parent-independence,paid-FE,interruptions,seed-replay");
    }
    static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
    static void close(double actual, double expected) {
        require(Math.abs(actual - expected) <= 1e-10 * Math.max(1, Math.abs(expected)), actual + " != " + expected);
    }
}
