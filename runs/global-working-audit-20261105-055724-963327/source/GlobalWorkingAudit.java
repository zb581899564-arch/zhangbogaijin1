package org.uma.jmetal.util.research.search;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.ThreeObjectiveArchive;
import research.dynamic.DynamicJson;

/** Read-only within-generation working-pool observation; no attributes, RNG or search feedback. */
public final class GlobalWorkingAudit {
    private static final boolean ENABLED=Boolean.getBoolean("research.working.capture");
    private static final Map<Direction,List<Particle>> working=new EnumMap<>(Direction.class);
    private static final Map<String,Long> known=new HashMap<>();
    private static final List<Map<String,Object>> snapshots=new ArrayList<>();
    private static int generation,step;private static long paid,lastOfBatch;
    private static Direction activeRole;private static double[][] archive;
    private GlobalWorkingAudit() { }

    public static void paid(PermutationSolution<?> s,long value,ThreeObjectiveArchive<?> source) {
        if(!ENABLED)return;paid=value;known.putIfAbsent(key(s),value);
        if(generation==1&&value==lastOfBatch)archive=source.objectiveSnapshot();
    }
    static void generationStarted(Map<Direction,List<Particle>> groups) {
        if(!ENABLED)return;generation++;working.clear();
        for(Direction role:Direction.values())working.put(role,new ArrayList<>(groups.get(role)));
    }
    static void beforeBatch(Direction role,int value,List<Particle> current) {
        if(!ENABLED)return;activeRole=role;step=value;working.put(role,new ArrayList<>(current));
        lastOfBatch=generation==1&&(step==0||step==24||step==49)?paid+current.size():-1;
        archive=null;
    }
    static void selected(List<Particle> parents,List<Particle> children,List<Particle> actual,Direction role) {
        if(!ENABLED)return;
        if(role!=activeRole)throw new AssertionError("Physical and preference role differ in this fixed SPECIAL audit");
        if(generation==1&&(step==0||step==24||step==49))capture(parents,children,actual);
        working.put(role,new ArrayList<>(actual));
    }

    private static void capture(List<Particle> parents,List<Particle> children,List<Particle> selected) {
        if(paid!=lastOfBatch||archive==null)throw new AssertionError("Wrong paid working-pool boundary");
        List<Particle> allParents=new ArrayList<>(),others=new ArrayList<>();
        for(Direction role:Direction.values()) {
            allParents.addAll(working.get(role));if(role!=activeRole)others.addAll(working.get(role));
        }
        if(allParents.size()!=100||parents.size()!=children.size())throw new AssertionError("Working-pool size changed");
        List<Particle> candidate=new ArrayList<>(allParents);candidate.addAll(children);
        List<Particle> actual=new ArrayList<>(others);actual.addAll(selected);
        List<Particle> local=new ArrayList<>(parents);local.addAll(children);
        List<Particle> within=WorkingPoolSelection.select(local,WorkingPoolSelection.quotas(parents));
        if(activeRole==Direction.CENTER&&!within.equals(selected))throw new AssertionError("Within-ALL scorer differs from actual CENTER");
        List<Particle> withinAll=new ArrayList<>(others);withinAll.addAll(within);
        int[] quotas=WorkingPoolSelection.quotas(allParents);
        List<Particle> global=WorkingPoolSelection.select(candidate,quotas);
        if(!Arrays.equals(quotas,WorkingPoolSelection.quotas(actual))||!Arrays.equals(quotas,WorkingPoolSelection.quotas(withinAll)))
            throw new AssertionError("Counterfactual changed overall family counts");
        IdentityHashMap<Particle,Integer> indices=new IdentityHashMap<>();List<Map<String,Object>> points=new ArrayList<>();
        for(int i=0;i<candidate.size();i++){if(indices.put(candidate.get(i),i)!=null)throw new AssertionError("Repeated particle identity");points.add(encoded(candidate.get(i)));}
        snapshots.add(row("generation",generation,"role",activeRole.name(),"step",step,"paidFE",paid,
                "familyQuotas",quotas,"parentCount",100,"roleParentCount",parents.size(),"points",points,"knownArchive",archive,
                "actualIndices",ids(actual,indices),"withinAllIndices",ids(withinAll,indices),"globalAllIndices",ids(global,indices)));
    }

    private static int[] ids(List<Particle> values,IdentityHashMap<Particle,Integer> indices) {
        int[] result=new int[values.size()];for(int i=0;i<result.length;i++) {
            Integer index=indices.get(values.get(i));if(index==null)throw new AssertionError("Unpaid candidate reference");result[i]=index;
        }return result;
    }
    private static Map<String,Object> encoded(Particle particle) {
        PermutationSolution<?> s=particle.current;Long first=known.get(key(s));
        if(first==null||first>paid)throw new AssertionError("Working parent lacks earlier paid provenance");
        return row("JS",new ArrayList<>(s.getVariables()),"FA",new ArrayList<>(s.getVariablesid()),
                "MA",new ArrayList<>((List<?>)s.getAttribute("machine")),"WA",new ArrayList<>(s.getVariablesworker()),
                "objectives",s.getObjectives().clone(),"category",WorkingPoolSelection.category(particle),"earliestKnownPaidFE",first);
    }
    private static String key(PermutationSolution<?> s) {
        return s.getVariables()+"|"+s.getVariablesid()+"|"+s.getAttribute("machine")+"|"+s.getVariablesworker()+"|"+Arrays.toString(s.getObjectives());
    }
    public static void finish(Path out) throws Exception {
        if(!ENABLED)return;if(snapshots.size()!=12)throw new AssertionError("Missing fixed global working-pool windows");
        List<String> lines=new ArrayList<>();for(Map<String,Object> snapshot:snapshots)lines.add(DynamicJson.encode(snapshot));
        Files.write(out.resolve("global-working-pools.jsonl"),lines,StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
    }
    private static Map<String,Object> row(Object...fields) {
        Map<String,Object> out=new LinkedHashMap<>();for(int i=0;i<fields.length;i+=2)out.put((String)fields[i],fields[i+1]);return out;
    }
}
