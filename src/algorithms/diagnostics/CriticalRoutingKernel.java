package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.DynamicSchedule;
import org.uma.jmetal.util.research.model.Instance;

/** Unchanged actual VNS with only its per-restart factory argument varied. */
public final class CriticalRoutingKernel {
    private final LocalSearch local;private final Instance in;private final Runnable checkpoint;
    private long calls,redirects,switches;
    public CriticalRoutingKernel(Problem<PermutationSolution<Integer>> problem,Instance in,Runnable checkpoint) {
        this.in=in;this.checkpoint=checkpoint;SearchState state=new SearchState(problem,in,null);
        state.observationGroup(Direction.MAKESPAN);local=new LocalSearch(in,4,new SearchConfig().resolved(4),state);
    }
    public PermutationSolution<Integer> run(PermutationSolution<Integer> parent,int fallback,String mode,int quota,long policySeed) {
        if(!Arrays.asList("FROZEN","RANDOM","CRITICAL").contains(mode))throw new IllegalArgumentException("Unknown routing mode");
        int[] remaining={quota};Random policy=new Random(policySeed);PermutationSolution<Integer> current=parent;int previous=-1;
        while(remaining[0]>0) {
            checkpoint.run();int random=policy.nextInt(in.factories());int factory=mode.equals("FROZEN")?fallback:mode.equals("RANDOM")?random:critical(current,fallback);
            calls++;if(factory!=fallback)redirects++;if(previous>=0&&previous!=factory)switches++;previous=factory;
            int before=remaining[0];current=local.vns(current,factory,Direction.MAKESPAN,Collections.singletonList(parent),remaining);
            if(remaining[0]>=before)throw new AssertionError("VNS made no paid progress");
        }return current;
    }
    private static int critical(PermutationSolution<Integer> parent,int fallback) {
        DynamicSchedule schedule=(DynamicSchedule)parent.getAttribute(DynamicEvaluation.KEY);double[] times=schedule.factoryMakespan();
        int best=0;for(int f=1;f<times.length;f++)if(times[f]>times[best])best=f;
        return times[fallback]==times[best]?fallback:best;
    }
    public Map<String,Object> diagnostics() {
        Map<String,Object> out=new LinkedHashMap<>();out.put("vnsCalls",calls);out.put("redirectsFromFrozen",redirects);out.put("factorySwitches",switches);return out;
    }
}
