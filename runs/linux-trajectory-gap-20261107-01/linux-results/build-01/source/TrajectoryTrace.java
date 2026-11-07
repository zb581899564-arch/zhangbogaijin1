package org.uma.jmetal.util.research.search;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.*;
import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.RunContext;
import research.dynamic.DynamicJson;

/** Read-only paid schedule-use graph. Hash equality is not asserted to be object genealogy. */
public final class TrajectoryTrace {
    private static TrajectoryTrace active;
    private final RunContext<PermutationSolution<Integer>> run;
    private final boolean enabled;
    private final BufferedWriter paid, events;
    private final MessageDigest digest;
    private final Set<String> seen = new HashSet<>();
    private final Map<Long,String> prefix = new LinkedHashMap<>();
    private final String arm;
    private String phase = "INITIAL", role = "NONE", parent = "", donor = "", teacher = "";
    private int[] parentJobs, parentFactories, parentMachines, parentWorkers;
    private long observationNanos, paidRows, acceptedRows, cycle;
    private int slot = -1, family = -1;

    public TrajectoryTrace(RunContext<PermutationSolution<Integer>> context, Path out, String label) throws Exception {
        if (active != null) throw new IllegalStateException("One trace per JVM");
        run = context; arm = label; active = this;
        enabled = Boolean.parseBoolean(System.getProperty("research.trajectory.observe", "true"));
        digest = MessageDigest.getInstance("SHA-256");
        paid = enabled ? Files.newBufferedWriter(out.resolve("trajectory-paid.csv"), StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW) : null;
        events = enabled ? Files.newBufferedWriter(out.resolve("trajectory-events.jsonl"), StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW) : null;
        if (enabled) paid.write("fe,cycle,phase,role,slot,family,key,parent,donor,teacher,admitted,duplicate,faChanged,resourceChanged,positionChanged,Cmax,TEC,TWC\n");
    }
    private static String hex(byte[] bytes) {
        StringBuilder out = new StringBuilder(64);
        for (byte b : bytes) out.append(Character.forDigit((b >>> 4)&15,16)).append(Character.forDigit(b&15,16));
        return out.toString();
    }
    private void emit(Map<String,Object> row) {
        if (!enabled) return;
        row.put("fe", run.budget().successful()); row.put("cycle", cycle);
        try { events.write(DynamicJson.encode(row)); events.newLine(); }
        catch (IOException e) { throw new UncheckedIOException(e); }
    }
    public static void proposal(String source, Direction preference, int receiver, int context,
            PermutationSolution<Integer> a, PermutationSolution<Integer> b, PermutationSolution<Integer> c) {
        TrajectoryTrace t = active; if (t == null || !t.enabled) return; long start = System.nanoTime();
        t.phase = source; t.role = preference == null ? "NONE" : preference.name(); t.slot = receiver; t.family = context;
        t.parent = GomRecords.rawHash(a); t.donor = b == null ? "" : GomRecords.rawHash(b); t.teacher = c == null ? "" : GomRecords.rawHash(c);
        org.uma.jmetal.util.research.modelglobal.FourVectors v = GomRecords.vectors(a);
        t.parentJobs=v.jobs(); t.parentFactories=v.factories(); t.parentMachines=v.machines(); t.parentWorkers=v.workers();
        t.observationNanos += System.nanoTime() - start;
    }
    private int[] differences(PermutationSolution<Integer> child) {
        if (parentJobs == null) return new int[]{-1,-1,-1};
        org.uma.jmetal.util.research.modelglobal.FourVectors v=GomRecords.vectors(child);
        int[] js=v.jobs(), fa=v.factories(), ma=v.machines(), wa=v.workers(), where=new int[js.length];
        for(int i=0;i<js.length;i++) where[parentJobs[i]]=i;
        int f=0,r=0,o=0;
        for(int i=0;i<js.length;i++) { int p=where[js[i]];
            if(fa[i]!=parentFactories[p]) f++;
            if(fa[i]!=parentFactories[p] || ma[i]!=parentMachines[p] || wa[i]!=parentWorkers[p]) r++;
            if(js[i]!=parentJobs[i]) o++;
        }
        return new int[]{f,r,o};
    }
    public void paid(PermutationSolution<Integer> point, long fe, boolean admitted) {
        long start=System.nanoTime(); digest.update(GomRecords.paidBytes(point,fe)); paidRows++;
        if(fe==30000 || fe==500000) try { prefix.put(fe,hex(((MessageDigest)digest.clone()).digest())); }
        catch(CloneNotSupportedException e) { throw new IllegalStateException(e); }
        if(enabled) try {
            String key=GomRecords.rawHash(point); boolean duplicate=!seen.add(key); int[] edits=differences(point); double[] a=point.getObjectives();
            String source=fe<=100?"INITIAL":arm.equals("PA_JOINT")?"PA_MIX":phase;
            paid.write(fe+","+cycle+","+source+","+role+","+slot+","+family+","+key+","+parent+","+donor+","+teacher+","+
                (admitted?1:0)+","+(duplicate?1:0)+","+edits[0]+","+edits[1]+","+edits[2]+","+a[0]+","+a[1]+","+a[2]+"\n");
        } catch(IOException e) { throw new UncheckedIOException(e); }
        observationNanos+=System.nanoTime()-start;
    }
    public static void accepted(boolean keep) {
        TrajectoryTrace t=active; if(t==null || !t.enabled)return;long start=System.nanoTime();t.acceptedRows++;
        t.emit(GomRecords.row("kind","accept","keep",keep));t.observationNanos+=System.nanoTime()-start;
    }
    public static void population(String label, List<PermutationSolution<Integer>> values) {
        TrajectoryTrace t=active;if(t==null || !t.enabled)return;long start=System.nanoTime();
        if(label.equals("PRE_GLOBAL") || label.equals("PA_MODEL")) t.cycle++;
        List<Map<String,Object>> points=new ArrayList<>();
        for(PermutationSolution<Integer> value:values) points.add(GomRecords.row("key",GomRecords.rawHash(value),
            "objectives",value.getObjectives().clone(),"family",value.getAttribute("cooperation.family")));
        t.emit(GomRecords.row("kind","population","label",label,"points",points));t.observationNanos+=System.nanoTime()-start;
    }
    public static void program(PermutationSolution<Integer> value, int index, Direction preference) {
        TrajectoryTrace t=active;if(t==null || !t.enabled)return;long start=System.nanoTime();
        t.emit(GomRecords.row("kind","programEnd","slot",index,"role",preference.name(),"key",GomRecords.rawHash(value),
            "objectives",value.getObjectives().clone()));t.observationNanos+=System.nanoTime()-start;
    }
    public static void paProposal(PermutationSolution<Integer> parent, Direction role, int slot, long generation,
            PermutationSolution<Integer> donor) {
        if(active!=null)active.cycle=generation;
        proposal("PA_MIX",role,slot,-1,parent,donor,null);
    }
    public Map<String,Object> finish() throws IOException {
        if(enabled){emit(GomRecords.row("kind","stop","reason",run.stopReason()));paid.close();events.close();}
        Map<String,Object> result=GomRecords.row("enabled",enabled,"paidRows",paidRows,"acceptRows",acceptedRows,
            "observationNanos",observationNanos,"paidSHA256",hex(digest.digest()),"prefixSHA256",prefix,
            "scheduleUseNotObjectGenealogy",true,"cycle",cycle);active=null;return result;
    }
}
