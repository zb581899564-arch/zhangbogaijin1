package org.uma.jmetal.util.research.modelglobal;

import java.util.Arrays;
import java.util.Random;

/** Independent per-factory random keys preserve physical factory chains, and may alter global interleaving. */
public final class FactoryKeyReencoder {
    private FactoryKeyReencoder() { }

    public static TypedScheduleGenome apply(FirstStageCatalog domain, TypedScheduleGenome source, Random noise) {
        FourVectors input = source.toVectors(); int[] jobs = input.jobs(), factories = input.factories();
        int[] resources = TypedScheduleGenome.fromVectors(domain, input).allocations();
        double[] keys = new double[domain.jobs()];
        for (int f = 0; f < domain.factories(); f++) {
            int size = 0; for (int value : factories) if (value == f) size++;
            double[] ordered = new double[size];
            for (int p = 0; p < size; p++) {
                ordered[p] = noise.nextDouble();
                if (ordered[p] == 0) throw new IllegalStateException("Finite RNG hit open-interval endpoint; retain failure, no redraw");
            }
            Arrays.sort(ordered);
            for (int p = 1; p < size; p++) if (ordered[p] == ordered[p - 1])
                throw new IllegalStateException("Finite RNG key collision; retain failure, no redraw");
            int rank = 0; for (int p = 0; p < jobs.length; p++) if (factories[p] == f) keys[jobs[p]] = ordered[rank++];
        }
        return TypedScheduleGenome.of(domain, resources, keys);
    }
}
