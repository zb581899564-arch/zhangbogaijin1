package research.dynamic;

import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.*;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;
import org.uma.jmetal.util.research.search.*;

/** Common light observation, strict FE and true clock; checkpoint physics QA happens after search. */
public final class GomCapabilityRun {
    private GomCapabilityRun() { }
    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]),out=Paths.get(args[3]); Files.createDirectories(out); String arm=args[4];
        if (!Arrays.asList("SHARE_CTX_GOM","SYNC_CTX_GOM","UNIFORM_CTX_GOM","NSGA_CTX_GOM", "PA_JOINT","PA_EQUAL",
                "NSGA2_PLAIN","NSGA2_DEEP","FULL_SHARED_DEEP","LI_RECON_DEEP").contains(arm)) throw new IllegalArgumentException("Unknown arm");
        System.setProperty("research.ctxGom.enabled",Boolean.toString(GomCapabilitySearch.contextArm(arm)));
        System.setProperty("research.pa.boundaryNonWorse",Boolean.toString(arm.equals("PA_EQUAL")));
        System.setProperty("dhfsp.dataDir",input.getParent().toString()); System.setProperty("dhfsp.setupFile",args[1]);
        System.setProperty("dhfsp.standbyPower","1"); System.setProperty("research.pddr.mode","LINEAR");
        System.setProperty("research.qgsAudit.mode","record"); System.setProperty("research.qgsAudit.ledger",out.resolve("unused-ledger.csv").toString());
        String[] d=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(d[0]),Integer.parseInt(d[1]),Integer.parseInt(d[2]),Integer.parseInt(d[3]));
        Instance in=raw.getSchedulingInstance(); if (!in.satisfiesDualResourceCondition()) throw new IllegalArgumentException("Unqualified instance");
        DynamicParameters fatigue=DynamicInputs.fatigue(in,Paths.get(args[2])); DynamicEvaluation decoder=new DynamicEvaluation(raw,in,fatigue,true);
        long limit=Long.parseLong(args[5]),seed=Long.parseLong(args[6]); double seconds=Double.parseDouble(args[7]);
        RunContext<PermutationSolution<Integer>> run=new RunContext<>(decoder,limit,seed,seconds); decoder.setCheckpoint(run::checkpoint);
        QgsLocalLedger.allowDeadlinePrefix(()->run.clock().elapsedSeconds()>=seconds);
        PaLightEvidence evidence=new PaLightEvidence(limit,seconds); GomCapabilitySearch search=new GomCapabilitySearch(arm,run,in,fatigue,decoder);
        TrajectoryTrace trajectory=new TrajectoryTrace(run,out,arm);
        run.problem().setObserver(new EvaluationObserver() {
            public void completed(long fe,double t,boolean changed,ThreeObjectiveArchive<?> archive) { throw new AssertionError("Paid point required"); }
            @SuppressWarnings("unchecked")
            public void completedSolution(Solution<?> value,long fe,double t,boolean changed,ThreeObjectiveArchive<?> archive) {
                search.observed((PermutationSolution<Integer>)value,fe); evidence.completedSolution(value,fe,t,changed,archive);
                trajectory.paid((PermutationSolution<Integer>)value,fe,changed);
            }
        });
        Throwable failure=null;
        try { SnapshotCopyMetrics.searchStarted(); run.run(search); }
        catch (RuntimeException|Error error) { failure=error; }
        finally { SnapshotCopyMetrics.searchEnded(); decoder.clearPrepared(); }
        PaLightEvidence.writeRows(out.resolve("trajectory-receipt.jsonl"),Collections.singletonList(trajectory.finish()));
        Map<String,Object> receipt=GomRecords.row("arm",arm,"seed",seed,"feLimit",limit,"timeLimitSeconds",Double.isFinite(seconds)?seconds:null,
            "attempted",run.budget().attempted(),"successful",run.budget().successful(),"failed",run.budget().failed(),
            "timeInterruptedAttempts",run.budget().timeInterruptedAttempts(),"stopReason",run.stopReason(),"searchSeconds",run.clock().elapsedSeconds(),
            "search",search.diagnostics(),"decoder",decoder.diagnostics(),"paidSHA256",evidence.digest==null?null:evidence.digest.finish(),
            "constructorsIncludedInClock",true,"paidTimelineQAInSearch",false,"detailedCandidateTrace",false,
            "error",failure==null?null:failure.toString(),"defaultMainlineChanged",false,"goalAchieved",false);
        PaLightEvidence.writeRows(out.resolve("run-receipt.jsonl"),Collections.singletonList(receipt));
        if (failure!=null) { evidence.last.writeFailure(out,failure.toString(),run.budget().attempted(),run.budget().successful(),run.budget().failed());
            throw new IllegalStateException("Capability failure retained",failure); }
        QgsLocalLedger.finish(out); evidence.write(out,in,fatigue);
        PaLightEvidence.writeRows(out.resolve("loaded-identity.jsonl"),Collections.singletonList(ClassResolutionProbe.capture(
            "research.dynamic.GomCapabilityRun","research.dynamic.GomCapabilitySearch","org.uma.jmetal.util.research.search.GomRunScope",
            "org.uma.jmetal.util.research.search.GomWorkspace","org.uma.jmetal.util.research.search.GomDomainModels",
            "org.uma.jmetal.util.research.search.GomLocalProgram","org.uma.jmetal.util.research.search.CanonicalHmopso",
            "org.uma.jmetal.util.research.search.LocalSearch","org.uma.jmetal.util.research.search.DeepLocalVisits",
            "org.uma.jmetal.util.research.classic.ClassicAlgorithm","org.uma.jmetal.util.research.classic.PlainNsgaAlgorithm",
            "org.uma.jmetal.util.research.cooperation.CooperationSupport","org.uma.jmetal.util.research.cooperation.FamilyContexts",
            "org.uma.jmetal.util.research.modelglobal.PaPopulation","org.uma.jmetal.util.research.modelglobal.PaDependencyModel",
            "org.uma.jmetal.util.research.modelglobal.PaMixingMove","org.uma.jmetal.util.research.modelglobal.FactoryKeyReencoder",
            "org.uma.jmetal.util.research.modelglobal.LinkageHierarchy","org.uma.jmetal.util.research.modelglobal.PaInternalArchive",
            "org.uma.jmetal.util.research.DynamicEvaluation","org.uma.jmetal.util.research.model.DynamicDecoder",
            "org.uma.jmetal.util.research.runtime.BudgetedProblem")));
        System.out.println("CTX_GOM_CAPABILITY_DONE "+arm+" "+run.budget().successful()+" "+run.stopReason());
    }
}
