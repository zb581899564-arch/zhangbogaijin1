package org.uma.jmetal.util.research.search;

import java.util.*;
import java.util.function.Supplier;
import org.uma.jmetal.solution.PermutationSolution;

/** Read-only snapshot of the already-paid whole-generation selection pool. */
public final class FinalSurvivalTrace {
    private static final boolean ENABLED=Boolean.getBoolean("research.finalSurvival.trace");
    private static final List<Map<String,Object>> events=new ArrayList<>();
    private static Supplier<List<PermutationSolution<Integer>>> archive;
    private static long paid;
    private FinalSurvivalTrace() { }
    public static void configure(Supplier<List<PermutationSolution<Integer>>> source){archive=source;}
    public static void paid(long count){if(ENABLED)paid=count;}

    static void selected(List<Particle> pool,int count,double[] fitness,int[] categories,int[] quotas,int[] indices) {
        if(!ENABLED)return;
        if(pool.size()!=2*count)throw new IllegalStateException("Unexpected whole-generation pool");
        List<Map<String,Object>> points=new ArrayList<>();
        for(int i=0;i<pool.size();i++) {
            Particle p=pool.get(i);PermutationSolution<Integer>s=p.current;
            Map<String,Object> r=new LinkedHashMap<>();r.put("index",i);r.put("origin",i<count?"GLOBAL":"LOCAL");
            r.put("category",categories==null?0:categories[i]);r.put("fitness",fitness[i]);
            r.put("lineage",p.lineageId());r.put("branch",p.branchId());
            r.put("objectives",s.getObjectives().clone());r.put("JS",new ArrayList<>(s.getVariables()));
            r.put("FA",new ArrayList<>(s.getVariablesid()));r.put("MA",new ArrayList<>((List<?>)s.getAttribute("machine")));
            r.put("WA",new ArrayList<>(s.getVariablesworker()));points.add(r);
        }
        Map<String,Object> event=new LinkedHashMap<>();event.put("paidFE",paid);event.put("count",count);
        event.put("quotas",quotas==null?new int[]{count}:quotas.clone());event.put("selected",indices.clone());
        event.put("points",points);List<double[]> background=new ArrayList<>();
        for(PermutationSolution<Integer>s:archive.get())background.add(s.getObjectives().clone());
        event.put("paidExternalArchive",background);events.add(event);
    }
    public static Map<String,Object> finish() {
        Map<String,Object> out=new LinkedHashMap<>();out.put("enabled",ENABLED);out.put("events",events);return out;
    }
}
