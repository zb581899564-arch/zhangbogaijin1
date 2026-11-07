package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.DynamicSchedule;

/** Isolated, parameter-free secondary order, restricted to exact makespan ties. */
public final class MakespanTiePolicy {
    private static String mode=System.getProperty("research.makespan.tie","STRICT");
    private static long tiedComparisons,acceptedTies;
    private MakespanTiePolicy() { }

    public static void configure(String value) {
        if(!Arrays.asList("STRICT","FACTORY_LEX","COST_LEX","PARETO_SAFE").contains(value))throw new IllegalArgumentException(value);
        mode=value;tiedComparisons=acceptedTies=0;
    }

    static boolean better(PermutationSolution<Integer> child,PermutationSolution<Integer> parent) {
        double c=child.getObjective(0),p=parent.getObjective(0);
        if(c!=p)return c<p;
        tiedComparisons++;
        boolean keep=false;
        if(mode.equals("FACTORY_LEX")) {
            double[] a=factories(child),b=factories(parent);Arrays.sort(a);Arrays.sort(b);
            keep=lessDescending(a,b);
        } else if(mode.equals("COST_LEX")) {
            keep=child.getObjective(1)<parent.getObjective(1)
                || child.getObjective(1)==parent.getObjective(1)&&child.getObjective(2)<parent.getObjective(2);
        } else if(mode.equals("PARETO_SAFE")) {
            keep=ParetoTools.dominates(child,parent);
        } else if(!mode.equals("STRICT"))throw new IllegalStateException(mode);
        if(keep)acceptedTies++;
        return keep;
    }

    static boolean lessDescending(double[] ascendingA,double[] ascendingB) {
        if(ascendingA.length!=ascendingB.length)throw new IllegalArgumentException("Different factory counts");
        for(int j=ascendingA.length-1;j>=0;j--) {
            if(ascendingA[j]!=ascendingB[j])return ascendingA[j]<ascendingB[j];
        }
        return false;
    }

    private static double[] factories(PermutationSolution<Integer> s) {
        Object value=s.getAttribute(DynamicEvaluation.KEY);
        if(!(value instanceof DynamicSchedule))throw new IllegalStateException("Missing paid dynamic timeline");
        return ((DynamicSchedule)value).factoryMakespan();
    }

    public static Map<String,Object> diagnostics() {
        Map<String,Object> out=new LinkedHashMap<>();out.put("mode",mode);
        out.put("tiedComparisons",tiedComparisons);out.put("acceptedTies",acceptedTies);return out;
    }

    public static void main(String[] args) {
        if(!lessDescending(new double[]{1,4,10},new double[]{2,5,10}))throw new AssertionError("Hidden improvement");
        if(lessDescending(new double[]{1,4,11},new double[]{2,5,10}))throw new AssertionError("Primary maximum violated");
        if(lessDescending(new double[]{2,5,10},new double[]{2,5,10}))throw new AssertionError("Tie accepted");
        if(!lessDescending(new double[]{1,4,10},new double[]{2,4,10}))throw new AssertionError("Last factory ignored");
        System.out.println("MAKESPAN_LEX_GEOMETRY_CHECK_PASS zero decoder calls");
    }
}
