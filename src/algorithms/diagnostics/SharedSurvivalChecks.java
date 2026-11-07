package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Zero-decoder fixture for last-composed-ancestor provenance and external archive identity. */
public final class SharedSurvivalChecks {
    private SharedSurvivalChecks() { }
    public static void main(String[] args) throws Exception {
        System.setProperty("dhfsp.dataDir",args[0]);System.setProperty("dhfsp.setupFile",args[1]);System.setProperty("dhfsp.standbyPower","1");
        EDHHFSPW problem=new EDHHFSPW(20,2,3,1);SeededRandom.reset(70003);
        SharedAncestry a=new SharedAncestry(3);PermutationSolution<Integer>s=problem.createSolution();
        for(int k=0;k<3;k++)s.setObjective(k,10);
        s.setAttribute(SharedAncestry.PAID,1);a.paid(s,1,0,false,"initialization",true);
        s.setAttribute(SharedAncestry.PAID,2);s.setObjective(0,9);a.paid(s,2,1,true,"global",true);
        a.selected(2,true,true);a.localEntry(2);
        s.setAttribute(SharedAncestry.PAID,3);s.setObjective(1,8);a.paid(s,3,2,false,"intra",true);
        if(a.root(3)!=2||a.parent(3)!=2)throw new AssertionError("Lost composed ancestor");
        Map<String,Object> result=a.finish(Collections.singletonList(s));
        List<?> roots=(List<?>)result.get("roots");Map<?,?> root=(Map<?,?>)roots.get(0);
        if(!root.get("directChildSelectedWithSibling").equals(true)||!root.get("finalPoints").equals(1L)
                ||!root.get("admissionsDominatingRoot").equals(1L))throw new AssertionError("Wrong ancestry accounting");
        System.out.println("SHARED_SURVIVAL_CHECKS_PASS zero decoder calls");
    }
}
