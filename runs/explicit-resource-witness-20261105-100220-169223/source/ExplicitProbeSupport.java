package research.dynamic;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Input import and exact timeline checks shared by the isolated engineering and witness entries. */
final class ExplicitProbeSupport {
    private ExplicitProbeSupport() { }

    static World load(String[] args) {
        Path input = Paths.get(args[0]);
        System.setProperty("dhfsp.dataDir", input.getParent().toString());
        System.setProperty("dhfsp.setupFile", args[1]); System.setProperty("dhfsp.standbyPower", "1.0");
        String[] dimensions = input.getFileName().toString().replace(".txt", "").split("_");
        EDHHFSPW raw = new EDHHFSPW(Integer.parseInt(dimensions[0]), Integer.parseInt(dimensions[1]),
                Integer.parseInt(dimensions[2]), Integer.parseInt(dimensions[3]));
        Instance instance = raw.getSchedulingInstance();
        if (!instance.satisfiesDualResourceCondition()) throw new IllegalArgumentException("Strict instance required");
        SeededRandom.reset(12920003L);
        return new World(raw, instance, DynamicInputs.fatigue(instance, Paths.get(args[2])));
    }

    @SuppressWarnings("unchecked")
    static PermutationSolution<Integer> parent(Problem<PermutationSolution<Integer>> problem,
            Instance instance, String[] fields) {
        PermutationSolution<Integer> point = problem.createSolution();
        List<Integer> machines = (List<Integer>) point.getAttribute("machine");
        for (int vector = 0; vector < 4; vector++) {
            int[] values = Arrays.stream(fields[7 + vector].split(",")).mapToInt(Integer::parseInt).toArray();
            if (values.length != instance.jobs()) throw new AssertionError("Invalid source vector length");
            for (int pos = 0; pos < values.length; pos++) {
                if (vector == 0) point.setVariableValue(pos, values[pos]);
                else if (vector == 1) point.setVariableValueid(pos, values[pos]);
                else if (vector == 2) machines.set(pos, values[pos]);
                else point.setVariableValueworker(pos, values[pos]);
            }
        }
        if (SchedulingEncoding.repair(point, instance) != 0) throw new AssertionError("Source needs repair");
        point.setAttribute(ExplicitProblem.PLAN, StageResourcePlan.empty(instance.jobs(), instance.stages()));
        return point;
    }

    static ExplicitSchedule decode(World world, PermutationSolution<Integer> point, StageResourcePlan plan) {
        ExplicitSchedule schedule = ExplicitResourceDecoder.full(world.instance, world.parameters,
                SchedulingEncoding.integers(point.getVariables()), SchedulingEncoding.integers(point.getVariablesid()),
                SchedulingEncoding.machineIntegers(point), SchedulingEncoding.integers(point.getVariablesworker()), plan, null);
        ExplicitResourceValidator.validate(world.instance, world.parameters, schedule);
        return schedule;
    }

    static void same(List<DynamicStep> first, List<DynamicStep> second, boolean firstStageOnly) {
        List<DynamicStep> a = filter(first, firstStageOnly), b = filter(second, firstStageOnly);
        if (a.size() != b.size()) throw new AssertionError("Timeline dimensions differ");
        for (int index = 0; index < a.size(); index++) {
            DynamicStep x = a.get(index), y = b.get(index);
            if (x.job() != y.job() || x.factory() != y.factory() || x.stage() != y.stage()
                    || x.machine() != y.machine() || x.worker() != y.worker()
                    || !Arrays.equals(values(x), values(y))) throw new AssertionError("Timeline not bit-exact");
        }
    }

    static DynamicStep operation(List<DynamicStep> steps, int job, int stage) {
        for (DynamicStep operation : steps) if (operation.job() == job && operation.stage() == stage) return operation;
        throw new AssertionError("Missing job/stage");
    }

    static double[] expected(String[] fields) {
        return Arrays.stream(fields[6].split(",")).mapToDouble(Double::parseDouble).toArray();
    }

    static Map<String,Object> encoding(PermutationSolution<Integer> point) {
        StageResourcePlan plan = (StageResourcePlan) point.getAttribute(ExplicitProblem.PLAN);
        return NeutralProbeSupport.row("JS", point.getVariables(), "FA", point.getVariablesid(),
                "MA", point.getAttribute("machine"), "WA", point.getVariablesworker(),
                "objectives", point.getObjectives().clone(), "policy", StageResourcePlan.POLICY,
                "plan", plan.entries(), "planIdentity", plan.identity());
    }

    static List<Map<String,Object>> timeline(ExplicitSchedule schedule) {
        List<Map<String,Object>> out = new ArrayList<>();
        for (DynamicStep step : schedule.steps()) out.add(NeutralProbeSupport.row(
                "job", step.job(), "factory", step.factory(), "stage", step.stage(),
                "machine", step.machine(), "worker", step.worker(), "values", values(step)));
        return out;
    }

    private static List<DynamicStep> filter(List<DynamicStep> steps, boolean firstOnly) {
        if (!firstOnly) return steps;
        List<DynamicStep> out = new ArrayList<>();
        for (DynamicStep step : steps) if (step.stage() == 0) out.add(step);
        return out;
    }

    private static double[] values(DynamicStep step) {
        return new double[] {step.start(), step.base(), step.duration(), step.setupDuration(), step.completion(),
                step.u(), step.v(), step.energy(), step.labor(), step.exposure()};
    }

    static final class World {
        final EDHHFSPW raw;
        final Instance instance;
        final DynamicParameters parameters;
        World(EDHHFSPW source, Instance in, DynamicParameters params) { raw = source; instance = in; parameters = params; }
        ExplicitProblem problem() { return new ExplicitProblem(raw, instance, parameters); }
    }
}
