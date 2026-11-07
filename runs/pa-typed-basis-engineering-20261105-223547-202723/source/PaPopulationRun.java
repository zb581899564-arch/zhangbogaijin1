package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.modelglobal.*;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.util.research.search.Direction;

/** Standalone free-source engineering run; no QGS/sharing/local search or mainline substitution. */
public final class PaPopulationRun {
    private PaPopulationRun() { }
    public static void main(String[] args) throws Exception {
        Path input = Paths.get(args[0]), out = Paths.get(args[4]); Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir", input.getParent().toString()); System.setProperty("dhfsp.setupFile", args[1]);
        System.setProperty("dhfsp.standbyPower", "1"); String[] parts = input.getFileName().toString().replace(".txt", "").split("_");
        EDHHFSPW raw = new EDHHFSPW(Integer.parseInt(parts[0]), Integer.parseInt(parts[1]), Integer.parseInt(parts[2]), Integer.parseInt(parts[3]));
        Instance instance = raw.getSchedulingInstance(); DynamicParameters params = DynamicInputs.fatigue(instance, Paths.get(args[2]));
        DynamicEvaluation decoder = new DynamicEvaluation(raw, instance, params, true);
        long limit = Long.parseLong(args[6]); RunContext<PermutationSolution<Integer>> run = new RunContext<>(decoder, limit, Long.parseLong(args[5]));
        decoder.setCheckpoint(run::checkpoint); PaRunChecks checks = new PaRunChecks(instance, params);
        PaEvidence evidence = new PaEvidence(out, checks); PaPaidEvaluation evaluation = new PaPaidEvaluation(run, instance, checks);
        PaPopulation population = new PaPopulation(evaluation, evidence); boolean complete = false;
        try {
            NeutralProbeSupport.append(out.resolve("loaded-identity.jsonl"), ClassResolutionProbe.capture("research.dynamic.PaPopulationRun",
                "org.uma.jmetal.util.research.modelglobal.PaPopulation", "org.uma.jmetal.util.research.modelglobal.PaPaidEvaluation",
                "org.uma.jmetal.util.research.modelglobal.PaIndividual", "org.uma.jmetal.util.research.modelglobal.FactoryKeyReencoder",
                "org.uma.jmetal.util.research.modelglobal.PaMixingMove", "org.uma.jmetal.util.research.modelglobal.PaInternalArchive",
                "org.uma.jmetal.util.research.modelglobal.PaDependencyModel", "org.uma.jmetal.util.research.modelglobal.LinkageHierarchy",
                "org.uma.jmetal.util.research.DynamicEvaluation", "org.uma.jmetal.util.research.model.DynamicDecoder",
                "org.uma.jmetal.util.research.model.DynamicValidator", "org.uma.jmetal.util.research.runtime.BudgetedProblem",
                "org.uma.jmetal.util.research.runtime.SolutionSnapshots"));
            List<int[]> tuples = new ArrayList<>();
            for (int i = 0; i < evaluation.catalog().size(); i++) tuples.add(evaluation.catalog().tuple(i));
            NeutralProbeSupport.append(out.resolve("catalog.jsonl"), NeutralProbeSupport.row("tuples", tuples,
                "jobs", instance.jobs(), "factories", instance.factories(), "seed", run.seed(), "feLimit", limit));
            List<String> sources = Files.readAllLines(Paths.get(args[3]), StandardCharsets.UTF_8);
            if (sources.size() != 100) throw new AssertionError("Expected100fixed engineering sources");
            run.run(new Algorithm<Object>() {
                private static final long serialVersionUID = 1L;
                public void run() {
                    for (String line : sources) {
                        String[] f = line.split("\t"); String[] text = f[3].split(","); double[] expected = new double[3];
                        for (int k = 0; k < 3; k++) expected[k] = Double.parseDouble(text[k]);
                        FourVectors vectors = new FourVectors(ProbeData.integers(f[4]), ProbeData.integers(f[5]), ProbeData.integers(f[6]), ProbeData.integers(f[7]));
                        population.addInitial(evaluation.initial(vectors, Direction.valueOf(f[1]), expected));
                    }
                    population.evolve();
                }
                public Object getResult() { return null; }
                public String getName() { return "PA_MO_FIXED_POP_ADAPTED_ENGINEERING"; }
                public String getDescription() { return getName(); }
            });
            if (run.budget().successful() != limit || run.budget().failed() != 0 || checks.paidQA != limit || !run.stopReason().equals("FE_LIMIT"))
                throw new AssertionError("Incomplete actual fee/QA accounting");
            complete = true;
        } finally {
            population.finishTypedTrace(); evidence.close(); List<Map<String,Object>> front = new ArrayList<>();
            for (PermutationSolution<Integer> point : run.result()) front.add(ProbeData.encoding(point));
            NeutralProbeSupport.append(out.resolve("receipt.jsonl"), NeutralProbeSupport.row("status", complete ? "COMPLETE" : "INCOMPLETE_RETAINED",
                "expectedFE", limit, "successfulFE", run.budget().successful(), "attemptedFE", run.budget().attempted(), "failedFE", run.budget().failed(),
                "paidFullTimelineQA", checks.paidQA, "reencodingFullTimelineQA", checks.neutralQA,
                "fullDecoderQA", checks.paidQA + checks.neutralQA, "stopReason", run.stopReason(),
                "paidSHA256", checks.paidDigest.finish(), "completeRawDuplicates", checks.rawDuplicates,
                "accepted", evidence.accepted, "fallbacks", evidence.fallbacks, "unchangedStoredStates", evidence.unchanged,
                "currentGenerationDonorReads", evidence.currentGenerationDonorReads,
                "changedCurrentGenerationDonorReads", evidence.changedCurrentGenerationDonorReads, "fees", evidence.fees,
                "generation", population.generation, "completedGenerations", population.completedGenerations, "completedPrograms", population.completedPrograms,
                "phase", population.phase, "slot", population.slot, "step", population.step,
                "lastPopulation", PaStateRecords.population(population.population()), "internalArchive", population.archive(),
                "lastValidFront", front, "paidQASeconds", checks.paidQANanos / 1e9, "neutralQASeconds", checks.neutralQANanos / 1e9,
                "decoder", decoder.diagnostics(), "jobs", instance.jobs(), "defaultMainlineChanged", false, "goalAchieved", false));
            decoder.clearPrepared();
        }
    }
}
