package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;

/** Read-only local PDDR observations. Sampling uses comparison indices, never search RNG. */
public final class AcceptancePlateauTrace {
    private static final boolean ENABLED = Boolean.getBoolean("research.acceptance.trace");
    private static long comparisons, changed, ties, tradeoffs, tradeoffTies, dominating, dominated, accepted;
    private static final List<Map<String,Object>> samples = new ArrayList<>();
    private static final List<double[][]> references = new ArrayList<>();
    private AcceptancePlateauTrace() { }

    static void record(PermutationSolution<Integer> child, PermutationSolution<Integer> parent,
            List<PermutationSolution<Integer>> reference, double childScore, double parentScore, boolean keep) {
        if (!ENABLED) return;
        comparisons++;
        double[] c = objectives(child), p = objectives(parent);
        boolean different = !Arrays.equals(c,p);
        boolean cDominates = ParetoTools.dominates(child,parent);
        boolean pDominates = ParetoTools.dominates(parent,child);
        boolean tradeoff = different && !cDominates && !pDominates;
        boolean tied = childScore == parentScore;
        if (different) changed++;
        if (tied) ties++;
        if (tradeoff) tradeoffs++;
        if (tradeoff && tied) tradeoffTies++;
        if (cDominates) dominating++;
        if (pDominates) dominated++;
        if (keep) accepted++;
        if (comparisons % 257 != 1) return;
        double[][] ref = new double[reference.size()][];
        for (int j=0;j<ref.length;j++) ref[j] = objectives(reference.get(j));
        int id=0;
        while(id<references.size() && !Arrays.deepEquals(references.get(id),ref)) id++;
        if(id==references.size()) references.add(ref);
        Map<String,Object> row=new LinkedHashMap<>();
        row.put("comparison",comparisons);row.put("reference",id);
        row.put("child",c);row.put("parent",p);
        row.put("childScore",childScore);row.put("parentScore",parentScore);
        row.put("tradeoff",tradeoff);row.put("tied",tied);row.put("accepted",keep);
        samples.add(row);
    }

    private static double[] objectives(PermutationSolution<Integer> solution) {
        return new double[]{solution.getObjective(0),solution.getObjective(1),solution.getObjective(2)};
    }

    public static Map<String,Object> diagnostics() {
        Map<String,Object> out=new LinkedHashMap<>();out.put("enabled",ENABLED);
        out.put("comparisons",comparisons);out.put("objectiveChanged",changed);out.put("ties",ties);
        out.put("tradeoffs",tradeoffs);out.put("tradeoffTies",tradeoffTies);
        out.put("dominating",dominating);out.put("dominated",dominated);out.put("accepted",accepted);
        out.put("sampleEvery",257);out.put("samples",samples);out.put("references",references);
        return out;
    }
}
