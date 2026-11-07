package org.uma.jmetal.util.research.search;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;

/** Read-only search observation; disabled hooks do not attach attributes or consume RNG. */
public final class SharedSurvivalTrace {
    private static final boolean ENABLED=Boolean.getBoolean("research.survival.trace");
    private static SharedAncestry ancestry;
    private static int generation,batch;
    private static Proposal pending;
    private static String stage;
    private static int parent;
    private static long nanos;
    private static final List<String> pools=new ArrayList<>(),localEntries=new ArrayList<>(),generationEnds=new ArrayList<>();
    private SharedSurvivalTrace() { }
    private static final class Proposal {
        final PermutationSolution<?> solution;final int parent;final boolean composed;
        Proposal(PermutationSolution<?> s,int p,boolean c){solution=s;parent=p;composed=c;}
    }
    public static void initialize(long limit) {
        if(!ENABLED)return;
        ancestry=new SharedAncestry(Math.toIntExact(limit));
        pools.add("generation,batch,role,index,paidFE,parentFE,lineage,branch,category,isChild,selectedOrder,directComposed,lastComposedAncestor,cmax,tec,twc");
        localEntries.add("generation,atFE,role,paidFE,lastComposedAncestor,lineage,branch");
        generationEnds.add("generation,paidFE,lastComposedAncestor");
    }
    static void generationStarted() {if(ENABLED)generation++;}
    static void generated(PermutationSolution<?> child,PermutationSolution<?> current,boolean composed) {
        if(ENABLED)pending=new Proposal(child,SharedAncestry.id(current),composed);
    }
    static void before(PermutationSolution<?> candidate,String value) {
        if(!ENABLED)return;long start=System.nanoTime();stage=value;
        parent=SharedAncestry.id(candidate);
        if(pending!=null) {
            if(pending.solution!=candidate || !value.equals("global"))throw new AssertionError("Proposal observation mismatch");
            parent=pending.parent;
        }
        // Attach before evaluation so independent external archive copies retain the valid paid id.
        candidate.setAttribute(SharedAncestry.PAID,ancestry.last()+1);nanos+=System.nanoTime()-start;
    }
    public static void paid(PermutationSolution<?> s,long fee,boolean admitted) {
        if(!ENABLED)return;long start=System.nanoTime();
        ancestry.paid(s,Math.toIntExact(fee),parent,pending!=null&&pending.composed,stage,admitted);
        pending=null;nanos+=System.nanoTime()-start;
    }
    static void selected(List<Particle> parents,List<Particle> children,List<Particle> survivors,Direction role) {
        if(!ENABLED)return;long start=System.nanoTime();batch++;
        IdentityHashMap<Particle,Integer> order=new IdentityHashMap<>();Map<Long,Integer> multiplicity=new HashMap<>();
        for(int i=0;i<survivors.size();i++) {
            Particle p=survivors.get(i);order.put(p,i);multiplicity.put(p.lineageId(),multiplicity.getOrDefault(p.lineageId(),0)+1);
        }
        List<Particle> all=new ArrayList<>(parents);all.addAll(children);
        for(int i=0;i<all.size();i++) {
            Particle p=all.get(i);int fe=SharedAncestry.id(p.current);boolean child=i>=parents.size();
            Object family=p.current.getAttribute("cooperation.family");int category=family==null?0:(Integer)family+1;
            int rank=order.getOrDefault(p,-1);
            if(rank>=0)ancestry.selected(fe,multiplicity.get(p.lineageId())>1,child);
            pools.add(generation+","+batch+","+role+","+i+","+fe+","+ancestry.parent(fe)+","+p.lineageId()+","+p.branchId()+","+category+","+child+","+rank+","+ancestry.composed(fe)+","+ancestry.root(fe)+","+p.current.getObjective(0)+","+p.current.getObjective(1)+","+p.current.getObjective(2));
        }
        nanos+=System.nanoTime()-start;
    }
    static void localEntry(Particle particle,Direction role) {
        if(!ENABLED)return;
        int fe=SharedAncestry.id(particle.current);ancestry.localEntry(fe);
        localEntries.add(generation+","+ancestry.last()+","+role+","+fe+","+ancestry.root(fe)+","+particle.lineageId()+","+particle.branchId());
    }
    static void generationEnd(List<PermutationSolution<Integer>> population) {
        if(!ENABLED)return;
        for(PermutationSolution<Integer> s:population) {
            int fe=SharedAncestry.id(s);ancestry.generationEnd(fe);generationEnds.add(generation+","+fe+","+ancestry.root(fe));
        }
    }
    public static Map<String,Object> finish(Path out,List<PermutationSolution<Integer>> finalArchive) throws IOException {
        if(!ENABLED)return Collections.singletonMap("enabled",false);
        Files.write(out.resolve("global-pools.csv"),pools,StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
        Files.write(out.resolve("local-entries.csv"),localEntries,StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
        Files.write(out.resolve("generation-ends.csv"),generationEnds,StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
        Map<String,Object> result=ancestry.finish(finalArchive);result.put("enabled",true);result.put("directObservationSeconds",nanos/1e9);
        result.put("unpaidProposalAtStop",pending!=null);return result;
    }
}
