package org.uma.jmetal.util.research.modelglobal;

import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.util.research.search.Direction;
import org.uma.jmetal.util.research.search.PaInitialBridge;

/** Common guarded evaluation for initial, changed, duplicate and fallback attempts; no hidden scoring. */
public final class QpaPaidEvaluation {
    private final RunContext<PermutationSolution<Integer>> run;
    private final Instance instance;
    private final FirstStageCatalog catalog;
    private final PaPaidEvaluation.Checks checks;
    private long stateId;

    public QpaPaidEvaluation(RunContext<PermutationSolution<Integer>> context, Instance value, PaPaidEvaluation.Checks observer) {
        run = context; instance = value; catalog = new FirstStageCatalog(value); checks = observer;
    }
    public FirstStageCatalog catalog() { return catalog; }
    public void checkpoint() { run.problem().checkpoint(); }

    public QpaIndividual initial(int index, Direction role, PaInitialBridge initializer) {
        PermutationSolution<Integer> point = run.problem().createSolution(); initializer.prepare(point, index);
        FourVectors vectors = new FourVectors(SchedulingEncoding.integers(point.getVariables()),
                SchedulingEncoding.integers(point.getVariablesid()), SchedulingEncoding.machineIntegers(point),
                SchedulingEncoding.integers(point.getVariablesworker()));
        DirectScheduleGenome genome = DirectScheduleGenome.fromVectors(catalog, vectors); evaluate(point);
        return new QpaIndividual(++stateId, run.budget().successful(), role, genome, point);
    }

    @SuppressWarnings("unchecked")
    public QpaIndividual candidate(DirectScheduleGenome genome, QpaIndividual parent) {
        PermutationSolution<Integer> child = (PermutationSolution<Integer>)parent.point.copy();
        write(child, genome.toVectors()); evaluate(child);
        return new QpaIndividual(++stateId, run.budget().successful(), parent.role, genome, child);
    }

    private void evaluate(PermutationSolution<Integer> point) {
        if (SchedulingEncoding.repair(point, instance) != 0) throw new AssertionError("Direct candidate required repair");
        run.problem().evaluate(point); checks.paid(point, run.budget().successful());
    }

    @SuppressWarnings("unchecked")
    private static void write(PermutationSolution<Integer> point, FourVectors vectors) {
        int[] js = vectors.jobs(), fa = vectors.factories(), ma = vectors.machines(), wa = vectors.workers();
        List<Integer> machines = (List<Integer>)point.getAttribute("machine");
        for (int p = 0; p < js.length; p++) {
            point.setVariableValue(p, js[p]); point.setVariableValueid(p, fa[p]);
            machines.set(p, ma[p]); point.setVariableValueworker(p, wa[p]);
        }
    }
}
