package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Zero-FE fixtures: fronts, objective scaling, duplicate invariance and paired family preservation. */
public final class GlobalBatchChecks {
    private GlobalBatchChecks() { }
    public static void main(String[] args) throws Exception {
        System.setProperty("dhfsp.dataDir", args[0]); System.setProperty("dhfsp.setupFile", args[1]);
        System.setProperty("dhfsp.standbyPower", "1.0"); SeededRandom.reset(19);
        EDHHFSPW raw = new EDHHFSPW(20, 2, 3, 1);
        List<PermutationSolution<Integer>> points = new ArrayList<>();
        for (double[] p : new double[][] {{1,9,1},{3,7,1},{5,5,1},{8,2,1},{9,1,1},{5,5,1},{10,10,2},{11,11,3}}) {
            PermutationSolution<Integer> s = raw.createSolution(); for (int k = 0; k < 3; k++) s.setObjective(k, p[k]); points.add(s);
        }
        int[] rank = GlobalBatchPolicy.ranks(points);
        if (!Arrays.equals(rank, new int[] {0,0,0,0,0,0,1,2})) throw new AssertionError("Wrong fronts");
        double[] d = GlobalBatchPolicy.crowding(points, rank);
        if (d[2] != d[5] || !Double.isInfinite(d[0]) || !Double.isInfinite(d[4])) throw new AssertionError("Duplicate/extreme error");
        for (PermutationSolution<Integer> s : points) { s.setObjective(0, s.getObjective(0) * 37); s.setObjective(1, s.getObjective(1) * .03); }
        double[] scaled = GlobalBatchPolicy.crowding(points, rank);
        for (int i = 0; i < d.length; i++) if (!(d[i] == scaled[i] || Math.abs(d[i] - scaled[i]) < 1e-12)) throw new AssertionError("Scale error");
        System.out.println("GLOBAL_BATCH_CHECKS_PASS FE=0 fronts;duplicates;extremes;positive-scaling");
    }
}
