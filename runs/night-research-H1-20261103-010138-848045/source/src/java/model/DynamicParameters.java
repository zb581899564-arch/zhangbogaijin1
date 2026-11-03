package org.uma.jmetal.util.research.model;

import java.io.Serializable;
import java.util.Arrays;

/** Immutable, explicitly sourced fatigue parameters, indexed by factory/stage/worker. */
public final class DynamicParameters implements Serializable {
    private static final long serialVersionUID = 1L;
    private final double[][][] alpha, mu, beta, h0;
    private final String source;

    public DynamicParameters(double[][][] alpha, double[][][] mu, double[][][] beta,
            double[][][] h0, String source) {
        if (source == null || source.trim().isEmpty()) {
            throw new IllegalArgumentException("Fatigue parameter source is required");
        }
        this.alpha = copy(alpha, "alpha", false);
        this.mu = copy(mu, "mu", false);
        this.beta = copy(beta, "beta", false);
        this.h0 = copy(h0, "h0", true);
        this.source = source;
        sameDimensions(this.alpha, this.mu);
        sameDimensions(this.alpha, this.beta);
        sameDimensions(this.alpha, this.h0);
    }

    public static DynamicParameters uniform(Instance in, double alpha, double mu,
            double beta, double h0) {
        double[][][][] fields = new double[4][][][];
        double[] values = {alpha, mu, beta, h0};
        for (int x = 0; x < fields.length; x++) {
            fields[x] = new double[in.factories()][in.stages()][];
            for (int f = 0; f < in.factories(); f++) for (int k = 0; k < in.stages(); k++) {
                fields[x][f][k] = new double[in.workers(f, k)];
                Arrays.fill(fields[x][f][k], values[x]);
            }
        }
        return new DynamicParameters(fields[0], fields[1], fields[2], fields[3],
                "RECONSTRUCTED-UNIFORM; alpha=" + alpha + "; mu=" + mu
                + "; beta=" + beta + "; h0=" + h0);
    }

    public double alpha(int f, int k, int w) { return alpha[f][k][w]; }
    public double mu(int f, int k, int w) { return mu[f][k][w]; }
    public double beta(int f, int k, int w) { return beta[f][k][w]; }
    public double h0(int f, int k, int w) { return h0[f][k][w]; }
    public String source() { return source; }

    void validateFor(Instance in) {
        if (in == null || in.kind() != ModelKind.CHAPTER4_DUAL_RESOURCE) {
            throw new IllegalArgumentException("Dynamic model requires a chapter4 dual-resource instance");
        }
        if (alpha.length != in.factories()) throw new IllegalArgumentException("Fatigue factory count differs");
        for (int f = 0; f < in.factories(); f++) {
            if (alpha[f].length != in.stages()) throw new IllegalArgumentException("Fatigue stage count differs");
            for (int k = 0; k < in.stages(); k++) if (alpha[f][k].length != in.workers(f, k)) {
                throw new IllegalArgumentException("Fatigue worker count differs");
            }
        }
    }

    boolean sameValues(DynamicParameters other) {
        return this == other || other != null && source.equals(other.source)
                && Arrays.deepEquals(alpha, other.alpha) && Arrays.deepEquals(mu, other.mu)
                && Arrays.deepEquals(beta, other.beta) && Arrays.deepEquals(h0, other.h0);
    }

    private static double[][][] copy(double[][][] values, String name, boolean bounded) {
        if (values == null || values.length == 0) throw new IllegalArgumentException("Empty " + name);
        double[][][] result = new double[values.length][][];
        for (int f = 0; f < values.length; f++) {
            if (values[f] == null || values[f].length == 0) throw new IllegalArgumentException("Empty " + name);
            result[f] = new double[values[f].length][];
            for (int k = 0; k < values[f].length; k++) {
                if (values[f][k] == null || values[f][k].length == 0) throw new IllegalArgumentException("Empty " + name);
                result[f][k] = values[f][k].clone();
                for (double v : result[f][k]) if (!Double.isFinite(v) || v < 0 || bounded && v > 1) {
                    throw new IllegalArgumentException("Invalid " + name);
                }
            }
        }
        return result;
    }

    private static void sameDimensions(double[][][] a, double[][][] b) {
        if (a.length != b.length) throw new IllegalArgumentException("Fatigue dimensions differ");
        for (int f = 0; f < a.length; f++) {
            if (a[f].length != b[f].length) throw new IllegalArgumentException("Fatigue dimensions differ");
            for (int k = 0; k < a[f].length; k++) if (a[f][k].length != b[f][k].length) {
                throw new IllegalArgumentException("Fatigue dimensions differ");
            }
        }
    }
}
