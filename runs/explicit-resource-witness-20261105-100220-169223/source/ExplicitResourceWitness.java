package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.util.research.search.ParetoTools;

/** Fully paid one-operation resource coverage, not an optimizer or a free choice oracle. */
public final class ExplicitResourceWitness {
    private final ExplicitProbeSupport.World world;
    private final Path output;
    private final ExplicitProblem problem;
    private final RunContext<PermutationSolution<Integer>> context;
    private long originalFullQA, independentValidations, policyRejections;

    private ExplicitResourceWitness(ExplicitProbeSupport.World value, Path out, long budget) {
        world = value; output = out; problem = world.problem();
        context = new RunContext<>(problem, budget, 12920003L); problem.setCheckpoint(context::checkpoint);
    }

    public static void main(String[] args) throws Exception {
        ExplicitProbeSupport.World world = ExplicitProbeSupport.load(args);
        List<String> cases = Files.readAllLines(Paths.get(args[3]), StandardCharsets.UTF_8);
        Path output = Paths.get(args[4]); Files.createDirectories(output);
        long expected = 0;
        for (String line : cases) {
            String[] fields = line.split("\t");
            int position = Integer.parseInt(fields[4]), stage = Integer.parseInt(fields[5]);
            int factory = Integer.parseInt(fields[8].split(",")[position]);
            expected += 1 + world.instance.machines(factory, 0) * world.instance.workers(factory, 0) - 1
                    + world.instance.machines(factory, stage) * world.instance.workers(factory, stage) - 1;
        }
        if (expected > 10000) throw new IllegalStateException("Predeclared per-instance FE cap exceeded");
        NeutralProbeSupport.append(output.resolve("before-decode.jsonl"), NeutralProbeSupport.row(
                "cases", cases.size(), "plannedFE", expected, "plannedFromResourceCountsOnly", true));
        ExplicitResourceWitness probe = new ExplicitResourceWitness(world, output, expected);
        boolean completed = false;
        try {
            probe.context.run(new Algorithm<Object>() {
                private static final long serialVersionUID = 1L;
                public void run() { for (String line : cases) probe.candidates(line.split("\t")); }
                public Object getResult() { return null; }
                public String getName() { return "EXPLICIT_RESOURCE_COVERAGE"; }
                public String getDescription() { return getName(); }
            });
            if (probe.context.budget().successful() != expected || probe.context.budget().failed() != 0)
                throw new AssertionError("Incomplete witness FE");
            completed = true;
        } finally {
            List<Map<String,Object>> last = new ArrayList<>();
            for (PermutationSolution<Integer> point : probe.context.result()) last.add(ExplicitProbeSupport.encoding(point));
            NeutralProbeSupport.append(output.resolve("receipt.jsonl"), NeutralProbeSupport.row(
                    "status", completed ? "COMPLETE" : "INCOMPLETE_RETAINED", "plannedFE", expected,
                    "successfulFE", probe.context.budget().successful(), "attemptedFE", probe.context.budget().attempted(),
                    "failedFE", probe.context.budget().failed(), "chargedFullDecodes", probe.problem.decoderCalls,
                    "offlineOriginalFullQA", probe.originalFullQA,
                    "independentTimelineValidations", probe.independentValidations,
                    "expectedOriginalPolicyRejections", probe.policyRejections,
                    "lastValidFront", last));
        }
    }

