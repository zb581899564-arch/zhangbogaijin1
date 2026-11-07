package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.model.ModelKind;
import org.uma.jmetal.util.research.runtime.BudgetedProblem;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Modular, sourced reconstruction of HMOPSO-QLS/QGS; strict FE stopping belongs to RunContext. */
public final class CanonicalHmopso implements Algorithm<List<PermutationSolution<Integer>>> {
    private static final long serialVersionUID = 1L;
    private final int chapter;
    private final SearchConfig config;
    private final SearchState state;
    private final ParticleOperators operators;
    private final LocalSearch local;
    private final GlobalUpdatePolicy updatePolicy;
    private final SwarmSupport support;
    private final SemanticAudit audit;
    private final MechanismCapture mechanism;
    private final BudgetedProblem<PermutationSolution<Integer>> guarded;
    private final Map<Direction, PermutationSolution<Integer>> previousLeaders = new EnumMap<>(Direction.class);
    private boolean started;

    public CanonicalHmopso(Problem<PermutationSolution<Integer>> problem, Instance instance,
            int chapter, SearchConfig config) {
        this(problem, instance, chapter, config, null);
    }

    @SuppressWarnings("unchecked")
    public CanonicalHmopso(Problem<PermutationSolution<Integer>> problem, Instance instance,
            int chapter, SearchConfig config, GlobalUpdatePolicy updatePolicy) {
        this(problem, instance, chapter, config, updatePolicy, null);
    }

    @SuppressWarnings("unchecked")
    public CanonicalHmopso(Problem<PermutationSolution<Integer>> problem, Instance instance,
            int chapter, SearchConfig config, GlobalUpdatePolicy updatePolicy, SwarmSupport support) {
        this(problem, instance, chapter, config, updatePolicy, support, null);
    }
    @SuppressWarnings("unchecked")
    public CanonicalHmopso(Problem<PermutationSolution<Integer>> problem, Instance instance,
            int chapter, SearchConfig config, GlobalUpdatePolicy updatePolicy, SwarmSupport support, SemanticAudit audit) {
        this(problem, instance, chapter, config, updatePolicy, support, audit, null);
    }
    @SuppressWarnings("unchecked")
    public CanonicalHmopso(Problem<PermutationSolution<Integer>> problem, Instance instance,
            int chapter, SearchConfig config, GlobalUpdatePolicy updatePolicy, SwarmSupport support,
            SemanticAudit audit, MechanismCapture mechanism) {
        Objects.requireNonNull(instance, "instance");
        if (!(problem instanceof BudgetedProblem)) throw new IllegalArgumentException("Use RunContext.problem() for strict FE stopping");
        if ((chapter == 3) != (instance.kind() == ModelKind.CHAPTER3_FIXED_WORKER)) {
            throw new IllegalArgumentException("Chapter and model kind do not agree");
        }
        this.chapter = chapter; this.config = Objects.requireNonNull(config, "config").resolved(chapter);
        this.support = support;
        this.audit = audit;
        this.mechanism = mechanism;
        state = new SearchState(problem, instance, support, audit);
        operators = new ParticleOperators(instance, this.config);
        local = new LocalSearch(instance, chapter, this.config, state);
        this.updatePolicy = updatePolicy;
        guarded = (BudgetedProblem<PermutationSolution<Integer>>) problem;
    }

