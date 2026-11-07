package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Demonstrate the PDDR tie consequence inside a personal ND history, without evaluating a schedule. */
public final class PersonalHistorySemanticsCheck {
    private PersonalHistorySemanticsCheck() { }
    public static void main(String[] args) throws Exception {
        System.setProperty("dhfsp.dataDir",args[0]);System.setProperty("dhfsp.setupFile",args[1]);System.setProperty("dhfsp.standbyPower","1");
        EDHHFSPW problem=new EDHHFSPW(20,2,3,1);SeededRandom.reset(1117003);
        double[][] values={{1,3,3},{3,1,3},{3,3,1}};
        int[][] orders={{0,1,2},{0,2,1},{1,0,2},{1,2,0},{2,0,1},{2,1,0}};
        for(int[] order:orders) {
            Particle particle=null;
            for(int index:order) {
                PermutationSolution<Integer>s=problem.createSolution();for(int k=0;k<3;k++)s.setObjective(k,values[index][k]);
                particle=particle==null?new Particle(s):particle.descend(s);
            }
            if(particle.personalArchive().size()!=3)throw new AssertionError("Fixture is not a three-point ND archive");
            if(!Arrays.equals(particle.personalBest(Direction.CENTER).getObjectives(),values[order[0]]))throw new AssertionError("CENTER did not keep first ND insertion");
            if(!Arrays.equals(particle.current.getObjectives(),values[order[2]]))throw new AssertionError("Fixture current mismatch");
        }
        System.out.println("PERSONAL_HISTORY_SEMANTICS_CONFIRMED six insertion orders, oldest surviving ND insertion selected; zero decoder calls");
    }
}
