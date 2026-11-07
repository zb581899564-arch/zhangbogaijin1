package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.*;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;

/** Two real evaluations then one deliberate evaluator fault: budget and nonempty failure front must survive. */
public final class NaturalEvaluatorFailureCheck {
    private NaturalEvaluatorFailureCheck() { }
    private static final class FailThird implements Problem<PermutationSolution<Integer>> {
        private static final long serialVersionUID=1L;
        final DynamicEvaluation delegate;int calls;
        FailThird(DynamicEvaluation delegate){this.delegate=delegate;}
        public void evaluate(PermutationSolution<Integer> value) {
            if(++calls==3)throw new IllegalStateException("INJECTED_EVALUATOR_FAILURE");delegate.evaluate(value);
        }
        public PermutationSolution<Integer> createSolution(){return delegate.createSolution();}
        public int getNumberOfVariables(){return delegate.getNumberOfVariables();}
        public int getNumberOfObjectives(){return delegate.getNumberOfObjectives();}
        public int getNumberOfConstraints(){return delegate.getNumberOfConstraints();}
        public String getName(){return "EXPECTED_FAILURE_FIXTURE";}
    }
    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]),out=Paths.get(args[3]);Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir",input.getParent().toString());System.setProperty("dhfsp.setupFile",args[1]);System.setProperty("dhfsp.standbyPower","1");
        String[] d=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(d[0]),Integer.parseInt(d[1]),Integer.parseInt(d[2]),Integer.parseInt(d[3]));
        Instance in=raw.getSchedulingInstance();DynamicParameters params=DynamicInputs.fatigue(in,Paths.get(args[2]));
        DynamicEvaluation decoder=new DynamicEvaluation(raw,in,params,true);
        RunContext<PermutationSolution<Integer>> context=new RunContext<>(new FailThird(decoder),10,10950003);decoder.setCheckpoint(context::checkpoint);
        NaturalRunEvidence last=new NaturalRunEvidence();List<PermutationSolution<Integer>> paid=new ArrayList<>();
        context.problem().setObserver(new EvaluationObserver() {
            public void completed(long fe,double seconds,boolean changed,ThreeObjectiveArchive<?> archive) { }
            @SuppressWarnings("unchecked") public void completedSolution(Solution<?> value,long fe,double seconds,boolean changed,ThreeObjectiveArchive<?> archive) {
                last.observed(archive,fe);paid.add((PermutationSolution<Integer>)value);
            }
        });
        boolean rejected=false;
        try {context.run(new Algorithm<Object>() {
            private static final long serialVersionUID=1L;
            public void run(){for(int i=0;i<3;i++)context.problem().evaluate(context.problem().createSolution());}
            public Object getResult(){return null;}public String getName(){return "EXPECTED_FAILURE_FIXTURE";}public String getDescription(){return getName();}
        });}catch(IllegalStateException failure) {
            if(!"INJECTED_EVALUATOR_FAILURE".equals(failure.getMessage()))throw failure;rejected=true;
            last.writeFailure(out,failure.toString(),context.budget().attempted(),context.budget().successful(),context.budget().failed());
        }
        if(!rejected||context.budget().attempted()!=3||context.budget().successful()!=2||context.budget().failed()!=1
            ||context.budget().timeInterruptedAttempts()!=0||!context.stopReason().equals("FAILED")||paid.size()!=2)
            throw new AssertionError("Evaluator fault budget was lost");
        for(PermutationSolution<Integer> value:paid)NeutralProbeSupport.sameTimeline((DynamicSchedule)value.getAttribute(DynamicEvaluation.KEY),NeutralProbeSupport.full(in,params,value));
        List<double[]> front=new ArrayList<>();for(PermutationSolution<Integer> value:context.result())front.add(value.getObjectives().clone());
        Map<String,Object> report=NeutralProbeSupport.row("status","PASS","attemptedFE",3,"successfulFE",2,"expectedEvaluationFailures",1,
            "timeInterruptedAttempts",0,"fullTimelineQA",2,"expectedFront",front,"scope","Injected fault after two real scheduling evaluations; not a scientific performance run");
        Files.write(out.resolve("acceptance.json"),Collections.singletonList(DynamicJson.encode(report)),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
    }
}
