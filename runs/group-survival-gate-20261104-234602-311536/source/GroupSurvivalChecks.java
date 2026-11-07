package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Zero-FE known-order fixture: two descendants of one useful lineage may replace an inferior lineage. */
public final class GroupSurvivalChecks {
    private GroupSurvivalChecks() { }
    public static void main(String[] args) throws Exception {
        System.setProperty("dhfsp.dataDir",args[0]);System.setProperty("dhfsp.setupFile",args[1]);System.setProperty("dhfsp.standbyPower","1.0");
        SeededRandom.reset(1);EDHHFSPW raw=new EDHHFSPW(20,2,3,1);List<Particle> old=new ArrayList<>(),child=new ArrayList<>();
        for(int i=0;i<3;i++){
            PermutationSolution<Integer> s=raw.createSolution();s.setObjective(0,new double[]{10,100,50}[i]);s.setObjective(1,10+i);s.setObjective(2,20+i);
            if(i==2)s.setAttribute("cooperation.family",0);old.add(new Particle(s));
            PermutationSolution<Integer> c=ParetoTools.copy(s);c.setObjective(0,new double[]{5,110,49}[i]);child.add(old.get(i).descend(c));
        }
        List<Particle> selected=GlobalGroupPolicy.select(old,child,Direction.MAKESPAN);
        double sum=0;int family=0;for(Particle p:selected){sum+=p.current.getObjective(0);if(p.current.getAttribute("cooperation.family")!=null)family++;}
        if(sum!=64||family!=1)throw new AssertionError("Set selection or quotas failed");
        double a=GroupReward.compute(old,selected,Direction.CENTER);Collections.reverse(selected);
        if(Math.abs(a-GroupReward.compute(old,selected,Direction.CENTER))>1e-12)throw new AssertionError("Reward is order dependent");
        System.out.println("GROUP_SURVIVAL_CHECKS_PASS FE=0 set elitism;family quota;permutation-invariant group reward");
    }
}
