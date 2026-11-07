package org.uma.jmetal.util.research.modelglobal;

/** Type-safe field exchange; no repair, quality filter or unpaid retry. */
public final class PaTypedMove {
    public final TypedScheduleGenome genome;
    public final boolean fallback;
    private PaTypedMove(TypedScheduleGenome value,boolean rejected) { genome=value; fallback=rejected; }
    public static PaTypedMove apply(FirstStageCatalog catalog,TypedScheduleGenome parent,TypedScheduleGenome donor,
            PaTypedTerm term,PaTypedTerm.Basis basis,boolean noDonor) {
        if (noDonor) return new PaTypedMove(parent,false);
        if (term.kind==PaTypedTerm.Kind.JOBS || basis==PaTypedTerm.Basis.SHAM_BLOCK) {
            PaMixingMove move=PaMixingMove.apply(catalog,parent,donor,term.jobs());
            return new PaTypedMove(move.genome,move.fallback);
        }
        int job=term.jobs()[0]; int[] resources=parent.allocations(); double[] keys=parent.priorities();
        int[] a=catalog.tuple(resources[job]), b=catalog.tuple(donor.allocationAt(job));
        if (term.conditional() && a[0]!=b[0]) throw new IllegalArgumentException("Incompatible typed donor");
        switch (term.kind) {
            case RESOURCE: resources[job]=donor.allocationAt(job); break;
            case MACHINE: resources[job]=catalog.id(a[0],b[1],a[2]); break;
            case WORKER: resources[job]=catalog.id(a[0],a[1],b[2]); break;
            case ORDER: keys[job]=donor.priorityAt(job); break;
            default: throw new IllegalStateException("Unsupported term");
        }
        boolean[] present=new boolean[catalog.factories()]; for(int r:resources)present[catalog.factory(r)]=true;
        for(boolean value:present)if(!value)return new PaTypedMove(parent,true);
        return new PaTypedMove(TypedScheduleGenome.of(catalog,resources,keys),false);
    }
}
