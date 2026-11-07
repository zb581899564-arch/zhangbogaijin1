package org.uma.jmetal.util.research.modelglobal;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.search.TrajectoryTrace;

/** Package bridge reads immutable states without exposing them to the search policy. */
public final class PaTrajectoryBridge {
    private PaTrajectoryBridge() { }
    public static void proposal(int generation,int slot,PaIndividual parent,PaIndividual donor) {
        TrajectoryTrace.paProposal(parent.point,parent.role,slot,generation,donor.point);
    }
    public static void population(String label,List<PaIndividual> values) {
        List<PermutationSolution<Integer>> points=new ArrayList<>();
        for(PaIndividual value:values)points.add(value.point);
        TrajectoryTrace.population(label,points);
    }
    public static void program(int slot,PaIndividual value) {TrajectoryTrace.program(value.point,slot,value.role);}
}
