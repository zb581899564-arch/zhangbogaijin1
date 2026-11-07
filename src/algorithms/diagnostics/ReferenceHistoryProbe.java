package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.mechanism.KernelVariants;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;
import org.uma.jmetal.util.research.search.SearchConfig;

/** Equal paid offspring counts and construction noise across six personal-guide rules. */
public final class ReferenceHistoryProbe {
    private ReferenceHistoryProbe() { }
    private static final int REPS=2;

    private static final class Probe {
        final Instance in;final DynamicParameters params;final EDHHFSPW source;final Path out;
        final Map<String,List<String[]>> histories;final Map<String,double[]> scales;final long baseSeed;
        long paid,qa;double offlineQASeconds;
        Probe(EDHHFSPW source,DynamicParameters params,Path out,Map<String,List<String[]>> histories,Map<String,double[]> scales,long seed) {
            this.source=source;this.in=source.getSchedulingInstance();this.params=params;this.out=out;
            this.histories=histories;this.scales=scales;this.baseSeed=seed;
        }
        void run(String line,int index) throws Exception {
            String[] fields=line.split("\t",-1);String id=fields[0];List<String[]> historyFields=histories.get(id);
            double[][] weights=ReferenceHistoryChoice.weights();
            long limit=3L+historyFields.size()+weights.length*REPS*ReferenceHistoryChoice.METHODS.length;
            DynamicEvaluation decoder=new DynamicEvaluation(source,in,params,true);
            RunContext<PermutationSolution<Integer>> context=new RunContext<>(decoder,limit,baseSeed+index);
            decoder.setCheckpoint(context::checkpoint);
            List<Map<String,Object>> records=new ArrayList<>();
            try {context.run(new Algorithm<Object>() {
                private static final long serialVersionUID=1L;
                public void run() {
                    List<PermutationSolution<Integer>> inputs=new ArrayList<>(),history=new ArrayList<>();
                    for(int t=0;t<3;t++) {
                        PermutationSolution<Integer> s=context.problem().createSolution();ProbeData.fill(s,fields,3+t*5,-1,null);
                        context.problem().evaluate(s);ProbeData.expected(s,fields[7+t*5]);inputs.add(s);
                    }
                    for(String[] h:historyFields) {
                        PermutationSolution<Integer> s=context.problem().createSolution();ProbeData.fill(s,h,1,-1,null);
                        context.problem().evaluate(s);ProbeData.expected(s,h[5]);history.add(s);
                    }
                    if(!ProbeData.key(inputs.get(1)).equals(ProbeData.key(history.get(0))))throw new AssertionError("Oldest source differs");
                    List<String> original=new ArrayList<>();for(PermutationSolution<Integer>s:inputs)original.add(ProbeData.key(s));
                    for(PermutationSolution<Integer>s:history)original.add(ProbeData.key(s));
                    SearchConfig cfg=new SearchConfig();cfg.mergeGlobalLocal=cfg.paperResourceOperators=true;
                    KernelVariants kernel=new KernelVariants(in,cfg,context::checkpoint);
                    for(int w=0;w<weights.length;w++)for(int rep=0;rep<REPS;rep++)for(int turn=0;turn<ReferenceHistoryChoice.METHODS.length;turn++) {
                        String method=ReferenceHistoryChoice.METHODS[(turn+w+rep+index)%ReferenceHistoryChoice.METHODS.length];
                        long noise=NeutralProbeSupport.mixed(baseSeed+index*1009L+w*117L+rep);
                        long start=System.nanoTime();int chosen=ReferenceHistoryChoice.choose(method,history,weights[w],scales.get(id),noise);
                        @SuppressWarnings("unchecked") PermutationSolution<Integer> personal=(PermutationSolution<Integer>)(chosen<0?inputs.get(0):history.get(chosen)).copy();
                        long selection=System.nanoTime()-start;SeededRandom.reset(noise);start=System.nanoTime();
                        PermutationSolution<Integer> child=kernel.child(KernelVariants.JOB_ALIGNED,inputs.get(0),personal,inputs.get(2));
                        int repaired=SchedulingEncoding.repair(child,in);long generation=System.nanoTime()-start;
                        start=System.nanoTime();context.problem().evaluate(child);long evaluation=System.nanoTime()-start;
                        long qaStart=System.nanoTime();DynamicSchedule schedule=(DynamicSchedule)child.getAttribute(DynamicEvaluation.KEY);
                        NeutralProbeSupport.sameTimeline(schedule,NeutralProbeSupport.full(in,params,child));qa++;
                        offlineQASeconds+=(System.nanoTime()-qaStart)/1e9;
                        records.add(NeutralProbeSupport.row("case",id,"weight",w,"rep",rep,"method",method,"noise",noise,
                            "chosenHistoryIndex",chosen,"objectives",child.getObjectives().clone(),"child",ProbeData.encoding(child),
                            "selectionSeconds",selection/1e9,"generationSeconds",generation/1e9,"evaluationSeconds",evaluation/1e9,
                            "commonRepairEdits",repaired));
                    }
                    List<PermutationSolution<Integer>> all=new ArrayList<>(inputs);all.addAll(history);
                    for(int i=0;i<all.size();i++)if(!original.get(i).equals(ProbeData.key(all.get(i))))throw new AssertionError("Kernel mutated paid source");
                }
                public Object getResult(){return null;}public String getName(){return "REFERENCE_HISTORY_PROBE";}public String getDescription(){return getName();}
            });}catch(RuntimeException|Error error) {
                NeutralProbeSupport.append(out.resolve("failure.jsonl"),NeutralProbeSupport.row("case",id,"attempted",context.budget().attempted(),
                    "successful",context.budget().successful(),"failed",context.budget().failed(),"error",error.toString()));throw error;
            }
            if(context.budget().successful()!=limit||context.budget().failed()!=0)throw new AssertionError("Incomplete reference probe");
            for(Map<String,Object> record:records)NeutralProbeSupport.append(out.resolve("outcomes.jsonl"),record);
            NeutralProbeSupport.append(out.resolve("case-receipts.jsonl"),NeutralProbeSupport.row("case",id,"successfulFE",limit,
                "historySize",historyFields.size(),"failedFE",0));paid+=limit;decoder.clearPrepared();
        }
    }

    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]),out=Paths.get(args[6]);Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir",input.getParent().toString());System.setProperty("dhfsp.setupFile",args[1]);System.setProperty("dhfsp.standbyPower","1");
        String[] dims=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(dims[0]),Integer.parseInt(dims[1]),Integer.parseInt(dims[2]),Integer.parseInt(dims[3]));
        Map<String,List<String[]>> histories=new LinkedHashMap<>();
        for(String line:Files.readAllLines(Paths.get(args[4]),StandardCharsets.UTF_8)) {
            String[] h=line.split("\t",-1);histories.computeIfAbsent(h[0],ignored->new ArrayList<>()).add(h);
        }
        Map<String,double[]> scales=new LinkedHashMap<>();
        for(String line:Files.readAllLines(Paths.get(args[5]),StandardCharsets.UTF_8)) {
            String[] f=line.split("\t",-1);scales.put(f[0],Arrays.stream(f[1].split(",")).mapToDouble(Double::parseDouble).toArray());
        }
        Probe probe=new Probe(raw,DynamicInputs.fatigue(raw.getSchedulingInstance(),Paths.get(args[2])),out,histories,scales,Long.parseLong(args[7]));
        int index=0;for(String line:Files.readAllLines(Paths.get(args[3]),StandardCharsets.UTF_8))probe.run(line,index++);
        NeutralProbeSupport.append(out.resolve("receipt.jsonl"),NeutralProbeSupport.row("successfulFE",probe.paid,"failedFE",0,
            "candidateFullTimelineQA",probe.qa,"offlineQASeconds",probe.offlineQASeconds,"weights",ReferenceHistoryChoice.weights(),
            "classIdentity",ClassResolutionProbe.capture("org.uma.jmetal.util.research.mechanism.KernelVariants",
                "org.uma.jmetal.util.research.mechanism.JobAlignedPaperKernel")));
        System.out.println("REFERENCE_HISTORY_PASS paid="+probe.paid+" qa="+probe.qa);
    }
}
