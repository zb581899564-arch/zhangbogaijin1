package org.uma.jmetal.util.research.cooperation;

import java.util.*;
import java.util.function.Supplier;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.search.Direction;
import org.uma.jmetal.util.research.search.SwarmSupport;

/** Phase snapshots of already-paid compatible factory records. Never supplies a candidate to search. */
public final class PoolPhaseAudit {
    private static Supplier<List<PermutationSolution<Integer>>> archive;
    private static long paid;
    private static int completedGlobalPhases;
    private static final List<Map<String,Object>> snapshots=new ArrayList<>();
    private static List<Map<String,Object>> firstReceivers,laterReceivers;
    private PoolPhaseAudit() { }
    public static void configure(Supplier<List<PermutationSolution<Integer>>> known) {archive=known;}
    public static void paid(long successful) {paid=successful;}
    static long paidFE() {return paid;}
    public static void groups(List<PermutationSolution<Integer>> center) {
        if(completedGlobalPhases==1)laterReceivers=receivers(center);
    }
    public static void globalEnd(SwarmSupport support,List<PermutationSolution<Integer>> center) {
        completedGlobalPhases++;
        if(completedGlobalPhases==1) {
            firstReceivers=receivers(center);capture(support,"GLOBAL_END");
        }
    }
    public static void localEnd(SwarmSupport support,Direction role) {
        if(completedGlobalPhases==1)capture(support,role.name()+"_LOCAL_END");
    }
    public static void centerEntry(SwarmSupport support,Direction role) {
        if(completedGlobalPhases==1 && role==Direction.CENTER)capture(support,"G2_CENTER_ENTRY");
    }
    private static void capture(SwarmSupport support,String phase) {
        if(!(support instanceof CooperationSupport))throw new IllegalArgumentException("Expected frozen cooperative support");
        Map<String,Object> row=new LinkedHashMap<>();row.put("phase",phase);row.put("paidFE",paid);
        row.put("pool",((CooperationSupport)support).phasePoolSnapshot());
        List<double[]> known=new ArrayList<>();for(PermutationSolution<Integer> s:archive.get())known.add(s.getObjectives().clone());
        row.put("knownArchive",known);snapshots.add(row);
    }
    private static List<Map<String,Object>> receivers(List<PermutationSolution<Integer>> center) {
        List<Map<String,Object>> out=new ArrayList<>();int[] count=new int[4];
        for(PermutationSolution<Integer> s:center) {
            int family=FamilyContexts.family(s);if(family<0)continue;
            count[family]++;Map<String,Object> row=new LinkedHashMap<>();row.put("family",family);
            row.put("objectives",s.getObjectives().clone());row.put("JS",new ArrayList<>(s.getVariables()));
            row.put("FA",new ArrayList<>(s.getVariablesid()));row.put("MA",new ArrayList<>((List<?>)s.getAttribute("machine")));
            row.put("WA",new ArrayList<>(s.getVariablesworker()));out.add(row);
        }
        if(!Arrays.equals(count,new int[]{2,2,2,2}))throw new AssertionError("Unexpected frozen CENTER family structure");
        return out;
    }
    static Map<String,Object> pool(FactoryPool[][] pools,FamilyContexts contexts,double energyScale,double wageScale) {
        Map<String,Object> out=new LinkedHashMap<>();out.put("energyScale",energyScale);out.put("wageScale",wageScale);
        List<Map<String,Object>> families=new ArrayList<>();
        for(int family=0;family<4;family++) {
            Map<String,Object> item=new LinkedHashMap<>();item.put("family",family);item.put("factoryByJob",contexts.assignment(family));
            List<List<Map<String,Object>>> factories=new ArrayList<>();
            for(FactoryPool p:pools[family]) {
                List<Map<String,Object>> records=new ArrayList<>();
                for(FactoryRecord r:p.records()) {
                    Map<String,Object> row=new LinkedHashMap<>();row.put("jobs",r.jobs.clone());row.put("machines",r.machines.clone());
                    row.put("workers",r.workers.clone());row.put("objectives",r.objectives.clone());
                    row.put("paidFE",r.paidFE);row.put("stage",r.stage);row.put("producer",r.producer);records.add(row);
                }
                factories.add(records);
            }
            item.put("factories",factories);families.add(item);
        }
        out.put("families",families);return out;
    }
    public static Map<String,Object> finish() {
        if(firstReceivers==null||laterReceivers==null||snapshots.size()!=6)throw new AssertionError("Missing predefined pool phases");
        Map<String,Object> out=new LinkedHashMap<>();out.put("firstReceivers",firstReceivers);out.put("laterReceivers",laterReceivers);
        out.put("snapshots",snapshots);out.put("finalPaidFE",paid);return out;
    }
}
