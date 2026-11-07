package org.uma.jmetal.util.research.search;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.ArrayList;
import org.uma.jmetal.solution.PermutationSolution;

/** Diagnostic only: swap one reference block on the exact same candidate/incumbent pair. */
final class CenterRoleSwapProbe {
    private static final String[] ROLES = {"MAKESPAN", "CENTER", "ENERGY", "WORKER_COST"};
    private static final int[] SIZES = {15, 55, 15, 15};
    private static final int[][] PARTITIONS = partitions();
    private final int[][][] delta = new int[PARTITIONS.length][4][4];
    private final int[] base = new int[4], other = new int[4], a = new int[4], b = new int[4];
    private final long[][][] counts = new long[PARTITIONS.length][4][4];
    private long fullFlips;

    void observe(PermutationSolution<Integer> candidate, PermutationSolution<Integer> incumbent,
            List<PermutationSolution<Integer>> actual, List<PermutationSolution<Integer>> alternate,
            boolean accept, boolean alternateAccept) {
        if (actual.size() != 100 || alternate.size() != 100) throw new IllegalStateException("Unexpected block sizes");
        Arrays.fill(base, 0); Arrays.fill(other, 0);
        for (int[][] partition : delta) for (int[] role : partition) Arrays.fill(role, 0);
        for (int i = 0; i < actual.size(); i++) {
            countsAgainst(candidate, incumbent, actual.get(i), a);
            countsAgainst(candidate, incumbent, alternate.get(i), b);
            for (int j = 0; j < 4; j++) {
                base[j] += a[j]; other[j] += b[j];
                int change = b[j] - a[j];
                for (int p = 0; p < PARTITIONS.length; p++) delta[p][PARTITIONS[p][i]][j] += change;
            }
        }
        if (ParetoTools.dominates(candidate, incumbent)) { base[0]++; base[3]++; other[0]++; other[3]++; }
        if (ParetoTools.dominates(incumbent, candidate)) { base[1]++; base[2]++; other[1]++; other[2]++; }
        if (decide(base, a, 0) != accept || decide(other, a, 0) != alternateAccept)
            throw new IllegalStateException("Block probe does not reproduce full decisions");
        boolean full = accept != alternateAccept;
        if (full) fullFlips++;
        for (int p = 0; p < PARTITIONS.length; p++) for (int g = 0; g < 4; g++) {
            boolean single = decide(base, delta[p][g], 1);
            boolean without = decide(other, delta[p][g], -1);
            if (single != accept) {
                counts[p][g][0]++;
                if (full) counts[p][g][1]++;
                if (single) counts[p][g][3]++;
            }
            if (full && without == accept) counts[p][g][2]++;
        }
    }

    List<Map<String, Object>> summary() {
        List<Map<String, Object>> rows = new ArrayList<>();
        for (int p = 0; p < PARTITIONS.length; p++) for (int g = 0; g < 4; g++) {
            long[] n = counts[p][g];
            rows.add(ReverseAudit.row("partition", p == 0 ? "physical" : "mixed-" + p,
                    "block", ROLES[g], "size", SIZES[g], "fullFlips", fullFlips,
                    "singleFlips", n[0], "singleRecoversFullFlips", n[1],
                    "restoringBlockCancelsFullFlips", n[2], "singleRejectToAccept", n[3]));
        }
        return rows;
    }

    private static void countsAgainst(PermutationSolution<Integer> c, PermutationSolution<Integer> i,
            PermutationSolution<Integer> r, int[] out) {
        out[0] = ParetoTools.dominates(c, r) ? 1 : 0;
        out[1] = ParetoTools.dominates(r, c) ? 1 : 0;
        out[2] = ParetoTools.dominates(i, r) ? 1 : 0;
        out[3] = ParetoTools.dominates(r, i) ? 1 : 0;
    }
    private static boolean decide(int[] x, int[] difference, int sign) {
        return x[1] + sign * difference[1] + 1.0 / (1 + x[0] + sign * difference[0])
                < x[3] + sign * difference[3] + 1.0 / (1 + x[2] + sign * difference[2]);
    }
    private static int[][] partitions() {
        int[][] result = new int[4][100];
        int i = 0;
        for (int g = 0; g < SIZES.length; g++) for (int n = 0; n < SIZES[g]; n++) result[0][i++] = g;
        int[] stride = {37, 43, 57}, offset = {11, 23, 61};
        for (int p = 1; p < result.length; p++) for (int j = 0; j < 100; j++)
            result[p][(stride[p - 1] * j + offset[p - 1]) % 100] = result[0][j];
        return result;
    }
}
