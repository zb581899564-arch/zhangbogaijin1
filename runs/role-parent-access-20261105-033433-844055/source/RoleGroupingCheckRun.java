package org.uma.jmetal.util.research.search;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.cooperation.CooperationSupport;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import research.dynamic.DynamicJson;

/** Actual frozen grouping on paid objective/category snapshots; no evaluation or decoding. */
public final class RoleGroupingCheckRun {
    private RoleGroupingCheckRun() { }
    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]);System.setProperty("dhfsp.dataDir",input.getParent().toString());
        System.setProperty("dhfsp.setupFile",args[1]);System.setProperty("dhfsp.standbyPower","1.0");
        String[] d=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(d[0]),Integer.parseInt(d[1]),Integer.parseInt(d[2]),Integer.parseInt(d[3]));
        SeededRandom.reset(0);PermutationSolution<Integer> template=raw.createSolution();
        List<PermutationSolution<Integer>> population=new ArrayList<>();
        for(String line:Files.readAllLines(Paths.get(args[2]),StandardCharsets.UTF_8)) {
            String[] f=line.split("\t");
            @SuppressWarnings("unchecked") PermutationSolution<Integer> s=(PermutationSolution<Integer>)template.copy();
            int category=Integer.parseInt(f[0]);if(category>0)s.setAttribute("cooperation.family",category-1);
            double[] v=Arrays.stream(f[1].split(",")).mapToDouble(Double::parseDouble).toArray();
            for(int k=0;k<3;k++)s.setObjective(k,v[k]);population.add(s);
        }
        CooperationSupport support=new CooperationSupport(raw.getSchedulingInstance(),null,false);
        Map<String,Object> out=new LinkedHashMap<>();Map<Direction,List<Integer>> groups=support.grouping(population,15);
        for(Direction role:Direction.values())out.put(role.name(),groups.get(role));
        System.out.println(DynamicJson.encode(out));
    }
}
