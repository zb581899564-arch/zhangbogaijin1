package org.uma.jmetal.util.research.classic;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;

/** TIK 103 sections 3.1/3.2: strength + density, then distance-vector truncation. */
final class SpeaSelection {
    static final class Scores {
        final int[] strength, raw;
        final double[] density, fitness;
        final double[][] distance;
        Scores(int n) {
            strength = new int[n]; raw = new int[n]; density = new double[n];
            fitness = new double[n]; distance = new double[n][n];
        }
    }
    private final Runnable checkpoint;
    private final double[] scale;
    SpeaSelection(Runnable checkpoint) { this(new double[] {1,1,1}, checkpoint); }
    SpeaSelection(double[] frozenScale, Runnable checkpoint) {
        this.checkpoint = checkpoint; scale = frozenScale.clone();
        if (scale.length != 3) throw new IllegalArgumentException("Three objective scales required");
        for (double value : scale) if (!Double.isFinite(value) || value <= 0) throw new IllegalArgumentException("Positive finite scales required");
    }

    Scores score(List<PermutationSolution<Integer>> pool) {
        int n = pool.size(); Scores result = new Scores(n);
        boolean[][] dominates = new boolean[n][n];
        for (int i = 0; i < n; i++) {
            checkpoint.run();
            for (int j = 0; j < n; j++) if (i != j) {
                dominates[i][j] = ClassicTools.dominates(pool.get(i), pool.get(j));
                if (dominates[i][j]) result.strength[i]++;
                double sum = 0;
                for (int m = 0; m < 3; m++) sum = Math.hypot(sum, (pool.get(i).getObjective(m) - pool.get(j).getObjective(m)) / scale[m]);
                result.distance[i][j] = sum;
            }
        }
        int k = Math.min(n - 1, Math.max(1, (int) Math.sqrt(n)));
        for (int i = 0; i < n; i++) {
            checkpoint.run();
            for (int j = 0; j < n; j++) if (dominates[j][i]) result.raw[i] += result.strength[j];
            double[] sorted = new double[Math.max(0, n - 1)]; int p = 0;
            for (int j = 0; j < n; j++) if (j != i) sorted[p++] = result.distance[i][j];
            Arrays.sort(sorted);
            result.density[i] = n <= 1 ? 0 : 1 / (sorted[k - 1] + 2);
            result.fitness[i] = result.raw[i] + result.density[i];
        }
        return result;
    }

    List<Integer> select(Scores scores, int capacity) {
        List<Integer> selected = new ArrayList<>();
        for (int i = 0; i < scores.fitness.length; i++) if (scores.fitness[i] < 1) selected.add(i);
        if (selected.size() > capacity) truncate(selected, capacity, scores.distance);
        else if (selected.size() < capacity) {
            List<Integer> dominated = new ArrayList<>();
            for (int i = 0; i < scores.fitness.length; i++) if (scores.fitness[i] >= 1) dominated.add(i);
            dominated.sort((a, b) -> { checkpoint.run(); int c = Double.compare(scores.fitness[a], scores.fitness[b]);
                return c == 0 ? Integer.compare(a, b) : c; });
            for (int index : dominated) { if (selected.size() == capacity) break; selected.add(index); }
        }
        return selected;
    }

    private void truncate(List<Integer> active, int capacity, double[][] distance) {
        while (active.size() > capacity) {
            checkpoint.run();
            int removeAt = 0; double[] smallest = neighbors(active, active.get(0), distance);
            for (int p = 1; p < active.size(); p++) {
                checkpoint.run();
                double[] candidate = neighbors(active, active.get(p), distance);
                if (lexicographic(candidate, smallest) < 0) { smallest = candidate; removeAt = p; }
            }
            active.remove(removeAt);
        }
    }
    private double[] neighbors(List<Integer> active, int index, double[][] distance) {
        double[] result = new double[active.size() - 1]; int p = 0;
        for (int other : active) if (other != index) result[p++] = distance[index][other];
        Arrays.sort(result); return result;
    }
    private static int lexicographic(double[] a, double[] b) {
        for (int k = 0; k < a.length; k++) { int c = Double.compare(a[k], b[k]); if (c != 0) return c; }
        return 0;
    }
}
