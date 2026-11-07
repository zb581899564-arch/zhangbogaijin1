package org.uma.jmetal.util.research.search;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.ThreeObjectiveArchive;
import research.dynamic.DynamicJson;

/** Records real pre-batch paid inputs; never selects a candidate or advances the RNG. */
public final class MatingSourceAudit {
    private static final Map<Direction,List<Particle>> working=new EnumMap<>(Direction.class);
    private static final Map<String,Long> known=new HashMap<>();
    private static final PaidObjectiveMirror mirror=new PaidObjectiveMirror();
    private static final List<Map<String,Object>> snapshots=new ArrayList<>();
    private static List<Map<String,Object>> initial;
    private static ThreeObjectiveArchive<?> actualArchive;
    private static int generation;private static long paid;
    private MatingSourceAudit() { }

    public static void paid(PermutationSolution<?> s,long fee,ThreeObjectiveArchive<?> archive) {
        if(fee!=paid+1)throw new AssertionError("Paid observer lost a fee");
        paid=fee;known.putIfAbsent(key(s),fee);mirror.add(s.getObjectives());actualArchive=archive;
    }
    static void generationStarted(Map<Direction,List<Particle>> groups) {
        generation++;working.clear();
        for(Direction role:Direction.values())working.put(role,new ArrayList<>(groups.get(role)));
        if(generation==1){if(paid!=100)throw new AssertionError("Wrong initialization boundary");initial=encodeWorking();}
    }
    static void beforeBatch(Direction role,int step,List<Particle> parents) {
        working.put(role,new ArrayList<>(parents));
        if(generation!=1||role!=Direction.CENTER||!(step==0||step==24||step==49))return;
        mirror.verify(actualArchive.objectiveSnapshot());
        snapshots.add(row("generation",generation,"role",role.name(),"step",step,"preBatchFE",paid,
            "preBatchArchive",mirror.snapshot(),"parents",encodeWorking()));
    }
    static void selected(List<Particle> selected,Direction role) {working.put(role,new ArrayList<>(selected));}

    private static List<Map<String,Object>> encodeWorking() {
        List<Map<String,Object>> out=new ArrayList<>();int[] counts=new int[5];
        for(Direction role:Direction.values())for(Particle particle:working.get(role)) {
            PermutationSolution<Integer> s=particle.current;Long first=known.get(key(s));
            if(first==null||first>paid)throw new AssertionError("Unpaid source in mating input");
            Object family=s.getAttribute("cooperation.family");int category=family==null?0:(Integer)family+1;
            counts[category]++;
            out.add(row("role",role.name(),"category",category,"earliestKnownPaidFE",first,
                "JS",new ArrayList<>(s.getVariables()),"FA",new ArrayList<>(s.getVariablesid()),
                "MA",new ArrayList<>((List<?>)s.getAttribute("machine")),"WA",new ArrayList<>(s.getVariablesworker()),
                "objectives",s.getObjectives().clone()));
        }
        if(out.size()!=100||!Arrays.equals(counts,new int[]{80,5,5,5,5}))throw new AssertionError("Source family counts differ");
        return out;
    }
    private static String key(PermutationSolution<?> s) {
        return s.getVariables()+"|"+s.getVariablesid()+"|"+s.getAttribute("machine")+"|"+s.getVariablesworker()+"|"+Arrays.toString(s.getObjectives());
    }
    public static void finish(Path out) throws Exception {
        if(snapshots.size()!=3||initial==null)throw new AssertionError("Missing fixed CENTER source windows");
        mirror.verify(actualArchive.objectiveSnapshot());
        write(out.resolve("mating-initial-points.jsonl"),initial);write(out.resolve("mating-source-pools.jsonl"),snapshots);
    }
    private static void write(Path path,List<Map<String,Object>> values) throws Exception {
        List<String> lines=new ArrayList<>();for(Map<String,Object> value:values)lines.add(DynamicJson.encode(value));
        Files.write(path,lines,StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
    }
    private static Map<String,Object> row(Object...fields) {
        Map<String,Object> result=new LinkedHashMap<>();
        for(int i=0;i<fields.length;i+=2)result.put((String)fields[i],fields[i+1]);return result;
    }
}
