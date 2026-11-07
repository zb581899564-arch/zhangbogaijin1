package org.uma.jmetal.util.research.classic;

import java.util.ArrayList;
import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Deb et al. (2002): nondominated fronts and normalized crowding elitism. */
final class NsgaSelection {
    static final class Scores {
        final int[] rank;
        final double[] crowding;
        final List<List<Integer>> fronts;
        Scores(int size, List<List<Integer>> fronts) {
            rank = new int[size]; crowding = new double[size]; this.fronts = fronts;
        }
    }
    static final class Selection {
        final List<PermutationSolution<Integer>> population;
        final Scores scores;
        Selection(List<PermutationSolution<Integer>> population, Scores scores) { this.population = population; this.scores = scores; }
    }
    private final Runnable checkpoint;
    NsgaSelection(Runnable checkpoint) { this.checkpoint = checkpoint; }

    Scores score(List<PermutationSolution<Integer>> pool) {
        List<List<Integer>> dominated = new ArrayList<>(), fronts = new ArrayList<>();
        int n = pool.size(); int[] incoming = new int[n];
        for (int i = 0; i < n; i++) dominated.add(new ArrayList<>());
        for (int i = 0; i < n; i++) {
            checkpoint.run();
            for (int j = i + 1; j < n; j++) {
                if (ClassicTools.dominates(pool.get(i), pool.get(j))) { dominated.get(i).add(j); incoming[j]++; }
                else if (ClassicTools.dominates(pool.get(j), pool.get(i))) { dominated.get(j).add(i); incoming[i]++; }
            }
        }
        List<Integer> current = new ArrayList<>();
        for (int i = 0; i < n; i++) if (incoming[i] == 0) current.add(i);
        Scores result = new Scores(n, fronts);
        while (!current.isEmpty()) {
            checkpoint.run();
            int rank = fronts.size(); fronts.add(current);
            List<Integer> next = new ArrayList<>();
            for (int i : current) {
                result.rank[i] = rank;
                for (int j : dominated.get(i)) if (--incoming[j] == 0) next.add(j);
            }
            crowding(pool, current, result.crowding); current = next;
        }
        return result;
    }

    List<PermutationSolution<Integer>> select(List<PermutationSolution<Integer>> pool, int size) {
        return environmental(pool, size).population;
    }

    Selection environmental(List<PermutationSolution<Integer>> pool, int size) {
        Scores scores = score(pool);
        List<Integer> selected = new ArrayList<>();
        for (List<Integer> front : scores.fronts) {
            checkpoint.run();
            List<Integer> order = new ArrayList<>(front);
            if (selected.size() + front.size() > size) order.sort((a, b) -> {
                checkpoint.run(); int c = Double.compare(scores.crowding[b], scores.crowding[a]);
                return c == 0 ? Integer.compare(a, b) : c;
            });
            for (int index : order) {
                if (selected.size() == size) return retain(pool, selected, scores);
                selected.add(index);
            }
        }
        return retain(pool, selected, scores);
    }

    private Selection retain(List<PermutationSolution<Integer>> pool, List<Integer> selected, Scores original) {
        List<PermutationSolution<Integer>> population = new ArrayList<>();
        Scores retained = new Scores(selected.size(), new ArrayList<>());
        for (int p = 0; p < selected.size(); p++) {
            int index = selected.get(p); population.add(pool.get(index));
            retained.rank[p] = original.rank[index]; retained.crowding[p] = original.crowding[index];
        }
        // Carry the union-front distances into mating, as in Deb et al. Algorithm C;
        // recomputing on the truncated population would change the crowded tournament.
        return new Selection(population, retained);
    }

    int tournament(Scores scores) {
        int a = SeededRandom.current().nextInt(scores.rank.length), b = SeededRandom.current().nextInt(scores.rank.length);
        if (scores.rank[a] != scores.rank[b]) return scores.rank[a] < scores.rank[b] ? a : b;
        int c = Double.compare(scores.crowding[a], scores.crowding[b]);
        return c == 0 ? (SeededRandom.current().nextBoolean() ? a : b) : c > 0 ? a : b;
    }

    private void crowding(List<PermutationSolution<Integer>> pool, List<Integer> front, double[] distances) {
        if (front.size() <= 2) { for (int i : front) distances[i] = Double.POSITIVE_INFINITY; return; }
        for (int objective = 0; objective < 3; objective++) {
            checkpoint.run(); final int m = objective;
            List<Integer> order = new ArrayList<>(front);
            order.sort((a, b) -> { checkpoint.run(); int c = Double.compare(pool.get(a).getObjective(m), pool.get(b).getObjective(m));
                return c == 0 ? Integer.compare(a, b) : c; });
            double low = pool.get(order.get(0)).getObjective(m), high = pool.get(order.get(order.size() - 1)).getObjective(m);
            distances[order.get(0)] = distances[order.get(order.size() - 1)] = Double.POSITIVE_INFINITY;
            // Keep the boundary policy; a constant objective adds zero internally instead of 0/0.
            if (high == low) continue;
            for (int p = 1; p < order.size() - 1; p++) distances[order.get(p)] +=
                    (pool.get(order.get(p + 1)).getObjective(m) - pool.get(order.get(p - 1)).getObjective(m)) / (high - low);
        }
    }
}
