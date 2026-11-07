package org.uma.jmetal.util.research.modelglobal;

import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import org.uma.jmetal.util.research.search.Direction;
import org.uma.jmetal.util.research.search.PaInitialBridge;

/** The only evaluation path; physical-neutral reencoding is explicitly observed outside search FE. */
public final class PaPaidEvaluation {
    public interface Checks {
        void paid(PermutationSolution<Integer> point, long successfulFE);
        void neutral(PermutationSolution<Integer> before, PermutationSolution<Integer> after);
    }
    private final RunContext<PermutationSolution<Integer>> context;
    private final Instance instance;
    private final FirstStageCatalog catalog;
    private final Checks checks;
    private long stateId;

    public PaPaidEvaluation(RunContext<PermutationSolution<Integer>> run, Instance value, Checks observer) {
        context = run; instance = value; catalog = new FirstStageCatalog(value); checks = observer;
    }

    public FirstStageCatalog catalog() { return catalog; }
    public void checkpoint() { context.problem().checkpoint(); }

    public PaIndividual initial(FourVectors genes, Direction role, double[] expected) {
        PermutationSolution<Integer> point = context.problem().createSolution(); write(point, genes);
        TypedScheduleGenome genome = TypedScheduleGenome.fromVectors(catalog, genes); evaluate(point);
        for (int k = 0; k < 3; k++) if (Double.doubleToLongBits(expected[k]) != Double.doubleToLongBits(point.getObjective(k)))
            throw new AssertionError("Captured initialization objective differs");
        return new PaIndividual(++stateId, context.budget().successful(), role, genome, point);
    }

    public PaIndividual randomInitial(int index, Direction role, PaInitialBridge initializer) {
        PermutationSolution<Integer> point = context.problem().createSolution(); initializer.prepare(point, index); NeutralInitialView.apply(instance, point, index);
        FourVectors vectors = new FourVectors(SchedulingEncoding.integers(point.getVariables()),
                SchedulingEncoding.integers(point.getVariablesid()), SchedulingEncoding.machineIntegers(point),
                SchedulingEncoding.integers(point.getVariablesworker()));
        TypedScheduleGenome genome = TypedScheduleGenome.fromVectors(catalog, vectors); evaluate(point);
        return new PaIndividual(++stateId, context.budget().successful(), role, genome, point);
    }

    public PaIndividual candidate(TypedScheduleGenome genome, PaIndividual receiver) {
        PermutationSolution<Integer> child = copy(receiver.point); write(child, genome.toVectors()); evaluate(child);
        return new PaIndividual(++stateId, context.budget().successful(), receiver.role, genome, child);
    }

    public PaIndividual reencode(PaIndividual before) {
        TypedScheduleGenome genome = FactoryKeyReencoder.apply(catalog, before.genome, SeededRandom.current());
        PermutationSolution<Integer> point = copy(before.point); write(point, genome.toVectors());
        checks.neutral(before.point, point);
        return new PaIndividual(++stateId, before.paidFE, before.role, genome, point);
    }

    private void evaluate(PermutationSolution<Integer> point) {
        if (SchedulingEncoding.repair(point, instance) != 0) throw new AssertionError("Joint representation unexpectedly needs repair");
        context.problem().evaluate(point); checks.paid(point, context.budget().successful()); NeutralInitialView.paid(point, context.budget().successful());
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

    @SuppressWarnings("unchecked")
    private static PermutationSolution<Integer> copy(PermutationSolution<Integer> value) {
        return (PermutationSolution<Integer>)value.copy();
    }
}
