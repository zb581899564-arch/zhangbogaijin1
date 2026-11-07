package org.uma.jmetal.util.research.model;

/** Immutable numerical instance. Resource ids are local to a factory and stage. */
public final class Instance implements java.io.Serializable {
    private static final long serialVersionUID = 1L;
    private final String name, provenance;
    private final ModelKind kind;
    private final int jobs, stages, factories;
    private final int[][] machines, workers;
    private final double[][] processing, setup;
    private final double[][][] speed, power, standby, efficiency, cost;

    public Instance(String name, ModelKind kind, double[][] processing, double[][] setup,
            double[][][] speed, double[][][] power, double[][][] standby,
            double[][][] efficiency, double[][][] cost, String provenance) {
        if (name == null || kind == null || provenance == null || provenance.trim().isEmpty()) {
            throw new IllegalArgumentException("Instance identity and provenance are required");
        }
        this.name = name;
        this.kind = kind;
        this.provenance = provenance;
        this.processing = copy(processing);
        this.setup = copy(setup);
        this.speed = copy(speed);
        this.power = copy(power);
        this.standby = copy(standby);
        this.efficiency = copy(efficiency);
        this.cost = copy(cost);
        jobs = processing.length;
        if (jobs == 0 || processing[0].length == 0 || speed.length == 0) {
            throw new IllegalArgumentException("Empty instance");
        }
        stages = processing[0].length;
        factories = speed.length;
        machines = new int[factories][stages];
        workers = new int[factories][stages];
        validateDimensions();
    }

    private void validateDimensions() {
        if (setup.length != jobs || power.length != factories || standby.length != factories
                || efficiency.length != factories || cost.length != factories || jobs < factories) {
            throw new IllegalArgumentException("Mismatched instance dimensions");
        }
        for (int j = 0; j < jobs; j++) {
            requireLength(processing[j].length, stages);
            requireLength(setup[j].length, stages);
            for (int k = 0; k < stages; k++) {
                positive(processing[j][k], "processing");
                nonnegative(setup[j][k], "setup");
                if (kind == ModelKind.CHAPTER3_FIXED_WORKER && setup[j][k] != 0) {
                    throw new IllegalArgumentException("Chapter3 has no setup component");
                }
            }
        }
        for (int f = 0; f < factories; f++) {
            requireLength(speed[f].length, stages);
            requireLength(power[f].length, stages);
            requireLength(standby[f].length, stages);
            requireLength(efficiency[f].length, stages);
            requireLength(cost[f].length, stages);
            for (int k = 0; k < stages; k++) {
                machines[f][k] = speed[f][k].length;
                workers[f][k] = efficiency[f][k].length;
                if (machines[f][k] == 0 || workers[f][k] == 0) throw new IllegalArgumentException("Empty resource pool");
                requireLength(power[f][k].length, machines[f][k]);
                requireLength(standby[f][k].length, machines[f][k]);
                requireLength(cost[f][k].length, workers[f][k]);
                for (double v : speed[f][k]) positive(v, "speed");
                for (double v : power[f][k]) nonnegative(v, "power");
                for (double v : standby[f][k]) nonnegative(v, "standby");
                for (double v : efficiency[f][k]) positive(v, "efficiency");
                for (double v : cost[f][k]) nonnegative(v, "cost");
            }
        }
    }

    public String name() { return name; }
    public String provenance() {
        return provenance + (satisfiesDualResourceCondition() ? "" : "; ESWA-Eq8-NOT-SATISFIED: at least one factory has no worker-constrained stage");
    }
    /** Supplied benchmarks may violate ESWA Eq8; expose this rather than altering their resources. */
    public boolean satisfiesDualResourceCondition() {
        if (kind != ModelKind.CHAPTER4_DUAL_RESOURCE) return true;
        for (int f = 0; f < factories; f++) {
            boolean constrained = false;
            for (int k = 0; k < stages; k++) constrained |= workers[f][k] < machines[f][k];
            if (!constrained) return false;
        }
        return true;
    }
    public ModelKind kind() { return kind; }
    public int jobs() { return jobs; }
    public int stages() { return stages; }
    public int factories() { return factories; }
    public int machines(int f, int k) { return machines[f][k]; }
    public int workers(int f, int k) { return workers[f][k]; }
    public double processing(int j, int k) { return processing[j][k]; }
    public double setup(int j, int k) { return setup[j][k]; }
    public double speed(int f, int k, int m) { return speed[f][k][m]; }
    public double power(int f, int k, int m) { return power[f][k][m]; }
    public double standby(int f, int k, int m) { return standby[f][k][m]; }
    public double efficiency(int f, int k, int w) { return efficiency[f][k][w]; }
    public double cost(int f, int k, int w) { return cost[f][k][w]; }
    public double duration(int j, int f, int k, int m, int w) {
        return processing(j, k) / (speed(f, k, m) * efficiency(f, k, w))
                + setup(j, k) / efficiency(f, k, w);
    }

    private static void requireLength(int actual, int expected) {
        if (actual != expected) throw new IllegalArgumentException("Mismatched resource dimensions");
    }
    private static void positive(double v, String name) {
        if (!Double.isFinite(v) || v <= 0) throw new IllegalArgumentException("Invalid " + name);
    }
    private static void nonnegative(double v, String name) {
        if (!Double.isFinite(v) || v < 0) throw new IllegalArgumentException("Invalid " + name);
    }
    private static double[][] copy(double[][] values) {
        double[][] result = new double[values.length][];
        for (int i = 0; i < values.length; i++) result[i] = values[i].clone();
        return result;
    }
    private static double[][][] copy(double[][][] values) {
        double[][][] result = new double[values.length][][];
        for (int i = 0; i < values.length; i++) result[i] = copy(values[i]);
        return result;
    }
}
