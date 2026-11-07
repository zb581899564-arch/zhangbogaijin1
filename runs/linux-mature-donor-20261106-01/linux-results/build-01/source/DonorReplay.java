package org.uma.jmetal.util.research.search;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.modelglobal.*;
import org.uma.jmetal.util.research.runtime.*;
import research.dynamic.DynamicJson;

/** One fixed receiver pass. External supply changes neither receiver/model membership nor acceptance. */
public final class DonorReplay implements Algorithm<Object> {
    private static final long serialVersionUID=1L;
    private final RunContext<PermutationSolution<Integer>> run;
    private final Instance instance;
    private final DonorData data;
    private final Path output;
    private final String mode;
    private final long seed;
    private final GomRunScope scope;
    private GomWorkspace work;
    private BufferedWriter log;
    private long expected;
    public DonorReplay(RunContext<PermutationSolution<Integer>> context,Instance in,Path input,Path out,String arm,long randomSeed)throws IOException {
        run=context;instance=in;output=out;mode=arm;seed=randomSeed;
        data=new DonorData(input,run.problem(),in,seed);SeededRandom.reset(seed);
        scope=new GomRunScope(run,new GomRunScope.Evidence(){
            public boolean recording(){return false;}
            public void record(Map<String,Object> row){throw new AssertionError("Unused detailed scope record");}
            public void view(PermutationSolution<Integer> a,PermutationSolution<Integer> b){throw new AssertionError("Unused scope view");}
        },phase->{});
        for(double[] p:data.background)scope.archive.offer(p);
    }
    public void observed(PermutationSolution<Integer> point,long fee){scope.observed(point,fee,null);}
    public Map<String,Object> validateImports(DynamicParameters params) {
        long start=System.nanoTime(),count=0;
        if(Boolean.getBoolean("research.donor.importQA"))for(DonorData.Entry e:data.imported) {
            FourVectors v=GomRecords.vectors(e.point);
            DynamicSchedule full=DynamicDecoder.full(instance,params,v.jobs(),v.factories(),v.machines(),v.workers(),()->{});
            DynamicValidator.validate(instance,params,full);
            if(!Arrays.equals(full.objectives(),e.point.getObjectives()))throw new AssertionError("Imported objectives disagree");count++;
        }
        return GomRecords.row("fullDecodes",count,"offlineSeconds",(System.nanoTime()-start)/1e9);
    }
    public void run() {
        try {
            List<PermutationSolution<Integer>> points=new ArrayList<>();for(DonorData.Entry e:data.receivers)points.add(e.point);
            GomRunScope.begin(points,instance);work=scope.workspace;
            expected=0;for(int slot=0;slot<100;slot++)expected+=work.masks.get(work.families.get(slot)).size();
            if(expected!=100L*(2*instance.jobs()-1)-20L*(instance.factories()-1))throw new AssertionError("Unexpected complete FOS budget");
            write(output.resolve("before.json"),population());write(output.resolve("models.json"),work.masks);
            List<Map<String,Object>> views=new ArrayList<>();for(int i=0;i<data.external.size();i++) {
                DonorData.Entry e=data.external.get(i);Map<String,Object> row=GomRecords.raw(GomRecords.copy(e.point,e.genes));
                row.putAll(GomRecords.row("id",i,"source",e.source,"family",e.family,"paidByFE",e.paidBy,
                    "resources",e.genes.allocations(),"keys",e.genes.priorities()));views.add(row);
            }
            write(output.resolve("views.json"),views);write(output.resolve("pool-counts.json"),data.counts);
            log=Files.newBufferedWriter(output.resolve("steps.jsonl"),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
            SearchState evaluator=new SearchState(run.problem(),instance,null);
            for(int slot=0;slot<100;slot++) {
                if(mode.equals("NATIVE"))GomLocalProgram.improve(new Particle(points.get(slot)),data.receivers.get(slot).role,evaluator);
                else program(slot);
            }
        }catch(IOException e){throw new UncheckedIOException(e);}
        finally {if(log!=null)try{log.close();}catch(IOException e){throw new UncheckedIOException(e);}}
    }
    private void program(int slot)throws IOException {
        int family=work.families.get(slot);Direction role=data.receivers.get(slot).role;
        List<int[]> masks=work.masks.get(family);List<Integer> order=new ArrayList<>();
        for(int i=0;i<masks.size();i++)order.add(i);Collections.shuffle(order,SeededRandom.current());
        List<Integer> live=new ArrayList<>(work.domains.get(family));live.remove(Integer.valueOf(slot));
        int[] fixed=(int[])data.receivers.get(slot).point.getAttribute("cooperation.fixedFactoryByJob");
        List<DonorData.Entry> extras=data.compatible(family,mode,fixed,work.catalog);
        for(int step=0;step<order.size();step++) {
            run.problem().checkpoint();int subset=order.get(step),size=live.size()+extras.size();
            long drawSeed=seed^(0x632be59bd9b4e019L*(slot+1)+0x9e3779b97f4a7c15L*(step+1));
            int draw=mode.equals("R_NATIVE")?SeededRandom.current().nextInt(size):new Random(drawSeed).nextInt(size);
            String source;int donorId;long paidBy;TypedScheduleGenome donor;
            if(draw<live.size()) {donorId=live.get(draw);GomRecords.State e=work.values.get(donorId);source="R";donor=e.genes;paidBy=e.paidFE;}
            else {DonorData.Entry e=extras.get(draw-live.size());donorId=data.external.indexOf(e);source=e.source;donor=e.genes;paidBy=e.paidBy;}
            GomRecords.State parent=work.values.get(slot);
            PaMixingMove move=PaMixingMove.apply(work.catalog,parent.genes,donor,masks.get(subset));
            PermutationSolution<Integer> child=GomRecords.copy(parent.point,move.genome);
            if(SchedulingEncoding.repair(child,instance)!=0)throw new AssertionError("Probe proposal required repair");
            run.problem().evaluate(child);GomRecords.sameView(child,move.genome);
            boolean keep=role==Direction.CENTER?PaInternalArchive.weaklyDominates(child.getObjectives(),parent.objectives)||!scope.lastFlags.dominated
                :child.getObjective(role.objective())<parent.objectives[role.objective()];
            if(keep)work.values.set(slot,new GomRecords.State(++scope.states,run.budget().successful(),move.genome,child));
            Map<String,Object> row=GomRecords.raw(child);row.putAll(GomRecords.row("fe",run.budget().successful(),"slot",slot,"step",step,
                "subset",subset,"mask",masks.get(subset),"role",role.name(),"family",family,"donorType",source,"donorId",donorId,
                "donorPaidByFE",paidBy,"poolSize",size,"draw",draw,"proposalSeed",drawSeed,"parentObjectives",parent.objectives,
                "accepted",keep,"admitted",scope.lastFlags.fresh,"dominated",scope.lastFlags.dominated,"equal",scope.lastFlags.equal,
                "fallback",move.fallback,"resources",move.genome.allocations(),"keys",move.genome.priorities()));
            log.write(DynamicJson.encode(row));log.newLine();
        }
    }
    public List<Map<String,Object>> population() {
        List<Map<String,Object>> result=new ArrayList<>();if(work==null)return result;
        for(int i=0;i<100;i++){GomRecords.State e=work.values.get(i);Map<String,Object> row=GomRecords.raw(GomRecords.copy(e.point,e.genes));
            row.putAll(GomRecords.row("slot",i,"family",work.families.get(i),"role",data.receivers.get(i).role.name(),
                "resources",e.genes.allocations(),"keys",e.genes.priorities()));result.add(row);}
        return result;
    }
    public void finish()throws IOException {write(output.resolve("after.json"),population());write(output.resolve("front.json"),scope.archive());}
    public long expected(){return expected;}
    public static void write(Path file,Object value)throws IOException {Files.write(file,DynamicJson.encode(value).getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);}
    public Object getResult(){return scope.archive();}
    public String getName(){return "MATURE_RECEIVER_DONOR_PROBE_"+mode;}
    public String getDescription(){return "One fixed-model donor supply probe, not a resumed full algorithm";}
}
