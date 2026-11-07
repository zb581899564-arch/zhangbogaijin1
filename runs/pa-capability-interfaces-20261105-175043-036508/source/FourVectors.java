package org.uma.jmetal.util.research.modelglobal;

/** Immutable interchange only. Legality is checked against a catalog by TypedScheduleGenome. */
public final class FourVectors {
    private final int[] jobs, factories, machines, workers;

    public FourVectors(int[] js, int[] fa, int[] ma, int[] wa) {
        if (js == null || fa == null || ma == null || wa == null)
            throw new IllegalArgumentException("Four vectors required");
        jobs = js.clone(); factories = fa.clone(); machines = ma.clone(); workers = wa.clone();
    }

    public int[] jobs() { return jobs.clone(); }
    public int[] factories() { return factories.clone(); }
    public int[] machines() { return machines.clone(); }
    public int[] workers() { return workers.clone(); }
}
