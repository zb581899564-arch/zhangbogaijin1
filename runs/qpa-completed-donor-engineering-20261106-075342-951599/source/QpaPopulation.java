package org.uma.jmetal.util.research.modelglobal;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.LinkedHashMap;
import java.util.Map;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import org.uma.jmetal.util.research.search.Direction;

/** Complete synchronous no-FI direct-joint lifecycle. Working states cannot become donors within a generation. */
public final class QpaPopulation {
    public interface Observer {
        default void initial(int slot, QpaIndividual point, PaInternalArchive.Flags flags) { }
        default void model(int generation, List<QpaIndividual> parents, QpaLinkageModel model, long nanos) { }
        default void step(int generation, int slot, int step, int subset, int phase, int donorSlot, int reference,
                QpaIndividual parent, QpaIndividual donor, QpaIndividual child, boolean fallback, PaInternalArchive.Flags flags, boolean accepted) { }
        default void programEnd(int generation, int slot, QpaIndividual result) { }
        default void generationEnd(int generation, List<QpaIndividual> values) { }
    }
    private List<QpaIndividual> population = new ArrayList<>(), parents = new ArrayList<>(), offspring = new ArrayList<>();
    private final QpaPaidEvaluation evaluation;
    private final Observer observer;
    private final PaInternalArchive archive = new PaInternalArchive();
    private QpaLinkageModel model;
    private QpaIndividual working;
    public int generation, completedGenerations, completedPrograms, slot = -1, step = -1, subset = -1, phase, donorSlot = -1, reference = -1;
    public String stage = "INITIALIZATION";
    private long initialFees, firstFees, secondFees, accepted, fallbacks, modelNanos;

    public QpaPopulation(QpaPaidEvaluation evaluator, Observer evidence) { evaluation = evaluator; observer = evidence; }

    public void addInitial(QpaIndividual point) {
        if (generation != 0 || population.size() >= 100) throw new IllegalStateException("Initialization already complete");
        population.add(point); initialFees++; observer.initial(population.size() - 1, point, archive.offer(point.objectives()));
    }

    public void evolve(int generationLimit) {
        if (population.size() != 100 || generationLimit == 0) throw new IllegalStateException("100 initial points and nonzero generation limit required");
        while (generationLimit < 0 || completedGenerations < generationLimit) {
            evaluation.checkpoint(); generation++; stage = "LEARNING";
            parents = new ArrayList<>(population); offspring = new ArrayList<>();
            long started = System.nanoTime(); model = new QpaLinkageModel(parents, evaluation); modelNanos += System.nanoTime() - started;
            observer.model(generation, parentPopulation(), model, System.nanoTime() - started); stage = "MIXING";
            for (int i = 0; i < parents.size(); i++) {
                evaluation.checkpoint(); slot = i; working = parents.get(i); improve();
                offspring.add(working); completedPrograms++; observer.programEnd(generation, slot, working);
            }
            population = new ArrayList<>(offspring); completedGenerations++; stage = "GENERATION_COMPLETE";
            observer.generationEnd(generation, population());
        }
    }

    private void improve() {
        List<Integer> order = new ArrayList<>();
        for (int i = 0; i < model.activeSubsets.size(); i++) order.add(i);
        Collections.shuffle(order, SeededRandom.current());
        for (int k = 0; k < order.size(); k++) {
            evaluation.checkpoint(); step = k; subset = order.get(k); donorSlot = SeededRandom.current().nextInt(parents.size());
            QpaIndividual donor = QpaCompletedDonors.choose(parents, offspring, donorSlot, working.role);
            attempt(1, donor); attempt(2, donor);
        }
    }

    private void attempt(int which, QpaIndividual donor) {
        evaluation.checkpoint(); phase = which;
        int[] mask = model.activeSubsets.get(subset);
        reference = which == 1 ? mask[SeededRandom.current().nextInt(mask.length)] : -1;
        QpaIndividual parent = working;
        DirectJointMove move = DirectJointMove.apply(evaluation.catalog(), parent.genome, donor.genome, mask, reference,
                which == 1 ? DirectJointMove.Kind.POSITION : DirectJointMove.Kind.ORDER);
        QpaIndividual child = evaluation.candidate(move.genome, parent);
        PaInternalArchive.Flags flags = archive.offer(child.objectives()); boolean keep = accepts(parent, child, flags);
        if (which == 1) firstFees++; else secondFees++;
        if (move.emptyFactoryFallback) fallbacks++; if (keep) { working = child; accepted++; }
        observer.step(generation, slot, step, subset, phase, donorSlot, reference, parent, donor, child, move.emptyFactoryFallback, flags, keep);
    }

    private static boolean accepts(QpaIndividual parent, QpaIndividual child, PaInternalArchive.Flags flags) {
        double[] a = child.objectives(), b = parent.objectives();
        return parent.role == Direction.CENTER ? PaInternalArchive.weaklyDominates(a, b) || !flags.dominated
                : a[parent.role.objective()] <= b[parent.role.objective()];
    }

    public List<QpaIndividual> population() { return Collections.unmodifiableList(new ArrayList<>(population)); }
    public List<QpaIndividual> parentPopulation() { return Collections.unmodifiableList(new ArrayList<>(parents)); }
    public List<QpaIndividual> offspring() { return Collections.unmodifiableList(new ArrayList<>(offspring)); }
    public QpaIndividual working() { return working; }
    public double[][] archive() { return archive.snapshot(); }
    public Map<String,Object> diagnostics() {
        Map<String,Object> result = new LinkedHashMap<>();
        result.put("initialization.evaluations", initialFees); result.put("global.evaluations", firstFees + secondFees);
        result.put("qpa.position.evaluations", firstFees); result.put("qpa.order.evaluations", secondFees);
        result.put("modelBuilds", generation); result.put("modelNanos", modelNanos); result.put("accepted", accepted);
        result.put("fallbacks", fallbacks); result.put("completePrograms", completedPrograms); result.put("completeGenerations", completedGenerations);
        return result;
    }
}