    @Override public void run() {
        if (started) throw new IllegalStateException("An algorithm instance may run once only");
        started = true;
        List<Particle> population = new ArrayList<>();
        for (int i = 0; i < config.populationSize; i++) population.add(new Particle(state.initialize()));
        if (support != null) support.initialized(solutions(population));
        if (updatePolicy != null) updatePolicy.initialized(solutions(population));
        if (audit != null) audit.feedbackInitialized();
        while (true) {
            guarded.checkpoint();
            if (audit != null) audit.feedbackBegin();
            if (mechanism != null) mechanism.begin(solutions(population));
            if (support != null) support.beginGeneration();
            renewContexts(population);
            Map<Direction, List<Particle>> groups = decompose(population);
            Map<Direction, List<Particle>> updated = new EnumMap<>(Direction.class);
            for (Direction direction : globalUpdateOrder()) {
                state.observationGroup(direction);
                updated.put(direction, chapter == 3 ? global(groups.get(direction), direction,
                        randomLeader()) : qgs(groups.get(direction), direction));
            }
            List<Particle> globallyUpdated = flatten(updated);
            if (mechanism != null) mechanism.globalPost(globallyUpdated);
            List<Particle> globalSnapshots = config.mergeGlobalLocal ? snapshots(globallyUpdated) : null;
            List<PermutationSolution<Integer>> reference = solutions(globallyUpdated);
            List<Particle> offspring = new ArrayList<>();
            if (chapter == 3) {
                // JMS Algorithm 1 completes the whole inter-factory phase before QLS.
                for (Direction direction : Direction.values()) {
                    state.observationGroup(direction);
                    List<Particle> balanced = new ArrayList<>();
                    for (Particle particle : updated.get(direction)) balanced.add(local.improveInter(particle, direction, reference));
                    updated.put(direction, balanced);
                }
                for (Direction direction : Direction.values()) for (Particle particle : updated.get(direction)) {
                    state.observationGroup(direction);
                    offspring.add(local.improveIntra(particle, direction, reference));
                }
            } else {
                for (Direction direction : Direction.values()) for (Particle particle : updated.get(direction)) {
                    state.observationGroup(direction);
                    Direction preference = preference(direction);
                    state.count("local.g" + direction.id() + ".preference." + preference.name());
                    guarded.checkpoint();
                    offspring.add(local.improve(particle, preference, reference));
                }
            }
            // JMS Algorithm 1 explicitly uses parents union final local-search offspring.
            // Legacy v2 follows the in-place pseudocode. S restores the thesis
            // Algorithm4-1/ESWA sec4.1 global-post + local-post candidate union.
            if (chapter == 3) offspring.addAll(population);
            List<Particle> candidates = offspring;
            if (config.mergeGlobalLocal) {
                candidates = new ArrayList<>(globalSnapshots); candidates.addAll(offspring);
            }
            if (mechanism != null && mechanism.retainParents()) {
                candidates = new ArrayList<>(candidates); candidates.addAll(population);
            }
            if (chapter == 4 && (config.mergeGlobalLocal || audit != null)) {
                SurvivorSelection.Result selected = SurvivorSelection.select(candidates, config.populationSize,
                        config.mergeGlobalLocal ? support : null, guarded::checkpoint);
                population = selected.survivors();
                if (audit != null) audit.pool(candidates, selected, globalSnapshots == null ? 0 : globalSnapshots.size());
            } else population = select(candidates, config.populationSize);
            if (mechanism != null) mechanism.end(offspring, population, support);
            // Search leaders come from accepted personal histories, as in the paper.
            // RunContext separately archives every successful evaluation, including rejected proposals.
            for (Particle particle : population) state.remember(particle.personalArchive());
            if (audit != null) audit.feedbackEnd();
            state.count("generations.completed");
        }
    }

