package org.uma.jmetal.util.research.classic;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Isolated access to the actually loaded NSGA scorer and crowded tournament. */
public final class ClassicMatingBridge {
    private final NsgaSelection selection;
    private final NsgaSelection.Scores scores;
    private final int size;
    public ClassicMatingBridge(List<PermutationSolution<Integer>> pool,Runnable checkpoint,boolean ranked) {
        selection=new NsgaSelection(checkpoint);size=pool.size();
        if(size==0)throw new IllegalArgumentException("Empty mating pool");scores=ranked?selection.score(pool):null;
    }
    public int draw() {return scores==null?SeededRandom.current().nextInt(size):selection.tournament(scores);}
}
