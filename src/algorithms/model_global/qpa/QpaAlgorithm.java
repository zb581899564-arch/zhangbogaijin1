package org.uma.jmetal.util.research.modelglobal;

import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.util.research.search.Direction;
import org.uma.jmetal.util.research.search.PaInitialBridge;

/** Ordinary canonical direct-joint reconstruction, fixed100 and explicit no-FI; not source-equivalent qGOMEA. */
public final class QpaAlgorithm implements Algorithm<Object> {
    private static final long serialVersionUID = 1L;
    private final RunContext<PermutationSolution<Integer>> run;
    private final Instance instance;
    private final PaPaidEvaluation.Checks checks;
    private final QpaPopulation.Observer observer;
    private final int generations;
    private QpaPopulation population;
    private QpaPaidEvaluation evaluation;

    public QpaAlgorithm(RunContext<PermutationSolution<Integer>> context, Instance value, PaPaidEvaluation.Checks validation,
            QpaPopulation.Observer evidence, int limit) { run = context; instance = value; checks = validation; observer = evidence; generations = limit; }

    public void run() {
        evaluation = new QpaPaidEvaluation(run, instance, checks); population = new QpaPopulation(evaluation, observer);
        PaInitialBridge initial = new PaInitialBridge(instance);
        for (int i = 0; i < 100; i++) {
            Direction role = i < 15 ? Direction.MAKESPAN : i < 70 ? Direction.CENTER : i < 85 ? Direction.ENERGY : Direction.WORKER_COST;
            population.addInitial(evaluation.initial(i, role, initial));
        }
        population.evolve(generations);
    }
    public QpaPopulation population() { return population; }
    public FirstStageCatalog catalog() { return evaluation.catalog(); }
    public Object getResult() { return null; }
    public String getName() { return "QPA_CANONICAL_FIXED100_NOFI"; }
    public String getDescription() { return "Complete ordinary direct-joint adaptation; canonical average linkage, synchronous donors, non-worse boundaries, all attempts charged"; }
}
