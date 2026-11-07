package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.DynamicSchedule;

/** Observe physical factory completion improvements hidden by an unchanged maximum. */
public final class MakespanPlateauTrace {
    private static long comparisons, ties, distinctFactoryTies, lexBetterTies, componentwiseBetterTies;
    private static final List<Map<String,Object>> samples=new ArrayList<>();
    private MakespanPlateauTrace() { }

    static void record(PermutationSolution<Integer> child, PermutationSolution<Integer> parent) {
        comparisons++;
        if(child.getObjective(0)!=parent.getObjective(0))return;
        ties++;
        double[] c=schedule(child).factoryMakespan(),p=schedule(parent).factoryMakespan();
        boolean distinct=!Arrays.equals(c,p),noWorse=true,oneBetter=false;
        for(int j=0;j<c.length;j++){noWorse&=c[j]<=p[j];oneBetter|=c[j]<p[j];}
        if(distinct)distinctFactoryTies++;
        double[] sortedC=c.clone(),sortedP=p.clone();Arrays.sort(sortedC);Arrays.sort(sortedP);
        boolean lexBetter=false;
        for(int j=c.length-1;j>=0;j--) {
            if(sortedC[j]==sortedP[j])continue;
            lexBetter=sortedC[j]<sortedP[j];break;
        }
        if(lexBetter)lexBetterTies++;
        if(noWorse&&oneBetter)componentwiseBetterTies++;
        if(comparisons%257!=1)return;
        Map<String,Object> row=new LinkedHashMap<>();row.put("comparison",comparisons);
        row.put("parentFactories",p);row.put("childFactories",c);row.put("lexBetter",lexBetter);
        row.put("componentwiseBetter",noWorse&&oneBetter);
        row.put("parentObjectives",parent.getObjectives().clone());row.put("childObjectives",child.getObjectives().clone());
        samples.add(row);
    }

    private static DynamicSchedule schedule(PermutationSolution<Integer> s) {
        Object value=s.getAttribute(DynamicEvaluation.KEY);
        if(!(value instanceof DynamicSchedule))throw new IllegalStateException("Missing paid dynamic timeline");
        return (DynamicSchedule)value;
    }

    public static Map<String,Object> diagnostics() {
        Map<String,Object> out=new LinkedHashMap<>();out.put("comparisons",comparisons);out.put("ties",ties);
        out.put("distinctFactoryTies",distinctFactoryTies);out.put("lexBetterTies",lexBetterTies);
        out.put("componentwiseBetterTies",componentwiseBetterTies);out.put("samples",samples);return out;
    }
}
