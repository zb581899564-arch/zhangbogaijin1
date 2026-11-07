package org.uma.jmetal.util.research.search;

import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;

/** Hold candidate and incumbent fixed; score the same comparison under both reference sets. */
final class CenterReferenceProbe {
    private final List<PermutationSolution<Integer>> alternate;
    private final CenterRoleSwapProbe blocks = Boolean.getBoolean("research.center.roleProbe") ? new CenterRoleSwapProbe() : null;
    private long count, actualAccept, alternateAccept, actualOnly, alternateOnly, actualTie, alternateTie;
    CenterReferenceProbe(List<PermutationSolution<Integer>> alternate) { this.alternate = alternate; }

    void observe(Direction direction, PermutationSolution<Integer> candidate, PermutationSolution<Integer> incumbent,
            List<PermutationSolution<Integer>> reference, boolean actual) {
        if (direction != Direction.CENTER) throw new IllegalStateException("Reference probe outside CENTER");
        int current = compare(candidate, incumbent, reference), other = compare(candidate, incumbent, alternate);
        if ((current < 0) != actual) throw new IllegalStateException("Reference probe differs from real PDDR decision");
        count++;
        if (actual) actualAccept++;
        if (other < 0) alternateAccept++;
        if (actual && other >= 0) actualOnly++;
        if (!actual && other < 0) alternateOnly++;
        if (current == 0) actualTie++;
        if (other == 0) alternateTie++;
        if (blocks != null) blocks.observe(candidate, incumbent, reference, alternate, actual, other < 0);
    }

    private static int compare(PermutationSolution<Integer> c, PermutationSolution<Integer> i,
            List<PermutationSolution<Integer>> reference) {
        int pC = 0, qC = 0, pI = 0, qI = 0;
        for (PermutationSolution<Integer> r : reference) {
            if (ParetoTools.dominates(c, r)) pC++;
            if (ParetoTools.dominates(r, c)) qC++;
            if (ParetoTools.dominates(i, r)) pI++;
            if (ParetoTools.dominates(r, i)) qI++;
        }
        if (ParetoTools.dominates(c, i)) { pC++; qI++; }
        if (ParetoTools.dominates(i, c)) { pI++; qC++; }
        return Double.compare(qC + 1.0 / (pC + 1), qI + 1.0 / (pI + 1));
    }
    Map<String, Object> summary() {
        return ReverseAudit.row("comparisons", count, "actualAccept", actualAccept, "alternateAccept", alternateAccept,
                "actualOnly", actualOnly, "alternateOnly", alternateOnly, "actualTie", actualTie, "alternateTie", alternateTie,
                "blockProbe", blocks == null ? null : blocks.summary());
    }
}
