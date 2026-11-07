package research.dynamic;

import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;
import org.uma.jmetal.util.research.search.QgsLocalLedger;

/** Six methods share one true-clock and paid-checkpoint observation contract. */
public final class PaCapabilityRun {
    private PaCapabilityRun() { }
    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]),out=Paths.get(args[3]); Files.createDirectories(out); String arm=args[4];
        if(!Arrays.asList("PA_JOINT","PA_RELABEL","NSGA2_PLAIN","NSGA2_DEEP","FULL_SHARED_DEEP","LI_RECON_DEEP").contains(arm))
            throw new IllegalArgumentException("Unknown capability arm");
        long limit=Long.parseLong(args[5]),seed=Long.parseLong(args[6]); double seconds=Double.parseDouble(args[7]);
        System.setProperty("dhfsp.dataDir",input.getParent().toString());System.setProperty("dhfsp.setupFile",args[1]);
        System.setProperty("dhfsp.standbyPower","1");System.setProperty("research.pddr.mode","LINEAR");
        System.setProperty("research.qgsAudit.mode","record"); System.setProperty("research.qgsAudit.ledger",out.resolve("unused-ledger.csv").toString());
        String[] d=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(d[0]),Integer.parseInt(d[1]),Integer.parseInt(d[2]),Integer.parseInt(d[3]));
        Instance instance=raw.getSchedulingInstance();if(!instance.satisfiesDualResourceCondition())throw new IllegalArgumentException("Unqualified instance");
        DynamicParameters fatigue=DynamicInputs.fatigue(instance,Paths.get(args[2])); DynamicEvaluation decoder=new DynamicEvaluation(raw,instance,fatigue,true);
        RunContext<PermutationSolution<Integer>> run=new RunContext<>(decoder,limit,seed,seconds);decoder.setCheckpoint(run::checkpoint);
        QgsLocalLedger.allowDeadlinePrefix(()->run.clock().elapsedSeconds()>=seconds);
        PaLightEvidence evidence=new PaLightEvidence(limit,seconds);run.problem().setObserver(evidence);
        PaCapabilitySearch search=new PaCapabilitySearch(arm,run,instance,fatigue,decoder);Throwable failure=null;
        try{SnapshotCopyMetrics.searchStarted();run.run(search);}catch(RuntimeException|Error e){failure=e;}
        finally{SnapshotCopyMetrics.searchEnded();decoder.clearPrepared();}
        Map<String,Object> receipt=NeutralProbeSupport.row("arm",arm,"seed",seed,"feLimit",limit,"timeLimitSeconds",Double.isFinite(seconds)?seconds:null,
            "attempted",run.budget().attempted(),"successful",run.budget().successful(),"failed",run.budget().failed(),
            "timeInterruptedAttempts",run.budget().timeInterruptedAttempts(),"stopReason",run.stopReason(),"searchSeconds",run.clock().elapsedSeconds(),
            "search",search.diagnostics(),"decoder",decoder.diagnostics(),"paidSHA256",evidence.digest==null?null:evidence.digest.finish(),
            "traceIdentity",Boolean.parseBoolean(System.getProperty("research.pa.traceIdentity","true")),
            "constructorsIncludedInClock",true,"error",failure==null?null:failure.toString(),"goalAchieved",false);
        PaLightEvidence.writeRows(out.resolve("run-receipt.jsonl"),Collections.singletonList(receipt));
        if(failure!=null){evidence.last.writeFailure(out,failure.toString(),run.budget().attempted(),run.budget().successful(),run.budget().failed());
            throw new IllegalStateException("Capability failure retained",failure);}
        QgsLocalLedger.finish(out); evidence.write(out,instance,fatigue);
        PaLightEvidence.writeRows(out.resolve("loaded-identity.jsonl"),Collections.singletonList(ClassResolutionProbe.capture(
            "research.dynamic.PaCapabilityRun","org.uma.jmetal.util.research.modelglobal.PaPopulation",
            "org.uma.jmetal.util.research.modelglobal.PaIndividual","org.uma.jmetal.util.research.modelglobal.PaSubsetPolicy",
            "org.uma.jmetal.util.research.classic.PlainNsgaAlgorithm","org.uma.jmetal.util.research.classic.ClassicAlgorithm",
            "org.uma.jmetal.util.research.search.DeepLocalVisits","org.uma.jmetal.util.research.search.CanonicalHmopso",
            "org.uma.jmetal.util.research.DynamicEvaluation","org.uma.jmetal.util.research.model.DynamicDecoder")));
        System.out.println("PA_CAPABILITY_DONE "+arm+" "+run.budget().successful()+" "+run.stopReason());
    }
}
