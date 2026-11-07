package org.uma.jmetal.util.research.modelglobal;

import java.util.*;

/** Deterministic structural fixtures; objectives are never read for selecting a case. */
public final class PaTypedFixtureCases {
    public final int receiver, donor;
    public final PaTypedTerm term;
    private PaTypedFixtureCases(int r,int d,PaTypedTerm t){receiver=r;donor=d;term=t;}
    public static List<PaTypedFixtureCases> make(FirstStageCatalog domain,List<PaIndividual> initial){
        List<PaTypedFixtureCases> result=new ArrayList<>();
        for(PaTypedTerm.Kind kind:PaTypedTerm.Kind.values())if(kind!=PaTypedTerm.Kind.JOBS){
            PaTypedTerm empty=new PaTypedTerm(kind,new int[]{0});
            if(PaTypedDonors.choose(domain,Collections.singletonList(initial.get(0)),0,empty,new Random(1)).slot!=-1)
                throw new AssertionError("Empty compatible pool must have no donor");
            result.add(new PaTypedFixtureCases(0,-1,empty));
            for(int k=1;k<16;k++)result.add(select(domain,initial,kind,(k-1)%domain.jobs(),k==1));
        }
        return result;
    }
    private static PaTypedFixtureCases select(FirstStageCatalog domain,List<PaIndividual> initial,PaTypedTerm.Kind kind,int first,boolean allJobs){
        PaTypedFixtureCases fallback=null;
        for(int offset=0;offset<(allJobs?domain.jobs():1);offset++){
            int job=(first+offset)%domain.jobs();PaTypedTerm term=new PaTypedTerm(kind,new int[]{job});
            Set<Integer> seen=new HashSet<>();for(PaIndividual p:initial)seen.add(p.genome.allocationAt(job));
            for(int r=0;r<initial.size();r++)for(int d:PaTypedDonors.eligible(domain,initial,r,term)){
                TypedScheduleGenome parent=initial.get(r).genome,donor=initial.get(d).genome;
                int[] a=domain.tuple(parent.allocationAt(job)),b=domain.tuple(donor.allocationAt(job));
                int resource=kind==PaTypedTerm.Kind.RESOURCE?donor.allocationAt(job)
                    :kind==PaTypedTerm.Kind.MACHINE?domain.id(a[0],b[1],a[2])
                    :kind==PaTypedTerm.Kind.WORKER?domain.id(a[0],a[1],b[2]):parent.allocationAt(job);
                PaTypedFixtureCases candidate=new PaTypedFixtureCases(r,d,term);
                boolean changed=resource!=parent.allocationAt(job)
                    || kind==PaTypedTerm.Kind.ORDER && donor.priorityAt(job)!=parent.priorityAt(job);
                boolean empty=false;
                if(kind==PaTypedTerm.Kind.RESOURCE && a[0]!=b[0]){
                    int count=0;for(int j=0;j<domain.jobs();j++)if(domain.factory(parent.allocationAt(j))==a[0])count++;
                    empty=count==1;
                }
                if(fallback==null && changed && !empty)fallback=candidate;
                if((kind==PaTypedTerm.Kind.MACHINE || kind==PaTypedTerm.Kind.WORKER)
                        && !seen.contains(resource))return candidate;
                if(changed && !empty && kind!=PaTypedTerm.Kind.MACHINE && kind!=PaTypedTerm.Kind.WORKER)return candidate;
            }
        }
        if(fallback!=null)return fallback;
        PaTypedTerm term=new PaTypedTerm(kind,new int[]{first});int[] eligible=PaTypedDonors.eligible(domain,initial,0,term);
        return new PaTypedFixtureCases(0,eligible.length==0?-1:eligible[0],term);
    }
}
