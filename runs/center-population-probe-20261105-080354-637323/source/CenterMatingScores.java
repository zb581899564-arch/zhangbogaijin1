package org.uma.jmetal.util.research.classic;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;

/** Research bridge: carry actual NSGA union scores into same-category parent tournaments. */
public final class CenterMatingScores {
    private final NsgaSelection selection;
    private final NsgaSelection.Scores original;
    private final IdentityHashMap<PermutationSolution<Integer>,Integer> positions = new IdentityHashMap<>();
    private final Map<List<Integer>,NsgaSelection.Scores> subsets = new HashMap<>();

    public CenterMatingScores(List<PermutationSolution<Integer>> union, Runnable checkpoint) {
        selection = new NsgaSelection(checkpoint);
        original = selection.score(union);
        for (int i=0; i<union.size(); i++) positions.put(union.get(i),i);
    }

    public int draw(List<PermutationSolution<Integer>> current, List<Integer> allowed) {
        List<Integer> source = new ArrayList<>();
        for (int index:allowed) {
            Integer position = positions.get(current.get(index));
            if (position==null) throw new IllegalStateException("Unscored central parent");
            source.add(position);
        }
        NsgaSelection.Scores scores = subsets.get(source);
        if (scores==null) {
            scores = new NsgaSelection.Scores(source.size(),new ArrayList<>());
            for (int i=0; i<source.size(); i++) {
                scores.rank[i]=original.rank[source.get(i)];
                scores.crowding[i]=original.crowding[source.get(i)];
            }
            subsets.put(source,scores);
        }
        return allowed.get(selection.tournament(scores));
    }
}
