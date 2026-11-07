package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.classic.*;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;

/** Same recipient and native classic kernel, with only the paid donor source varied. */
public final class MatingPoolProbe {
    private static final String[] METHODS={"WITHIN","SHARED","RANDOM_SHARED","INITIAL_SHARED"};
    private static final int REPS=16,RECIPIENTS=8;
    private MatingPoolProbe() { }

    private static final class Probe {
        final EDHHFSPW raw;final Instance in;final DynamicParameters params;final Path out;final long baseSeed;
        long paid,qa;double qaSeconds;
        Probe(EDHHFSPW raw,DynamicParameters params,Path out,long seed) {
            this.raw=raw;this.in=raw.getSchedulingInstance();this.params=params;this.out=out;this.baseSeed=seed;
        }
        List<PermutationSolution<Integer>> replay(RunContext<PermutationSolution<Integer>> context,List<String[]> fields) {
            List<PermutationSolution<Integer>> values=new ArrayList<>();
            for(String[] f:fields) {
                PermutationSolution<Integer> s=context.problem().createSolution();ProbeData.fill(s,f,3,-1,null);
                context.problem().evaluate(s);ProbeData.expected(s,f[7]);check(s);values.add(s);
            }return values;
        }
        void check(PermutationSolution<Integer> s) {
            long start=System.nanoTime();
            NeutralProbeSupport.sameTimeline((DynamicSchedule)s.getAttribute(DynamicEvaluation.KEY),NeutralProbeSupport.full(in,params,s));
            qa++;qaSeconds+=(System.nanoTime()-start)/1e9;
        }
        void run(String id,List<String[]> currentFields,List<String[]> initialFields,int contextIndex) {
            long limit=currentFields.size()+initialFields.size()+METHODS.length*REPS*RECIPIENTS;
            DynamicEvaluation decoder=new DynamicEvaluation(raw,in,params,true);
            RunContext<PermutationSolution<Integer>> context=new RunContext<>(decoder,limit,baseSeed+contextIndex);
            decoder.setCheckpoint(context::checkpoint);List<Map<String,Object>> records=new ArrayList<>(),batches=new ArrayList<>();
            try {context.run(new Algorithm<Object>() {
                private static final long serialVersionUID=1L;
                public void run() {
                    List<PermutationSolution<Integer>> current=replay(context,currentFields),initial=replay(context,initialFields);
                    if(current.size()!=80||initial.size()!=80)throw new AssertionError("Wrong free donor counts");
                    List<PermutationSolution<Integer>> within=new ArrayList<>();List<Integer> centerIndices=new ArrayList<>();
                    for(int i=0;i<currentFields.size();i++)if(currentFields.get(i)[2].equals("CENTER")){within.add(current.get(i));centerIndices.add(i);}
                    if(within.size()!=47)throw new AssertionError("Wrong free CENTER count");
                    List<String> before=new ArrayList<>();for(PermutationSolution<Integer> s:current)before.add(ProbeData.key(s));
                    for(PermutationSolution<Integer> s:initial)before.add(ProbeData.key(s));
                    ClassicKernelBridge kernel=new ClassicKernelBridge(in,context::checkpoint);
                    for(int rep=0;rep<REPS;rep++)for(int turn=0;turn<METHODS.length;turn++) {
                        String method=METHODS[(turn+rep+contextIndex)%METHODS.length];
                        List<PermutationSolution<Integer>> donors=method.equals("WITHIN")?within:method.equals("INITIAL_SHARED")?initial:current;
                        long start=System.nanoTime();ClassicMatingBridge bridge=new ClassicMatingBridge(donors,context::checkpoint,!method.equals("RANDOM_SHARED"));
                        long score=System.nanoTime()-start;
                        batches.add(NeutralProbeSupport.row("context",id,"rep",rep,"method",method,"scoreSeconds",score/1e9,"offspring",RECIPIENTS));
                        for(int recipient=0;recipient<RECIPIENTS;recipient++) {
                            int centerIndex=recipient*(within.size()-1)/(RECIPIENTS-1),currentIndex=centerIndices.get(centerIndex);
                            long noise=NeutralProbeSupport.mixed(baseSeed+contextIndex*100003L+rep*997L+recipient);
                            SeededRandom.reset(NeutralProbeSupport.mixed(noise^0x5ac37L));start=System.nanoTime();int donorIndex=bridge.draw();
                            long draw=System.nanoTime()-start;SeededRandom.reset(noise);start=System.nanoTime();
                            PermutationSolution<Integer> child=kernel.child(within.get(centerIndex),donors.get(donorIndex));
                            int edits=SchedulingEncoding.repair(child,in);long generation=System.nanoTime()-start;
                            start=System.nanoTime();context.problem().evaluate(child);long evaluation=System.nanoTime()-start;check(child);
                            String role=method.equals("WITHIN")?"CENTER":(method.equals("INITIAL_SHARED")?initialFields:currentFields).get(donorIndex)[2];
                            records.add(NeutralProbeSupport.row("context",id,"rep",rep,"recipient",recipient,"currentRecipientIndex",currentIndex,
                                "method",method,"donorIndex",donorIndex,"donorRole",role,"constructionNoise",noise,"drawSeconds",draw/1e9,
                                "generationSeconds",generation/1e9,"evaluationSeconds",evaluation/1e9,"repairEdits",edits,"child",ProbeData.encoding(child),
                                "objectives",child.getObjectives().clone()));
                        }
                    }
                    List<PermutationSolution<Integer>> all=new ArrayList<>(current);all.addAll(initial);
                    for(int i=0;i<all.size();i++)if(!before.get(i).equals(ProbeData.key(all.get(i))))throw new AssertionError("Mating mutated paid inputs");
                }
                public Object getResult(){return null;}public String getName(){return "MATING_POOL_PROBE";}public String getDescription(){return getName();}
            });}catch(RuntimeException|Error error) {
                NeutralProbeSupport.append(out.resolve("failure.jsonl"),NeutralProbeSupport.row("context",id,"attempted",context.budget().attempted(),
                    "successful",context.budget().successful(),"failed",context.budget().failed(),"error",error.toString()));throw error;
            }
            if(context.budget().successful()!=limit||context.budget().failed()!=0)throw new AssertionError("Incomplete mating FE");
            for(Map<String,Object> record:records)NeutralProbeSupport.append(out.resolve("outcomes.jsonl"),record);
            for(Map<String,Object> batch:batches)NeutralProbeSupport.append(out.resolve("batch-costs.jsonl"),batch);
            NeutralProbeSupport.append(out.resolve("context-receipts.jsonl"),NeutralProbeSupport.row("context",id,"successfulFE",limit,"failedFE",0));
            paid+=limit;decoder.clearPrepared();
        }
    }
    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]),out=Paths.get(args[5]);Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir",input.getParent().toString());System.setProperty("dhfsp.setupFile",args[1]);System.setProperty("dhfsp.standbyPower","1");
        String[] dims=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(dims[0]),Integer.parseInt(dims[1]),Integer.parseInt(dims[2]),Integer.parseInt(dims[3]));
        Map<String,List<String[]>> current=new LinkedHashMap<>(),initial=new LinkedHashMap<>();
        for(String line:Files.readAllLines(Paths.get(args[4]),StandardCharsets.UTF_8)) {
            String[] f=line.split("\t",-1);(f[1].equals("CURRENT")?current:initial).computeIfAbsent(f[0],ignored->new ArrayList<>()).add(f);
        }
        Probe probe=new Probe(raw,DynamicInputs.fatigue(raw.getSchedulingInstance(),Paths.get(args[2])),out,Long.parseLong(args[6]));
        int index=0;for(String id:Files.readAllLines(Paths.get(args[3]),StandardCharsets.UTF_8))probe.run(id,current.get(id),initial.get(id),index++);
        NeutralProbeSupport.append(out.resolve("receipt.jsonl"),NeutralProbeSupport.row("successfulFE",probe.paid,"failedFE",0,"fullTimelineQA",probe.qa,
            "offlineQASeconds",probe.qaSeconds,"contexts",index,"replicates",REPS,"recipients",RECIPIENTS,
            "classIdentity",ClassResolutionProbe.capture("org.uma.jmetal.util.research.classic.NsgaSelection",
                "org.uma.jmetal.util.research.classic.ClassicVariation","org.uma.jmetal.util.research.classic.ClassicKernelBridge")));
        System.out.println("MATING_POOL_PASS paid="+probe.paid+" qa="+probe.qa);
    }
}
