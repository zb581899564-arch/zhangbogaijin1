package org.uma.jmetal.util.research.modelglobal;

import java.util.*;

/** Explicit proposal units; job-level linkage learning itself is unchanged. */
public final class PaTypedTerm {
    public enum Kind { JOBS, RESOURCE, MACHINE, WORKER, ORDER }
    public enum Basis { ATOM, TYPED, SHAM_BLOCK }
    public final Kind kind;
    private final int[] jobs;
    public PaTypedTerm(Kind type, int[] subset) { kind=type; jobs=subset.clone(); }
    public int[] jobs() { return jobs.clone(); }
    public boolean conditional() { return kind==Kind.MACHINE || kind==Kind.WORKER || kind==Kind.ORDER; }
    public static List<PaTypedTerm> expand(List<int[]> jobsets, int jobs, Basis basis) {
        List<PaTypedTerm> result = new ArrayList<>();
        for (int[] subset:jobsets) result.add(new PaTypedTerm(Kind.JOBS,subset));
        if (basis!=Basis.ATOM) for (Kind kind:Kind.values()) if (kind!=Kind.JOBS)
            for (int j=0;j<jobs;j++) result.add(new PaTypedTerm(kind,new int[]{j}));
        return result;
    }
}
