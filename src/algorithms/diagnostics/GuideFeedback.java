package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;

/** Isolated internal-guide refresh timing; only accepted particle states feed earlier offers. */
public final class GuideFeedback {
    private static final String MODE=System.getProperty("research.guide.mode","GEN");
    private static final boolean TRACE=Boolean.parseBoolean(System.getProperty("research.guide.trace","true"));
    private static final Map<String,Stamp> firstPaid=new HashMap<>();
    private static final List<Map<String,Object>> selections=new ArrayList<>();
    private static long paid, offered, nanos;
    private static Direction producingRole;
    private GuideFeedback() { }
    private static final class Stamp {
        final long fe; final String role;
        Stamp(long fe,String role){this.fe=fe;this.role=role;}
    }
    private static String key(PermutationSolution<?> s) {
        return s.getVariables()+"|"+s.getVariablesid()+"|"+s.getAttribute("machine")+"|"+s.getVariablesworker();
    }
    /** Diagnostic provenance uses the first paid occurrence of the exact four-vector genome. */
    public static void evaluated(PermutationSolution<?> s,long successful) {
        paid=successful;
        if(TRACE)firstPaid.putIfAbsent(key(s),new Stamp(paid,producingRole==null?"INITIALIZATION":producingRole.name()));
    }
    static void selected(PermutationSolution<Integer> leader,Direction role,int step,int action) {
        producingRole=role;
        if(!TRACE)return;
        Stamp origin=firstPaid.get(key(leader));
        if(origin==null)throw new IllegalStateException("Guide has no prior paid genome");
        Map<String,Object> row=new LinkedHashMap<>();
        row.put("role",role.name());row.put("step",step);row.put("action",action);row.put("atFE",paid);
        row.put("firstPaidFE",origin.fe);row.put("ageFE",paid-origin.fe);row.put("originRole",origin.role);
        selections.add(row);
    }
    static void afterBatch(SearchState state,List<Particle> accepted,Direction role,int step) {
        if(!Arrays.asList("GEN","ROLE_END","BATCH").contains(MODE))throw new IllegalArgumentException("Unknown guide timing");
        boolean due=MODE.equals("BATCH") || MODE.equals("ROLE_END") && step==49;
        if(!due)return;
        long start=System.nanoTime();
        for(Particle p:accepted) {
            List<PermutationSolution<Integer>> values=MODE.equals("BATCH")?Collections.singletonList(p.current):p.personalArchive();
            state.remember(values);offered+=values.size();
        }
        nanos+=System.nanoTime()-start;
    }
    public static Map<String,Object> diagnostics() {
        Map<String,Object> out=new LinkedHashMap<>();out.put("mode",MODE);out.put("trace",TRACE);
        out.put("offerCount",offered);out.put("refreshSeconds",nanos/1e9);out.put("selections",selections);
        return out;
    }
}
