package org.uma.jmetal.util.research.modelglobal;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.PriorityQueue;

/** Average-linkage hierarchy with explicit lexicographic ties, including root. O(N^2 log N). */
public final class LinkageHierarchy {
    private final List<int[]> subsets = new ArrayList<>();

    private static final class Edge implements Comparable<Edge> {
        final int a, b; final double score; final int[] left, right;
        Edge(int first, int second, double value, int[][] jobs) {
            boolean ordered = lex(jobs[first], jobs[second]) < 0;
            a = ordered ? first : second; b = ordered ? second : first;
            left = jobs[a]; right = jobs[b]; score = value;
        }
        public int compareTo(Edge other) {
            int result = Double.compare(other.score, score);
            if (result == 0) result = lex(left, other.left);
            return result != 0 ? result : lex(right, other.right);
        }
    }

    public LinkageHierarchy(double[][] dependency) {
        if (dependency == null || dependency.length == 0) throw new IllegalArgumentException("Nonempty matrix required");
        int n = dependency.length, capacity = 2 * n - 1;
        double[][] scores = new double[capacity][capacity]; int[][] jobs = new int[capacity][];
        boolean[] active = new boolean[capacity]; PriorityQueue<Edge> queue = new PriorityQueue<>();
        for (double[] row : dependency) if (row == null || row.length != n) throw new IllegalArgumentException("Square matrix required");
        for (int i = 0; i < n; i++) {
            jobs[i] = new int[]{i}; active[i] = true; subsets.add(jobs[i]);
            for (int j = i + 1; j < n; j++) {
                double value = dependency[i][j];
                if (!Double.isFinite(value) || value < 0 || value > 1 || value != dependency[j][i])
                    throw new IllegalArgumentException("Symmetric finite dependency in [0,1] required");
                scores[i][j] = scores[j][i] = value;
            }
        }
        for (int i = 0; i < n; i++) for (int j = i + 1; j < n; j++) queue.add(new Edge(i, j, scores[i][j], jobs));
        for (int next = n; next < capacity; next++) {
            Edge edge; do { edge = queue.remove(); } while (!active[edge.a] || !active[edge.b]);
            int a = edge.a, b = edge.b; active[a] = active[b] = false; active[next] = true;
            jobs[next] = new int[jobs[a].length + jobs[b].length];
            System.arraycopy(jobs[a], 0, jobs[next], 0, jobs[a].length);
            System.arraycopy(jobs[b], 0, jobs[next], jobs[a].length, jobs[b].length); Arrays.sort(jobs[next]);
            subsets.add(jobs[next]);
            for (int k = 0; k < next; k++) if (active[k]) {
                double value = (jobs[a].length * scores[a][k] + jobs[b].length * scores[b][k]) / jobs[next].length;
                scores[next][k] = scores[k][next] = value; queue.add(new Edge(next, k, value, jobs));
            }
        }
    }

    public List<int[]> subsets() {
        List<int[]> result = new ArrayList<>(); for (int[] jobs : subsets) result.add(jobs.clone()); return result;
    }

    private static int lex(int[] a, int[] b) {
        for (int i = 0; i < Math.min(a.length, b.length); i++) if (a[i] != b[i]) return Integer.compare(a[i], b[i]);
        return Integer.compare(a.length, b.length);
    }
}
