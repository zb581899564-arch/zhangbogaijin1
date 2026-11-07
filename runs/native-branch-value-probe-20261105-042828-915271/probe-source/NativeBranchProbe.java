package org.uma.jmetal.util.research.joint;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;
import research.dynamic.DynamicInputs;
import research.dynamic.DynamicJson;
import research.dynamic.ClassResolutionProbe;

/** Objective-blind native actions plus designated legal completions; all labels use guarded FE. */
public final class NativeBranchProbe {
    private NativeBranchProbe() { }
    private static final class Trial {
        final Instance in;final DynamicParameters params;final EDHHFSPW raw;final Path out;final double[] scales;
        long paid,qa,prefixAppends,featurePrecompute;final JointFeatures features;
        Trial(EDHHFSPW raw,DynamicParameters p,Path out,double[] scales) {
            this.raw=raw;in=raw.getSchedulingInstance();params=p;this.out=out;this.scales=scales;
            long start=System.nanoTime();features=new JointFeatures(in,p,()->{});featurePrecompute=System.nanoTime()-start;
        }
        void run(String[] fields) throws Exception {
            String id=fields[0];long seed=Long.parseLong(fields[1]);
            DynamicEvaluation decoder=new DynamicEvaluation(raw,in,params,true);
            RunContext<PermutationSolution<Integer>> context=new RunContext<>(decoder,3+JointPolicy.CANDIDATE_LIMIT,seed);
            decoder.setCheckpoint(context::checkpoint);List<Map<String,Object>> inputs=new ArrayList<>(),labels=new ArrayList<>();
            long[] construction={0},featureTime={0},evaluation={0},inputEvaluation={0},qaTime={0};int[] candidateCount={0};
            try { context.run(new Algorithm<Object>() {
                private static final long serialVersionUID=1L;
                public void run() {
                    @SuppressWarnings("unchecked") PermutationSolution<Integer>[] teachers=new PermutationSolution[3];
                    for(int t=0;t<3;t++) {
                        teachers[t]=context.problem().createSolution();NativeBranchSupport.fill(teachers[t],fields,2+t*5);
                        double[] expected=teachers[t].getObjectives().clone();
                        if(SchedulingEncoding.repair(teachers[t],in)!=0)throw new AssertionError("Illegal native source");
                        long inputStart=System.nanoTime();context.problem().evaluate(teachers[t]);inputEvaluation[0]+=System.nanoTime()-inputStart;
                        if(!Arrays.equals(expected,teachers[t].getObjectives()))throw new AssertionError("Source replay differs");
                    }
                    PermutationSolution<Integer> parent=teachers[0];Random random=new Random(seed);
                    long start=System.nanoTime();int length=Math.min(JointPolicy.BLOCK_LENGTH,in.jobs()),begin=random.nextInt(in.jobs()-length+1);
                    BlockContext block=new BlockContext(in,parent,begin,length);DynamicPrefix before=new DynamicPrefix(in,params);
                    block.restorePrefix(before,()->{});prefixAppends+=before.size();
                    List<JointAction> actions=JointCandidates.propose(block,teachers,random);candidateCount[0]=actions.size();
                    if(actions.isEmpty())throw new AssertionError("Native source has no legal actions");
                    construction[0]+=System.nanoTime()-start;
                    for(int i=0;i<actions.size();i++) {
                        JointAction action=actions.get(i);start=System.nanoTime();
                        DynamicPrefix after=before.copy();BlockContext.append(after,action);prefixAppends++;
                        PermutationSolution<Integer> child=NativeBranchSupport.completion(in,parent,begin,length,action);
                        if(SchedulingEncoding.repair(child,in)!=0)throw new AssertionError("Witness required repair");
                        construction[0]+=System.nanoTime()-start;start=System.nanoTime();
                        JointFeatures.State state=features.summarize(after,BlockContext.byJob(in,child,true),NativeBranchSupport.future(in,child,begin+1),length-1,scales);
                        featureTime[0]+=System.nanoTime()-start;
                        Map<String,Object> input=NativeBranchSupport.row("case",id,"candidate",i,"begin",begin,"blockLength",length,
                            "action",action.tuple(),"parentObjectives",parent.getObjectives().clone(),"scales",scales.clone(),
                            "prefix",NativeBranchSupport.prefix(in,after),"genome",NativeBranchSupport.genome(child),
                            "partial",state.partial.clone(),"tail",state.tail.clone());inputs.add(input);
                        decoder.prepare(child,after);start=System.nanoTime();context.problem().evaluate(child);
                        long nanos=System.nanoTime()-start;evaluation[0]+=nanos;
                        long qaStart=System.nanoTime();DynamicSchedule schedule=(DynamicSchedule)child.getAttribute(DynamicEvaluation.KEY);DynamicValidator.validate(in,params,schedule);
                        DynamicSchedule full=DynamicDecoder.full(in,params,SchedulingEncoding.integers(child.getVariables()),
                            SchedulingEncoding.integers(child.getVariablesid()),SchedulingEncoding.machineIntegers(child),SchedulingEncoding.integers(child.getVariablesworker()),null);
                        qa++;NativeBranchSupport.sameTimeline(schedule,full);qaTime[0]+=System.nanoTime()-qaStart;
                        labels.add(NativeBranchSupport.row("case",id,"candidate",i,"objectives",child.getObjectives().clone(),"evaluationSeconds",nanos/1e9));
                    }
                }
                public Object getResult(){return null;}
                public String getName(){return "NATIVE_LEGAL_BRANCH_PROBE";}
                public String getDescription(){return getName();}
            }); } catch(RuntimeException|Error failure) {
                append(out.resolve("failure.jsonl"),NativeBranchSupport.row("case",id,"attempted",context.budget().attempted(),
                    "successful",context.budget().successful(),"failed",context.budget().failed(),"decoder",decoder.diagnostics(),"error",failure.toString()));
                throw failure;
            }
            if(context.budget().successful()!=3+candidateCount[0]||context.budget().failed()!=0)throw new AssertionError("Native FE receipt mismatch");
            for(Map<String,Object> r:inputs)append(out.resolve("features.jsonl"),r);
            for(Map<String,Object> r:labels)append(out.resolve("outcomes.jsonl"),r);
            append(out.resolve("cases-receipt.jsonl"),NativeBranchSupport.row("case",id,"successfulFE",context.budget().successful(),
                "failedFE",context.budget().failed(),"candidates",candidateCount[0],"constructionSeconds",construction[0]/1e9,
                "cheapFeatureSeconds",featureTime[0]/1e9,"allCandidateEvaluationSeconds",evaluation[0]/1e9,
                "inputEvaluationSeconds",inputEvaluation[0]/1e9,"offlineQASeconds",qaTime[0]/1e9,"contextSeconds",context.clock().elapsedSeconds()));
            paid+=context.budget().successful();decoder.clearPrepared();
        }
    }
    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]),out=Paths.get(args[4]);Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir",input.getParent().toString());System.setProperty("dhfsp.setupFile",args[1]);System.setProperty("dhfsp.standbyPower","1");
        String[] d=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(d[0]),Integer.parseInt(d[1]),Integer.parseInt(d[2]),Integer.parseInt(d[3]));
        DynamicParameters params=DynamicInputs.fatigue(raw.getSchedulingInstance(),Paths.get(args[2]));
        List<String> lines=Files.readAllLines(Paths.get(args[3]),StandardCharsets.UTF_8);
        double[] scales=Arrays.stream(args[5].split(",")).mapToDouble(Double::parseDouble).toArray();Trial trial=new Trial(raw,params,out,scales);
        for(String line:lines)trial.run(line.split("\t"));
        append(out.resolve("receipt.jsonl"),NativeBranchSupport.row("successfulFE",trial.paid,"failedFE",0,"candidateFullQA",trial.qa,
            "explicitPrefixAppends",trial.prefixAppends,"featurePrecomputeSeconds",trial.featurePrecompute/1e9,
            "classIdentity",ClassResolutionProbe.capture("org.uma.jmetal.util.research.joint.JointCandidates", "org.uma.jmetal.util.research.joint.BlockContext", "org.uma.jmetal.util.research.joint.JointFeatures")));
    }
    private static void append(Path path,Map<String,Object> row) throws Exception {
        Files.write(path,Collections.singletonList(DynamicJson.encode(row)),StandardCharsets.UTF_8,StandardOpenOption.CREATE,StandardOpenOption.APPEND);
    }
}
