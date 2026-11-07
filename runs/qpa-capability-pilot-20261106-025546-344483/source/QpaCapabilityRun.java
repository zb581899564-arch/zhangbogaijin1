package research.dynamic;

import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.modelglobal.*;
import org.uma.jmetal.util.research.runtime.*;
import org.uma.jmetal.util.research.search.QgsLocalLedger;

/** Common light paid checkpoint entry. Heavy engineering QA is replaced by post-clock checkpoint QA. */
public final class QpaCapabilityRun {
    private QpaCapabilityRun() { }
    public static void main(String[] args) throws Exception {
        Path input = Paths.get(args[0]), out = Paths.get(args[3]); Files.createDirectories(out); String arm = args[4];
        boolean direct = arm.equals("QPA_DIRECT");
        System.setProperty("research.pa.boundaryNonWorse", Boolean.toString(arm.equals("PA_EQUAL")));
        System.setProperty("dhfsp.dataDir", input.getParent().toString()); System.setProperty("dhfsp.setupFile", args[1]);
        System.setProperty("dhfsp.standbyPower", "1"); System.setProperty("research.pddr.mode", "LINEAR");
        System.setProperty("research.qgsAudit.mode", "record"); System.setProperty("research.qgsAudit.ledger", out.resolve("unused-ledger.csv").toString());
        String[] d = input.getFileName().toString().replace(".txt", "").split("_");
        EDHHFSPW raw = new EDHHFSPW(Integer.parseInt(d[0]), Integer.parseInt(d[1]), Integer.parseInt(d[2]), Integer.parseInt(d[3]));
        Instance instance = raw.getSchedulingInstance();
        if (!instance.satisfiesDualResourceCondition()) throw new IllegalArgumentException("Unqualified instance");
        DynamicParameters fatigue = DynamicInputs.fatigue(instance, Paths.get(args[2]));
        DynamicEvaluation decoder = new DynamicEvaluation(raw, instance, fatigue, true);
        long limit = Long.parseLong(args[5]); double seconds = Double.parseDouble(args[7]);
        RunContext<PermutationSolution<Integer>> run = new RunContext<>(decoder, limit, Long.parseLong(args[6]), seconds);
        decoder.setCheckpoint(run::checkpoint); QgsLocalLedger.allowDeadlinePrefix(() -> run.clock().elapsedSeconds() >= seconds);
        PaLightEvidence evidence = new PaLightEvidence(limit, seconds); run.problem().setObserver(evidence);
        PaCapabilitySearch legacy = direct ? null : new PaCapabilitySearch(arm.equals("PA_EQUAL") ? "PA_JOINT" : arm, run, instance, fatigue, decoder);
        QpaAlgorithm qpa = direct ? new QpaAlgorithm(run, instance, noQA(), new QpaPopulation.Observer() { }, -1) : null;
        Algorithm<?> algorithm = direct ? qpa : legacy; Throwable failure = null;
        try { SnapshotCopyMetrics.searchStarted(); run.run(algorithm); }
        catch (RuntimeException | Error error) { failure = error; }
        finally { SnapshotCopyMetrics.searchEnded(); decoder.clearPrepared(); }
        Map<String,Object> receipt = NeutralProbeSupport.row("arm", arm, "seed", run.seed(), "feLimit", limit,
            "timeLimitSeconds", Double.isFinite(seconds) ? seconds : null, "attempted", run.budget().attempted(),
            "successful", run.budget().successful(), "failed", run.budget().failed(), "timeInterruptedAttempts", run.budget().timeInterruptedAttempts(),
            "stopReason", run.stopReason(), "searchSeconds", run.clock().elapsedSeconds(),
            "search", direct ? qpa.population().diagnostics() : legacy.diagnostics(), "decoder", decoder.diagnostics(),
            "paidSHA256", evidence.digest == null ? null : evidence.digest.finish(), "constructorsIncludedInClock", true,
            "traceIdentity", Boolean.parseBoolean(System.getProperty("research.pa.traceIdentity", "true")),
            "boundaryNonWorse", arm.equals("PA_EQUAL") || direct, "error", failure == null ? null : failure.toString(), "goalAchieved", false);
        PaLightEvidence.writeRows(out.resolve("run-receipt.jsonl"), Collections.singletonList(receipt));
        if (failure != null) {
            evidence.last.writeFailure(out, failure.toString(), run.budget().attempted(), run.budget().successful(), run.budget().failed());
            throw new IllegalStateException("QPA capability failure retained", failure);
        }
        QgsLocalLedger.finish(out); evidence.write(out, instance, fatigue);
        PaLightEvidence.writeRows(out.resolve("loaded-identity.jsonl"), Collections.singletonList(ClassResolutionProbe.capture(
            "research.dynamic.QpaCapabilityRun", "org.uma.jmetal.util.research.modelglobal.QpaAlgorithm",
            "org.uma.jmetal.util.research.modelglobal.QpaPopulation", "org.uma.jmetal.util.research.modelglobal.QpaPaidEvaluation",
            "org.uma.jmetal.util.research.modelglobal.QpaIndividual", "org.uma.jmetal.util.research.modelglobal.QpaLinkageModel",
            "org.uma.jmetal.util.research.modelglobal.DirectScheduleGenome", "org.uma.jmetal.util.research.modelglobal.DirectPositionMixing",
            "org.uma.jmetal.util.research.modelglobal.DirectJointMove", "org.uma.jmetal.util.research.modelglobal.PaPopulation",
            "org.uma.jmetal.util.research.modelglobal.PaPaidEvaluation", "org.uma.jmetal.util.research.search.CanonicalHmopso",
            "org.uma.jmetal.util.research.classic.ClassicAlgorithm", "org.uma.jmetal.util.research.search.DeepLocalVisits",
            "org.uma.jmetal.util.research.DynamicEvaluation", "org.uma.jmetal.util.research.model.DynamicDecoder")));
        System.out.println("QPA_CAPABILITY_DONE " + arm + " " + run.budget().successful() + " " + run.stopReason());
    }
    private static PaPaidEvaluation.Checks noQA() {
        return new PaPaidEvaluation.Checks() {
            public void paid(PermutationSolution<Integer> point, long fe) { }
            public void neutral(PermutationSolution<Integer> before, PermutationSolution<Integer> after) { }
        };
    }
}
