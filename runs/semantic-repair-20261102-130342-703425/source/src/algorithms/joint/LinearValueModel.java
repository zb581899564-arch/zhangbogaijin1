package org.uma.jmetal.util.research.joint;

import java.util.List;

/** Small weighted ridge solve. The intercept is unregularized; predictions cannot be negative. */
final class LinearValueModel {
    static final double RIDGE = .001;
    private LinearValueModel() { }
    static double predict(double[] coefficients, double[] features) {
        double result = coefficients[0];
        for (int i = 0; i < features.length; i++) result += coefficients[i + 1] * features[i];
        if (!Double.isFinite(result)) throw new IllegalStateException("Non-finite value prediction");
        return Math.max(0, result);
    }
    static double[] fit(List<Sample> samples, int dimension, Runnable checkpoint) {
        if (samples.isEmpty()) throw new IllegalArgumentException("No completed trajectories to fit");
        double[][] normal = new double[dimension + 1][dimension + 2];
        for (Sample sample : samples) {
            checkpoint.run();
            if (sample.features.length != dimension || !Double.isFinite(sample.target)
                    || !Double.isFinite(sample.weight) || sample.weight <= 0) {
                throw new IllegalArgumentException("Invalid value sample");
            }
            for (int r = 0; r <= dimension; r++) {
                double x = r == 0 ? 1 : sample.features[r - 1];
                if (!Double.isFinite(x)) throw new IllegalArgumentException("Non-finite feature");
                for (int c = 0; c <= dimension; c++) {
                    double y = c == 0 ? 1 : sample.features[c - 1];
                    normal[r][c] += sample.weight * x * y;
                }
                normal[r][dimension + 1] += sample.weight * x * sample.target;
            }
        }
        for (int i = 1; i <= dimension; i++) normal[i][i] += RIDGE;
        return solve(normal, checkpoint);
    }
    private static double[] solve(double[][] matrix, Runnable checkpoint) {
        int n = matrix.length;
        for (int c = 0; c < n; c++) {
            checkpoint.run(); int pivot = c;
            for (int r = c + 1; r < n; r++) if (Math.abs(matrix[r][c]) > Math.abs(matrix[pivot][c])) pivot = r;
            if (!(Math.abs(matrix[pivot][c]) > 1e-14)) throw new IllegalStateException("Singular regularized value regression");
            double[] row = matrix[c]; matrix[c] = matrix[pivot]; matrix[pivot] = row;
            double divisor = matrix[c][c];
            for (int k = c; k <= n; k++) matrix[c][k] /= divisor;
            for (int r = 0; r < n; r++) if (r != c) {
                double factor = matrix[r][c];
                for (int k = c; k <= n; k++) matrix[r][k] -= factor * matrix[c][k];
            }
        }
        double[] coefficients = new double[n];
        for (int i = 0; i < n; i++) {
            coefficients[i] = matrix[i][n];
            if (!Double.isFinite(coefficients[i])) throw new IllegalStateException("Non-finite fitted value model");
        }
        return coefficients;
    }
    static final class Sample {
        final double[] features; final double target, weight;
        Sample(double[] features, double target, double weight) {
            this.features = features.clone(); this.target = target; this.weight = weight;
        }
    }
}
