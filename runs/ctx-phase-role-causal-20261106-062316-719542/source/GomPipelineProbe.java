package org.uma.jmetal.util.research.search;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import research.dynamic.DynamicJson;

/** Fixed-FE read-only pipeline snapshots. No RNG, evaluation, attribute writes or feedback. */
public final class GomPipelineProbe {
    private static GomPipelineProbe current;
    private final GomRunScope scope;
    private final BufferedWriter writer;
    private long events;
    private final GomPhasePaidDigest paid=new GomPhasePaidDigest();
    private GomPipelineProbe(GomRunScope value,Path file) {
        scope=value;
        try { writer=Files.newBufferedWriter(file,StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW); }
        catch(IOException error) { throw new UncheckedIOException(error); }
    }
    static void attach(GomRunScope scope) {
        String file=System.getProperty("research.ctxPipeline.file");
        if(file!=null) { if(current!=null) throw new AssertionError("Only one pipeline per JVM"); current=new GomPipelineProbe(scope,Paths.get(file)); }
    }
    private void emit(Map<String,Object> row) {
        row.put("fe",scope.run.budget().successful());events++;
        try { writer.write(DynamicJson.encode(row));writer.newLine(); }
        catch(IOException error) { throw new UncheckedIOException(error); }
    }
    private static Map<String,Object> point(PermutationSolution<Integer> value,boolean full) {
        Map<String,Object> row=full?GomRecords.raw(value):GomRecords.row("objectives",value.getObjectives().clone());
        row.put("key",GomRecords.rawHash(value));Object family=value.getAttribute("cooperation.family");
        row.put("family",family==null?-1:family);return row;
    }
    private static Map<String,Object> particle(Particle p,boolean full) {
        Map<String,Object> row=point(p.current,full);row.put("lineage",p.lineageId());row.put("branch",p.branchId());return row;
    }
    static void population(String phase,List<Particle> values,SearchState state) {
        if(current==null)return;
        int cycle=(phase.equals("PRE_GLOBAL")||phase.equals("POST_GLOBAL"))?current.scope.passes+1:current.scope.passes;
        List<Map<String,Object>> points=new ArrayList<>(),memory=new ArrayList<>();
        for(Particle p:values)points.add(particle(p,true));
        for(PermutationSolution<Integer> p:state.archive())memory.add(point(p,false));
        current.emit(GomRecords.row("kind","population","phase",phase,"cycle",cycle,"points",points,"memory",memory,"allPaid",current.scope.archive()));
    }
    static void selection(List<Particle> candidates,SurvivorSelection.Result result) {
        if(current==null)return;List<Map<String,Object>> points=new ArrayList<>();
        for(Particle p:candidates)points.add(particle(p,false));
        current.emit(GomRecords.row("kind","selection","cycle",current.scope.passes,"pool",points,
            "selected",result.indices(),"fitness",result.fitness(),"categories",result.categories(),"quotas",result.quotas()));
    }
    static void workspace(GomWorkspace w) {
        if(current==null)return;List<Map<String,Object>> states=new ArrayList<>();
        for(int i=0;i<w.values.size();i++) {
            GomRecords.State s=w.values.get(i);Map<String,Object> row=s.record(true);
            row.put("sourceKey",GomRecords.rawHash(s.point));row.put("family",w.families.get(i));states.add(row);
        }
        current.emit(GomRecords.row("kind","workspace","cycle",current.scope.passes,"states",states));
    }
    static void admission(PermutationSolution<Integer> p,long fe) {
        if(current==null)return;
        current.paid.update(p,fe);
        if(fe==223840||fe==228840)current.emit(GomRecords.row("kind","paidPrefix","sha256",current.paid.snapshot()));
        if(!current.scope.lastFlags.fresh)return;
        current.emit(GomRecords.row("kind","admission","cycle",current.scope.passes,"stage",current.scope.stage,"point",point(p,false)));
    }
    static void program(GomWorkspace w,Direction preference) {
        if(current==null)return;
        current.emit(GomRecords.row("kind","program","cycle",current.scope.passes,"slot",w.slot,
            "preference",preference.name(),"point",point(w.values.get(w.slot).point,false)));
    }
    public static void finish() {
        if(current==null)return;GomPipelineProbe probe=current;
        probe.emit(GomRecords.row("kind","finish","eventsBeforeFinish",probe.events,"passes",probe.scope.completedPasses,"paidSHA256",probe.paid.snapshot()));
        try { probe.writer.close(); }
        catch(IOException error) { throw new UncheckedIOException(error); }
        finally { current=null; }
    }
}
