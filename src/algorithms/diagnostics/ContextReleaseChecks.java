package org.uma.jmetal.util.research.cooperation;

import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.search.Direction;

/** Zero-search-FE certificate, family-release and population/quota checks. */
public final class ContextReleaseChecks {
    private ContextReleaseChecks() { }
    public static void main(String[] args) throws Exception {
        System.setProperty("dhfsp.dataDir",args[0]);System.setProperty("dhfsp.setupFile",args[1]);System.setProperty("dhfsp.standbyPower","1");
        EDHHFSPW problem=new EDHHFSPW(20,2,3,1);
        org.uma.jmetal.util.research.runtime.SeededRandom.reset(1234567);
        List<List<double[]>> pools=Arrays.asList(Arrays.asList(new double[]{5,10,20},new double[]{7,8,19}),
                Arrays.asList(new double[]{4,11,15},new double[]{8,9,17}));
        double[] bound=ContextRelease.lowerBound(pools);
        PermutationSolution<Integer> witness=problem.createSolution();
        witness.setObjective(0,4);witness.setObjective(1,16);witness.setObjective(2,33);
        List<PermutationSolution<Integer>> known=Collections.singletonList(witness);
        if(!ContextRelease.covered(bound,known))throw new AssertionError("Missed coverage");
        for(double[] a:pools.get(0))for(double[] b:pools.get(1)) {
            double[] combined={Math.max(a[0],b[0]),a[1]+b[1],a[2]+b[2]};
            for(int k=0;k<3;k++)if(witness.getObjective(k)>combined[k])throw new AssertionError("False certificate");
        }
        witness.setObjective(0,6);if(ContextRelease.covered(bound,known))throw new AssertionError("Uncovered pool certified");
        if(ContextRelease.lowerBound(Arrays.asList(Collections.emptyList()))!=null)throw new AssertionError("Empty pool bound");
        FamilyContexts contexts=new FamilyContexts(problem.getSchedulingInstance());List<PermutationSolution<Integer>> pop=new ArrayList<>();
        for(int i=0;i<100;i++){PermutationSolution<Integer>s=problem.createSolution();contexts.initialize(s,i);for(int k=0;k<3;k++)s.setObjective(k,i+1);pop.add(s);}
        ContextRelease.releaseForCheck(0);ContextRelease.releaseForCheck(2);
        Map<Direction,List<Integer>> groups=contexts.grouping(pop,15);
        for(Direction d:Direction.values())if(groups.get(d).size()!=(d==Direction.CENTER?55:15))throw new AssertionError("Role quota changed");
        if(!Arrays.equals(ContextRelease.quotas(),new int[]{90,0,5,0,5}))throw new AssertionError("Release quota mismatch");
        if(pop.get(0).getAttribute(FamilyContexts.FIXED)!=null || ContextRelease.category(pop.get(0))!=0)throw new AssertionError("Protection remained");
        int before=pop.get(0).getVariableValueid(0);pop.get(0).setVariableValueid(0,(before+1)%3);contexts.restore(pop.get(0));
        if(pop.get(0).getVariableValueid(0)==before)throw new AssertionError("Released FA restored");
        contexts.restore(pop.get(5));contexts.validate(pop.get(5));
        System.out.println("CONTEXT_RELEASE_CHECKS_PASS zero search FE");
    }
}
