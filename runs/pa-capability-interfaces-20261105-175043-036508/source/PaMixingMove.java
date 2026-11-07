package org.uma.jmetal.util.research.modelglobal;

/** Stored keys and complete categorical tuples are copied together; no reranking or repair. */
public final class PaMixingMove {
    public final TypedScheduleGenome genome;
    public final boolean fallback;

    private PaMixingMove(TypedScheduleGenome value, boolean unchanged) { genome = value; fallback = unchanged; }

    public static PaMixingMove apply(FirstStageCatalog domain, TypedScheduleGenome receiver,
            TypedScheduleGenome donor, int[] subset) {
        int[] resources = receiver.allocations(), incoming = donor.allocations();
        double[] keys = receiver.priorities(), incomingKeys = donor.priorities();
        boolean[] seen = new boolean[domain.jobs()];
        for (int job : subset) {
            FirstStageCatalog.range(job, domain.jobs(), "subset job");
            if (seen[job]) throw new IllegalArgumentException("Repeated subset job"); seen[job] = true;
            resources[job] = incoming[job]; keys[job] = incomingKeys[job];
        }
        boolean[] present = new boolean[domain.factories()]; for (int resource : resources) present[domain.factory(resource)] = true;
        for (boolean value : present) if (!value) return new PaMixingMove(receiver, true);
        return new PaMixingMove(TypedScheduleGenome.of(domain, resources, keys), false);
    }
}
