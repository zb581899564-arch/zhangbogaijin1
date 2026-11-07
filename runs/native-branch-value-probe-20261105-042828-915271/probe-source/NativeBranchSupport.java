package org.uma.jmetal.util.research.joint;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.*;

/** Shared import/state/witness helpers for one-step legal native branch diagnostics. */
final class NativeBranchSupport {
    private NativeBranchSupport() { }
    @SuppressWarnings("unchecked")
    static void fill(PermutationSolution<Integer>s,String[]f,int offset) {
        double[] expected=Arrays.stream(f[offset].split(",")).mapToDouble(Double::parseDouble).toArray();
        List<Integer> machines=(List<Integer>)s.getAttribute("machine");
        for(int k=0;k<4;k++) {
            int[]v=Arrays.stream(f[offset+1+k].split(",")).mapToInt(Integer::parseInt).toArray();
            for(int j=0;j<v.length;j++) {
                if(k==0)s.setVariableValue(j,v[j]);else if(k==1)s.setVariableValueid(j,v[j]);
                else if(k==2)machines.set(j,v[j]);else s.setVariableValueworker(j,v[j]);
            }
        }
        for(int k=0;k<3;k++)s.setObjective(k,expected[k]);
    }
    static PermutationSolution<Integer> completion(Instance in,PermutationSolution<Integer>parent,int begin,int length,JointAction action) {
        BlockContext block=new BlockContext(in,parent,begin,length);block.commit(action,block.afterWitness(action));
        while(block.remainingCount()>0){JointAction next=block.witness().get(0);block.commit(next,block.afterWitness(next));}
        return block.child(parent);
    }
    static Map<String,Object> prefix(Instance in,DynamicPrefix p) {
        boolean[] done=new boolean[in.jobs()];double[] ready=new double[in.jobs()];
        for(int j=0;j<in.jobs();j++){done[j]=p.completed(j);ready[j]=p.firstCompletion(j);}
        List<double[]> machines=new ArrayList<>(),workers=new ArrayList<>(),fatigue=new ArrayList<>();
        for(int f=0;f<in.factories();f++) {
            double[] m=new double[in.machines(f,0)],w=new double[in.workers(f,0)],h=new double[w.length];
            for(int i=0;i<m.length;i++)m[i]=p.machineEnd(f,i);
            for(int i=0;i<w.length;i++){w[i]=p.workerEnd(f,i);h[i]=p.workerFatigue(f,i);}
            machines.add(m);workers.add(w);fatigue.add(h);
        }
        return row("prefixSize",p.size(),"completedJobs",done,"firstCompletion",ready,"partialObjectives",p.partialObjectives(),
            "machineEnd",machines,"workerEnd",workers,"workerFatigue",fatigue);
    }
    static Map<String,Object> genome(PermutationSolution<Integer>s) {
        return row("JS",new ArrayList<>(s.getVariables()),"FA",new ArrayList<>(s.getVariablesid()),
            "MA",new ArrayList<>((List<?>)s.getAttribute("machine")),"WA",new ArrayList<>(s.getVariablesworker()));
    }
    static List<JointAction> future(Instance in,PermutationSolution<Integer>child,int from) {
        JointAction[] values=BlockContext.byJob(in,child,true);List<JointAction> out=new ArrayList<>();
        for(int i=from;i<in.jobs();i++)out.add(values[child.getVariableValue(i)]);return out;
    }
    static void sameTimeline(DynamicSchedule a,DynamicSchedule b) {
        if(!Arrays.equals(a.objectives(),b.objectives())||a.steps().size()!=b.steps().size())throw new AssertionError("Native witness objectives differ");
        for(int i=0;i<a.steps().size();i++) {
            DynamicStep x=a.steps().get(i),y=b.steps().get(i);
            if(x.job()!=y.job()||x.factory()!=y.factory()||x.stage()!=y.stage()||x.machine()!=y.machine()||x.worker()!=y.worker()
                ||!Arrays.equals(values(x),values(y)))throw new AssertionError("Native witness timeline differs");
        }
    }
    private static double[] values(DynamicStep x){return new double[]{x.start(),x.base(),x.duration(),x.setupDuration(),x.completion(),x.u(),x.v(),x.energy(),x.labor(),x.exposure()};}
    static Map<String,Object> row(Object...entries){Map<String,Object> out=new LinkedHashMap<>();for(int i=0;i<entries.length;i+=2)out.put((String)entries[i],entries[i+1]);return out;}
}
