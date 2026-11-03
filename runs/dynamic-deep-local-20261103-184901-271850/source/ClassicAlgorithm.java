package org.uma.jmetal.util.research.classic;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.model.ModelKind;
import org.uma.jmetal.util.research.runtime.BudgetedProblem;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import org.uma.jmetal.util.research.search.OrdinaryVns;
import org.uma.jmetal.util.research.search.DeepLocalVisits;
import org.uma.jmetal.util.research.search.SemanticAudit;
import org.uma.jmetal.util.research.search.MechanismCapture;

/** Standard selection mechanisms with a common, explicitly adapted scheduling kernel.
 * RunContext owns termination and the external result archive; budget exceptions pass through.
 */
public final class ClassicAlgorithm implements Algorithm<List<PermutationSolution<Integer>>> {
    private static final long serialVersionUID = 1L;
    private final Problem<PermutationSolution<Integer>> problem;
    private final Instance instance;
    private final ClassicConfig config;
    private final Runnable checkpoint;
    private final ClassicVariation variation;
    private final SemanticAudit audit;
    private final MechanismCapture mechanism;
    private final Map<String, Long> counts = new LinkedHashMap<>();
    private List<PermutationSolution<Integer>> population = new ArrayList<>(), archive = new ArrayList<>();
    private OrdinaryVns vns;
    private DeepLocalVisits deep;
    private MoeadDecomposition decomposition;
    private double[] speaScale;
    private boolean started;
    private long globalOffspring;
    private int maximumReplacements;

    public ClassicAlgorithm(Problem<PermutationSolution<Integer>> guarded, Instance in,
            ClassicConfig cfg, Runnable timeCheckpoint) {
        this(guarded, in, cfg, timeCheckpoint, null);
    }
    public ClassicAlgorithm(Problem<PermutationSolution<Integer>> guarded, Instance in,
            ClassicConfig cfg, Runnable timeCheckpoint, SemanticAudit audit) {
        this(guarded, in, cfg, timeCheckpoint, audit, null);
    }
    public ClassicAlgorithm(Problem<PermutationSolution<Integer>> guarded, Instance in,
            ClassicConfig cfg, Runnable timeCheckpoint, SemanticAudit audit, MechanismCapture mechanism) {
        if (guarded == null || in == null || cfg == null || timeCheckpoint == null)
            throw new IllegalArgumentException("Classic algorithm requires guarded problem, instance, config and checkpoint");
        if (!(guarded instanceof BudgetedProblem))
            throw new IllegalArgumentException("Classic algorithm requires a BudgetedProblem from RunContext");
        if (in.kind() != ModelKind.CHAPTER4_DUAL_RESOURCE || guarded.getNumberOfObjectives() != 3)
            throw new IllegalArgumentException("Classic 4V adaptation requires chapter4 and three objectives");
        problem = guarded; instance = in; config = cfg; checkpoint = timeCheckpoint;
        this.audit = audit;
        this.mechanism = mechanism;
        variation = new ClassicVariation(in, cfg, timeCheckpoint);
    }

    @Override public void run() {
        if (started) throw new IllegalStateException("Classic algorithm may run only once");
        started = true;
        if (!"NSGA2_4V".equals(config.mode)) throw new IllegalStateException("Deep NSGA-II control only");
        deep = new DeepLocalVisits(problem, instance);
        for (int i = 0; i < ClassicConfig.POPULATION; i++) {
            checkpoint.run();
            PermutationSolution<Integer> initial = problem.createSolution();
            deep.prepareInitial(initial, i);
            population.add(evaluate(initial, "initialization"));
        }
        if ("MOEAD_4V".equals(config.mode)) runMoead();
        else if ("SPEA2_4V".equals(config.mode)) runSpea();
        else runNsga();
    }

    private void runNsga() {
        NsgaSelection selection = new NsgaSelection(checkpoint);
        if ("NSGA2_VNS_4V".equals(config.mode)) vns = new OrdinaryVns(problem, instance, config.localProposalCap, checkpoint, audit);
        NsgaSelection.Scores scores = selection.score(population);
        while (true) {
            checkpoint.run();
            if (mechanism != null) mechanism.begin(population);
            List<PermutationSolution<Integer>> offspring = new ArrayList<>();
            for (int i = 0; i < ClassicConfig.POPULATION; i++) {
                checkpoint.run();
                PermutationSolution<Integer> child = generate(population.get(selection.tournament(scores)),
                        population.get(selection.tournament(scores)));
                if (vns != null && globalOffspring % config.localInterval == 0)
                    child = vns.improve(child, population);
                offspring.add(child);
            }
            List<PermutationSolution<Integer>> pool = ClassicTools.union(population, offspring);
            NsgaSelection.Selection next = selection.environmental(pool, ClassicConfig.POPULATION);
            if (audit != null) audit.classicPool(pool, next.population, population.size());
            if (mechanism != null) mechanism.classicEnd(offspring, next.population);
            population = next.population; scores = next.scores;
            count("generations");
            if (deep.due(globalOffspring)) {
                List<PermutationSolution<Integer>> local = deep.improve(population);
                next = selection.environmental(ClassicTools.union(population, local), ClassicConfig.POPULATION);
                population = next.population; scores = next.scores;
            }
        }
    }

