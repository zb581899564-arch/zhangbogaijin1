package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;

/** Particle identity carries its own non-dominated personal history through selection. */
final class Particle {
    final PermutationSolution<Integer> current;
    private final List<PermutationSolution<Integer>> history;
    Particle(PermutationSolution<Integer> evaluated) {
        current = evaluated; history = new ArrayList<>(); ParetoTools.offer(history, evaluated);
    }
    private Particle(PermutationSolution<Integer> evaluated, List<PermutationSolution<Integer>> history) {
        current = evaluated; this.history = ParetoTools.copies(history); ParetoTools.offer(this.history, evaluated);
    }
    Particle descend(PermutationSolution<Integer> evaluated) { return new Particle(evaluated, history); }
    List<PermutationSolution<Integer>> personalArchive() { return ParetoTools.copies(history); }
    PermutationSolution<Integer> personalBest(Direction direction) {
        return ParetoTools.copy(history.get(ParetoTools.order(history, direction).get(0)));
    }
}
