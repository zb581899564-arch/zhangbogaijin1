package research.dynamic;

import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.*;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;
import org.uma.jmetal.util.research.search.*;

/** Isolated phase ablations of the frozen SHARE_CTX_GOM; no production API change. */
public final class PilotRun {
    private PilotRun() { }
    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]),out=Paths.get(args[3]);Files.createDirectories(out);
        String phase=args[4];if(!Arrays.asList("FULL","GLOBAL_ONLY","LOCAL_ONLY").contains(phase))throw new IllegalArgumentException(phase);
        System.setProperty("research.pilot.phase",phase);System.setProperty("research.ctxGom.enabled","true");
        System.setProperty("dhfsp.dataDir",input.getParent().toString());System.setProperty("dhfsp.setupFile",args[1]);
        System.setProperty("dhfsp.standbyPower","1");System.setProperty("research.pddr.mode","LINEAR");
        System.setProperty("research.qgsAudit.mode","record");System.setProperty("research.qgsAudit.ledger",out.resolve("unused-ledger.csv").toString());
        String[] d=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(d[0]),Integer.parseInt(d[1]),Integer.parseInt(d[2]),Integer.parseInt(d[3]));
        Instance in=raw.getSchedulingInstance();if(!in.satisfiesDualResourceCondition())throw new IllegalArgumentException("Unqualified");
        DynamicParameters fatigue=DynamicInputs.fatigue(in,Paths.get(args[2]));
        DynamicEvaluation decoder=new DynamicEvaluation(raw,in,fatigue,true);
        long limit=Long.parseLong(args[5]),seed=Long.parseLong(args[6]);double seconds=Double.parseDouble(args[7]);
        RunContext<PermutationSolution<Integer>> run=new RunContext<>(PilotPhysics.delegate(decoder),limit,seed,seconds);decoder.setCheckpoint(run::checkpoint);
        PilotPhysics physics=new PilotPhysics(in,fatigue);
        QgsLocalLedger.allowDeadlinePrefix(()->run.clock().elapsedSeconds()>=seconds);
        PilotEvidence evidence=new PilotEvidence(limit,seconds);
        PilotTrace trace=new PilotTrace(run,out,!Boolean.getBoolean("research.pilot.observationOff"));
        GomCapabilitySearch search=new GomCapabilitySearch("SHARE_CTX_GOM",run,in,fatigue,decoder);
        run.problem().setObserver(new EvaluationObserver() {
            public void completed(long fe,double t,boolean changed,ThreeObjectiveArchive<?> archive){throw new AssertionError("Paid point required");}
            @SuppressWarnings("unchecked") public void completedSolution(Solution<?> value,long fe,double t,boolean changed,ThreeObjectiveArchive<?> archive) {
                search.observed((PermutationSolution<Integer>)value,fe);
                trace.paid((PermutationSolution<Integer>)value,fe,t,changed);evidence.completed(value,fe,t,changed,archive);
                physics.check((PermutationSolution<Integer>)value);
            }
        });
        Throwable failure=null;
        try{SnapshotCopyMetrics.searchStarted();run.run(search);}catch(RuntimeException|Error e){failure=e;}
        finally{SnapshotCopyMetrics.searchEnded();decoder.clearPrepared();}
        Map<String,Object> receipt=GomRecords.row("method","SHARE_CTX_GOM","phaseArm",phase,"seed",seed,"feLimit",limit,
            "attempted",run.budget().attempted(),"successful",run.budget().successful(),"failed",run.budget().failed(),
            "timeInterruptedAttempts",run.budget().timeInterruptedAttempts(),"stopReason",run.stopReason(),
            "searchSeconds",run.clock().elapsedSeconds(),"search",search.diagnostics(),"decoder",decoder.diagnostics(),
            "paidSHA256",evidence.digest.finish(),"observationCheckpointSeconds",evidence.nanos/1e9,"trace",trace.finish(),"physicsQA",physics.receipt(),
            "error",failure==null?null:failure.toString(),"defaultMainlineChanged",false,"constructorsIncludedInClock",true);
        PaLightEvidence.writeRows(out.resolve("run-receipt.jsonl"),Collections.singletonList(receipt));
        if(failure!=null){evidence.last.writeFailure(out,failure.toString(),run.budget().attempted(),run.budget().successful(),run.budget().failed());throw new IllegalStateException("Retained failure",failure);}
        QgsLocalLedger.finish(out);evidence.write(out,in,fatigue);
        PaLightEvidence.writeRows(out.resolve("loaded-identity.jsonl"),Collections.singletonList(ClassResolutionProbe.capture(
            "research.dynamic.PilotRun","research.dynamic.GomCapabilitySearch","org.uma.jmetal.util.research.search.PilotTrace",
            "org.uma.jmetal.util.research.search.CanonicalHmopso","org.uma.jmetal.util.research.search.SearchState",
            "org.uma.jmetal.util.research.search.GomLocalProgram","org.uma.jmetal.util.research.search.GomWorkspace",
            "org.uma.jmetal.util.research.DynamicEvaluation","org.uma.jmetal.util.research.runtime.BudgetedProblem")));
        System.out.println("PILOT_DONE "+phase+" "+run.budget().successful());
    }
}
