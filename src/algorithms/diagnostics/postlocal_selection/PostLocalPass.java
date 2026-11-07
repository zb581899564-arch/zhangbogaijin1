package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.runtime.*;

/** One unmodified native program per receiver, including live accepted donor states. */
final class PostLocalPass {
    private final RunContext<PermutationSolution<Integer>> run;
    private final Instance instance;
    private final GomRunScope scope;
    private final PostLocalArchives archives;
    private final PostLocalEvidence evidence;
    final List<Map<String,Object>> receipts=new ArrayList<>();
    private List<Map<String,Object>> latestPopulation=new ArrayList<>();
    PostLocalPass(RunContext<PermutationSolution<Integer>> context,Instance input,GomRunScope value,
            PostLocalArchives history,PostLocalEvidence sink) {
        run=context;instance=input;scope=value;archives=history;evidence=sink;
    }
    List<PostLocalData.Member> execute(String phase,List<PostLocalData.Member> members,long seed,List<double[]> independentA0) {
        evidence.phase=phase;SeededRandom.reset(seed);archives.begin(independentA0);
        long before=run.budget().successful(),attempted=run.budget().attempted(),failed=run.budget().failed();
        int number=scope.passes+1;GomWorkspace previous=scope.workspace;boolean complete=false;Throwable error=null;
        List<PostLocalData.Member> result=new ArrayList<>();long expected=budget(instance);
        evidence.record(GomRecords.row("kind","passStart","pass",number,"seed",seed,"beforeFE",before,"expectedFE",expected,
            "archiveBasis",independentA0==null?"CURRENT_PUBLIC":"A0_INDEPENDENT","internalArchive",archives.internal(),
            "publicArchive",scope.archive(),"beforePopulation",PostLocalData.records(members)));
        try {
            List<PermutationSolution<Integer>> points=new ArrayList<>();for(PostLocalData.Member member:members)points.add(member.particle.current);
            GomRunScope.begin(points,instance);long masks=0;
            for(int family:scope.workspace.families)masks+=scope.workspace.masks.get(family).size();
            if(masks!=expected)throw new AssertionError("Complete native FOS cost differs: "+masks+" != "+expected);
            SearchState evaluator=new SearchState(run.problem(),instance,null);
            for(PostLocalData.Member member:members)result.add(member.with(GomLocalProgram.improve(member.particle,member.role,evaluator)));
            if(run.budget().successful()-before!=expected||scope.workspace.programs!=100)throw new AssertionError("Incomplete native pass");
            complete=true;return result;
        } catch(RuntimeException|Error failure) {error=failure;throw failure;}
        finally {
            latestPopulation=population(members,scope.workspace==previous?null:scope.workspace);
            Map<String,Object> receipt=GomRecords.row("kind","passFinish","pass",number,"phase",phase,"seed",seed,
                "beforeFE",before,"afterFE",run.budget().successful(),"expectedFE",expected,
                "attempted",run.budget().attempted()-attempted,"successful",run.budget().successful()-before,
                "failed",run.budget().failed()-failed,"complete",complete,"error",error==null?null:error.toString(),
                "afterPopulation",latestPopulation,"internalArchive",archives.internal(),"publicArchive",scope.archive(),"native",scope.diagnostics());
            receipts.add(receipt);evidence.record(receipt);
        }
    }
    private static List<Map<String,Object>> population(List<PostLocalData.Member> members,GomWorkspace workspace) {
        List<Map<String,Object>> result=PostLocalData.records(members);
        if(workspace==null)return result;
        for(int i=0;i<workspace.values.size();i++) {
            GomRecords.State state=workspace.values.get(i);Map<String,Object> row=result.get(i);
            row.put("raw",GomRecords.raw(state.point));row.put("workingView",GomRecords.raw(GomRecords.copy(state.point,state.genes)));
            row.put("resources",state.genes.allocations());row.put("keys",state.genes.priorities());
            row.put("stateId",state.id);row.put("paidFE",state.paidFE);
        }
        return result;
    }
    List<Map<String,Object>> latestPopulation(){return latestPopulation;}
    static long budget(Instance instance){return 100L*(2*instance.jobs()-1)-20L*(instance.factories()-1);}
}
