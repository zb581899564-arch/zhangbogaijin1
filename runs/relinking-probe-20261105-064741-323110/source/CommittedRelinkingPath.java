package research.dynamic;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.Instance;

/** One legal complete encoding per committed job, ending at the already-paid teacher. */
final class CommittedRelinkingPath {
    private final Instance in;private final String method;
    private final int[] targetSequence,targetPositions,commitOrder;
    private final int[][] target;
    private final boolean[] committed;
    private PermutationSolution<Integer> current;
    int auxiliaryJobs,repairEdits,committedViolations,endpointRestorationEdits;

    CommittedRelinkingPath(Instance in,PermutationSolution<Integer> parent,PermutationSolution<Integer> teacher,String method,long seed) {
        this.in=in;this.method=method;current=parent;
        targetSequence=sequence(teacher);target=byJob(teacher);targetPositions=new int[in.jobs()];committed=new boolean[in.jobs()];
        for(int p=0;p<in.jobs();p++)targetPositions[targetSequence[p]]=p;
        commitOrder=targetSequence.clone();
        if(method.equals("RANDOM_PATH")) {
            Random random=new Random(seed);
            for(int p=commitOrder.length-1;p>0;p--){int q=random.nextInt(p+1),saved=commitOrder[p];commitOrder[p]=commitOrder[q];commitOrder[q]=saved;}
        }
        checkEncoding(parent,in);checkEncoding(teacher,in);
    }
    @SuppressWarnings("unchecked")
    PermutationSolution<Integer> next(int step) {
        PermutationSolution<Integer> child=(PermutationSolution<Integer>)current.copy();
        int[] order=sequence(current);int[][] genes=byJob(current);int job=commitOrder[step];
        int oldPosition=-1;for(int p=0;p<order.length;p++)if(order[p]==job)oldPosition=p;
        int position=targetPositions[job],displaced=order[position];order[position]=job;order[oldPosition]=displaced;
        auxiliaryJobs=0;endpointRestorationEdits=0;
        if(method.equals("REPAIR_PATH"))genes[job]=target[job].clone();
        else auxiliaryJobs=FactoryCoverTransfer.apply(genes,target,committed,job,in.factories());
        committed[job]=true;
        if(method.equals("REPAIR_PATH")&&step==order.length-1) {
            for(int j=0;j<genes.length;j++)for(int k=0;k<3;k++)if(genes[j][k]!=target[j][k])endpointRestorationEdits++;
            for(int p=0;p<order.length;p++)if(order[p]!=targetSequence[p])endpointRestorationEdits++;
            order=targetSequence.clone();for(int j=0;j<genes.length;j++)genes[j]=target[j].clone();
        }
        write(child,order,genes);repairEdits=SchedulingEncoding.repair(child,in);checkEncoding(child,in);
        if(!method.equals("REPAIR_PATH")&&repairEdits!=0)throw new AssertionError("Cover construction required generic repair");
        committedViolations=violations(child);
        if(!method.equals("REPAIR_PATH")&&committedViolations!=0)throw new AssertionError("A committed tuple was changed");
        current=child;return child;
    }
    private int violations(PermutationSolution<Integer> s) {
        int result=0;int[] order=sequence(s);int[][] genes=byJob(s);
        for(int j=0;j<genes.length;j++)if(committed[j]&&(order[targetPositions[j]]!=j||!Arrays.equals(genes[j],target[j])))result++;
        return result;
    }
    static boolean sameEncoding(PermutationSolution<Integer> a,PermutationSolution<Integer> b) {
        return Arrays.equals(sequence(a),sequence(b))&&Arrays.deepEquals(byJob(a),byJob(b));
    }
    static void checkEncoding(PermutationSolution<Integer> s,Instance in) {
        int[][] values=byJob(s);int[] counts=new int[in.factories()];
        for(int j=0;j<values.length;j++) {
            int[] value=values[j];int f=value[0];
            if(f<0||f>=counts.length||value[1]<0||value[1]>=in.machines(f,0)||value[2]<0||value[2]>=in.workers(f,0))
                throw new AssertionError("Illegal complete path tuple");counts[f]++;
        }
        for(int count:counts)if(count==0)throw new AssertionError("Path emptied a factory");
    }
    static int[] sequence(PermutationSolution<Integer> s) {
        int[] out=new int[s.getNumberOfVariables()];for(int p=0;p<out.length;p++)out[p]=s.getVariableValue(p);return out;
    }
    @SuppressWarnings("unchecked")
    private static int[][] byJob(PermutationSolution<Integer> s) {
        int[][] values=new int[s.getNumberOfVariables()][];List<Integer> machines=(List<Integer>)s.getAttribute("machine");
        for(int p=0;p<values.length;p++) {
            int j=s.getVariableValue(p);if(j<0||j>=values.length||values[j]!=null)throw new AssertionError("Invalid job permutation");
            values[j]=new int[]{s.getVariableValueid(p),machines.get(p),s.getVariableValueworker(p)};
        }return values;
    }
    @SuppressWarnings("unchecked")
    private static void write(PermutationSolution<Integer> s,int[] order,int[][] genes) {
        List<Integer> machines=(List<Integer>)s.getAttribute("machine");
        for(int p=0;p<order.length;p++) {
            int j=order[p];s.setVariableValue(p,j);s.setVariableValueid(p,genes[j][0]);
            machines.set(p,genes[j][1]);s.setVariableValueworker(p,genes[j][2]);
        }
    }
}