    private void candidates(String[] fields) {
        PermutationSolution<Integer> parent = ExplicitProbeSupport.parent(context.problem(), world.instance, fields);
        context.problem().evaluate(parent); validate(parent);
        if (!Arrays.equals(parent.getObjectives(), ExplicitProbeSupport.expected(fields)))
            throw new AssertionError("Paid source objective mismatch");
        ExplicitSchedule baseline = schedule(parent);
        checkOriginal(parent, baseline);
        int position = Integer.parseInt(fields[4]), stage = Integer.parseInt(fields[5]);
        int job = parent.getVariableValue(position), factory = parent.getVariableValueid(position);
        DynamicStep selected = ExplicitProbeSupport.operation(baseline.steps(), job, stage);
        NeutralProbeSupport.append(output.resolve("parents.jsonl"), NeutralProbeSupport.row(
                "id", fields[0], "origin", fields[1], "sourceFE", Integer.parseInt(fields[2]),
                "position", position, "job", job, "factory", factory, "stage", stage,
                "originalLaterMachine", selected.machine(), "originalLaterWorker", selected.worker(),
                "paidFE", context.budget().successful(), "genome", ExplicitProbeSupport.encoding(parent)));
        for (String channel : new String[] {"FIRST", "LATER"}) {
            int targetStage = channel.equals("FIRST") ? 0 : stage;
            DynamicStep original = ExplicitProbeSupport.operation(baseline.steps(), job, targetStage);
            boolean saved = false;
            for (int machine = 0; machine < world.instance.machines(factory, targetStage); machine++) {
                for (int worker = 0; worker < world.instance.workers(factory, targetStage); worker++) {
                    if (machine == original.machine() && worker == original.worker()) continue;
                    long started = System.nanoTime();
                    PermutationSolution<Integer> child = proposal(parent, channel, position, job, stage, machine, worker);
                    long generationNanos = System.nanoTime() - started;
                    started = System.nanoTime(); context.problem().evaluate(child);
                    long evaluationNanos = System.nanoTime() - started;
                    validate(child);
                    ExplicitSchedule result = schedule(child);
                    if (channel.equals("FIRST")) checkOriginal(child, result);
                    else {
                        ExplicitProbeSupport.same(baseline.steps(), result.steps(), true);
                        requireSameVectors(parent, child);
                        ExplicitLegacyChecks.requireRejection(world.instance, world.parameters, result);
                        policyRejections++;
                    }
                    NeutralProbeSupport.append(output.resolve("outcomes.jsonl"), NeutralProbeSupport.row(
                            "id", fields[0], "channel", channel, "machine", machine, "worker", worker,
                            "paidFE", context.budget().successful(), "generationNanos", generationNanos,
                            "evaluationNanos", evaluationNanos, "genome", ExplicitProbeSupport.encoding(child)));
                    if (!saved) {
                        NeutralProbeSupport.append(output.resolve("first-candidate-timelines.jsonl"),
                                NeutralProbeSupport.row("id", fields[0], "channel", channel,
                                        "genome", ExplicitProbeSupport.encoding(child),
                                        "steps", ExplicitProbeSupport.timeline(result)));
                        saved = true;
                    }
                }
            }
        }
    }

    @SuppressWarnings("unchecked")
    private PermutationSolution<Integer> proposal(PermutationSolution<Integer> parent, String channel,
            int position, int job, int stage, int machine, int worker) {
        PermutationSolution<Integer> child = ParetoTools.copy(parent);
        if (channel.equals("FIRST")) {
            ((List<Integer>) child.getAttribute("machine")).set(position, machine);
            child.setVariableValueworker(position, worker);
        } else child.setAttribute(ExplicitProblem.PLAN,
                ((StageResourcePlan) parent.getAttribute(ExplicitProblem.PLAN)).with(job, stage, machine, worker));
        return child;
    }

    private void checkOriginal(PermutationSolution<Integer> point, ExplicitSchedule result) {
        originalFullQA++;
        DynamicSchedule original = NeutralProbeSupport.full(world.instance, world.parameters, point);
        ExplicitProbeSupport.same(original.steps(), result.steps(), false);
        if (!Arrays.equals(original.objectives(), result.objectives())) throw new AssertionError("Old policy objectives differ");
    }

    private void validate(PermutationSolution<Integer> point) {
        independentValidations++;
        ExplicitResourceValidator.validate(world.instance, world.parameters, schedule(point));
    }

    private static ExplicitSchedule schedule(PermutationSolution<Integer> point) {
        return (ExplicitSchedule) point.getAttribute(ExplicitProblem.SCHEDULE);
    }

    private static void requireSameVectors(PermutationSolution<Integer> first, PermutationSolution<Integer> second) {
        if (!first.getVariables().equals(second.getVariables()) || !first.getVariablesid().equals(second.getVariablesid())
                || !first.getAttribute("machine").equals(second.getAttribute("machine"))
                || !first.getVariablesworker().equals(second.getVariablesworker()))
            throw new AssertionError("Later-stage decision changed original four vectors");
    }
}
