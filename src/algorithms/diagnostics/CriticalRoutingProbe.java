package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.Solution;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;
import org.uma.jmetal.util.research.search.CriticalRoutingKernel;

/** Free M parents only, paired proposal stream, all three modes share the actual frozen VNS. */
public final class CriticalRoutingProbe {
    private static final String[] MODES={"FROZEN","RANDOM","CRITICAL"};
    private static final int QUOTA=256,REPS=2;
    private CriticalRoutingProbe() { }
    private static final class PaidPoint {
        final Map<String,Object> encoding;final DynamicSchedule schedule;
        PaidPoint(PermutationSolution<Integer> value) {encoding=ProbeData.encoding(value);schedule=(DynamicSchedule)value.getAttribute(DynamicEvaluation.KEY);}
        void verify(Instance in,DynamicParameters params) {
            String[] keys={"JS","FA","MA","WA"};int[][] genes=new int[4][];
            for(int k=0;k<keys.length;k++) {
                List<?> values=(List<?>)encoding.get(keys[k]);genes[k]=new int[values.size()];
                for(int p=0;p<values.size();p++)genes[k][p]=((Number)values.get(p)).intValue();
            }
            DynamicSchedule full=DynamicDecoder.full(in,params,genes[0],genes[1],genes[2],genes[3],null);
            DynamicValidator.validate(in,params,full);NeutralProbeSupport.sameTimeline(schedule,full);
        }
    }
    private static final class Probe {
        final EDHHFSPW raw;final Instance in;final DynamicParameters params;final Path out;final long seed;
        long paid,qa,runs;double qaSeconds;
        Probe(EDHHFSPW raw,DynamicParameters params,Path out,long seed) {
            this.raw=raw;in=raw.getSchedulingInstance();this.params=params;this.out=out;this.seed=seed;
        }
        void run(String[] fields,int index,int rep,String mode) {
            DynamicEvaluation decoder=new DynamicEvaluation(raw,in,params,true);
            RunContext<PermutationSolution<Integer>> context=new RunContext<>(decoder,1+QUOTA,seed+index*1009L+rep);decoder.setCheckpoint(context::checkpoint);
            List<PaidPoint> points=new ArrayList<>();Map<String,Object> result=new LinkedHashMap<>();
            context.problem().setObserver(new EvaluationObserver() {
                public void completed(long fee,double seconds,boolean changed,ThreeObjectiveArchive<?> archive) { }
                @SuppressWarnings("unchecked") public void completedSolution(Solution<?> value,long fee,double seconds,boolean changed,ThreeObjectiveArchive<?> archive) {
                    points.add(new PaidPoint((PermutationSolution<Integer>)value));
                }
            });
            long noise=NeutralProbeSupport.mixed(seed+index*100003L+rep*997L);
            try {context.run(new Algorithm<Object>() {
                private static final long serialVersionUID=1L;
                public void run() {
                    PermutationSolution<Integer> parent=context.problem().createSolution();ProbeData.fill(parent,fields,3,-1,null);
                    context.problem().evaluate(parent);ProbeData.expected(parent,fields[7]);String before=ProbeData.key(parent);
                    CriticalRoutingKernel kernel=new CriticalRoutingKernel(context.problem(),in,context::checkpoint);SeededRandom.reset(noise);
                    PermutationSolution<Integer> returned=kernel.run(parent,Integer.parseInt(fields[2]),mode,QUOTA,noise^0x51ac37L);
                    if(!before.equals(ProbeData.key(parent)))throw new AssertionError("Routing mutated paid parent");
                    result.put("returned",ProbeData.encoding(returned));result.put("routing",kernel.diagnostics());
                }
                public Object getResult(){return null;}public String getName(){return "CRITICAL_ROUTING_PROBE";}public String getDescription(){return getName();}
            });}catch(RuntimeException|Error error) {
                NeutralProbeSupport.append(out.resolve("failure.jsonl"),NeutralProbeSupport.row("case",fields[0],"mode",mode,"rep",rep,
                    "attempted",context.budget().attempted(),"successful",context.budget().successful(),"failed",context.budget().failed(),"error",error.toString()));throw error;
            }
            if(context.budget().successful()!=1+QUOTA||context.budget().failed()!=0||points.size()!=1+QUOTA)
                throw new AssertionError("Unbalanced routing trial FE");
            double elapsed=context.clock().elapsedSeconds();long start=System.nanoTime();
            for(PaidPoint point:points){point.verify(in,params);qa++;}
            qaSeconds+=(System.nanoTime()-start)/1e9;
            List<Map<String,Object>> encodings=new ArrayList<>();for(PaidPoint point:points)encodings.add(point.encoding);
            result.putAll(NeutralProbeSupport.row("case",fields[0],"sourceMethod",fields[1],"mode",mode,"rep",rep,"noise",noise,
                "successfulFE",context.budget().successful(),"failedFE",0,"paid",encodings,"measuredRunSeconds",elapsed));
            NeutralProbeSupport.append(out.resolve("outcomes.jsonl"),result);paid+=1+QUOTA;runs++;decoder.clearPrepared();
        }
    }
    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]),out=Paths.get(args[4]);Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir",input.getParent().toString());System.setProperty("dhfsp.setupFile",args[1]);System.setProperty("dhfsp.standbyPower","1");
        System.setProperty("research.qgsAudit.mode","record");System.setProperty("research.makespan.tie","STRICT");
        String[] dims=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(dims[0]),Integer.parseInt(dims[1]),Integer.parseInt(dims[2]),Integer.parseInt(dims[3]));
        Probe probe=new Probe(raw,DynamicInputs.fatigue(raw.getSchedulingInstance(),Paths.get(args[2])),out,Long.parseLong(args[5]));
        int index=0;for(String line:Files.readAllLines(Paths.get(args[3]),StandardCharsets.UTF_8)) {
            String[] f=line.split("\t",-1);
            for(int rep=0;rep<REPS;rep++)for(int turn=0;turn<MODES.length;turn++)probe.run(f,index,rep,MODES[(turn+rep+index)%MODES.length]);index++;
        }
        NeutralProbeSupport.append(out.resolve("receipt.jsonl"),NeutralProbeSupport.row("successfulFE",probe.paid,"failedFE",0,
            "fullTimelineQA",probe.qa,"offlineQASeconds",probe.qaSeconds,"trials",probe.runs,"quota",QUOTA,
            "classIdentity",ClassResolutionProbe.capture("org.uma.jmetal.util.research.search.LocalSearch",
                "org.uma.jmetal.util.research.search.SearchState","org.uma.jmetal.util.research.search.IntraNeighborhoods")));
        System.out.println("CRITICAL_ROUTING_PASS paid="+probe.paid+" qa="+probe.qa);
    }
}
