package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;

/** Paired global survival: preserve each lineage/family while making CENTER diversity explicit. */
public final class GlobalBatchPolicy {
    private static final String MODE = System.getProperty("research.batch.mode", "FORCE");
    private static final Map<String,Long> counts = new LinkedHashMap<>();
    private GlobalBatchPolicy() { }
    private static void count(String k) { counts.put(k, counts.getOrDefault(k, 0L) + 1); }

    static List<Particle> select(List<Particle> parents, List<Particle> children, Direction role) {
        if (parents.size() != children.size()) throw new IllegalArgumentException("Unpaired batch");
        List<PermutationSolution<Integer>> reference = new ArrayList<>();
        for (Particle p : parents) reference.add(p.current);
        if (MODE.equals("FORCE")) return children;
        boolean crowd = MODE.equals("ROLE_CROWD") || MODE.equals("ALL_CROWD");
        boolean ranked = MODE.equals("ROLE_RANK") || crowd;
        if (!ranked && !MODE.equals("ROLE_GREEDY")) throw new IllegalArgumentException("Unknown batch survival");
        boolean multiobjective = ranked && (role == Direction.CENTER || MODE.equals("ALL_CROWD"));
        List<PermutationSolution<Integer>> pool = new ArrayList<>(reference);
        for (Particle p : children) pool.add(p.current);
        int[] rank = multiobjective ? ranks(pool) : null;
        double[] distance = multiobjective && crowd ? crowding(pool, rank) : null;
        List<Particle> next = new ArrayList<>();
        for (int i = 0; i < parents.size(); i++) {
            PermutationSolution<Integer> old = parents.get(i).current, child = children.get(i).current;
            int j = i + parents.size(); boolean accept;
            count("paid." + role.name());
            if (multiobjective) {
                boolean tie = rank[j] == rank[i];
                if (tie) count("rankTie." + role.name());
                accept = rank[j] < rank[i] || tie && crowd && !Arrays.equals(old.getObjectives(), child.getObjectives())
                        && distance[j] > distance[i];
                if (accept && tie) count("crowdingAccepted." + role.name());
            } else accept = LocalPddrKernel.better(role, child, old, reference);
            count((accept ? "accepted." : "rejected.") + role.name());
            next.add(accept ? children.get(i) : parents.get(i));
        }
        return next;
    }

    static int[] ranks(List<PermutationSolution<Integer>> points) {
        int n = points.size(); int[] degree = new int[n], rank = new int[n];
        List<List<Integer>> dominates = new ArrayList<>();
        for (int i = 0; i < n; i++) dominates.add(new ArrayList<>());
        List<Integer> front = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                if (ParetoTools.dominates(points.get(i), points.get(j))) dominates.get(i).add(j);
                if (ParetoTools.dominates(points.get(j), points.get(i))) degree[i]++;
            }
            if (degree[i] == 0) front.add(i);
        }
        int level = 0;
        while (!front.isEmpty()) {
            List<Integer> next = new ArrayList<>();
            for (int i : front) {
                rank[i] = level;
                for (int j : dominates.get(i)) if (--degree[j] == 0) next.add(j);
            }
            front = next; level++;
        }
        return rank;
    }

    static double[] crowding(List<PermutationSolution<Integer>> points, int[] ranks) {
        double[] result = new double[points.size()]; int max = Arrays.stream(ranks).max().orElse(0);
        for (int level = 0; level <= max; level++) {
            // Objective duplicates receive identical distances, independent of parent/child ordering.
            Map<String,List<Integer>> copies = new LinkedHashMap<>();
            for (int i = 0; i < points.size(); i++) if (ranks[i] == level)
                copies.computeIfAbsent(Arrays.toString(points.get(i).getObjectives()), x -> new ArrayList<>()).add(i);
            List<Integer> unique = new ArrayList<>(); for (List<Integer> ids : copies.values()) unique.add(ids.get(0));
            double[] distance = new double[points.size()];
            for (int objective = 0; objective < 3; objective++) {
                final int k = objective; unique.sort(Comparator.comparingDouble(i -> points.get(i).getObjective(k)));
                if (unique.isEmpty()) continue;
                int first = unique.get(0), last = unique.get(unique.size() - 1);
                double span = points.get(last).getObjective(k) - points.get(first).getObjective(k);
                if (span == 0) continue;
                distance[first] = distance[last] = Double.POSITIVE_INFINITY;
                for (int p = 1; p + 1 < unique.size(); p++) distance[unique.get(p)] +=
                        (points.get(unique.get(p + 1)).getObjective(k) - points.get(unique.get(p - 1)).getObjective(k)) / span;
            }
            for (List<Integer> ids : copies.values()) for (int i : ids) result[i] = distance[ids.get(0)];
        }
        return result;
    }

    public static Map<String,Object> diagnostics() {
        Map<String,Object> out = new LinkedHashMap<>(); out.put("mode", MODE); out.put("counts", counts); return out;
    }
}
