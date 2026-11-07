package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** Exact three-objective minimization volume; no scheduling or objective evaluation. */
final class ProgramExitHv3D {
    private ProgramExitHv3D() { }

    static double volume(double[][] input, double reference) {
        List<double[]> valid = new ArrayList<>();
        for (double[] point : input) {
            if (point.length != 3) throw new IllegalArgumentException("Exactly three objectives required");
            boolean inside = true;
            for (double value : point) {
                if (!Double.isFinite(value) || value < 0) throw new IllegalArgumentException("Invalid normalized objective");
                inside &= value < reference;
            }
            if (inside) valid.add(point);
        }
        double[][] points = valid.toArray(new double[valid.size()][]);
        Arrays.sort(points, (a, b) -> {
            for (int d = 0; d < 3; d++) { int result = Double.compare(a[d], b[d]);if (result != 0) return result; }
            return 0;
        });
        List<Double> ys = new ArrayList<>(), zs = new ArrayList<>();
        double area = 0, total = 0, previousX = 0;
        for (double[] point : points) {
            double x = point[0], y = point[1], z = point[2];
            total += (x - previousX) * area;previousX = x;
            int index = lowerBound(ys, y);
            if (index > 0 && zs.get(index - 1) <= z || index < ys.size() && ys.get(index) == y && zs.get(index) <= z) continue;
            double oldZ = index > 0 ? zs.get(index - 1) : reference, lastY = y, gain = 0;
            int end = index;
            while (end < ys.size() && zs.get(end) >= z) {
                gain += (ys.get(end) - lastY) * (oldZ - z);lastY = ys.get(end);oldZ = zs.get(end);end++;
            }
            double nextY = end < ys.size() ? ys.get(end) : reference;
            gain += (nextY - lastY) * (oldZ - z);area += gain;
            ys.subList(index, end).clear();zs.subList(index, end).clear();ys.add(index, y);zs.add(index, z);
        }
        return total + (reference - previousX) * area;
    }

    static double[][] nondominated(double[][] points) {
        List<double[]> result = new ArrayList<>();
        for (int i = 0; i < points.length; i++) {
            boolean remove = false;
            for (int j = 0; j < points.length && !remove; j++) {
                if (i == j) continue;
                boolean all = true, strict = false;
                for (int d = 0; d < 3; d++) { all &= points[j][d] <= points[i][d];strict |= points[j][d] < points[i][d]; }
                remove = all && (strict || j < i);
            }
            if (!remove) result.add(points[i]);
        }
        return result.toArray(new double[result.size()][]);
    }

    private static int lowerBound(List<Double> values, double value) {
        int left = 0, right = values.size();
        while (left < right) { int middle = (left + right) >>> 1;if (values.get(middle) < value) left = middle + 1;else right = middle; }
        return left;
    }
}
