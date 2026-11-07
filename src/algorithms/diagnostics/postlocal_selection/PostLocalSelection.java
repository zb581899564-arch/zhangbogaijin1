package org.uma.jmetal.util.research.search;

import java.util.*;

/** Calls the unchanged role-local selector and records every chosen pool index. */
final class PostLocalSelection {
    final List<Map<String,Object>> groups=new ArrayList<>();
    List<PostLocalData.Member> select(List<PostLocalData.Member> parents,List<PostLocalData.Member> children) {
        List<PostLocalData.Member> result=new ArrayList<>();
        for(Direction role:Direction.values()) {
            List<PostLocalData.Member> p=members(parents,role),c=members(children,role),pool=new ArrayList<>(p);pool.addAll(c);
            List<Particle> a=particles(p),b=particles(c);List<Particle> selected=GlobalGroupPolicy.select(a,b,role);
            List<Integer> indices=new ArrayList<>();
            for(Particle particle:selected) {
                int index=identityIndex(pool,particle);indices.add(index);result.add(pool.get(index));
            }
            groups.add(GomRecords.row("role",role.name(),"parents",PostLocalData.records(p),"children",PostLocalData.records(c),
                "selectedPoolIndices",indices,"parentFamilyQuotas",quotas(p),"selectedFamilyQuotas",quotas(selected,pool)));
        }
        if(result.size()!=100)throw new AssertionError("Selection changed population size");return result;
    }
    private static List<PostLocalData.Member> members(List<PostLocalData.Member> points,Direction role) {
        List<PostLocalData.Member> result=new ArrayList<>();for(PostLocalData.Member point:points)if(point.role==role)result.add(point);return result;
    }
    private static List<Particle> particles(List<PostLocalData.Member> points) {
        List<Particle> result=new ArrayList<>();for(PostLocalData.Member point:points)result.add(point.particle);return result;
    }
    private static int identityIndex(List<PostLocalData.Member> pool,Particle point) {
        for(int i=0;i<pool.size();i++)if(pool.get(i).particle==point)return i;throw new AssertionError("Selector returned an unknown particle");
    }
    private static Map<Integer,Integer> quotas(List<PostLocalData.Member> points) {
        Map<Integer,Integer> result=new TreeMap<>();for(PostLocalData.Member point:points)result.put(point.family,result.getOrDefault(point.family,0)+1);return result;
    }
    private static Map<Integer,Integer> quotas(List<Particle> selected,List<PostLocalData.Member> pool) {
        List<PostLocalData.Member> points=new ArrayList<>();for(Particle p:selected)points.add(pool.get(identityIndex(pool,p)));return quotas(points);
    }
}
