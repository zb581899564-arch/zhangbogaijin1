package research.dynamic;

import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.modelglobal.*;
import org.uma.jmetal.util.research.runtime.RunContext;

/** Complete isolated engineering lifecycle; all paid points receive independent full timeline QA. */
public final class QpaPopulationRun {
    private QpaPopulationRun() { }
    public static void main(String[] args) throws Exception {
        Path input = Paths.get(args[0]), out = Paths.get(args[3]); Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir", input.getParent().toString()); System.setProperty("dhfsp.setupFile", args[1]);
        System.setProperty("dhfsp.standbyPower", "1");
        String[] d = input.getFileName().toString().replace(".txt", "").split("_");
        EDHHFSPW raw = new EDHHFSPW(Integer.parseInt(d[0]), Integer.parseInt(d[1]), Integer.parseInt(d[2]), Integer.parseInt(d[3]));
        Instance instance = raw.getSchedulingInstance();
        if (!instance.satisfiesDualResourceCondition()) throw new IllegalArgumentException("Unqualified instance");
        DynamicParameters fatigue = DynamicInputs.fatigue(instance, Paths.get(args[2]));
        DynamicEvaluation decoder = new DynamicEvaluation(raw, instance, fatigue, true);
        long limit = Long.parseLong(args[5]); int generations = Integer.parseInt(args[6]);
        RunContext<PermutationSolution<Integer>> run = new RunContext<>(decoder, limit, Long.parseLong(args[4]));
        decoder.setCheckpoint(run::checkpoint); PaRunChecks checks = new PaRunChecks(instance, fatigue);
        QpaEvidence evidence = new QpaEvidence(out, checks);
        QpaAlgorithm algorithm = new QpaAlgorithm(run, instance, checks, evidence, generations);
        boolean complete = false; Throwable failure = null;
        capture(out);
        try {
            run.run(algorithm);
            if (run.budget().failed() != 0 || run.budget().attempted() != run.budget().successful()
                    || checks.paidQA != run.budget().successful()) throw new AssertionError("Actual fee/QA mismatch");
            if (generations > 0) {
                if (!run.stopReason().equals("ALGORITHM_RETURNED") || algorithm.population().completedGenerations != generations)
                    throw new AssertionError("Complete generations not reached");
            } else if (!run.stopReason().equals("FE_LIMIT") || run.budget().successful() != limit)
                throw new AssertionError("Incorrect cutoff");
            complete = true;
        } catch (RuntimeException | Error error) { failure = error; }
        finally {
            evidence.close(); save(out, run, algorithm, checks, evidence, decoder, complete, failure, limit, generations);
            decoder.clearPrepared();
        }
        if (failure != null) throw new IllegalStateException("QPA engineering failed; evidence retained", failure);
        System.out.println("QPA_ENGINEERING_DONE " + run.budget().successful() + " " + run.stopReason());
    }
    private static void capture(Path out) throws Exception {
        NeutralProbeSupport.append(out.resolve("loaded-identity.jsonl"), ClassResolutionProbe.capture(
            "research.dynamic.QpaPopulationRun", "research.dynamic.QpaEvidence", "research.dynamic.PaRunChecks",
            "org.uma.jmetal.util.research.modelglobal.QpaAlgorithm", "org.uma.jmetal.util.research.modelglobal.QpaPopulation",
            "org.uma.jmetal.util.research.modelglobal.QpaPaidEvaluation", "org.uma.jmetal.util.research.modelglobal.QpaIndividual",
            "org.uma.jmetal.util.research.modelglobal.QpaLinkageModel", "org.uma.jmetal.util.research.modelglobal.DirectScheduleGenome",
            "org.uma.jmetal.util.research.modelglobal.DirectPositionMixing", "org.uma.jmetal.util.research.modelglobal.DirectJointMove",
            "org.uma.jmetal.util.research.modelglobal.FirstStageCatalog", "org.uma.jmetal.util.research.modelglobal.LinkageHierarchy",
            "org.uma.jmetal.util.research.modelglobal.PaInternalArchive", "org.uma.jmetal.util.research.search.PaInitialBridge",
            "org.uma.jmetal.util.research.DynamicEvaluation", "org.uma.jmetal.util.research.model.DynamicDecoder",
            "org.uma.jmetal.util.research.model.DynamicValidator", "org.uma.jmetal.util.research.runtime.BudgetedProblem",
            "org.uma.jmetal.util.research.runtime.SolutionSnapshots"));
    }
    private static void save(Path out, RunContext<PermutationSolution<Integer>> run, QpaAlgorithm algorithm, PaRunChecks checks,
            QpaEvidence evidence, DynamicEvaluation decoder, boolean complete, Throwable failure, long limit, int generations) throws Exception {
        QpaPopulation pop = algorithm.population(); FirstStageCatalog catalog = algorithm.catalog();
        List<int[]> tuples = new ArrayList<>(); for (int i = 0; i < catalog.size(); i++) tuples.add(catalog.tuple(i));
        NeutralProbeSupport.append(out.resolve("catalog.jsonl"), NeutralProbeSupport.row("tuples", tuples, "jobs", catalog.jobs(),
            "factories", catalog.factories(), "seed", run.seed(), "feLimit", limit, "generationLimit", generations));
        List<Map<String,Object>> front = new ArrayList<>();
        for (PermutationSolution<Integer> value : run.result()) front.add(ProbeData.encoding(value));
        NeutralProbeSupport.append(out.resolve("receipt.jsonl"), NeutralProbeSupport.row("status", complete ? "COMPLETE" : "INCOMPLETE_RETAINED",
            "error", failure == null ? null : failure.toString(), "expectedFE", limit, "successfulFE", run.budget().successful(),
            "attemptedFE", run.budget().attempted(), "failedFE", run.budget().failed(), "stopReason", run.stopReason(),
            "paidSHA256", checks.paidDigest.finish(), "paidFullTimelineQA", checks.paidQA, "neutralFullTimelineQA", checks.neutralQA,
            "completeRawDuplicates", checks.rawDuplicates, "accepted", evidence.accepted, "fallbacks", evidence.fallbacks,
            "unchangedStoredStates", evidence.unchanged, "fees", evidence.fees, "diagnostics", pop.diagnostics(),
            "stage", pop.stage, "generation", pop.generation, "completedGenerations", pop.completedGenerations,
            "completedPrograms", pop.completedPrograms, "slot", pop.slot, "step", pop.step, "subset", pop.subset, "phase", pop.phase,
            "donorSlot", pop.donorSlot, "reference", pop.reference, "lastPopulation", QpaStateRecords.population(pop.population()),
            "frozenParents", QpaStateRecords.population(pop.parentPopulation()), "partialOffspring", QpaStateRecords.population(pop.offspring()),
            "working", QpaStateRecords.state(pop.working(), false), "internalArchive", pop.archive(), "lastValidFront", front,
            "paidQASeconds", checks.paidQANanos / 1e9, "searchSecondsIncludingEngineeringQA", run.clock().elapsedSeconds(),
            "decoder", decoder.diagnostics(), "defaultMainlineChanged", false, "goalAchieved", false));
    }
}
