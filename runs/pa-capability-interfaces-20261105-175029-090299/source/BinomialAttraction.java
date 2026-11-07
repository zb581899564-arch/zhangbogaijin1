package org.uma.jmetal.util.research.modelglobal;

/** paGOMEA Eq3.14 for the explicit null pi=1/factories. Not a calibrated test of our initialization. */
public final class BinomialAttraction {
    private final int population, factories;
    private final double[] lower, upper;

    public BinomialAttraction(int size, int count) {
        if (size <= 0 || count < 2) throw new IllegalArgumentException("Positive population and at least2factories required");
        population = size; factories = count;
        double p = 1.0 / count; double[] weights = new double[size + 1];
        int mode = (int)Math.floor((size + 1.0) * p); weights[mode] = 1;
        for (int k = mode; k > 0; k--)
            weights[k - 1] = weights[k] * k / (size - k + 1.0) * (1 - p) / p;
        for (int k = mode; k < size; k++)
            weights[k + 1] = weights[k] * (size - k) / (k + 1.0) * p / (1 - p);
        double total = 0; for (double w : weights) total += w;
        lower = new double[size + 1]; upper = new double[size + 1];
        double sum = 0; for (int k = 0; k <= size; k++) { sum += weights[k] / total; lower[k] = sum; }
        sum = 0; for (int k = size; k >= 0; k--) { upper[k] = sum; sum += weights[k] / total; }
    }

    public boolean attracts(int sameCount) { check(sameCount); return (long)sameCount * factories > population; }

    public double value(int sameCount) {
        check(sameCount); int meanFloor = population / factories;
        double ratio = attracts(sameCount) ? upper[sameCount] / upper[meanFloor] : lower[sameCount] / lower[meanFloor];
        double result = 1 - ratio;
        if (!Double.isFinite(result) || result < -1e-12 || result > 1 + 1e-12)
            throw new ArithmeticException("Invalid normalized binomial tail");
        return Math.max(0, Math.min(1, result));
    }

    private void check(int count) {
        if (count < 0 || count > population) throw new IllegalArgumentException("Invalid same-factory count");
    }
}
