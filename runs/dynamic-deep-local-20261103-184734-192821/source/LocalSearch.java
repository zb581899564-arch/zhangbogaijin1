package org.uma.jmetal.util.research.search;

import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.FactoryNeighborhoods;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Inter-factory load balancing followed by QLS (chapter 3) or random-factory VNS (chapter 4). */
final class LocalSearch {
    private final Instance instance;
    private final int chapter;
    private final SearchConfig config;
    private final SearchState state;
    private final IntraNeighborhoods neighborhoods;
    private final QgsLocalLedger ledger = QgsLocalLedger.instance();
    LocalSearch(Instance instance, int chapter, SearchConfig config, SearchState state) {
        this.instance = instance; this.chapter = chapter; this.config = config; this.state = state;
        neighborhoods = new IntraNeighborhoods(instance);
    }
    Particle improve(Particle particle, Direction direction, List<PermutationSolution<Integer>> reference) {
        return improveIntra(improveInter(particle, direction, reference), direction, reference);
    }
    Particle improveInter(Particle particle, Direction direction, List<PermutationSolution<Integer>> reference) {
        QgsLocalLedger.Slot slot = ledger.inter(direction.id());
        try { return particle.descend(inter(particle.current, direction, reference, slot)); }
        finally { ledger.end(slot); }
    }
    Particle improveIntra(Particle particle, Direction direction, List<PermutationSolution<Integer>> reference) {
        PermutationSolution<Integer> current = particle.current;
        if (chapter == 3) {
            QTable table = new QTable(instance.factories(), config.alpha, config.gamma);
            int observation = 1;
            for (int q = 0; q < config.qIterations; q++) {
                int factory = table.choose(observation, config.exploration);
                PermutationSolution<Integer> next = vns(current, factory, direction, reference);
                double reward = direction.reward(current, next);
                int nextState = direction.state(reward, chapter);
                table.update(observation, factory, reward, nextState);
                state.count("qls.g" + direction.id() + ".updates");
                observation = nextState;
                current = next; // Each action continues from the previous action's result.
            }
        } else {
            state.count("audit.paperLS.particlesStarted");
            for (int round = 0; round < config.localProposalCap && ledger.hasRound(); round++) {
                int factory = SeededRandom.current().nextInt(instance.factories());
                factory = state.localFactory(current, direction, factory);
                state.count("audit.paperLS.roundsStarted");
                QgsLocalLedger.Slot slot = ledger.round(direction.id(), round, factory);
                int[] remaining = {slot.limit};
                try {
                    do {
                        current = vns(current, slot.factory, direction, reference, remaining);
                        if (slot.fixed && remaining[0] > 0) slot.restarts++;
                    } while (slot.fixed && remaining[0] > 0);
                } finally {
                    slot.paid = slot.limit - remaining[0];
                    ledger.end(slot);
                }
                state.count("audit.paperLS.roundsCompleted");
            }
            state.count("audit.paperLS.particlesCompleted");
        }
        return particle.descend(current);
    }
    private PermutationSolution<Integer> inter(PermutationSolution<Integer> parent, Direction direction,
            List<PermutationSolution<Integer>> reference, QgsLocalLedger.Slot slot) {
        PermutationSolution<Integer> current = parent;
        int operator = 0;
        while (slot.paid < slot.limit && (operator < 2 || slot.fixed)) {
            if (operator == 2) { operator = 0; slot.restarts++; }
            PermutationSolution<Integer> child = FactoryNeighborhoods.move(current, direction.id(), operator == 0, instance);
            state.count("inter.operator" + operator + ".proposals");
            state.evaluate(child, "inter", direction);
            slot.paid++;
            if (direction.better(child, current, reference)) {
                current = child; operator = 0;
                state.count("inter.accepted");
            } else operator++;
        }
        return current;
    }
    private PermutationSolution<Integer> vns(PermutationSolution<Integer> parent, int factory,
            Direction direction, List<PermutationSolution<Integer>> reference) {
        return vns(parent, factory, direction, reference, new int[] {config.localProposalCap});
    }
    private PermutationSolution<Integer> vns(PermutationSolution<Integer> parent, int factory,
            Direction direction, List<PermutationSolution<Integer>> reference, int[] remaining) {
        PermutationSolution<Integer> incumbent = parent;
        int operator = 0;
        while (operator < IntraNeighborhoods.COUNT && remaining[0] > 0) {
            PermutationSolution<Integer> shaken = evaluateNeighborhood(incumbent, factory, operator, direction, remaining);
            PermutationSolution<Integer> improved = descent(shaken, factory, direction, reference, remaining);
            if (direction.better(improved, incumbent, reference)) {
                incumbent = improved; operator = 0; state.count("intra.accepted");
            } else operator++;
        }
        return incumbent;
    }
    private PermutationSolution<Integer> descent(PermutationSolution<Integer> parent, int factory,
            Direction direction, List<PermutationSolution<Integer>> reference, int[] remaining) {
        PermutationSolution<Integer> incumbent = parent;
        int operator = 0;
        while (operator < IntraNeighborhoods.COUNT && remaining[0] > 0) {
            PermutationSolution<Integer> child = evaluateNeighborhood(incumbent, factory, operator, direction, remaining);
            if (direction.better(child, incumbent, reference)) { incumbent = child; operator = 0; }
            else operator++;
        }
        return incumbent;
    }
    private PermutationSolution<Integer> evaluateNeighborhood(PermutationSolution<Integer> parent, int factory,
            int operator, Direction direction, int[] remaining) {
        state.count("intra.neighborhood" + operator + ".proposals");
        PermutationSolution<Integer> evaluated = state.evaluate(neighborhoods.propose(parent, factory, operator), "intra", direction);
        remaining[0]--;
        return evaluated;
    }
}
