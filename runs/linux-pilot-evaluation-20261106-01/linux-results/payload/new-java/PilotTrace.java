package org.uma.jmetal.util.research.search;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.RunContext;
import research.dynamic.DynamicJson;

/** Isolated read-only provenance. No random calls, attributes, decisions or evaluations. */
public final class PilotTrace {
    private static PilotTrace current;
    private final RunContext<PermutationSolution<Integer>> run;
    private final BufferedWriter paid, events;
    private final boolean observing;
    private final Map<String,Long> fees = new LinkedHashMap<>(), observation = new LinkedHashMap<>();
    private final Map<String,Double> phaseSeconds = new LinkedHashMap<>();
    private String phase = "INITIAL", role = "NONE", mechanism = "initialization";
    private long cycle, lastFE;
    private double phaseStart;
    private boolean shared, lastAdmitted;

    public PilotTrace(RunContext<PermutationSolution<Integer>> context,Path out,boolean enabled) throws IOException {
        if(current!=null)throw new IllegalStateException("One trace per JVM");
        run=context;observing=enabled;current=this;
        paid=enabled?Files.newBufferedWriter(out.resolve("paid-events.csv"),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW):null;
        events=enabled?Files.newBufferedWriter(out.resolve("stage-events.jsonl"),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW):null;
        if(enabled)paid.write("fe,cycle,stage,role,source,admitted,elapsedSeconds,Cmax,TEC,TWC\n");
    }
    public static boolean globalEnabled(){return !System.getProperty("research.pilot.phase","FULL").equals("LOCAL_ONLY");}
    public static boolean localEnabled(){return !System.getProperty("research.pilot.phase","FULL").equals("GLOBAL_ONLY");}
    public static void phase(String name) {
        if(current==null)return;
        PilotTrace p=current;double now=p.run.clock().elapsedSeconds();
        p.phaseSeconds.put(p.phase,p.phaseSeconds.getOrDefault(p.phase,0.0)+now-p.phaseStart);
        p.phase=name;p.phaseStart=now;
    }
    public static void context(String source,Direction physical) {
        if(current==null)return;
        current.role=physical==null?"NONE":physical.name();current.mechanism=source;
        if(!source.equals("global"))current.shared=false;
    }
    public static void composed(boolean value){if(current!=null)current.shared=value;}
    private void charge(long start){observation.put(phase,observation.getOrDefault(phase,0L)+System.nanoTime()-start);}
    private void emit(Map<String,Object> row) {
        if(!observing)return;
        row.put("fe",run.budget().successful());row.put("cycle",cycle);row.put("phase",phase);
        row.put("elapsedSeconds",run.clock().elapsedSeconds());
        try {events.write(DynamicJson.encode(row));events.newLine();}
        catch(IOException e){throw new UncheckedIOException(e);}
    }
    public void paid(PermutationSolution<Integer> point,long fe,double seconds,boolean admitted) {
        long start=System.nanoTime();lastFE=fe;lastAdmitted=admitted;
        String source=shared?"SHARED_COMPOSITION":mechanism;
        fees.put(phase,fees.getOrDefault(phase,0L)+1);
        fees.put(phase+"/"+source,fees.getOrDefault(phase+"/"+source,0L)+1);
        if(observing)try {
            double[] a=point.getObjectives();
            paid.write(fe+","+cycle+","+phase+","+role+","+source+","+(admitted?1:0)+","+seconds+","+a[0]+","+a[1]+","+a[2]+"\n");
            if(admitted)emit(GomRecords.row("kind","admission","source",source,"role",role,"point",point(point)));
        }catch(IOException e){throw new UncheckedIOException(e);}
        charge(start);
    }
    private static Map<String,Object> point(PermutationSolution<Integer> value) {
        return GomRecords.row("objectives",value.getObjectives().clone(),"key",GomRecords.rawHash(value),
            "family",value.getAttribute("cooperation.family"));
    }
    public static void population(String label,List<Particle> values) {
        if(current==null)return;PilotTrace p=current;long start=System.nanoTime();
        if(label.equals("PRE_GLOBAL"))p.cycle++;
        if(p.observing) {
            List<Map<String,Object>> points=new ArrayList<>();
            for(Particle value:values) {
                Map<String,Object> row=point(value.current);row.put("lineage",value.lineageId());row.put("branch",value.branchId());points.add(row);
            }
            p.emit(GomRecords.row("kind","population","label",label,"points",points));
        }
        p.charge(start);
    }
    public static void selection(List<Particle> candidates,SurvivorSelection.Result result) {
        if(current==null)return;PilotTrace p=current;long start=System.nanoTime();
        p.emit(GomRecords.row("kind","selection","candidateCount",candidates.size(),"selected",result.indices(),"quotas",result.quotas()));
        p.charge(start);
    }
    public static void acceptedLocal(boolean accepted,PermutationSolution<Integer> point) {
        if(current==null)return;PilotTrace p=current;long start=System.nanoTime();
        if(p.observing && p.lastAdmitted)p.emit(GomRecords.row("kind","workingAcceptance","accepted",accepted,
            "paidFE",p.lastFE,"point",point(point)));
        p.charge(start);
    }
    public Map<String,Object> finish() throws IOException {
        phase(phase);
        if(observing){emit(GomRecords.row("kind","stop","stopReason",run.stopReason(),"partialPhase",phase));paid.close();events.close();}
        Map<String,Object> result=GomRecords.row("phaseFE",fees,"phaseSecondsInclusive",phaseSeconds,
            "observationNanosByPhase",observation,"cycle",cycle,"enabled",observing,"directProvenanceNotCausal",true);
        current=null;return result;
    }
}
