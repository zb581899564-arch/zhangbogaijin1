package org.uma.jmetal.util.research.model;

/** Exact context checks for immutable cache reuse, with a fast identity path. */
final class DynamicContext {
    private DynamicContext() { }

    static void requireSame(Instance in, DynamicParameters p, Instance cached, DynamicParameters q) {
        if (!p.sameValues(q) || !sameInstance(in, cached)) {
            throw new IllegalArgumentException("Dynamic cache instance/parameter context differs");
        }
    }

    private static boolean sameInstance(Instance a, Instance b) {
        if (a == b) return true;
        if (a == null || b == null || !a.name().equals(b.name())
                || !a.provenance().equals(b.provenance()) || a.kind() != b.kind()
                || a.jobs() != b.jobs() || a.stages() != b.stages()
                || a.factories() != b.factories()) return false;
        for (int j = 0; j < a.jobs(); j++) for (int k = 0; k < a.stages(); k++) {
            if (!equal(a.processing(j, k), b.processing(j, k))
                    || !equal(a.setup(j, k), b.setup(j, k))) return false;
        }
        for (int f = 0; f < a.factories(); f++) for (int k = 0; k < a.stages(); k++) {
            if (a.machines(f, k) != b.machines(f, k) || a.workers(f, k) != b.workers(f, k)) return false;
            for (int m = 0; m < a.machines(f, k); m++) {
                if (!equal(a.speed(f, k, m), b.speed(f, k, m))
                        || !equal(a.power(f, k, m), b.power(f, k, m))
                        || !equal(a.standby(f, k, m), b.standby(f, k, m))) return false;
            }
            for (int w = 0; w < a.workers(f, k); w++) {
                if (!equal(a.efficiency(f, k, w), b.efficiency(f, k, w))
                        || !equal(a.cost(f, k, w), b.cost(f, k, w))) return false;
            }
        }
        return true;
    }

    private static boolean equal(double a, double b) {
        return Double.doubleToLongBits(a) == Double.doubleToLongBits(b);
    }
}
