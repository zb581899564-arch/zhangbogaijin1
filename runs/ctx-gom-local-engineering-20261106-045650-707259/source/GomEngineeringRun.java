package research.dynamic;

import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.*;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;
import org.uma.jmetal.util.research.search.*;

/** Same driver can run frozen core or isolated overrides. All algorithm construction is clocked. */
public final class GomEngineeringRun {
    private GomEngineeringRun() { }
    private static final class Search implements Algorithm<Object> {
        private static final long serialVersionUID = 1L;
        final String mode; final Instance in; final DynamicParameters fatigue; final DynamicEvaluation decoder;
        final RunContext<PermutationSolution<Integer>> run; final GomEngineeringEvidence evidence; final String synthetic;
        GomRunScope scope; DynamicSearch delegate;
        Search(String name, Instance value, DynamicParameters params, DynamicEvaluation raw, RunContext<PermutationSolution<Integer>> context,
                GomEngineeringEvidence sink, String injection) { mode = name; in = value; fatigue = params; decoder = raw; run = context; evidence = sink; synthetic = injection; }
        public void run() {
            scope = new GomRunScope(run, evidence, phase -> {
                if (synthetic.equals("MODEL_ROW") && phase.equals("MODEL_ROW")) GomSyntheticStop.stop(run.clock());
                if (synthetic.equals("BEFORE_SECOND_LOCAL_PROPOSAL") && phase.equals("LOCAL_PROPOSAL") && scope.localFees() == 1) GomSyntheticStop.stop(run.clock());
            });
            SearchConfig cfg = new SearchConfig(); cfg.mergeGlobalLocal = cfg.paperResourceOperators = !DynamicSearch.isClassic(mode);
            delegate = DynamicSearch.create(mode,in,fatigue,decoder,run,cfg,false,0,0); delegate.algorithm.run();
        }
        public Object getResult() { return null; }
        public String getName() { return "CONTEXT_GOM_ENGINEERING"; }
        public String getDescription() { return getName(); }
    }
    public static void main(String[] args) throws Exception {
        Path input = Paths.get(args[0]), out = Paths.get(args[3]); Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir", input.getParent().toString()); System.setProperty("dhfsp.setupFile", args[1]); System.setProperty("dhfsp.standbyPower", "1");
        System.setProperty("research.pddr.mode", "LINEAR"); System.setProperty("research.qgsAudit.mode", "record");
        System.setProperty("research.qgsAudit.ledger", out.resolve("unused-ledger.csv").toString());
        String[] d = input.getFileName().toString().replace(".txt", "").split("_");
        EDHHFSPW raw = new EDHHFSPW(Integer.parseInt(d[0]),Integer.parseInt(d[1]),Integer.parseInt(d[2]),Integer.parseInt(d[3]));
        Instance instance = raw.getSchedulingInstance(); if (!instance.satisfiesDualResourceCondition()) throw new IllegalArgumentException("Unqualified instance");
        DynamicParameters fatigue = DynamicInputs.fatigue(instance, Paths.get(args[2])); DynamicEvaluation decoder = new DynamicEvaluation(raw,instance,fatigue,true);
        long limit = Long.parseLong(args[5]); double seconds = Double.parseDouble(args[7]);
        RunContext<PermutationSolution<Integer>> run = new RunContext<>(decoder,limit,Long.parseLong(args[6]),seconds); decoder.setCheckpoint(run::checkpoint);
        PaRunChecks checks = new PaRunChecks(instance,fatigue); PaLightEvidence light = new PaLightEvidence(limit,seconds); GomPrefixDigest prefixes = new GomPrefixDigest();
        GomEngineeringEvidence evidence = new GomEngineeringEvidence(out,checks);
        Search search = new Search(args[4],instance,fatigue,decoder,run,evidence,args[8]);
        run.problem().setObserver(new EvaluationObserver() {
            public void completed(long fe,double t,boolean changed,ThreeObjectiveArchive<?> archive) { throw new AssertionError("Paid point required"); }
            @SuppressWarnings("unchecked")
            public void completedSolution(Solution<?> p,long fe,double t,boolean changed,ThreeObjectiveArchive<?> archive) {
                PermutationSolution<Integer> point = (PermutationSolution<Integer>)p;
                checks.paid(point,fe); prefixes.update(point,fe); search.scope.observed(point,fe,checks.lastRawHash); light.completedSolution(point,fe,t,changed,archive);
            }
        });
        Throwable failure = null;
        try { SnapshotCopyMetrics.searchStarted(); run.run(search); }
        catch (RuntimeException | Error error) { failure = error; }
        finally { SnapshotCopyMetrics.searchEnded(); evidence.close(); }
        List<Map<String,Object>> front = new ArrayList<>(); for (PermutationSolution<Integer> p : run.result()) front.add(ProbeData.encoding(p));
        String paidSHA = checks.paidDigest.finish();
        if (!paidSHA.equals(prefixes.snapshot())) failure = new AssertionError("Diagnostic paid digest differs from common digest");
        Map<String,Object> receipt = GomRecords.row("status", failure == null ? "COMPLETE" : "INCOMPLETE_RETAINED", "error", failure == null ? null : failure.toString(),
            "mode",args[4],"enabled",GomRunScope.enabled(),"syntheticClock",args[8],"evaluationLimit",limit,"timeLimitSeconds",seconds,
            "successful",run.budget().successful(),"attempted",run.budget().attempted(),
            "failed",run.budget().failed(),"timeInterruptedAttempts",run.budget().timeInterruptedAttempts(),"stopReason",run.stopReason(),
            "searchSecondsIncludingEngineeringQA",run.clock().elapsedSeconds(),"paidSHA256",paidSHA,"paidPrefixes",prefixes.prefixes,"paidFullTimelineQA",checks.paidQA,
            "viewFullTimelineQA",checks.neutralQA,"gom",search.scope == null ? null : search.scope.diagnostics(),"internalArchive",search.scope == null ? null : search.scope.archive(),
            "search",search.delegate == null ? null : search.delegate.diagnostics(),"decoder",decoder.diagnostics(),"lastValidFront",front,"defaultMainlineChanged",false,"goalAchieved",false);
        NeutralProbeSupport.append(out.resolve("receipt.jsonl"),receipt); decoder.clearPrepared();
        org.uma.jmetal.util.research.modelglobal.FirstStageCatalog catalog = new org.uma.jmetal.util.research.modelglobal.FirstStageCatalog(instance);
        List<int[]> tuples = new ArrayList<>(); for (int i = 0; i < catalog.size(); i++) tuples.add(catalog.tuple(i));
        NeutralProbeSupport.append(out.resolve("catalog.jsonl"), GomRecords.row("tuples",tuples,"jobs",instance.jobs(),"factories",instance.factories(),"seed",run.seed()));
        if (failure != null) throw new IllegalStateException("Engineering failure retained",failure);
        QgsLocalLedger.finish(out); light.write(out,instance,fatigue);
        PaLightEvidence.writeRows(out.resolve("loaded-identity.jsonl"),Collections.singletonList(ClassResolutionProbe.capture(
            "research.dynamic.GomEngineeringRun","org.uma.jmetal.util.research.search.GomRunScope","org.uma.jmetal.util.research.search.GomWorkspace",
            "org.uma.jmetal.util.research.search.GomDomainModels","org.uma.jmetal.util.research.search.GomLocalProgram",
            "org.uma.jmetal.util.research.search.CanonicalHmopso","org.uma.jmetal.util.research.search.LocalSearch",
            "org.uma.jmetal.util.research.search.DeepLocalVisits","org.uma.jmetal.util.research.classic.ClassicAlgorithm",
            "org.uma.jmetal.util.research.cooperation.FamilyContexts","org.uma.jmetal.util.research.cooperation.CooperationSupport",
            "org.uma.jmetal.util.research.modelglobal.PaDependencyModel","org.uma.jmetal.util.research.modelglobal.PaMixingMove",
            "org.uma.jmetal.util.research.modelglobal.LinkageHierarchy",
            "org.uma.jmetal.util.research.modelglobal.FactoryKeyReencoder","org.uma.jmetal.util.research.modelglobal.PaInternalArchive",
            "org.uma.jmetal.util.research.DynamicEvaluation","org.uma.jmetal.util.research.model.DynamicDecoder","org.uma.jmetal.util.research.runtime.BudgetedProblem")));
        System.out.println("CTX_GOM_ENGINEERING_DONE "+run.budget().successful()+" "+run.stopReason());
    }
}
