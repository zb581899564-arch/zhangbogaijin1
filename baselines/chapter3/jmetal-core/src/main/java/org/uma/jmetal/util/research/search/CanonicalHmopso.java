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
    private final Map<Direction, PermutationSolution<Integer>> previousLeaders = new EnumMap<>(Direction.class);
    private boolean started;

    public CanonicalHmopso(Problem<PermutationSolution<Integer>> problem, Instance instance,
            int chapter, SearchConfig config) {
        Objects.requireNonNull(instance, "instance");
        if (!(problem instanceof BudgetedProblem)) throw new IllegalArgumentException("Use RunContext.problem() for strict FE stopping");
        if ((chapter == 3) != (instance.kind() == ModelKind.CHAPTER3_FIXED_WORKER)) {
            throw new IllegalArgumentException("Chapter and model kind do not agree");
        }
        this.chapter = chapter; this.config = Objects.requireNonNull(config, "config").resolved(chapter);
        state = new SearchState(problem, instance);
        operators = new ParticleOperators(instance, this.config);
        local = new LocalSearch(instance, chapter, this.config, state);
    }

    @Override public void run() {
        if (started) throw new IllegalStateException("An algorithm instance may run once only");
        started = true;
        List<Particle> population = new ArrayList<>();
        for (int i = 0; i < config.populationSize; i++) population.add(new Particle(state.initialize()));
        while (true) {
            Map<Direction, List<Particle>> groups = decompose(population);
            Map<Direction, List<Particle>> updated = new EnumMap<>(Direction.class);
            for (Direction direction : Direction.values()) {
                updated.put(direction, chapter == 3 ? global(groups.get(direction), direction,
                        randomLeader()) : qgs(groups.get(direction), direction));
            }
            List<Particle> globallyUpdated = flatten(updated);
            List<PermutationSolution<Integer>> reference = solutions(globallyUpdated);
            List<Particle> offspring = new ArrayList<>();
            if (chapter == 3) {
                // JMS Algorithm 1 completes the whole inter-factory phase before QLS.
                for (Direction direction : Direction.values()) {
                    List<Particle> balanced = new ArrayList<>();
                    for (Particle particle : updated.get(direction)) balanced.add(local.improveInter(particle, direction, reference));
                    updated.put(direction, balanced);
                }
                for (Direction direction : Direction.values()) for (Particle particle : updated.get(direction)) {
                    offspring.add(local.improveIntra(particle, direction, reference));
                }
            } else {
                for (Direction direction : Direction.values()) for (Particle particle : updated.get(direction)) {
                    offspring.add(local.improve(particle, direction, reference));
                }
            }
            // JMS Algorithm 1 explicitly uses parents union final local-search offspring.
            // ESWA Algorithm 1 selects from the four updated sub-swarms only.
            if (chapter == 3) offspring.addAll(population);
            population = select(offspring, config.populationSize);
            // Search leaders come from accepted personal histories, as in the paper.
            // RunContext separately archives every successful evaluation, including rejected proposals.
            for (Particle particle : population) state.remember(particle.personalArchive());
            state.count("generations.completed");
        }
    }

    private List<Particle> qgs(List<Particle> group, Direction direction) {
        QTable table = new QTable(3, config.alpha, config.gamma);
        int observation = 1;
        List<Particle> current = group;
        for (int step = 0; step < config.qIterations; step++) {
            int action = table.choose(observation, config.exploration);
            PermutationSolution<Integer> leader = chooseLeader(action, direction, current);
            List<Particle> next = global(current, direction, leader);
            double reward = 0;
            for (int i = 0; i < current.size(); i++) reward += direction.reward(current.get(i).current, next.get(i).current);
            reward /= current.size();
            int nextState = direction.state(reward, chapter);
            table.update(observation, action, reward, nextState);
            state.count("qgs.g" + direction.id() + ".updates");
            state.count("qgs.g" + direction.id() + ".action" + action);
            previousLeaders.put(direction, ParetoTools.copy(leader));
            current = next; observation = nextState;
        }
        return current;
    }
    private PermutationSolution<Integer> chooseLeader(int action, Direction direction, List<Particle> group) {
        if (action == 0 && previousLeaders.containsKey(direction)) return ParetoTools.copy(previousLeaders.get(direction));
        if (action <= 1) {
            List<PermutationSolution<Integer>> candidates = solutions(group);
            return ParetoTools.copy(candidates.get(ParetoTools.order(candidates, direction).get(0)));
        }
        List<PermutationSolution<Integer>> archive = state.archive();
        PermutationSolution<Integer> first = archive.get(SeededRandom.current().nextInt(archive.size()));
        PermutationSolution<Integer> second = archive.get(SeededRandom.current().nextInt(archive.size()));
        return ParetoTools.copy(direction.better(second, first, archive) ? second : first);
    }
    private List<Particle> global(List<Particle> group, Direction direction, PermutationSolution<Integer> leader) {
        List<Particle> result = new ArrayList<>();
        for (Particle particle : group) {
            PermutationSolution<Integer> child = operators.update(particle.current, particle.personalBest(direction), leader);
            state.evaluate(child, "global", direction);
            result.add(particle.descend(child));
        }
        return result;
    }
    private PermutationSolution<Integer> randomLeader() {
        List<PermutationSolution<Integer>> archive = state.archive();
        return archive.get(SeededRandom.current().nextInt(archive.size()));
    }
    private Map<Direction, List<Particle>> decompose(List<Particle> population) {
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
    public Map<String, Long> diagnostics() { return state.diagnostics(); }
    public String configuration() { return config.describe(); }
    @Override public List<PermutationSolution<Integer>> getResult() { return state.archive(); }
    @Override public String getName() { return chapter == 3 ? "HMOPSO-QLS-reconstruction-v2" : "HMOPSO-QGS-reconstruction-v2"; }
    @Override public String getDescription() { return "A0-sourced-reconstruction-v2; explicit alpha/local-cap/grouping conventions"; }
}
