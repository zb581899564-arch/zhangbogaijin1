package research.dynamic;

import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.*;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;
import org.uma.jmetal.util.research.search.*;

/** One independently charged domain-production JVM; q0 and source/protocol control remain external. */
public final class DomainProductionRun {
    private DomainProductionRun() { }

    public static void main(String[] args) throws Exception {
        if (args.length < 7 || args.length > 8)
            throw new IllegalArgumentException("INPUT SETUP FATIGUE OUT CONTEXT ARM SOURCE_SEED [requestIndex]");
        Path input = Paths.get(args[0]), output = Paths.get(args[3]); Files.createDirectories(output);
        String arm = args[5]; long sourceSeed = Long.parseLong(args[6]);
        int requestIndex = args.length == 8 ? Integer.parseInt(args[7]) : 0;
        if (requestIndex != 0) throw new IllegalArgumentException("This frozen domain probe uses requestIndex 0 only");
        long seed = sourceSeed ^ 0x37a9185bL;
        int productionFE = Integer.getInteger("research.domain.productionFE", 4095);
        if (productionFE < 1 || productionFE == Integer.MAX_VALUE) throw new IllegalArgumentException("Invalid production FE");
        long totalFE = productionFE + 1L, limit = Long.getLong("research.domain.limit", totalFE);
        if (limit < 1 || limit > totalFE) throw new IllegalArgumentException("Domain probe limit must be 1..productionFE+1");
        System.setProperty("research.ctxGom.enabled", "true");
        System.setProperty("dhfsp.dataDir", input.getParent().toString());
        System.setProperty("dhfsp.setupFile", args[1]); System.setProperty("dhfsp.standbyPower", "1");
        String[] name = input.getFileName().toString().replace(".txt", "").split("_");
        EDHHFSPW raw = new EDHHFSPW(Integer.parseInt(name[0]), Integer.parseInt(name[1]), Integer.parseInt(name[2]), Integer.parseInt(name[3]));
        Instance in = raw.getSchedulingInstance();
        if (!in.satisfiesDualResourceCondition()) throw new IllegalArgumentException("Unqualified instance");
        DynamicParameters params = DynamicInputs.fatigue(in, Paths.get(args[2]));
        DynamicEvaluation decoder = new DynamicEvaluation(raw, in, params, true);
        RunContext<PermutationSolution<Integer>> run = new RunContext<>(PilotPhysics.delegate(decoder), limit, seed);
        decoder.setCheckpoint(run::checkpoint);
        long prepareStart = System.nanoTime();
        DomainProductionReplay probe = new DomainProductionReplay(run, in, params, Paths.get(args[4]), output, arm, seed, productionFE);
        double prepareSeconds = (System.nanoTime() - prepareStart) / 1e9;
        GomPrefixDigest digest = new GomPrefixDigest(); PilotPhysics physics = new PilotPhysics(in, params);
        run.problem().setObserver(new EvaluationObserver() {
            public void completed(long fe, double seconds, boolean changed, ThreeObjectiveArchive<?> archive) {
                throw new AssertionError("Full paid candidate notification required");
            }
            @SuppressWarnings("unchecked") public void completedSolution(Solution<?> value, long fe,
                    double seconds, boolean changed, ThreeObjectiveArchive<?> archive) {
                PermutationSolution<Integer> point = (PermutationSolution<Integer>) value;
                probe.observed(point, fe); digest.update(point, fe); physics.check(point);
            }
        });
        Throwable failure = null;
        try { run.run(probe); } catch (RuntimeException | Error error) { failure = error; }
        finally { decoder.clearPrepared(); }
        try { probe.finish(); }
        catch (RuntimeException | Error error) { if (failure == null) failure = error; else failure.addSuppressed(error); }
        Map<String,Object> receipt = probe.receipt();
        receipt.putAll(GomRecords.row("sourceSeed", sourceSeed, "requestIndex", requestIndex, "seed", seed,
            "attempted", run.budget().attempted(), "successful", run.budget().successful(), "failed", run.budget().failed(),
            "feLimit", limit, "stopReason", run.stopReason(), "searchSeconds", run.clock().elapsedSeconds(),
            "prepareSeconds", prepareSeconds, "paidSHA256", digest.snapshot(), "prefixSHA256", digest.prefixes,
            "physicsQA", physics.receipt(), "searchClockIncludesPaidEngineeringQA", Boolean.getBoolean("research.pilot.physics"),
            "decoder", decoder.diagnostics(), "error", failure == null ? null : failure.toString(),
            "loaded", ClassResolutionProbe.capture("research.dynamic.DomainProductionRun",
                "org.uma.jmetal.util.research.search.DomainProductionReplay", "org.uma.jmetal.util.research.search.DomainJointMove",
                "org.uma.jmetal.util.research.search.RequestInputs", "org.uma.jmetal.util.research.search.RequestAcceptance",
                "org.uma.jmetal.util.research.cooperation.RequestPoolAccess", "org.uma.jmetal.util.research.cooperation.FactoryPool",
                "org.uma.jmetal.util.research.cooperation.FactoryRecord", "org.uma.jmetal.util.research.search.GomRunScope",
                "org.uma.jmetal.util.research.search.GomWorkspace", "org.uma.jmetal.util.research.search.GomDomainModels",
                "org.uma.jmetal.util.research.modelglobal.FirstStageCatalog", "org.uma.jmetal.util.research.modelglobal.TypedScheduleGenome",
                "org.uma.jmetal.util.research.modelglobal.PaMixingMove", "org.uma.jmetal.util.research.DynamicEvaluation",
                "org.uma.jmetal.util.research.runtime.BudgetedProblem")));
        DomainProductionReplay.write(output.resolve("receipt.json"), receipt);
        if (failure != null) throw new IllegalStateException("Preserved domain-production failure", failure);
        System.out.println("DOMAIN_PRODUCTION_DONE " + arm + " " + run.budget().successful());
    }
}
