package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicLong;
import org.uma.jmetal.solution.PermutationSolution;

/** Particle identity carries its own non-dominated personal history through selection. */
final class Particle {
    private static final AtomicLong NEXT_BRANCH = new AtomicLong();
    final PermutationSolution<Integer> current;
    private final List<PermutationSolution<Integer>> history;
    private final long lineageId, branchId;
    Particle(PermutationSolution<Integer> evaluated) {
        current = evaluated; history = new ArrayList<>(); ParetoTools.offer(history, evaluated);
        branchId = NEXT_BRANCH.incrementAndGet(); lineageId = branchId;
    }
    private Particle(PermutationSolution<Integer> evaluated, List<PermutationSolution<Integer>> history,
            long lineageId, long branchId, boolean includeCurrent) {
        current = evaluated; this.history = ParetoTools.copies(history);
        this.lineageId = lineageId; this.branchId = branchId;
        if (includeCurrent) ParetoTools.offer(this.history, evaluated);
    }
    Particle descend(PermutationSolution<Integer> evaluated) {
        return new Particle(evaluated, history, lineageId, NEXT_BRANCH.incrementAndGet(), true);
    }
    /** Freeze this branch before local search without consuming RNG or another evaluation. */
    Particle snapshot() { return new Particle(ParetoTools.copy(current), history, lineageId, branchId, false); }
    long lineageId() { return lineageId; }
    long branchId() { return branchId; }
    List<PermutationSolution<Integer>> personalArchive() { return ParetoTools.copies(history); }
    PermutationSolution<Integer> personalBest(Direction direction) {
        return ParetoTools.copy(history.get(ParetoTools.order(history, direction).get(0)));
    }
}
