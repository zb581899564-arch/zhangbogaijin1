package org.uma.jmetal.util.research.modelglobal;

/** Proposed joint-domain extension only: every mask also copies complete by-job FMW; no acceptance rule. */
public final class DirectJointMove {
    public enum Kind { POSITION, ORDER }
    public final DirectScheduleGenome genome;
    public final boolean emptyFactoryFallback;

    private DirectJointMove(DirectScheduleGenome value, boolean fallback) {
        genome = value; emptyFactoryFallback = fallback;
    }

    /** A fallback is still a generated attempt; a future search evaluator must charge it. */
    public static DirectJointMove apply(FirstStageCatalog domain, DirectScheduleGenome parent, DirectScheduleGenome donor,
            int[] mask, int reference, Kind kind) {
        if (domain == null || parent == null || donor == null || kind == null
                || !parent.uses(domain) || !donor.uses(domain)) throw new IllegalArgumentException("One common catalog required");
        int[] ranks = kind == Kind.POSITION ? DirectPositionMixing.position(parent.positions(), donor.positions(), mask, reference)
                : DirectPositionMixing.order(parent.positions(), donor.positions(), mask);
        int[] tuples = parent.resources(), incoming = donor.resources();
        for (int job : mask) tuples[job] = incoming[job];
        boolean[] present = new boolean[domain.factories()];
        for (int tuple : tuples) present[domain.factory(tuple)] = true;
        for (boolean value : present) if (!value) return new DirectJointMove(parent, true);
        return new DirectJointMove(DirectScheduleGenome.of(domain, tuples, ranks), false);
    }
}
