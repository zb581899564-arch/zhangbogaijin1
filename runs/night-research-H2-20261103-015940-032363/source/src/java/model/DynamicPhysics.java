package org.uma.jmetal.util.research.model;

/** Shared exact one-operation physics, without search state or evaluation accounting. */
final class DynamicPhysics {
    private DynamicPhysics() { }

    static DynamicStep transition(Instance in, DynamicParameters p, int j, int f, int k,
            int m, int w, double jobReady, double machineEnd, boolean machineUsed,
            double workerEnd, double previousFatigue) {
        double start = Math.max(jobReady, Math.max(machineEnd, workerEnd));
        double u = previousFatigue * Math.exp(-p.mu(f, k, w) * (start - workerEnd));
        double base = (in.processing(j, k) / in.speed(f, k, m) + in.setup(j, k))
                / in.efficiency(f, k, w);
        double factor = 1.0 + p.beta(f, k, w) * u;
        double duration = base * factor;
        double v = 1.0 - (1.0 - u) * Math.exp(-p.alpha(f, k, w) * duration);
        double setup = in.setup(j, k) / in.efficiency(f, k, w) * factor;
        double energy = in.power(f, k, m) * duration
                + (machineUsed ? in.standby(f, k, m) * (start - machineEnd) : 0.0);
        double labor = in.cost(f, k, w) * duration;
        double exposure = workExposure(u, p.alpha(f, k, w), duration);
        if (!Double.isFinite(start + duration) || !Double.isFinite(duration) || duration <= 0
                || !Double.isFinite(energy) || !Double.isFinite(labor) || !Double.isFinite(exposure)) {
            throw new IllegalArgumentException("Non-finite dynamic transition");
        }
        return new DynamicStep(j, f, k, m, w, start, base, duration, setup,
                u, v, energy, labor, exposure);
    }

    static double workExposure(double u, double alpha, double duration) {
        if (alpha == 0.0) return u * duration;
        double x = alpha * duration;
        // 1 - (1-exp(-x))/x; series avoids subtracting nearly equal terms.
        double growth = x < 1e-5
                ? x * (0.5 + x * (-1.0 / 6.0 + x * (1.0 / 24.0
                        + x * (-1.0 / 120.0 + x / 720.0))))
                : 1.0 + Math.expm1(-x) / x;
        return duration * (u + (1.0 - u) * growth);
    }
}
