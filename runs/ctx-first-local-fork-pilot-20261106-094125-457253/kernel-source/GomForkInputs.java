package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;

/** First-pass local ancestry fork; every generator, acceptance and candidate-pool rule stays external. */
public final class GomForkInputs {
    private static final String MODE=System.getProperty("research.ctxFork.localInput","POST");
    private static final List<Map<String,Object>> EVENTS=new ArrayList<>();
    private static int cycle,cloneChecks;
    private static List<Map<String,Object>> before;
    private GomForkInputs() { }

    static Map<Direction,List<Particle>> capture(Map<Direction,List<Particle>> groups) {
        if(!GomRunScope.enabled())return null;
        if(!MODE.equals("POST")&&!MODE.equals("PRE_FIRST"))throw new IllegalArgumentException("Unknown fork mode");
        cycle++;before=record(groups);
        if(!MODE.equals("PRE_FIRST")||cycle!=1)return null;
        Map<Direction,List<Particle>> copied=new EnumMap<>(Direction.class);
        for(Direction direction:Direction.values()) {
            List<Particle> values=new ArrayList<>();
            for(Particle original:groups.get(direction)) {
                Particle snapshot=original.snapshot();validateSnapshot(original,snapshot);values.add(snapshot);cloneChecks++;
            }
            copied.put(direction,values);
        }
        return copied;
    }

    static void selected(Map<Direction,List<Particle>> inputs,Map<Direction,List<Particle>> global) {
        if(!GomRunScope.enabled())return;
        List<Map<String,Object>> chosen=record(inputs),post=record(global);
        boolean fork=MODE.equals("PRE_FIRST")&&cycle==1;
        List<Map<String,Object>> expected=fork?before:post;
        for(int i=0;i<chosen.size();i++) {
            Map<String,Object> a=chosen.get(i),b=expected.get(i);
            for(String key:Arrays.asList("rawSHA256","family","direction","lineage","branch"))
                if(!a.get(key).equals(b.get(key)))throw new AssertionError("Wrong local input: "+key);
        }
        EVENTS.add(GomRecords.row("cycle",cycle,"source",fork?"PRE":"POST","before",before,"global",post,"local",chosen));
        before=null;
    }

    private static void validateSnapshot(Particle a,Particle b) {
        if(a.current==b.current||!Arrays.equals(GomRecords.paidBytes(a.current,0),GomRecords.paidBytes(b.current,0))
            ||a.lineageId()!=b.lineageId()||a.branchId()!=b.branchId())throw new AssertionError("Snapshot changed particle");
        if(!history(a).equals(history(b)))throw new AssertionError("Snapshot changed personal history");
        if(!Objects.equals(a.current.getAttribute("cooperation.family"),b.current.getAttribute("cooperation.family"))
            ||!Arrays.equals((int[])a.current.getAttribute("cooperation.fixedFactoryByJob"),(int[])b.current.getAttribute("cooperation.fixedFactoryByJob")))
            throw new AssertionError("Snapshot changed family context");
    }

    private static List<String> history(Particle p) {
        List<String> result=new ArrayList<>();for(PermutationSolution<Integer> s:p.personalArchive())result.add(GomRecords.rawHash(s));return result;
    }

    private static List<Map<String,Object>> record(Map<Direction,List<Particle>> groups) {
        List<Map<String,Object>> result=new ArrayList<>();Map<Integer,Integer> counts=new TreeMap<>();
        for(Direction d:Direction.values()) {
            if(groups.get(d).size()!=(d==Direction.CENTER?55:15))throw new AssertionError("Role quota changed");
            for(Particle p:groups.get(d)) {
                Object family=p.current.getAttribute("cooperation.family");int f=family==null?-1:(Integer)family;
                Map<String,Object> row=GomRecords.raw(p.current);
                row.putAll(GomRecords.row("rawSHA256",GomRecords.rawHash(p.current),"direction",d.name(),"family",f,
                    "lineage",p.lineageId(),"branch",p.branchId()));result.add(row);counts.put(f,counts.getOrDefault(f,0)+1);
            }
        }
        if(counts.getOrDefault(-1,0)!=80||counts.size()!=5)throw new AssertionError("Free domain changed");
        for(int f=0;f<4;f++)if(counts.getOrDefault(f,0)!=5)throw new AssertionError("Fixed family quota changed");
        return result;
    }

    public static Map<String,Object> diagnostics() {
        return GomRecords.row("mode",MODE,"cyclesStarted",cycle,"snapshotChecks",cloneChecks,"entries",EVENTS,"uncompletedPre",before);
    }
}
