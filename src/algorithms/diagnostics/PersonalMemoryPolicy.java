package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Parameter-free CENTER ND-history tie policies. Other objective directions keep their original rule. */
public final class PersonalMemoryPolicy {
    private static final String MODE=System.getProperty("research.personal.mode","OLDEST");
    private static long centerCalls,historySizes,latestDiffersFromOldest;
    private PersonalMemoryPolicy() { }
    @SuppressWarnings("unchecked")
    static PermutationSolution<Integer> choose(PermutationSolution<Integer> current,
            List<PermutationSolution<Integer>> history,Direction direction) {
        if(direction!=Direction.CENTER)return ParetoTools.copy(history.get(ParetoTools.order(history,direction).get(0)));
        centerCalls++;historySizes+=history.size();if(history.size()>1)latestDiffersFromOldest++;
        PermutationSolution<Integer> value;
        switch(MODE) {
            // Own personal history is maintained ND, so all its PDDR scores tie exactly.
            // First insertion is equivalent to the frozen stable PDDR sort, at O(1) cost.
            case "OLDEST":value=history.get(0);break;
            case "LATEST":value=history.get(history.size()-1);break;
            case "CURRENT":value=current;break;
            case "UNIFORM":value=history.get(SeededRandom.current().nextInt(history.size()));break;
            default:throw new IllegalArgumentException("Unknown personal memory policy "+MODE);
        }
        return (PermutationSolution<Integer>)value.copy();
    }
    public static Map<String,Object> diagnostics() {
        Map<String,Object> out=new LinkedHashMap<>();out.put("mode",MODE);out.put("centerCalls",centerCalls);
        out.put("historySizeSum",historySizes);out.put("nontrivialHistoryCalls",latestDiffersFromOldest);return out;
    }
}
