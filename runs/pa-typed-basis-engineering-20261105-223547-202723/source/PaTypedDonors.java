package org.uma.jmetal.util.research.modelglobal;

import java.util.*;

/** Static type compatibility only; no objective inspection or candidate evaluation. */
public final class PaTypedDonors {
    public final int slot, eligibleCount, rank;
    private PaTypedDonors(int value,int count,int selected) { slot=value; eligibleCount=count; rank=selected; }
    public static int[] eligible(FirstStageCatalog catalog,List<PaIndividual> population,int receiver,PaTypedTerm term) {
        int[] values=new int[population.size()]; int count=0, job=term.jobs()[0];
        int factory=catalog.factory(population.get(receiver).genome.allocationAt(job));
        for (int i=0;i<population.size();i++) if (i!=receiver && (!term.conditional()
                || catalog.factory(population.get(i).genome.allocationAt(job))==factory)) values[count++]=i;
        return Arrays.copyOf(values,count);
    }
    public static PaTypedDonors choose(FirstStageCatalog catalog,List<PaIndividual> population,int receiver,PaTypedTerm term,Random noise) {
        if (!term.conditional()) {
            if(population.size()==1) return new PaTypedDonors(-1,0,-1);
            int rank=noise.nextInt(population.size()-1), slot=rank>=receiver?rank+1:rank;
            return new PaTypedDonors(slot,population.size()-1,rank);
        }
        int[] choices=eligible(catalog,population,receiver,term);
        if (choices.length==0) return new PaTypedDonors(-1,0,-1);
        int rank=noise.nextInt(choices.length); return new PaTypedDonors(choices[rank],choices.length,rank);
    }
}
