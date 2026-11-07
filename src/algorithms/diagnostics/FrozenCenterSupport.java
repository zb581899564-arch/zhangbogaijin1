package org.uma.jmetal.util.research.cooperation;

import java.util.Arrays;
import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.search.Direction;
import org.uma.jmetal.util.research.search.SwarmSupport;

/** Apply the existing FA restoration and validation; CENTER LS does not read the shared pools. */
public final class FrozenCenterSupport implements SwarmSupport {
    private final FamilyContexts contexts;
    public FrozenCenterSupport(Instance instance, List<PermutationSolution<Integer>> entrants) {
        contexts = new FamilyContexts(instance);
        int[][] known = new int[4][];
        for (PermutationSolution<Integer> s : entrants) {
            int family = FamilyContexts.family(s);
            if (family < 0) continue;
            int[] fixed = (int[]) s.getAttribute(FamilyContexts.FIXED);
            if (!Arrays.equals(fixed, FamilyContexts.byJob(s)))
                throw new IllegalStateException("Entrant does not satisfy its frozen family");
            if (known[family] != null && !Arrays.equals(known[family], fixed))
                throw new IllegalStateException("Inconsistent frozen family");
            known[family] = fixed.clone();
        }
        for (int f = 0; f < known.length; f++) {
            if (known[f] == null) throw new IllegalStateException("Missing frozen family " + f);
            contexts.replace(f, known[f]);
        }
    }
    @Override public void beforeEvaluation(PermutationSolution<Integer> s, String stage, Direction d) { contexts.restore(s); }
    @Override public void evaluated(PermutationSolution<Integer> s, String stage, Direction d) { contexts.validate(s); }
}
