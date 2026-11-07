package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;

/** Creator-role availability only; does not claim actual gene transfer or causal credit. */
public final class GlobalFlowTrace {
    private static final boolean ENABLED=Boolean.getBoolean("research.globalFlow.trace");
    private static final String ROLE="observation.globalFlow.role",GEN="observation.globalFlow.epoch";
    private static final Map<String,Long> edges=new LinkedHashMap<>();
    private static long offered,nanos;
    private static int epoch;
    private GlobalFlowTrace() { }
    static void epochStarted() {epoch++;}
    static void before(PermutationSolution<Integer> s,String stage,Direction direction) {
        if(!ENABLED)return;
        s.setAttribute(ROLE,stage.equals("initialization")?"INITIALIZATION":direction.name());s.setAttribute(GEN,epoch);
    }
    static void selected(PermutationSolution<Integer> guide,Direction receiver,int step,int action) {
        if(!ENABLED||action!=2)return;
        Object producer=guide.getAttribute(ROLE),born=guide.getAttribute(GEN);
        if(producer==null||born==null)throw new AssertionError("Selected guide missing creator metadata");
        String key=epoch+":"+receiver+":"+producer+":"+(((Number)born).intValue()==epoch?"SAME_EPOCH":"OLDER");
        edges.put(key,edges.getOrDefault(key,0L)+1);
    }
    static void offered(int count,long elapsed) {offered+=count;nanos+=elapsed;}
    public static Map<String,Object> diagnostics() {
        Map<String,Object> result=new LinkedHashMap<>();result.put("layout",System.getProperty("research.qgs.layout","SERIAL"));
        result.put("fresh",QgsEpochSchedule.fresh());result.put("trace",ENABLED);result.put("epoch",epoch);
        result.put("action2CreatorEdges",edges);result.put("offeredAcceptedCurrentStates",offered);result.put("refreshSeconds",nanos/1e9);
        return result;
    }
}
