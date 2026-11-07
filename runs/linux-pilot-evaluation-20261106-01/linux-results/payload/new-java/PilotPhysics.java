package research.dynamic;

import java.lang.reflect.Method;
import java.util.*;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;

/** Engineering-only full timeline equivalence and a deliberately charged failure fixture. */
final class PilotPhysics {
    private static final String[] FIELDS={"job","factory","stage","machine","worker","start","base","duration",
        "setupDuration","completion","u","v","energy","labor","exposure"};
    private final Instance in;
    private final DynamicParameters params;
    private long checks,nanos;
    PilotPhysics(Instance value,DynamicParameters fatigue){in=value;params=fatigue;}
    void check(PermutationSolution<Integer> p) {
        if(!Boolean.getBoolean("research.pilot.physics"))return;
        long start=System.nanoTime();DynamicSchedule paid=(DynamicSchedule)p.getAttribute(DynamicEvaluation.KEY);
        DynamicSchedule full=DynamicDecoder.full(in,params,paid.js(),paid.fa(),paid.ma(),paid.wa(),()->{});
        DynamicValidator.validate(in,params,full);
        if(!Arrays.equals(full.objectives(),paid.objectives())||full.steps().size()!=paid.steps().size())throw new AssertionError("Physics differs");
        try {
            for(String field:FIELDS){Method method=DynamicStep.class.getMethod(field);
                for(int i=0;i<full.steps().size();i++)if(!method.invoke(full.steps().get(i)).equals(method.invoke(paid.steps().get(i))))
                    throw new AssertionError("Timeline differs: "+field+" at "+i);
            }
        }catch(ReflectiveOperationException e){throw new IllegalStateException(e);}
        checks++;nanos+=System.nanoTime()-start;
    }
    Map<String,Object> receipt(){Map<String,Object> r=new LinkedHashMap<>();r.put("fullTimelineChecks",checks);r.put("engineeringOnlySeconds",nanos/1e9);return r;}
    static Problem<PermutationSolution<Integer>> delegate(DynamicEvaluation decoder) {
        final long failAt=Long.getLong("research.pilot.failAt",-1L);
        if(failAt<0)return decoder;
        return new Problem<PermutationSolution<Integer>>() {
            private static final long serialVersionUID=1L;private long attempts;
            public void evaluate(PermutationSolution<Integer> p){if(++attempts==failAt)throw new IllegalStateException("EXPECTED_PAID_FAILURE");decoder.evaluate(p);}
            public PermutationSolution<Integer> createSolution(){return decoder.createSolution();}
            public int getNumberOfVariables(){return decoder.getNumberOfVariables();}
            public int getNumberOfObjectives(){return 3;}
            public int getNumberOfConstraints(){return decoder.getNumberOfConstraints();}
            public String getName(){return "ENGINEERING_FAILURE_WRAPPER";}
        };
    }
}
