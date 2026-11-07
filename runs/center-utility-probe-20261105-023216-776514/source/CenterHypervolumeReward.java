package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;

/** Optional CENTER retained-region utility. All information comes from paid initial/current groups. */
public final class CenterHypervolumeReward {
    private static final String MODE=System.getProperty("research.center.reward","MEAN");
    private static double[] reference;
    private static long calls,positive,negative,zero,nanos;
    private CenterHypervolumeReward() { }
    public static void initialize(List<PermutationSolution<Integer>> initial) {
        if(!Arrays.asList("MEAN","HV","ZERO").contains(MODE))throw new IllegalArgumentException("Unknown CENTER reward");
        if(!MODE.equals("HV"))return;
        reference=new double[3];for(PermutationSolution<Integer>s:initial)for(int k=0;k<3;k++)reference[k]=Math.max(reference[k],s.getObjective(k));
        for(int k=0;k<3;k++)reference[k]=reference[k]==0?1:1.1*reference[k];
    }
    static double compute(List<Particle> before,List<Particle> after,Direction role) {
        if(role!=Direction.CENTER||MODE.equals("MEAN"))return GroupReward.compute(before,after,role);
        long start=System.nanoTime();double reward=0;
        if(MODE.equals("HV"))reward=groupVolume(after)-groupVolume(before);
        calls++;if(reward>0)positive++;else if(reward<0)negative++;else zero++;
        nanos+=System.nanoTime()-start;return reward;
    }
    private static double groupVolume(List<Particle> group) {
        double[][] points=new double[group.size()][];for(int i=0;i<group.size();i++)points[i]=group.get(i).current.getObjectives();
        return volume(points,reference);
    }
    /** Exact3D box sweep in double precision, normalized to reference-box volume. */
    static double volume(double[][] values,double[] ref) {
        List<double[]> points=new ArrayList<>();
        for(double[] raw:values) {
            double[] p={raw[0]/ref[0],raw[1]/ref[1],raw[2]/ref[2]};
            if(p[0]<1&&p[1]<1&&p[2]<1)points.add(p);
        }
        points.sort((a,b)->{for(int k=0;k<3;k++){int c=Double.compare(a[k],b[k]);if(c!=0)return c;}return 0;});
        List<double[]> active=new ArrayList<>();double previous=0,total=0;
        for(double[] p:points) {
            total+=(p[0]-previous)*area(active);active.add(p);previous=p[0];
        }
        return total+(1-previous)*area(active);
    }
    private static double area(List<double[]> points) {
        List<double[]> order=new ArrayList<>(points);
        order.sort((a,b)->{int c=Double.compare(a[1],b[1]);return c==0?Double.compare(a[2],b[2]):c;});
        double previous=0,best=1,total=0;
        for(double[] p:order) {total+=(p[1]-previous)*(1-best);best=Math.min(best,p[2]);previous=p[1];}
        return total+(1-previous)*(1-best);
    }
    public static Map<String,Object> diagnostics() {
        Map<String,Object> out=new LinkedHashMap<>();out.put("mode",MODE);out.put("reference",reference);out.put("centerCalls",calls);
        out.put("positive",positive);out.put("negative",negative);out.put("zero",zero);out.put("utilitySeconds",nanos/1e9);return out;
    }
}
