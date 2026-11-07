package org.uma.jmetal.util.research.search;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.DynamicSchedule;
import org.uma.jmetal.util.research.runtime.ThreeObjectiveArchive;
import research.dynamic.DynamicJson;

/** Observer-only accounting of complete M intra slots, including incidental three-objective discoveries. */
public final class CriticalSlotAudit {
    private static final List<Map<String,Object>> rows=new ArrayList<>();
    private static ThreeObjectiveArchive<?> archive;
    private static Path output;private static String pendingFailure;
    private static long paid,observed;private static int visit,visitGroup;private static Active active;
    private CriticalSlotAudit() { }
    public static void output(Path path) {output=path;CriticalSlotCertificate.fixtures();}

    private static final class Active {
        final Map<String,Object> row;final double[] time,energy,cost;final boolean impossible;
        final int factory;final long startPaid;final double cmax;final String encoding;
        int admissions,candidates;
        Active(PermutationSolution<Integer> parent,Direction preference,QgsLocalLedger.Slot slot,int drawn) {
            DynamicSchedule schedule=schedule(parent);time=schedule.factoryMakespan();energy=schedule.factoryEnergy();cost=schedule.factoryCost();
            factory=slot.factory;impossible=CriticalSlotCertificate.impossible(time,factory);startPaid=paid;cmax=parent.getObjective(0);encoding=key(parent);
            if(Arrays.stream(time).max().getAsDouble()!=cmax)throw new AssertionError("Factory maximum differs from global objective");
            row=row("visit",visit,"group",slot.group,"round",slot.round,"factory",factory,"drawnFactory",drawn,"fixed",slot.fixed,
                "limit",slot.limit,"preference",preference.name(),"beforeFE",paid,"beforeObjectives",parent.getObjectives().clone(),
                "factoryMakespan",time,"factoryEnergy",energy,"factoryCost",cost,"strictMakespanImprovementImpossible",impossible,
                "beforeArchive",archive.objectiveSnapshot(),"entry",encoding(parent));
        }
    }
    public static void paid(PermutationSolution<?> value,long fee,boolean changed,ThreeObjectiveArchive<?> result) {
        if(fee!=paid+1)throw new AssertionError("Lost guarded evaluation in slot observer");paid=fee;archive=result;
        if(active==null)return;active.candidates++;observed++;if(changed)active.admissions++;
        DynamicSchedule schedule=schedule(value);double[] time=schedule.factoryMakespan(),energy=schedule.factoryEnergy(),cost=schedule.factoryCost();
        for(int f=0;f<time.length;f++)if(f!=active.factory&&(time[f]!=active.time[f]||energy[f]!=active.energy[f]||cost[f]!=active.cost[f]))
            violation("Intra candidate changed another factory "+f,value,schedule);
        if(active.impossible&&value.getObjective(0)<active.cmax)violation("Certified impossible slot lowered global Cmax",value,schedule);
    }
    static void visitStarted(int group) {
        if(active!=null)throw new AssertionError("An intra slot remained open before next visit");visit++;visitGroup=group;
    }
    static void begin(PermutationSolution<Integer> parent,Direction preference,QgsLocalLedger.Slot slot,int drawn) {
        if(active!=null)throw new AssertionError("Nested intra audit");
        if(slot.group!=visitGroup)throw new AssertionError("Physical visit group differs from intra slot");
        if(preference!=Direction.MAKESPAN||slot.group!=Direction.MAKESPAN.id())return;
        if(archive==null)throw new AssertionError("No paid archive at intra entry");active=new Active(parent,preference,slot,drawn);
    }
    static void end(PermutationSolution<Integer> current,QgsLocalLedger.Slot slot,boolean returned) {
        if(active==null)return;
        if(pendingFailure!=null){active=null;return;}
        if(slot.group!=0||slot.round<0||active.factory!=slot.factory||active.candidates!=slot.paid||paid-active.startPaid!=slot.paid)
            throw new AssertionError("M slot physical accounting mismatch: group="+slot.group+" round="+slot.round+" actualFactory="+slot.factory
                +" observedFactory="+active.factory+" successfulCandidates="+active.candidates+" ledgerPaid="+slot.paid+" observerPaid="+(paid-active.startPaid));
        if(current.getObjective(0)>active.cmax||active.impossible&&current.getObjective(0)!=active.cmax)
            throw new AssertionError("M outer VNS exit violates strict makespan acceptance");
        Map<String,Object> row=active.row;
        row.put("afterFE",paid);row.put("paid",slot.paid);row.put("restarts",slot.restarts);row.put("returnedNormally",returned);
        row.put("afterObjectives",current.getObjectives().clone());row.put("sameExitEncoding",active.encoding.equals(key(current)));
        row.put("archiveAdmissionEvents",active.admissions);row.put("afterArchive",archive.objectiveSnapshot());
        rows.add(row);active=null;
    }
    private static DynamicSchedule schedule(PermutationSolution<?> s) {
        Object value=s.getAttribute(DynamicEvaluation.KEY);
        if(!(value instanceof DynamicSchedule))throw new AssertionError("Missing exact dynamic schedule");return (DynamicSchedule)value;
    }
    private static String key(PermutationSolution<?> s) {
        return s.getVariables()+"|"+s.getVariablesid()+"|"+s.getAttribute("machine")+"|"+s.getVariablesworker();
    }
    private static void violation(String reason,PermutationSolution<?> value,DynamicSchedule schedule) {
        pendingFailure=reason;
        Map<String,Object> record=row("reason",reason,"paidFE",paid,"entrySlot",active.row,"candidate",encoding(value),
            "candidateFactoryMakespan",schedule.factoryMakespan(),"candidateFactoryEnergy",schedule.factoryEnergy(),"candidateFactoryCost",schedule.factoryCost());
        try {Files.write(output.resolve("critical-observer-failure.jsonl"),Collections.singletonList(DynamicJson.encode(record)),
            StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);}
        catch(java.io.IOException error){throw new java.io.UncheckedIOException(error);}
        System.err.println("CRITICAL_SLOT_ORIGINAL_FAILURE "+reason+" paid="+paid);throw new AssertionError(reason);
    }
    private static Map<String,Object> encoding(PermutationSolution<?> s) {
        Object fixed=s.getAttribute("cooperation.fixedFactoryByJob");
        return row("JS",new ArrayList<>(s.getVariables()),"FA",new ArrayList<>(s.getVariablesid()),
            "MA",new ArrayList<>((List<?>)s.getAttribute("machine")),"WA",new ArrayList<>(s.getVariablesworker()),
            "objectives",s.getObjectives().clone(),"family",s.getAttribute("cooperation.family"),
            "fixedFactoryByJob",fixed==null?null:((int[])fixed).clone());
    }
    public static void finish(Path out) throws Exception {
        if(active!=null||rows.isEmpty())throw new AssertionError("Open or missing M slot observations");
        CriticalSlotCertificate.fixtures();List<String> lines=new ArrayList<>();
        for(Map<String,Object> row:rows)lines.add(DynamicJson.encode(row));
        Files.write(out.resolve("critical-slots.jsonl"),lines,StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
        Files.write(out.resolve("critical-slot-receipt.jsonl"),Collections.singletonList(DynamicJson.encode(row("status","PASS",
            "observedSuccessfulFE",observed,"globalPaidFE",paid,"visits",visit,"Mslots",rows.size(),"fixtureCases",6,
            "otherFactoryVectorsUnchangedEveryCandidate",true,"certificateViolations",0,"consumesRNG",false))),
            StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
    }
    private static Map<String,Object> row(Object...fields) {
        Map<String,Object> out=new LinkedHashMap<>();for(int i=0;i<fields.length;i+=2)out.put((String)fields[i],fields[i+1]);return out;
    }
}
