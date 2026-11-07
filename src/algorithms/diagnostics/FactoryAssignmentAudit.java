package org.uma.jmetal.util.research.search;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.Solution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.DynamicSchedule;
import research.dynamic.DynamicJson;

/** Read-only paid-stage FA accounting. No attributes, RNG, archive offers or selection are changed. */
public final class FactoryAssignmentAudit {
    private static final Map<DynamicSchedule,Event> known=new WeakHashMap<>();
    private static final Map<String,Long> firstAssignments=new HashMap<>();
    private static final Map<String,Map<String,Long>> counters=new LinkedHashMap<>();
    private static final List<Map<String,Object>> admissions=new ArrayList<>(),interAcceptances=new ArrayList<>();
    private static final Set<Long> accepted=new HashSet<>();
    private static Pending pending;private static long paid,unknownParents,protectedChanges;
    private FactoryAssignmentAudit() { }
    private static final class Pending {
        PermutationSolution<Integer> value;DynamicSchedule parent;Event parentEvent;
        String stage,role;boolean protectedFamily;int rawChanges,changes;int[] assignment;
    }
    private static final class Event {
        long fe;String stage,role;boolean protectedFamily;int rawChanges,changes;boolean novel,admitted;
        long parentFE;
        String counterKey() {return stage+"/"+role+"/"+(protectedFamily?"PROTECTED":"FREE")+"/"+(changes<0?"INITIAL":changes>0?"FA_CHANGED":"FA_SAME");}
        Map<String,Object> record() {
            return row("fe",fe,"stage",stage,"role",role,"protectedFamily",protectedFamily,"rawChangedJobs",rawChanges,
                "changedJobs",changes,"novelFA",novel,"admitted",admitted,"parentHintPaidFE",parentFE);
        }
    }
    public static void begin(PermutationSolution<Integer> value,String stage,Direction role) {
        if(pending!=null)throw new AssertionError("Nested unpaid FA observation");
        Pending p=new Pending();p.value=value;p.stage=stage;p.role=role==null?"NONE":role.name();
        p.protectedFamily=value.getAttribute("cooperation.family")!=null;
        Object old=value.getAttribute(DynamicEvaluation.KEY);
        if(old instanceof DynamicSchedule) {
            p.parent=(DynamicSchedule)old;p.parentEvent=known.get(p.parent);
            int[] previous=FactoryAssignmentEncoding.byJob(p.parent.js(),p.parent.fa());
            p.rawChanges=FactoryAssignmentEncoding.changes(previous,FactoryAssignmentEncoding.byJob(value));
        } else p.rawChanges=-1;
        pending=p;
    }
    public static void ready(PermutationSolution<Integer> value) {
        if(pending==null||pending.value!=value)throw new AssertionError("Missing FA stage boundary");
        pending.assignment=FactoryAssignmentEncoding.byJob(value);
        pending.changes=pending.parent==null?-1:FactoryAssignmentEncoding.changes(
            FactoryAssignmentEncoding.byJob(pending.parent.js(),pending.parent.fa()),pending.assignment);
    }
    @SuppressWarnings("unchecked")
    public static void paid(Solution<?> value,long fe,boolean admitted) {
        Pending p=pending;
        if(p==null||p.value!=value||p.assignment==null||fe!=paid+1)throw new AssertionError("Paid FA accounting mismatch");
        boolean initial=p.stage.equals("initialization");
        if(initial!=(p.parent==null))throw new AssertionError("Missing or unexpected physical parent hint");
        if(!initial && (p.parentEvent==null || p.parentEvent.fe>=fe)) {unknownParents++;throw new AssertionError("Parent hint lacks earlier paid provenance");}
        Event event=new Event();event.fe=fe;event.stage=p.stage;event.role=p.role;event.protectedFamily=p.protectedFamily;
        event.rawChanges=p.rawChanges;event.changes=p.changes;event.parentFE=initial?0:p.parentEvent.fe;event.admitted=admitted;
        String key=Arrays.toString(p.assignment);event.novel=!firstAssignments.containsKey(key);firstAssignments.putIfAbsent(key,fe);
        Map<String,Long> count=counters.computeIfAbsent(event.counterKey(),x->new LinkedHashMap<>());
        add(count,"successfulFE",1);if(admitted)add(count,"admissions",1);if(event.novel)add(count,"novelFA",1);
        if(p.rawChanges>0)add(count,"rawFAIntentFE",1);
        if(p.rawChanges>0 && p.changes==0)add(count,"rawFAIntentCanceledFE",1);
        if(p.changes>0)add(count,"changedJobsTotal",p.changes);
        if(p.protectedFamily && p.changes>0){protectedChanges++;throw new AssertionError("Protected actual FA changed");}
        if(p.stage.equals("intra") && p.changes!=0)throw new AssertionError("Intra stage changed physical factory assignment");
        DynamicSchedule schedule=(DynamicSchedule)value.getAttribute(DynamicEvaluation.KEY);
        if(!Arrays.equals(p.assignment,FactoryAssignmentEncoding.byJob(schedule.js(),schedule.fa())))throw new AssertionError("Evaluated FA differs");
        known.put(schedule,event);
        if(admitted) {Map<String,Object> record=event.record();record.put("objectives",value.getObjectives().clone());admissions.add(record);}
        paid=fe;pending=null;
    }
    public static void acceptedInter(PermutationSolution<Integer> value) {
        Event event=known.get((DynamicSchedule)value.getAttribute(DynamicEvaluation.KEY));
        if(event==null||!event.stage.equals("inter")||!accepted.add(event.fe))throw new AssertionError("Unpaid or duplicate inter acceptance");
        add(counters.get(event.counterKey()),"interAccepted",1);interAcceptances.add(event.record());
    }
    private static void add(Map<String,Long> count,String key,long n) {count.put(key,count.getOrDefault(key,0L)+n);}
    public static void write(Path out,boolean completed) throws Exception {
        Map<String,Object> receipt=row("status",completed&&unknownParents==0&&protectedChanges==0?"PASS":"INCOMPLETE_RETAINED","successfulFE",paid,"unknownParentHints",unknownParents,
            "protectedActualFAChanges",protectedChanges,"uniquePaidAssignments",firstAssignments.size(),
            "admissionEvents",admissions.size(),"interAcceptanceEvents",interAcceptances.size(),
            "unpaidPendingAtFinish",pending!=null,"counters",counters,
            "scope","Incremental parent hints proved paid and traced to copied first/current parents in frozen kernels. Sequential admission credit is not causal FA value.");
        writeLines(out.resolve("fa-audit.jsonl"),Collections.singletonList(receipt));
        writeLines(out.resolve("fa-admissions.jsonl"),admissions);writeLines(out.resolve("fa-inter-acceptances.jsonl"),interAcceptances);
    }
    private static void writeLines(Path file,List<Map<String,Object>> records)throws Exception {
        List<String> lines=new ArrayList<>();for(Map<String,Object> record:records)lines.add(DynamicJson.encode(record));
        Files.write(file,lines,StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
    }
    private static Map<String,Object> row(Object...fields) {
        Map<String,Object> result=new LinkedHashMap<>();for(int i=0;i<fields.length;i+=2)result.put((String)fields[i],fields[i+1]);return result;
    }
}
