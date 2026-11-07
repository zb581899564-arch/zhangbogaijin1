package research.dynamic;

import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.*;

/** An isolated evaluation delegate. Every call must be wrapped by RunContext. No cache reuse. */
final class ExplicitProblem implements Problem<PermutationSolution<Integer>> {
    private static final long serialVersionUID = 1L;
    static final String PLAN = "research.explicit.plan.v1", SCHEDULE = "research.explicit.schedule.v1";
    final Instance instance;
    final DynamicParameters parameters;
    private final Problem<PermutationSolution<Integer>> original;
    private Runnable checkpoint;
    long decoderCalls;

    ExplicitProblem(Problem<PermutationSolution<Integer>> source, Instance in, DynamicParameters params) {
        original = source; instance = in; parameters = params;
    }

    void setCheckpoint(Runnable value) { checkpoint = value; }

    public void evaluate(PermutationSolution<Integer> point) {
        point.getAttributes().remove(DynamicEvaluation.KEY);
        point.getAttributes().remove(SCHEDULE);
        StageResourcePlan plan = (StageResourcePlan) point.getAttribute(PLAN);
        if (plan == null) throw new IllegalArgumentException("Explicit policy identity is required");
        int[] js = SchedulingEncoding.integers(point.getVariables());
        int[] fa = SchedulingEncoding.integers(point.getVariablesid());
        plan.validate(instance, js, fa);
        decoderCalls++;
        ExplicitSchedule schedule = ExplicitResourceDecoder.full(instance, parameters, js, fa,
                SchedulingEncoding.machineIntegers(point), SchedulingEncoding.integers(point.getVariablesworker()),
                plan, checkpoint);
        for (int objective = 0; objective < 3; objective++) point.setObjective(objective, schedule.objectives()[objective]);
        point.setAttribute(SCHEDULE, schedule);
        point.setAttribute("research.decoderPolicy", StageResourcePlan.POLICY);
    }

    public PermutationSolution<Integer> createSolution() { return original.createSolution(); }
    public int getNumberOfVariables() { return original.getNumberOfVariables(); }
    public int getNumberOfObjectives() { return 3; }
    public int getNumberOfConstraints() { return original.getNumberOfConstraints(); }
    public String getName() { return StageResourcePlan.POLICY; }
}
