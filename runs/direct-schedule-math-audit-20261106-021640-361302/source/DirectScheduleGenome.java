package org.uma.jmetal.util.research.modelglobal;

/** Immutable by-job complete FMW tuples and an exact inverse global permutation; no search or repair. */
public final class DirectScheduleGenome {
    private final FirstStageCatalog catalog;
    private final int[] resources, positions;

    private DirectScheduleGenome(FirstStageCatalog domain, int[] tuples, int[] ranks) {
        if (domain == null || tuples == null || ranks == null
                || tuples.length != domain.jobs() || ranks.length != domain.jobs())
            throw new IllegalArgumentException("N tuples and N positions required");
        DirectPositionMixing.requirePermutation(ranks);
        boolean[] present = new boolean[domain.factories()];
        for (int resource : tuples) present[domain.factory(resource)] = true;
        for (boolean value : present) if (!value) throw new IllegalArgumentException("Empty factory");
        catalog = domain; resources = tuples.clone(); positions = ranks.clone();
    }

    public static DirectScheduleGenome of(FirstStageCatalog domain, int[] tuples, int[] ranks) {
        return new DirectScheduleGenome(domain, tuples, ranks);
    }

    public static DirectScheduleGenome fromVectors(FirstStageCatalog domain, FourVectors input) {
        if (domain == null || input == null) throw new IllegalArgumentException("Catalog and vectors required");
        int n = domain.jobs(); int[] js = input.jobs(), fa = input.factories(), ma = input.machines(), wa = input.workers();
        if (js.length != n || fa.length != n || ma.length != n || wa.length != n)
            throw new IllegalArgumentException("Four vectors must have N positions");
        int[] ranks = DirectPositionMixing.inverse(js), tuples = new int[n];
        for (int p = 0; p < n; p++) tuples[js[p]] = domain.id(fa[p], ma[p], wa[p]);
        return of(domain, tuples, ranks);
    }

    public int[] resources() { return resources.clone(); }
    public int[] positions() { return positions.clone(); }
    boolean uses(FirstStageCatalog domain) { return catalog == domain; }

    public FourVectors toVectors() {
        int[] js = DirectPositionMixing.inverse(positions), fa = new int[js.length], ma = new int[js.length], wa = new int[js.length];
        for (int p = 0; p < js.length; p++) {
            int[] tuple = catalog.tuple(resources[js[p]]); fa[p] = tuple[0]; ma[p] = tuple[1]; wa[p] = tuple[2];
        }
        return new FourVectors(js, fa, ma, wa);
    }
}