    private void runSpea() {
        speaScale = FrozenObjectiveScale.from(population, checkpoint);
        SpeaSelection selection = new SpeaSelection(speaScale, checkpoint);
        while (true) {
            checkpoint.run();
            List<PermutationSolution<Integer>> union = ClassicTools.union(population, archive);
            SpeaSelection.Scores scores = selection.score(union);
            List<Integer> selected = selection.select(scores, ClassicConfig.POPULATION);
            archive = new ArrayList<>();
            for (int index : selected) archive.add(union.get(index));
            count("archiveUpdates");
            List<PermutationSolution<Integer>> offspring = new ArrayList<>();
            for (int i = 0; i < ClassicConfig.POPULATION; i++) {
                checkpoint.run();
                offspring.add(generate(union.get(speaTournament(selected, scores)), union.get(speaTournament(selected, scores))));
            }
            population = offspring; count("generations");
        }
    }

    private int speaTournament(List<Integer> archiveIndices, SpeaSelection.Scores scores) {
        int a = archiveIndices.get(SeededRandom.current().nextInt(archiveIndices.size()));
        int b = archiveIndices.get(SeededRandom.current().nextInt(archiveIndices.size()));
        int c = Double.compare(scores.fitness[a], scores.fitness[b]);
        return c == 0 ? (SeededRandom.current().nextBoolean() ? a : b) : c < 0 ? a : b;
    }

    private void runMoead() {
        decomposition = new MoeadDecomposition(population, config.neighborhoodSize, checkpoint);
        while (true) {
            checkpoint.run(); List<Integer> order = ClassicTools.indices(ClassicConfig.POPULATION); SeededRandom.shuffle(order);
            for (int subproblem : order) {
                checkpoint.run(); List<Integer> pool = matingPool(subproblem);
                int a = SeededRandom.current().nextInt(pool.size());
                int b = SeededRandom.current().nextInt(pool.size() - 1); if (b >= a) b++;
                PermutationSolution<Integer> child = generate(population.get(pool.get(a)), population.get(pool.get(b)));
                decomposition.updateIdeal(child); count("idealPaidUpdates");
                SeededRandom.shuffle(pool); int replaced = 0;
                for (int index : pool) {
                    checkpoint.run();
                    if (decomposition.scalar(child, index) <= decomposition.scalar(population.get(index), index)) {
                        population.set(index, ClassicTools.copy(child)); replaced++; count("replacements");
                        if (replaced == config.replacementLimit) break;
                    }
                }
                maximumReplacements = Math.max(maximumReplacements, replaced);
            }
            count("generations");
        }
    }

    private List<Integer> matingPool(int subproblem) {
        if (SeededRandom.current().nextDouble() >= config.neighborhoodProbability) {
            count("globalMating"); return ClassicTools.indices(ClassicConfig.POPULATION);
        }
        count("neighborMating"); List<Integer> pool = new ArrayList<>();
        for (int index : decomposition.neighbors[subproblem]) pool.add(index);
        return pool;
    }
    private PermutationSolution<Integer> generate(PermutationSolution<Integer> a, PermutationSolution<Integer> b) {
        if (mechanism != null) mechanism.proposal(a, a, b, false);
        PermutationSolution<Integer> child = variation.child(a, b);
        if (audit != null) audit.generated(child, a, false);
        child = evaluate(child, "global");
        globalOffspring++; return child;
    }
    private PermutationSolution<Integer> evaluate(PermutationSolution<Integer> child, String stage) {
        checkpoint.run(); count(stage + ".proposals");
        SchedulingEncoding.repair(child, instance);
        if (audit != null) audit.proposal(child, stage);
        problem.evaluate(child); count(stage + ".evaluations");
        for (int m = 0; m < 3; m++) if (!Double.isFinite(child.getObjective(m)))
            throw new IllegalStateException("Classic selection requires finite evaluated objectives");
        checkpoint.run(); return child;
    }
    private void count(String key) { counts.put(key, counts.getOrDefault(key, 0L) + 1); }

    public Map<String, Object> diagnostics() {
        Map<String, Object> result = new LinkedHashMap<>(); result.putAll(counts);
        result.put("globalOffspring", globalOffspring); result.put("populationSize", population.size());
        result.put("internalArchiveSize", archive.size()); result.put("maximumReplacementsPerChild", maximumReplacements);
        result.put("externalArchive", "RunContext-independent");
        if (deep != null) result.putAll(deep.diagnostics());
        if (vns != null) { result.put("ordinaryVns", vns.diagnostics()); result.put("localProposalCapScope", "intra-only; inter-additional-paid"); }
        if (decomposition != null) {
            result.put("objectiveScaleFrozen", numbers(decomposition.scale)); result.put("paidIdeal", numbers(decomposition.ideal));
            result.put("weightCount", decomposition.weights.length); result.put("weightConstructionConsumesRng", false);
        }
        if (speaScale != null) result.put("objectiveScaleFrozen", numbers(speaScale));
        return Collections.unmodifiableMap(result);
    }
    private static List<Double> numbers(double[] array) {
        List<Double> result = new ArrayList<>(); for (double value : array) result.add(value); return result;
    }
    public String configuration() { return config.describe(); }
    @Override public List<PermutationSolution<Integer>> getResult() {
        return ClassicTools.copies(archive.isEmpty() ? population : archive);
    }
    @Override public String getName() { return config.mode; }
    @Override public String getDescription() { return configuration(); }
}
