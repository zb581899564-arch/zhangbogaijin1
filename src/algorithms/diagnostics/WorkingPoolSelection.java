package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;

/** Offline standard rank/crowding truncation, preserving the exact original family counts. */
final class WorkingPoolSelection {
    private WorkingPoolSelection() { }
    static int category(Particle p) {
        Object value=p.current.getAttribute("cooperation.family");return value==null?0:(Integer)value+1;
    }
    static int[] quotas(List<Particle> points) {
        int[] counts=new int[5];for(Particle p:points)counts[category(p)]++;return counts;
    }
    static List<Particle> select(List<Particle> pool,int[] quotas) {
        List<PermutationSolution<Integer>> values=new ArrayList<>();for(Particle p:pool)values.add(p.current);
        int[] rank=GlobalBatchPolicy.ranks(values);double[] crowd=GlobalBatchPolicy.crowding(values,rank);
        List<Integer> order=new ArrayList<>();for(int i=0;i<pool.size();i++)order.add(i);
        order.sort((a,b)->{int c=Integer.compare(rank[a],rank[b]);if(c!=0)return c;
            c=Double.compare(crowd[b],crowd[a]);return c!=0?c:Integer.compare(a,b);});
        int[] remaining=quotas.clone();Set<Integer> selected=new HashSet<>();Set<String> seen=new HashSet<>();List<Particle> out=new ArrayList<>();
        for(int pass=0;pass<2;pass++)for(int index:order) {
            Particle p=pool.get(index);int category=category(p);String key=category+":"+Arrays.toString(p.current.getObjectives());
            if(selected.contains(index)||remaining[category]==0||pass==0&&seen.contains(key))continue;
            out.add(p);selected.add(index);seen.add(key);remaining[category]--;
        }
        if(!Arrays.equals(quotas,quotas(out)))throw new AssertionError("Offline family counts changed");return out;
    }
}