    private void renewContexts(List<Particle> population) {
        if (support == null || !support.hasContextRenewal()) return;
        Map<Integer, PermutationSolution<Integer>> replacements = support.renewContexts(solutions(population));
        state.observationGroup(null);
        for (Map.Entry<Integer, PermutationSolution<Integer>> entry : replacements.entrySet()) {
            guarded.checkpoint();
            int index = entry.getKey();
            if (index < 0 || index >= population.size()) throw new IllegalStateException("Invalid renewed particle index");
            population.set(index, new Particle(state.evaluate(entry.getValue(), "context-renewal", null)));
            state.count("context-renewal.personalHistoriesReset");
        }
    }
    private List<Particle> qgs(List<Particle> group, Direction direction) {
        Direction preference = preference(direction);
        QTable table = new QTable(3, config.alpha, config.gamma);
        int observation = 1;
        List<Particle> current = group;
        for (int step = 0; step < config.qIterations; step++) {
            int action = table.choose(observation, config.exploration);
            PermutationSolution<Integer> leader = chooseLeader(action, direction, current);
            if (audit != null) audit.feedbackQgs(direction, step, action, leader);
            if (audit != null) audit.teacherSelected(leader);
            List<Particle> next = global(current, direction, leader);
            if (mechanism != null) mechanism.batch(direction, step, next);
            double reward = 0;
            for (int i = 0; i < current.size(); i++) reward += preference.reward(current.get(i).current, next.get(i).current);
            reward /= current.size();
            int nextState = preference.state(reward, chapter);
            table.update(observation, action, reward, nextState);
            state.count("qgs.g" + direction.id() + ".updates");
            state.count("qgs.g" + direction.id() + ".preference." + preference.name());
            state.count("qgs.g" + direction.id() + ".action" + action);
            previousLeaders.put(direction, ParetoTools.copy(leader));
            current = next; observation = nextState;
        }
        return current;
    }
    private Direction[] globalUpdateOrder() {
        Direction[] order = support == null ? Direction.values() : support.globalUpdateOrder();
        if (order == null || order.length != Direction.values().length)
            throw new IllegalStateException("Global order must contain each target group once");
        boolean[] seen = new boolean[order.length];
        for (Direction d : order) {
            if (d == null || seen[d.ordinal()]) throw new IllegalStateException("Repeated or null target group");
            seen[d.ordinal()] = true;
        }
        return order;
    }
    private PermutationSolution<Integer> chooseLeader(int action, Direction direction, List<Particle> group) {
        if (action == 0 && previousLeaders.containsKey(direction)) return ParetoTools.copy(previousLeaders.get(direction));
        Direction preference = preference(direction);
        if (action <= 1) {
            List<PermutationSolution<Integer>> candidates = solutions(group);
            return ParetoTools.copy(candidates.get(ParetoTools.order(candidates, preference).get(0)));
        }
        List<PermutationSolution<Integer>> archive = state.archive();
        PermutationSolution<Integer> first = archive.get(SeededRandom.current().nextInt(archive.size()));
        PermutationSolution<Integer> second = archive.get(SeededRandom.current().nextInt(archive.size()));
        return ParetoTools.copy(preference.better(second, first, archive) ? second : first);
    }
    private Direction preference(Direction group) { return support == null ? group : support.preference(group); }
    private List<Particle> global(List<Particle> group, Direction direction, PermutationSolution<Integer> leader) {
        List<Particle> result = new ArrayList<>();
        Direction preference = preference(direction);
        if (updatePolicy != null) updatePolicy.beginBatch(preference);
        for (Particle particle : group) {
            guarded.checkpoint();
            PermutationSolution<Integer> personal = particle.personalBest(preference);
            if (audit != null) audit.teacherSelected(personal);
            PermutationSolution<Integer> child = support == null ? null : support.compose(particle.current, direction);
            boolean composed = child != null;
            if (mechanism != null) mechanism.proposal(particle.current, personal, leader, composed);
            if (!composed) {
                if (audit != null) { audit.teacherConsumed(personal); audit.teacherConsumed(leader); }
                child = updatePolicy == null ? operators.update(particle.current, personal, leader)
                        : updatePolicy.propose(particle.current, personal, leader, preference);
            }
            if (audit != null) audit.generated(child, particle.current, composed);
            state.evaluate(child, "global", direction);
            if (updatePolicy != null && !composed) updatePolicy.evaluated(child, preference);
            result.add(particle.descend(child));
        }
        if (updatePolicy != null) updatePolicy.endBatch(preference);
        return GlobalBatchPolicy.select(group, result, preference);
    }
    private PermutationSolution<Integer> randomLeader() {
        List<PermutationSolution<Integer>> archive = state.archive();
        return archive.get(SeededRandom.current().nextInt(archive.size()));
    }
    private Map<Direction, List<Particle>> decompose(List<Particle> population) {
        if (support != null) {
            Map<Direction, List<Integer>> partition = support.grouping(solutions(population), config.boundarySize);
            if (partition != null) {
                Map<Direction, List<Particle>> groups = new EnumMap<>(Direction.class);
                boolean[] seen = new boolean[population.size()]; int count = 0;
                for (Direction d : Direction.values()) {
                    List<Particle> group = new ArrayList<>();
                    for (int index : partition.get(d)) {
                        if (index < 0 || index >= seen.length || seen[index]) throw new IllegalStateException("Invalid cooperative partition");
                        seen[index] = true; count++; group.add(population.get(index));
                    }
                    groups.put(d, group);
                }
                if (count != population.size()) throw new IllegalStateException("Incomplete cooperative partition");
                return groups;
            }
        }
        Map<Direction, List<Particle>> result = new EnumMap<>(Direction.class);
        List<Particle> remaining = new ArrayList<>(population);
        for (Direction direction : new Direction[] {Direction.MAKESPAN, Direction.ENERGY, Direction.WORKER_COST}) {
            List<Particle> chosen = take(remaining, direction, config.boundarySize);
            result.put(direction, chosen); remaining.removeAll(chosen);
        }
        result.put(Direction.CENTER, take(remaining, Direction.CENTER, remaining.size()));
        return result;
    }
    private static List<Particle> take(List<Particle> population, Direction direction, int count) {
        List<Integer> order = ParetoTools.order(solutions(population), direction);
        List<Particle> result = new ArrayList<>();
        for (int i = 0; i < count; i++) result.add(population.get(order.get(i)));
        return result;
    }
    private static List<Particle> select(List<Particle> candidates, int count) { return take(candidates, Direction.CENTER, count); }
    private static List<Particle> flatten(Map<Direction, List<Particle>> groups) {
        List<Particle> result = new ArrayList<>();
        for (Direction direction : Direction.values()) result.addAll(groups.get(direction));
        return result;
    }
    private static List<PermutationSolution<Integer>> solutions(List<Particle> population) {
        List<PermutationSolution<Integer>> result = new ArrayList<>();
        for (Particle particle : population) result.add(particle.current);
        return result;
    }
    private static List<Particle> snapshots(List<Particle> particles) {
        List<Particle> out = new ArrayList<>();
        for (Particle p : particles) out.add(p.snapshot());
        return out;
    }
    public Map<String, Long> diagnostics() { return state.diagnostics(); }
    public String configuration() { return config.describe(); }
    @Override public List<PermutationSolution<Integer>> getResult() { return state.archive(); }
    @Override public String getName() { return chapter == 3 ? "HMOPSO-QLS-reconstruction-v2" : "HMOPSO-QGS-reconstruction-v2"; }
    @Override public String getDescription() { return "A0-sourced-reconstruction-v2; explicit alpha/local-cap/grouping conventions"; }
}
