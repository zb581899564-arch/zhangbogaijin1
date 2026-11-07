package research.dynamic;

import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.modelglobal.*;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.util.research.search.*;

/** Observation of the already-frozen strict/equal PA programs, with fresh common initialization. */
public final class PaNeutralTraceRun {
    private PaNeutralTraceRun() { }
    public static void main(String[] args) throws Exception {
        Path input = Paths.get(args[0]), out = Paths.get(args[3]); Files.createDirectories(out);
        boolean equal = args[4].equals("PA_EQUAL");
        if (!equal && !args[4].equals("PA_JOINT")) throw new IllegalArgumentException("Strict or equal PA required");
        System.setProperty("research.pa.boundaryNonWorse", Boolean.toString(equal));
        System.setProperty("dhfsp.dataDir", input.getParent().toString()); System.setProperty("dhfsp.setupFile", args[1]);
        System.setProperty("dhfsp.standbyPower", "1");
        String[] d = input.getFileName().toString().replace(".txt", "").split("_");
        EDHHFSPW raw = new EDHHFSPW(Integer.parseInt(d[0]), Integer.parseInt(d[1]), Integer.parseInt(d[2]), Integer.parseInt(d[3]));
        Instance instance = raw.getSchedulingInstance();
        if (!instance.satisfiesDualResourceCondition()) throw new IllegalArgumentException("Unqualified instance");
        DynamicParameters fatigue = DynamicInputs.fatigue(instance, Paths.get(args[2]));
        DynamicEvaluation decoder = new DynamicEvaluation(raw, instance, fatigue, true);
        long limit = Long.parseLong(args[5]); RunContext<PermutationSolution<Integer>> run = new RunContext<>(decoder, limit, Long.parseLong(args[6]));
        decoder.setCheckpoint(run::checkpoint); PaRunChecks checks = new PaRunChecks(instance, fatigue);
        PaEvidence evidence = new PaEvidence(out, checks); PaPaidEvaluation evaluation = new PaPaidEvaluation(run, instance, checks);
        PaPopulation population = new PaPopulation(evaluation, evidence); Throwable failure = null;
        try {
            run.run(new Algorithm<Object>() {
                private static final long serialVersionUID = 1L;
                public void run() {
                    PaInitialBridge initializer = new PaInitialBridge(instance);
                    for (int i = 0; i < 100; i++) {
                        Direction role = i < 15 ? Direction.MAKESPAN : i < 70 ? Direction.CENTER : i < 85 ? Direction.ENERGY : Direction.WORKER_COST;
                        population.addInitial(evaluation.randomInitial(i, role, initializer));
                    }
                    population.evolve();
                }
                public Object getResult() { return null; }
                public String getName() { return "FROZEN_PA_NEUTRAL_TRACE"; }
                public String getDescription() { return "Read-only strict/equal trace; no new algorithm"; }
            });
            if (!run.stopReason().equals("FE_LIMIT") || run.budget().successful() != limit || run.budget().failed() != 0
                    || checks.paidQA != limit || population.completedGenerations != 2) throw new AssertionError("Trace accounting/generations differ");
        } catch (RuntimeException | Error error) { failure = error; }
        finally {
            evidence.close(); save(out, run, population, evaluation.catalog(), checks, evidence, decoder, equal, failure);
            decoder.clearPrepared();
        }
        if (failure != null) throw new IllegalStateException("Trace failure retained", failure);
        NeutralProbeSupport.append(out.resolve("loaded-identity.jsonl"), ClassResolutionProbe.capture(
            "research.dynamic.PaNeutralTraceRun", "research.dynamic.PaEvidence", "research.dynamic.PaRunChecks",
            "org.uma.jmetal.util.research.modelglobal.PaPopulation", "org.uma.jmetal.util.research.modelglobal.PaPaidEvaluation",
            "org.uma.jmetal.util.research.modelglobal.PaIndividual", "org.uma.jmetal.util.research.modelglobal.PaDependencyModel",
            "org.uma.jmetal.util.research.modelglobal.PaMixingMove", "org.uma.jmetal.util.research.modelglobal.FactoryKeyReencoder",
            "org.uma.jmetal.util.research.modelglobal.LinkageHierarchy", "org.uma.jmetal.util.research.search.PaInitialBridge",
            "org.uma.jmetal.util.research.DynamicEvaluation", "org.uma.jmetal.util.research.model.DynamicDecoder"));
    }
    private static void save(Path out, RunContext<PermutationSolution<Integer>> run, PaPopulation population, FirstStageCatalog catalog,
            PaRunChecks checks, PaEvidence evidence, DynamicEvaluation decoder, boolean equal, Throwable failure) throws Exception {
        List<int[]> tuples = new ArrayList<>(); for (int i = 0; i < catalog.size(); i++) tuples.add(catalog.tuple(i));
        NeutralProbeSupport.append(out.resolve("catalog.jsonl"), NeutralProbeSupport.row("tuples", tuples, "jobs", catalog.jobs(),
            "factories", catalog.factories(), "seed", run.seed()));
        List<Map<String,Object>> front = new ArrayList<>();
        for (PermutationSolution<Integer> value : run.result()) front.add(ProbeData.encoding(value));
        NeutralProbeSupport.append(out.resolve("receipt.jsonl"), NeutralProbeSupport.row("status", failure == null ? "COMPLETE" : "INCOMPLETE_RETAINED",
            "error", failure == null ? null : failure.toString(), "boundaryEqual", equal, "successfulFE", run.budget().successful(),
            "attemptedFE", run.budget().attempted(), "failedFE", run.budget().failed(), "stopReason", run.stopReason(),
            "paidSHA256", checks.paidDigest.finish(), "paidFullTimelineQA", checks.paidQA, "neutralFullTimelineQA", checks.neutralQA,
            "completeRawDuplicates", checks.rawDuplicates, "fees", evidence.fees, "completedGenerations", population.completedGenerations,
            "completedPrograms", population.completedPrograms, "lastPopulation", PaStateRecords.population(population.population()),
            "internalArchive", population.archive(), "lastValidFront", front, "decoder", decoder.diagnostics(),
            "defaultMainlineChanged", false, "goalAchieved", false));
    }
}
