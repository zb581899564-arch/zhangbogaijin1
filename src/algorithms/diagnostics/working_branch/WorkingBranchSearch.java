package research.dynamic;

import java.io.*;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.modelglobal.*;
import org.uma.jmetal.util.research.runtime.RunContext;

/** Four bounded treatments; each branch owns its accepted state and its archive. */
final class WorkingBranchSearch implements Algorithm<Void> {
    static final String[] ARMS={"ONE","RESTART","CURRENT","BRANCH"};
    private static final class State {
        final TypedScheduleGenome genome;final double[] objectives;final long fee;final String id;
        State(TypedScheduleGenome g,double[] a,long n,String key){genome=g;objectives=a.clone();fee=n;id=key;}
    }
    private final RunContext<PermutationSolution<Integer>> run;
    private final Instance instance;private final DynamicParameters params;private final WorkingBranchData data;
    private final BufferedWriter paid,endpoints;
    long written,programs;String pending;
    WorkingBranchSearch(RunContext<PermutationSolution<Integer>> r,Instance in,DynamicParameters p,
                        WorkingBranchData d,BufferedWriter output,BufferedWriter ends) {
        run=r;instance=in;params=p;data=d;paid=output;endpoints=ends;
    }
    private static void append(BufferedWriter out,Map<String,Object> row) {
        try{out.write(DynamicJson.encode(row));out.newLine();out.flush();}catch(IOException e){throw new UncheckedIOException(e);}
    }
    private State evaluate(WorkingBranchData.Case c,String arm,int branch,int step,String seedTag,
            CounterfactualInputs.Entry entry,State parent,PaInternalArchive archive,WorkingBranchData.Move move,boolean fallback) {
        pending=entry.id;PermutationSolution<Integer> p=CounterfactualInputs.point(run.problem(),entry);
        run.problem().evaluate(p);DynamicSchedule s=(DynamicSchedule)p.getAttribute(DynamicEvaluation.KEY);
        DynamicValidator.validate(instance,params,s);double[] obj=s.objectives();
        if(parent==null)for(int k=0;k<3;k++)if(Double.doubleToLongBits(obj[k])!=Double.doubleToLongBits(entry.expected[k]))
            throw new AssertionError("Paid seed differs from known input: "+entry.id);
        PaInternalArchive.Flags flags=archive.offer(obj);
        boolean keep=parent==null || WorkingBranchRules.keep(c.role,obj,parent.objectives,flags);
        long fee=run.budget().successful();Map<String,Object> row=CounterfactualInputs.record(entry,s,fee);
        row.put("case",c.id);row.put("context",c.context);row.put("role",c.role.name());row.put("arm",arm);
        row.put("branch",branch);row.put("step",step);row.put("seedTag",seedTag);row.put("isSeed",parent==null);
        row.put("parentNumber",parent==null?0:parent.fee);row.put("accepted",parent==null?null:keep);
        row.put("archiveDominated",flags.dominated);row.put("archiveEqual",flags.equal);
        row.put("archiveBefore",flags.before);row.put("archiveAfter",flags.after);
        row.put("node",move==null?-1:move.node);row.put("donorSlot",move==null?-1:move.donor);
        row.put("maskJobs",move==null?null:move.mask);row.put("fallback",fallback);
        append(paid,row);written++;pending=null;
        return keep ? new State(data.genome(entry),obj,fee,entry.id) : parent;
    }
    private void program(WorkingBranchData.Case c,String arm,int branch,String seedTag,int steps) {
        PaInternalArchive archive=data.archive(c);CounterfactualInputs.Entry seed=data.seed(c,seedTag);
        String prefix=c.id+"-"+arm+"-"+branch;long first=run.budget().successful()+1;
        State state=evaluate(c,arm,branch,-1,seedTag,data.entry(prefix+"-INIT",data.genome(seed),seed.expected),null,archive,null,false);
        for(int k=0;k<steps;k++) {
            WorkingBranchData.Move move=data.plans.get(c.id).get(branch).get(k);
            TypedScheduleGenome donor=data.donors.get(c.context).get(move.donor);
            PaMixingMove mixed=PaMixingMove.apply(data.catalog,state.genome,donor,move.mask);
            state=evaluate(c,arm,branch,k,seedTag,data.entry(prefix+"-"+k,mixed.genome),state,archive,move,mixed.fallback);
        }
        CounterfactualInputs.Entry end=data.entry(prefix+"-END",state.genome);Map<String,Object> row=new LinkedHashMap<>();
        row.put("case",c.id);row.put("context",c.context);row.put("role",c.role.name());row.put("arm",arm);
        row.put("branch",branch);row.put("seedTag",seedTag);row.put("seedNumber",first);row.put("lastAcceptedNumber",state.fee);
        row.put("lastAcceptedId",state.id);row.put("lastGeneratedNumber",run.budget().successful());row.put("programFE",steps+1);
        row.put("resources",end.resources);row.put("keys",end.keys);row.put("JS",end.vectors.jobs());row.put("FA",end.vectors.factories());
        row.put("MA",end.vectors.machines());row.put("WA",end.vectors.workers());row.put("objectives",state.objectives);
        row.put("wouldCommit",WorkingBranchRules.commit(c.role,state.objectives,data.seed(c,"P").expected,data.archives.get(c.context)));
        row.put("freshToA0",WorkingBranchRules.fresh(state.objectives,data.archives.get(c.context)));row.put("fromSuccessor",state.fee>first);
        append(endpoints,row);programs++;
    }
    @Override public void run() {
        for(WorkingBranchData.Case c:data.cases)for(String arm:ARMS) {
            long before=run.budget().successful();program(c,arm,0,"P",arm.equals("ONE")?31:15);
            if(!arm.equals("ONE"))program(c,arm,1,arm.equals("CURRENT")?"R":arm.equals("BRANCH")?"Q":"P",15);
            if(run.budget().successful()-before!=32)throw new AssertionError("Treatment cost differs");
        }
    }
    @Override public Void getResult(){return null;}
    @Override public String getName(){return "BOUNDED_WORKING_BRANCH";}
    @Override public String getDescription(){return "Fixed donor/model short programs; no production changes";}
}
