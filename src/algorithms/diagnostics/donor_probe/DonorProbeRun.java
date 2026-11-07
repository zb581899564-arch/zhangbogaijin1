package research.dynamic;

import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.*;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;
import org.uma.jmetal.util.research.search.*;

/** Linux controller owns ordering, source charge and engineering gates. */
public final class DonorProbeRun {
    private DonorProbeRun() { }
    public static void main(String[] args)throws Exception {
        Path input=Paths.get(args[0]),out=Paths.get(args[3]),capture=Paths.get(args[4]);Files.createDirectories(out);
        String mode=args[5];long sourceSeed=Long.parseLong(args[6]),seed=sourceSeed^0x51d0a7e3L;
        if(!Arrays.asList("R","G","S","UNION","NATIVE","R_NATIVE").contains(mode))throw new IllegalArgumentException(mode);
        System.setProperty("research.ctxGom.enabled","true");System.setProperty("dhfsp.dataDir",input.getParent().toString());
        System.setProperty("dhfsp.setupFile",args[1]);System.setProperty("dhfsp.standbyPower","1");
        String[] name=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(name[0]),Integer.parseInt(name[1]),Integer.parseInt(name[2]),Integer.parseInt(name[3]));
        Instance in=raw.getSchedulingInstance();if(!in.satisfiesDualResourceCondition())throw new IllegalArgumentException("Unqualified instance");
        DynamicParameters params=DynamicInputs.fatigue(in,Paths.get(args[2]));
        DynamicEvaluation decoder=new DynamicEvaluation(raw,in,params,true);
        long full=100L*(2*in.jobs()-1)-20L*(in.factories()-1),limit=Long.getLong("research.donor.limit",full);
        RunContext<PermutationSolution<Integer>> run=new RunContext<>(PilotPhysics.delegate(decoder),limit,seed);decoder.setCheckpoint(run::checkpoint);
        long prepareStart=System.nanoTime();DonorReplay probe=new DonorReplay(run,in,capture,out,mode,seed);
        double prepareSeconds=(System.nanoTime()-prepareStart)/1e9;
        Map<String,Object> imports=probe.validateImports(params);
        GomPrefixDigest digest=new GomPrefixDigest();PilotPhysics physics=new PilotPhysics(in,params);
        run.problem().setObserver(new EvaluationObserver(){
            public void completed(long fe,double t,boolean a,ThreeObjectiveArchive<?> archive){throw new AssertionError("Paid solution required");}
            @SuppressWarnings("unchecked") public void completedSolution(Solution<?> s,long fe,double t,boolean a,ThreeObjectiveArchive<?> archive){
                PermutationSolution<Integer> p=(PermutationSolution<Integer>)s;probe.observed(p,fe);digest.update(p,fe);physics.check(p);
            }
        });
        Throwable failure=null;try{run.run(probe);}catch(RuntimeException|Error e){failure=e;}finally{decoder.clearPrepared();}
        probe.finish();
        DonorReplay.write(out.resolve("receipt.json"),GomRecords.row("mode",mode,"sourceSeed",sourceSeed,"seed",seed,"attempted",run.budget().attempted(),
            "successful",run.budget().successful(),"failed",run.budget().failed(),"searchSeconds",run.clock().elapsedSeconds(),"prepareSeconds",prepareSeconds,
            "expectedFE",full,"plannedFE",probe.expected(),"feLimit",limit,"stopReason",run.stopReason(),"paidSHA256",digest.snapshot(),
            "physicsQA",physics.receipt(),"importQA",imports,"decoder",decoder.diagnostics(),"error",failure==null?null:failure.toString(),"loaded",ClassResolutionProbe.capture(
                "research.dynamic.DonorProbeRun","org.uma.jmetal.util.research.search.DonorReplay","org.uma.jmetal.util.research.search.DonorData",
                "org.uma.jmetal.util.research.search.GomWorkspace","org.uma.jmetal.util.research.modelglobal.PaMixingMove",
                "org.uma.jmetal.util.research.DynamicEvaluation","org.uma.jmetal.util.research.runtime.BudgetedProblem")));
        if(failure!=null)throw new IllegalStateException("Preserved donor probe failure",failure);
        System.out.println("DONOR_PROBE_DONE "+mode+" "+run.budget().successful());
    }
}
