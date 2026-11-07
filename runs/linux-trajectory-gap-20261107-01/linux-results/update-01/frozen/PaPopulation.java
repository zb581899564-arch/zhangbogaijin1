package org.uma.jmetal.util.research.modelglobal;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import org.uma.jmetal.util.research.search.Direction;

/** Complete in-place population lifecycle; RunContext terminates search, including partial generations. */
public final class PaPopulation {
    public interface Observer {
        void initial(int slot, PaIndividual individual, PaInternalArchive.Flags flags);
        void reencoded(int generation, int slot, PaIndividual before, PaIndividual after);
        void model(int generation, List<PaIndividual> population, double[][] dependency, List<int[]> subsets, long modelNanos);
        void step(int generation, int slot, int step, int subset, int donorSlot, PaIndividual parent, PaIndividual donor,
                  PaIndividual child, boolean fallback, PaInternalArchive.Flags flags, boolean accepted);
        void programEnd(int generation, int slot, PaIndividual result);
        void generationEnd(int generation, List<PaIndividual> population);
    }
    private final List<PaIndividual> population = new ArrayList<>();
    private final PaInternalArchive archive = new PaInternalArchive();
    private final PaPaidEvaluation evaluation;
    private final Observer observer;
    private final PaSubsetPolicy subsetPolicy;
    public int generation, completedGenerations, completedPrograms, slot = -1, step = -1;
    public String phase = "INITIALIZATION";

    public PaPopulation(PaPaidEvaluation evaluator, Observer evidence) { this(evaluator, evidence, PaSubsetPolicy.identity()); }
    public PaPopulation(PaPaidEvaluation evaluator, Observer evidence, PaSubsetPolicy policy) {
        evaluation = evaluator; observer = evidence; subsetPolicy = java.util.Objects.requireNonNull(policy);
    }

    public void addInitial(PaIndividual point) {
        if (generation != 0 || population.size() >= 100) throw new IllegalStateException("Initialization already complete");
        population.add(point); observer.initial(population.size() - 1, point, archive.offer(point.objectives()));
    }

    public void evolve() {
        if (population.size() != 100) throw new IllegalStateException("Expected100initial points");
        while (true) {
            evaluation.checkpoint(); generation++; phase = "REENCODING";
            for (int i = 0; i < population.size(); i++) {
                evaluation.checkpoint(); PaIndividual before = population.get(i), after = evaluation.reencode(before);
                population.set(i, after); observer.reencoded(generation, i, before, after);
            }
            List<int[]> subsets = learn(); phase = "MIXING";
            for (int i = 0; i < population.size(); i++) {
                evaluation.checkpoint(); slot = i; List<Integer> order = new ArrayList<>();
                for (int k = 0; k < subsets.size(); k++) order.add(k); Collections.shuffle(order, SeededRandom.current());
                for (int k = 0; k < order.size(); k++) {
                    evaluation.checkpoint(); step = k; int donorSlot = SeededRandom.current().nextInt(population.size() - 1);
                    if (donorSlot >= i) donorSlot++;
                    PaIndividual parent = population.get(i), donor = population.get(donorSlot);
                    int subsetIndex = order.get(k); PaMixingMove move = PaMixingMove.apply(evaluation.catalog(), parent.genome, donor.genome, subsets.get(subsetIndex));
                    PaIndividual child = evaluation.candidate(move.genome, parent);
                    PaInternalArchive.Flags flags = archive.offer(child.objectives()); boolean accepted = accepts(parent, child, flags);
                    if (accepted) population.set(i, child);
                    observer.step(generation, i, k, subsetIndex, donorSlot, parent, donor, child, move.fallback, flags, accepted);
                }
                completedPrograms++; observer.programEnd(generation, i, population.get(i));
            }
            completedGenerations++; phase = "GENERATION_COMPLETE"; observer.generationEnd(generation, population());
        }
    }

    private List<int[]> learn() {
        phase = "LEARNING"; int n = evaluation.catalog().jobs(); int[][] factories = new int[population.size()][n];
        double[][] keys = new double[population.size()][]; long started = System.nanoTime();
        for (int i = 0; i < population.size(); i++) {
            int[] resources = population.get(i).genome.allocations(); keys[i] = population.get(i).genome.priorities();
            for (int j = 0; j < n; j++) factories[i][j] = evaluation.catalog().factory(resources[j]);
        }
        double[][] dependency = new PaDependencyModel(factories, keys, evaluation.catalog().factories()).matrix();
        List<int[]> subsets = subsetPolicy.apply(generation, n, new LinkageHierarchy(dependency).subsets());
        observer.model(generation, population(), dependency, subsets, System.nanoTime() - started); return subsets;
    }

    private static boolean accepts(PaIndividual parent, PaIndividual child, PaInternalArchive.Flags flags) {
        double[] a = child.objectives(), b = parent.objectives();
        return parent.role == Direction.CENTER ? PaInternalArchive.weaklyDominates(a, b) || !flags.dominated
                : (a[parent.role.objective()] < b[parent.role.objective()]
                    || Boolean.getBoolean("research.pa.boundaryNonWorse") && a[parent.role.objective()] == b[parent.role.objective()]);
    }

    public List<PaIndividual> population() { return Collections.unmodifiableList(new ArrayList<>(population)); }
    public double[][] archive() { return archive.snapshot(); }
}
