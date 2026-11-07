package research.dynamic;

import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;
import org.uma.jmetal.util.research.search.QgsLocalLedger;

/** Common paid checkpoints and true clock, with an explicit ordinary MOEA/D branch. */
public final class PlainMoeadRun {
    private PlainMoeadRun(){ }
    public static void main(String[] args) throws Exception {
        if(!args[4].equals("MOEAD_4V"))throw new IllegalArgumentException("MOEAD_4V required");
        Path input=Paths.get(args[0]),out=Paths.get(args[3]);Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir",input.getParent().toString());System.setProperty("dhfsp.setupFile",args[1]);
        System.setProperty("dhfsp.standbyPower","1");System.setProperty("research.pddr.mode","LINEAR");
        System.setProperty("research.qgsAudit.mode","record");System.setProperty("research.qgsAudit.ledger",out.resolve("unused-ledger.csv").toString());
        String[] d=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(d[0]),Integer.parseInt(d[1]),Integer.parseInt(d[2]),Integer.parseInt(d[3]));
        Instance in=raw.getSchedulingInstance();if(!in.satisfiesDualResourceCondition())throw new IllegalArgumentException("Unqualified instance");
        DynamicParameters fatigue=DynamicInputs.fatigue(in,Paths.get(args[2]));DynamicEvaluation decoder=new DynamicEvaluation(raw,in,fatigue,true);
        long limit=Long.parseLong(args[5]),seed=Long.parseLong(args[6]);double seconds=Double.parseDouble(args[7]);
        RunContext<PermutationSolution<Integer>> run=new RunContext<>(decoder,limit,seed,seconds);decoder.setCheckpoint(run::checkpoint);
        QgsLocalLedger.allowDeadlinePrefix(()->run.clock().elapsedSeconds()>=seconds);
        PaLightEvidence evidence=new PaLightEvidence(limit,seconds);run.problem().setObserver(evidence);
        boolean reference=Boolean.getBoolean("research.moead.reference");PlainMoeadSearch search=new PlainMoeadSearch(run,in,reference);Throwable failure=null;
        try{SnapshotCopyMetrics.searchStarted();run.run(search);}catch(RuntimeException|Error error){failure=error;}
        finally{SnapshotCopyMetrics.searchEnded();decoder.clearPrepared();}
        Map<String,Object> receipt=NeutralProbeSupport.row("arm","MOEAD_4V","seed",seed,"feLimit",limit,"attempted",run.budget().attempted(),
            "successful",run.budget().successful(),"failed",run.budget().failed(),"timeInterruptedAttempts",run.budget().timeInterruptedAttempts(),
            "stopReason",run.stopReason(),"searchSeconds",run.clock().elapsedSeconds(),"search",search.diagnostics(),"decoder",decoder.diagnostics(),
            "paidSHA256",evidence.digest==null?null:evidence.digest.finish(),"constructorsIncludedInClock",true,
            "referenceAdapter",reference,"executedAlgorithm",search.executedClass(),"localSearchInvoked",false,
            "configuration",new org.uma.jmetal.util.research.classic.ClassicConfig("MOEAD_4V",0).describe(),
            "error",failure==null?null:failure.toString(),"goalAchieved",false);
        PaLightEvidence.writeRows(out.resolve("run-receipt.jsonl"),Collections.singletonList(receipt));
        if(failure!=null){evidence.last.writeFailure(out,failure.toString(),run.budget().attempted(),run.budget().successful(),run.budget().failed());throw new IllegalStateException("MOEA/D failure retained",failure);}
        QgsLocalLedger.finish(out);evidence.write(out,in,fatigue);
        PaLightEvidence.writeRows(out.resolve("loaded-identity.jsonl"),Collections.singletonList(ClassResolutionProbe.capture(
            "research.dynamic.PlainMoeadRun","research.dynamic.PlainMoeadSearch","org.uma.jmetal.util.research.classic.OrdinaryMoeadAlgorithm",
            "org.uma.jmetal.util.research.classic.MoeadReferenceAlgorithm","org.uma.jmetal.util.research.classic.MoeadDecomposition",
            "org.uma.jmetal.util.research.classic.ClassicConfig","org.uma.jmetal.util.research.classic.ClassicVariation",
            "org.uma.jmetal.util.research.classic.FrozenObjectiveScale","org.uma.jmetal.util.research.search.DeepLocalVisits",
            "org.uma.jmetal.util.research.search.PaInitialBridge","org.uma.jmetal.util.research.DynamicEvaluation",
            "org.uma.jmetal.util.research.model.DynamicDecoder","org.uma.jmetal.util.research.runtime.BudgetedProblem")));
        System.out.println("PLAIN_MOEAD_DONE "+reference+" "+run.budget().successful());
    }
}
