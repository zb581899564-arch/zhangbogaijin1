package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.classic.ClassicKernelBridge;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;

/** Complete paid intermediates, paired endpoints and identical per-method evaluation counts. */
public final class RelinkingProbe {
    private static final String[] METHODS={"COVER_PATH","REPAIR_PATH","RANDOM_PATH","CLASSIC"};
    private RelinkingProbe() { }
    private static final class Probe {
        final EDHHFSPW raw;final Instance in;final DynamicParameters params;final Path out;final long seed;
        long paid,qa,pairs;double qaSeconds;
        Probe(EDHHFSPW raw,DynamicParameters params,Path out,long seed) {
            this.raw=raw;in=raw.getSchedulingInstance();this.params=params;this.out=out;this.seed=seed;
        }
        void qa(PermutationSolution<Integer> s) {
            long start=System.nanoTime();
            NeutralProbeSupport.sameTimeline((DynamicSchedule)s.getAttribute(DynamicEvaluation.KEY),NeutralProbeSupport.full(in,params,s));
            qa++;qaSeconds+=(System.nanoTime()-start)/1e9;
        }
        void run(String line,int index) {
            String[] f=line.split("\t",-1);String id=f[0];long limit=2+4L*in.jobs();
            DynamicEvaluation decoder=new DynamicEvaluation(raw,in,params,true);
            RunContext<PermutationSolution<Integer>> context=new RunContext<>(decoder,limit,seed+index);decoder.setCheckpoint(context::checkpoint);
            List<Map<String,Object>> records=new ArrayList<>(),costs=new ArrayList<>();
            try {context.run(new Algorithm<Object>() {
                private static final long serialVersionUID=1L;
                public void run() {
                    List<PermutationSolution<Integer>> inputs=new ArrayList<>();
                    for(int k=0;k<2;k++) {
                        PermutationSolution<Integer> s=context.problem().createSolution();ProbeData.fill(s,f,4+k*5,-1,null);
                        context.problem().evaluate(s);ProbeData.expected(s,f[8+k*5]);qa(s);inputs.add(s);
                    }
                    String parentKey=ProbeData.key(inputs.get(0)),teacherKey=ProbeData.key(inputs.get(1));
                    Map<String,CommittedRelinkingPath> paths=new LinkedHashMap<>();
                    Map<String,PermutationSolution<Integer>> previous=new LinkedHashMap<>();
                    long start=System.nanoTime();ClassicKernelBridge kernel=new ClassicKernelBridge(in,context::checkpoint);
                    costs.add(NeutralProbeSupport.row("pair",id,"method","CLASSIC","setupSeconds",(System.nanoTime()-start)/1e9));
                    for(String method:METHODS) {
                        previous.put(method,inputs.get(0));if(method.equals("CLASSIC"))continue;
                        start=System.nanoTime();paths.put(method,new CommittedRelinkingPath(in,inputs.get(0),inputs.get(1),method,
                            NeutralProbeSupport.mixed(seed+index*1009L)));
                        costs.add(NeutralProbeSupport.row("pair",id,"method",method,"setupSeconds",(System.nanoTime()-start)/1e9));
                    }
                    for(int step=0;step<in.jobs();step++)for(int turn=0;turn<METHODS.length;turn++) {
                        String method=METHODS[(turn+step+index)%METHODS.length];CommittedRelinkingPath path=paths.get(method);
                        long noise=NeutralProbeSupport.mixed(seed+index*100003L+step*997L);SeededRandom.reset(noise);start=System.nanoTime();
                        PermutationSolution<Integer> child;
                        int edits;
                        if(path==null){child=kernel.child(inputs.get(0),inputs.get(1));edits=SchedulingEncoding.repair(child,in);}
                        else{child=path.next(step);edits=path.repairEdits;}
                        long generation=System.nanoTime()-start;
                        boolean unchanged=CommittedRelinkingPath.sameEncoding(child,previous.get(method));
                        start=System.nanoTime();context.problem().evaluate(child);long evaluation=System.nanoTime()-start;qa(child);
                        if(path!=null&&step==in.jobs()-1) {
                            if(!CommittedRelinkingPath.sameEncoding(child,inputs.get(1)))throw new AssertionError("Paid endpoint differs from teacher");
                            ProbeData.expected(child,f[13]);
                        }
                        records.add(NeutralProbeSupport.row("pair",id,"step",step,"method",method,"constructionNoise",noise,
                            "generationSeconds",generation/1e9,"evaluationSeconds",evaluation/1e9,"repairEdits",edits,
                            "extraCoverJobs",path==null?0:path.auxiliaryJobs,"committedViolations",path==null?0:path.committedViolations,
                            "endpointRestorationEdits",path==null?0:path.endpointRestorationEdits,"sameAsPrevious",unchanged,
                            "objectives",child.getObjectives().clone(),"child",ProbeData.encoding(child)));
                        previous.put(method,child);
                    }
                    if(!parentKey.equals(ProbeData.key(inputs.get(0)))||!teacherKey.equals(ProbeData.key(inputs.get(1))))
                        throw new AssertionError("Path or classic kernel mutated paid endpoints");
                }
                public Object getResult(){return null;}public String getName(){return "RELINKING_PROBE";}public String getDescription(){return getName();}
            });}catch(RuntimeException|Error failure) {
                NeutralProbeSupport.append(out.resolve("failure.jsonl"),NeutralProbeSupport.row("pair",id,"attempted",context.budget().attempted(),
                    "successful",context.budget().successful(),"failed",context.budget().failed(),"error",failure.toString()));throw failure;
            }
            if(context.budget().successful()!=limit||context.budget().failed()!=0)throw new AssertionError("Unbalanced relinking fees");
            for(Map<String,Object> record:records)NeutralProbeSupport.append(out.resolve("outcomes.jsonl"),record);
            for(Map<String,Object> cost:costs)NeutralProbeSupport.append(out.resolve("setup-costs.jsonl"),cost);
            NeutralProbeSupport.append(out.resolve("pair-receipts.jsonl"),NeutralProbeSupport.row("pair",id,"successfulFE",limit,"failedFE",0));
            paid+=limit;pairs++;decoder.clearPrepared();
        }
    }
    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]),out=Paths.get(args[4]);Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir",input.getParent().toString());System.setProperty("dhfsp.setupFile",args[1]);System.setProperty("dhfsp.standbyPower","1");
        String[] dims=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(dims[0]),Integer.parseInt(dims[1]),Integer.parseInt(dims[2]),Integer.parseInt(dims[3]));
        Probe probe=new Probe(raw,DynamicInputs.fatigue(raw.getSchedulingInstance(),Paths.get(args[2])),out,Long.parseLong(args[5]));
        int index=0;for(String line:Files.readAllLines(Paths.get(args[3]),StandardCharsets.UTF_8))probe.run(line,index++);
        NeutralProbeSupport.append(out.resolve("receipt.jsonl"),NeutralProbeSupport.row("successfulFE",probe.paid,"failedFE",0,
            "fullTimelineQA",probe.qa,"offlineQASeconds",probe.qaSeconds,"pairs",probe.pairs,
            "classIdentity",ClassResolutionProbe.capture("org.uma.jmetal.util.research.classic.ClassicVariation",
                "org.uma.jmetal.util.research.classic.ClassicKernelBridge","org.uma.jmetal.util.research.DynamicEvaluation")));
        System.out.println("RELINKING_PASS pairs="+probe.pairs+" paid="+probe.paid+" qa="+probe.qa);
    }
}
