package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.List;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.util.research.search.ParetoTools;

/** Engineering gate only: original-policy equality, decision identity, strict charging and failure retention. */
public final class ExplicitResourceEngineering {
    private ExplicitResourceEngineering() { }

    public static void main(String[] args) throws Exception {
        ExplicitProbeSupport.World world = ExplicitProbeSupport.load(args);
        Path output = Paths.get(args[4]); Files.createDirectories(output);
        List<String> cases = Files.readAllLines(Paths.get(args[3]), StandardCharsets.UTF_8);
        for (String line : cases) {
            String[] fields = line.split("\t");
            PermutationSolution<Integer> point = ExplicitProbeSupport.parent(world.raw, world.instance, fields);
            DynamicSchedule original = NeutralProbeSupport.full(world.instance, world.parameters, point);
            if (!Arrays.equals(original.objectives(), ExplicitProbeSupport.expected(fields)))
                throw new AssertionError("Source differs from original decoder");
            StageResourcePlan empty = (StageResourcePlan) point.getAttribute(ExplicitProblem.PLAN);
            ExplicitSchedule plain = ExplicitProbeSupport.decode(world, point, empty);
            ExplicitProbeSupport.same(original.steps(), plain.steps(), false);
            if (!Arrays.equals(original.objectives(), plain.objectives())) throw new AssertionError("Objectives differ");
            int job = point.getVariableValue(Integer.parseInt(fields[4])), stage = Integer.parseInt(fields[5]);
            DynamicStep existing = ExplicitProbeSupport.operation(original.steps(), job, stage);
            StageResourcePlan sameDecision = empty.with(job, stage, existing.machine(), existing.worker());
            ExplicitSchedule matched = ExplicitProbeSupport.decode(world, point, sameDecision);
            ExplicitProbeSupport.same(original.steps(), matched.steps(), false);
            if (empty.identity().equals(sameDecision.identity()) || !empty.entries().isEmpty())
                throw new AssertionError("Plan identity or immutability failed");
            NeutralProbeSupport.append(output.resolve("case-checks.jsonl"), NeutralProbeSupport.row(
                    "id", fields[0], "completedOfflineFullDecodes", 3, "bitExact", true));
        }
        long success = 0, failure = 0;
        for (int limit = 1; limit <= 3; limit++) {
            ExplicitProblem problem = world.problem();
            RunContext<PermutationSolution<Integer>> run = new RunContext<>(problem, limit, 12920003L);
            problem.setCheckpoint(run::checkpoint);
            final int fixture = limit;
            run.problem().setAudit((point, paid, elapsed, changed) -> NeutralProbeSupport.append(
                    output.resolve("fixture-paid.jsonl"), NeutralProbeSupport.row(
                            "fixture", fixture, "paidFE", paid, "genome", ExplicitProbeSupport.encoding(point))));
            boolean caught = false;
            try {
                run.run(new Algorithm<Object>() {
                    private static final long serialVersionUID = 1L;
                    public void run() {
                        PermutationSolution<Integer> parent = ExplicitProbeSupport.parent(run.problem(), world.instance,
                                cases.get(0).split("\t"));
                        run.problem().evaluate(parent);
                        ExplicitResourceValidator.validate(world.instance, world.parameters,
                                (ExplicitSchedule) parent.getAttribute(ExplicitProblem.SCHEDULE));
                        if (limitValue() == 1) return;
                        PermutationSolution<Integer> next = ParetoTools.copy(parent);
                        ExplicitSchedule previous = (ExplicitSchedule) parent.getAttribute(ExplicitProblem.SCHEDULE);
                        DynamicStep selected = alternative(world.instance, previous);
                        int machine = selected.machine(), worker = selected.worker();
                        if (world.instance.machines(selected.factory(), selected.stage()) > 1)
                            machine = (machine + 1) % world.instance.machines(selected.factory(), selected.stage());
                        else worker = (worker + 1) % world.instance.workers(selected.factory(), selected.stage());
                        StageResourcePlan plan = previous.plan().with(selected.job(), selected.stage(), machine, worker);
                        next.setAttribute(ExplicitProblem.PLAN, plan); run.problem().evaluate(next);
                        ExplicitSchedule changed = (ExplicitSchedule) next.getAttribute(ExplicitProblem.SCHEDULE);
                        ExplicitResourceValidator.validate(world.instance, world.parameters, changed);
                        ExplicitProbeSupport.same(previous.steps(), changed.steps(), true);
                        ExplicitLegacyChecks.requireRejection(world.instance, world.parameters, changed);
                        if (limitValue() == 2) return;
                        PermutationSolution<Integer> invalid = ParetoTools.copy(parent);
                        invalid.setAttribute(ExplicitProblem.PLAN, previous.plan().with(selected.job(), selected.stage(),
                                world.instance.machines(selected.factory(), selected.stage()), 0));
                        run.problem().evaluate(invalid);
                    }
                    private int limitValue() { return (int) run.budget().limit(); }
                    public Object getResult() { return null; }
                    public String getName() { return "EXPLICIT_ENGINEERING_FIXTURE"; }
                    public String getDescription() { return getName(); }
                });
            } catch (IllegalArgumentException expected) {
                if (limit != 3 || !expected.getMessage().contains("Explicit resource outside")) throw expected;
                caught = true;
            }
            long expectedSuccess = Math.min(limit, 2);
            if (run.budget().attempted() != limit || run.budget().successful() != expectedSuccess
                    || run.budget().failed() != (limit == 3 ? 1 : 0) || caught != (limit == 3)
                    || problem.decoderCalls != expectedSuccess || run.result().isEmpty())
                throw new AssertionError("Last FE, failure charging or last valid archive failed");
            success += run.budget().successful(); failure += run.budget().failed();
            List<java.util.Map<String,Object>> valid = new java.util.ArrayList<>();
            for (PermutationSolution<Integer> point : run.result()) valid.add(ExplicitProbeSupport.encoding(point));
            NeutralProbeSupport.append(output.resolve("fixture-results.jsonl"), NeutralProbeSupport.row(
                    "fixture", limit, "attemptedFE", run.budget().attempted(),
                    "successfulFE", run.budget().successful(), "failedFE", run.budget().failed(),
                    "expectedGuardFailure", caught, "decoderCalls", problem.decoderCalls,
                    "stopReason", run.stopReason(), "lastValidFront", valid));
        }
        NeutralProbeSupport.append(output.resolve("receipt.jsonl"), NeutralProbeSupport.row(
                "status", "PASS", "sourceCases", cases.size(), "offlineFullDecodes", 3L * cases.size(),
                "engineeringSuccessfulFE", success, "expectedFailedFE", failure,
                "engineeringChargedDecoderCalls", success, "fixtureIndependentValidations", success,
                "originalPolicyAndExplicitMatchingBindingBitExact", true,
                "firstStageUnchanged", true, "legacyChangedBindingRejected", true,
                "noCacheReuse", true, "productionModified", false));
    }

    private static DynamicStep alternative(Instance instance, ExplicitSchedule schedule) {
        for (DynamicStep step : schedule.steps()) if (step.stage() > 0
                && instance.machines(step.factory(), step.stage()) * instance.workers(step.factory(), step.stage()) > 1)
            return step;
        throw new AssertionError("No later-stage alternative in engineering fixture");
    }
}
