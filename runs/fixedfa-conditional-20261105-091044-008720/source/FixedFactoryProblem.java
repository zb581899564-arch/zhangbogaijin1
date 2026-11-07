package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.search.FactoryAssignmentEncoding;

/** Initialize a common fixed-FA feasible set; reject later drift rather than projecting paid candidates. */
public final class FixedFactoryProblem implements Problem<PermutationSolution<Integer>> {
    private static final long serialVersionUID=1L;
    private final DynamicEvaluation delegate;
    private final Instance instance;
    private final int[] fixed;
    private long created,checked,rejected;

    public FixedFactoryProblem(DynamicEvaluation delegate,Instance instance)throws Exception {
        this.delegate=delegate;this.instance=instance;
        if(Boolean.getBoolean("research.fixedFA.enabled")) {
            String filename=System.getProperty("research.fixedFA.file");
            if(filename==null)throw new IllegalArgumentException("Fixed FA file is required");
            String[] cells=new String(Files.readAllBytes(Paths.get(filename)),StandardCharsets.UTF_8).trim().split("[,\\s]+");
            fixed=Arrays.stream(cells).mapToInt(Integer::parseInt).toArray();
            if(fixed.length!=instance.jobs())throw new IllegalArgumentException("Fixed FA job count differs");
            int[] count=new int[instance.factories()];
            for(int f:fixed) {if(f<0||f>=count.length)throw new IllegalArgumentException("Fixed factory id invalid");count[f]++;}
            for(int n:count)if(n==0)throw new IllegalArgumentException("Fixed FA contains empty factory");
        } else fixed=null;
    }
    @Override public PermutationSolution<Integer> createSolution() {
        PermutationSolution<Integer> value=delegate.createSolution();created++;
        if(fixed!=null) {
            for(int p=0;p<value.getNumberOfVariables();p++)value.setVariableValueid(p,fixed[value.getVariableValue(p)]);
            SchedulingEncoding.repair(value,instance);
            requireFixed(value,false);
        }
        return value;
    }
    private void requireFixed(PermutationSolution<Integer> value,boolean countFailure) {
        if(!Arrays.equals(fixed,FactoryAssignmentEncoding.byJob(
                SchedulingEncoding.integers(value.getVariables()),SchedulingEncoding.integers(value.getVariablesid())))) {
            if(countFailure)rejected++;
            throw new IllegalStateException("FIXED_FA_DRIFT; candidate rejected before physical decode");
        }
    }
    @Override public void evaluate(PermutationSolution<Integer> value) {
        checked++;if(fixed!=null)requireFixed(value,true);
        delegate.evaluate(value);
        if(fixed!=null) {
            DynamicSchedule schedule=(DynamicSchedule)value.getAttribute(DynamicEvaluation.KEY);
            if(!Arrays.equals(fixed,FactoryAssignmentEncoding.byJob(schedule.js(),schedule.fa())))
                throw new AssertionError("Decoder changed fixed FA");
        }
    }
    @Override public int getNumberOfVariables(){return delegate.getNumberOfVariables();}
    @Override public int getNumberOfObjectives(){return delegate.getNumberOfObjectives();}
    @Override public int getNumberOfConstraints(){return delegate.getNumberOfConstraints();}
    @Override public String getName(){return delegate.getName();}
    public Map<String,Object> diagnostics() {
        Map<String,Object> out=new LinkedHashMap<>();out.put("enabled",fixed!=null);out.put("fixedFactoryByJob",fixed==null?null:fixed.clone());
        out.put("createdInitials",created);out.put("evaluationAttemptsChecked",checked);out.put("driftRejected",rejected);
        out.put("mutationMask",org.uma.jmetal.util.research.search.FixedFAMutationMask.diagnostics());
        out.put("evaluationProjectionUsed",false);return out;
    }
}
