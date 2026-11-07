package org.uma.jmetal.util.research.modelglobal;

/** Independently implemented paGOMEA Eq3.14-3.19, shift mapped explicitly to factory; source weight2/3. */
public final class PaDependencyModel {
    public static final double WEIGHT = 2.0 / 3;
    private final int[][] factories;
    private final double[][] keys;
    private final int count, size, jobs;
    private final int[][] marginal;
    private final BinomialAttraction binomial;

    public PaDependencyModel(int[][] assignments, double[][] priorities, int factoryCount) {
        if (assignments == null || priorities == null || assignments.length == 0 || assignments.length != priorities.length
                || assignments[0] == null || assignments[0].length == 0 || factoryCount < 1)
            throw new IllegalArgumentException("Nonempty matching model input required");
        size = assignments.length; jobs = assignments[0].length; count = factoryCount;
        factories = new int[size][]; keys = new double[size][]; marginal = new int[jobs][count];
        for (int k = 0; k < size; k++) {
            if (assignments[k] == null || priorities[k] == null || assignments[k].length != jobs || priorities[k].length != jobs)
                throw new IllegalArgumentException("Inconsistent model dimensions");
            factories[k] = assignments[k].clone(); keys[k] = priorities[k].clone();
            for (int j = 0; j < jobs; j++) {
                FirstStageCatalog.range(factories[k][j], count, "model factory");
                if (!Double.isFinite(keys[k][j]) || keys[k][j] < 0 || keys[k][j] > 1)
                    throw new IllegalArgumentException("Invalid priority key");
                marginal[j][factories[k][j]]++;
            }
        }
        binomial = count == 1 ? null : new BinomialAttraction(size, count);
    }

    /** Full, statistical, internal, external, same-factory count; no evaluation or learned reward. */
    public double[] components(int a, int b) {
        FirstStageCatalog.range(a, jobs, "job"); FirstStageCatalog.range(b, jobs, "job");
        if (a == b) throw new IllegalArgumentException("Distinct jobs required");
        int same = 0, before = 0; double distance = 0; int[][] joint = new int[count][count];
        for (int k = 0; k < size; k++) {
            int f = factories[k][a], g = factories[k][b]; joint[f][g]++;
            if (f == g) {
                same++; if (keys[k][a] < keys[k][b]) before++;
                double difference = keys[k][a] - keys[k][b]; distance += difference * difference;
            }
        }
        double internal = same == 0 ? 0 : (1 - entropy((double)before / same)) * (1 - distance / same);
        double external = 0;
        if (count > 1) for (int f = 0; f < count; f++) for (int g = 0; g < count; g++) if (joint[f][g] != 0)
            external += (double)joint[f][g] / size * Math.log((double)joint[f][g] * size / marginal[a][f] / marginal[b][g]) / Math.log(count);
        double statistical = count == 1 ? 1 : binomial.value(same);
        double full = count == 1 ? internal : statistical * (WEIGHT + (1 - WEIGHT)
                * (binomial.attracts(same) ? internal : external));
        for (double v : new double[]{internal, external, full}) if (!Double.isFinite(v) || v < -1e-12 || v > 1 + 1e-12)
            throw new ArithmeticException("Dependency outside [0,1]");
        return new double[]{full, statistical, internal, Math.max(0, external), same};
    }

    public double[][] matrix() {
        double[][] out = new double[jobs][jobs];
        for (int a = 0; a < jobs; a++) for (int b = a + 1; b < jobs; b++) out[a][b] = out[b][a] = components(a, b)[0];
        return out;
    }

    private static double entropy(double p) {
        return p == 0 || p == 1 ? 0 : -(p * Math.log(p) + (1 - p) * Math.log(1 - p)) / Math.log(2);
    }
}
