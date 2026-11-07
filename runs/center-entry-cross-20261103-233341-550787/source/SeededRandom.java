package org.uma.jmetal.util.research.runtime;

import java.util.Collections;
import java.util.List;
import java.util.Random;
import org.uma.jmetal.util.pseudorandom.JMetalRandom;
import org.uma.jmetal.util.pseudorandom.PseudoRandomGenerator;

/** One deterministic random stream per single-threaded JVM run. */
public final class SeededRandom {
    private static Random random;
    private static Thread owner;
    private static long seed;

    private SeededRandom() { }

    public static void reset(long runSeed) {
        owner = Thread.currentThread();
        seed = runSeed;
        random = new Random(runSeed);
        JMetalRandom.getInstance().setRandomGenerator(new SharedGenerator());
    }

    public static Random current() {
        if (random == null || Thread.currentThread() != owner) {
            throw new IllegalStateException("Call SeededRandom.reset(seed) on the run's sole thread first");
        }
        return random;
    }

    public static void restoreForCenterReplay(Random state) {
        current();
        random = java.util.Objects.requireNonNull(state);
    }
    public static long seed() { current(); return seed; }
    public static <T> void shuffle(List<T> values) { Collections.shuffle(values, current()); }

    private static final class SharedGenerator implements PseudoRandomGenerator {
        private static final long serialVersionUID = 1L;
        @Override public int nextInt(int lower, int upper) {
            if (upper < lower) { throw new IllegalArgumentException("Invalid integer bounds"); }
            long range = (long) upper - lower + 1;
            if (range <= Integer.MAX_VALUE) { return lower + current().nextInt((int) range); }
            int value;
            do { value = current().nextInt(); } while (value < lower || value > upper);
            return value;
        }
        @Override public double nextDouble() { return current().nextDouble(); }
        @Override public double nextDouble(double lower, double upper) {
            if (!(lower <= upper)) { throw new IllegalArgumentException("Invalid double bounds"); }
            return lower + (upper - lower) * nextDouble();
        }
        @Override public void setSeed(long value) { current().setSeed(value); seed = value; }
        @Override public long getSeed() { return seed(); }
        @Override public String getName() { return "ResearchSharedJavaRandom"; }
    }
}
