package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;

/** Parent-union-child set survival, with unchanged per-family quotas and an explicit duplicate control. */
public final class GlobalGroupPolicy {
    private static final String MODE = System.getProperty("research.group.mode", "PAIR");
    private static final Map<String,Long> counts = new LinkedHashMap<>();
    private GlobalGroupPolicy() { }
    private static void add(String k,long n) { counts.put(k,counts.getOrDefault(k,0L)+n); }
    private static int category(Particle p) {
        Object family=p.current.getAttribute("cooperation.family"); return family == null ? 0 : (Integer)family+1;
    }
    private static Map<Integer,Integer> categories(List<Particle> p) {
        Map<Integer,Integer> out=new LinkedHashMap<>();
        for (Particle x:p) out.put(category(x),out.getOrDefault(category(x),0)+1); return out;
    }
    static List<Particle> select(List<Particle> parents,List<Particle> children,Direction role) {
        if (MODE.equals("PAIR")) return GlobalBatchPolicy.select(parents,children,role);
        if (!Arrays.asList("FULL_ROLE","FULL_ALL","FULL_DUP").contains(MODE)) throw new IllegalArgumentException("Unknown set policy");
        if (parents.size()!=children.size()) throw new IllegalArgumentException("Batch size changed");
        List<Particle> pool=new ArrayList<>(parents);pool.addAll(children);
        List<PermutationSolution<Integer>> values=new ArrayList<>();for (Particle p:pool) values.add(p.current);
        int[] rank=GlobalBatchPolicy.ranks(values);double[] crowd=GlobalBatchPolicy.crowding(values,rank);
        List<Integer> order=new ArrayList<>();for(int i=0;i<pool.size();i++)order.add(i);
        boolean multi=role==Direction.CENTER||MODE.equals("FULL_ALL");
        order.sort((a,b)->{
            if(!multi){int c=Double.compare(values.get(a).getObjective(role.objective()),values.get(b).getObjective(role.objective()));if(c!=0)return c;}
            int c=Integer.compare(rank[a],rank[b]);if(c!=0)return c;
            c=Double.compare(crowd[b],crowd[a]);return c!=0?c:Integer.compare(a,b);
        });
        Map<Integer,Integer> remaining=categories(parents);Set<Integer> selected=new HashSet<>();Set<String> seen=new HashSet<>();
        List<Particle> out=new ArrayList<>();
        for(int pass=0;pass<2;pass++) for(int i:order){
            Particle p=pool.get(i);int cat=category(p);
            String key=cat+":"+Arrays.toString(p.current.getObjectives());
            if(selected.contains(i)||remaining.getOrDefault(cat,0)==0)continue;
            if(pass==0&&!MODE.equals("FULL_DUP")&&seen.contains(key))continue;
            out.add(p);selected.add(i);seen.add(key);remaining.put(cat,remaining.get(cat)-1);
        }
        if(out.size()!=parents.size()||!categories(out).equals(categories(parents)))throw new AssertionError("Family quota changed");
        Set<Long> original=new HashSet<>(),survived=new HashSet<>();for(Particle p:parents)original.add(p.lineageId());for(Particle p:out)survived.add(p.lineageId());
        original.removeAll(survived);add("retiredLineages."+role.name(),original.size());
        add("survivors."+role.name(),out.size());
        add("selectedChildren."+role.name(),selected.stream().filter(i->i>=parents.size()).count());
        MatingSourceAudit.selected(out, role);
        return out;
    }
    public static Map<String,Object> diagnostics(){Map<String,Object> out=new LinkedHashMap<>();out.put("mode",MODE);out.put("counts",counts);out.put("reward",GroupReward.mode());return out;}
}
