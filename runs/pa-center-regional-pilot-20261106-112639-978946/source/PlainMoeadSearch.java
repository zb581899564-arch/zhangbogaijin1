package research.dynamic;

import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.classic.*;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.runtime.RunContext;

/** Explicit MOEA/D dispatch; both independently sourced adapters use the same canonical100 initials. */
final class PlainMoeadSearch implements Algorithm<Object> {
    private static final long serialVersionUID=1L;
    private final RunContext<PermutationSolution<Integer>> run;private final Instance instance;private final boolean reference;
    private OrdinaryMoeadAlgorithm current;private MoeadReferenceAlgorithm original;
    PlainMoeadSearch(RunContext<PermutationSolution<Integer>> context,Instance input,boolean useReference){run=context;instance=input;reference=useReference;}
    public void run(){
        ClassicConfig config=new ClassicConfig("MOEAD_4V",0);
        if(reference){original=new MoeadReferenceAlgorithm(run.problem(),instance,config,run::checkpoint);original.run();}
        else {current=new OrdinaryMoeadAlgorithm(run.problem(),instance,config,run::checkpoint);current.run();}
    }
    Map<String,Object> diagnostics(){return original!=null?original.diagnostics():current!=null?current.diagnostics():Collections.emptyMap();}
    String executedClass(){return original!=null?original.getClass().getName():current!=null?current.getClass().getName():"NOT_STARTED";}
    public Object getResult(){return null;}
    public String getName(){return "MOEAD_4V";}
    public String getDescription(){return "Explicit ordinary discrete MOEA/D,setting0,canonical100initials,no local-search invocation";}
}
