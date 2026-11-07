package org.uma.jmetal.util.research.search;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;

/** Per-JVM task geometry and causal paid ideal. It never changes physical objective values. */
public final class CenterTaskState {
    enum Mode { OFF, OWNER_PDDR, EQUAL, FIXED, PERMUTE }
    static final Mode MODE = Mode.valueOf(System.getProperty("research.centerTasks.mode", "OFF"));
    static final String KEY = "research.centerTaskOwner.v1";
    static final double[][] WEIGHTS = weights();
    static final double[] SCALE = enabled() ? parseScale() : new double[] {1, 1, 1};
    static final double[] IDEAL = {Double.POSITIVE_INFINITY, Double.POSITIVE_INFINITY, Double.POSITIVE_INFINITY};
    static final Map<String,Long> COUNTS = new LinkedHashMap<>();
    static final List<Map<String,Object>> EVENTS = new ArrayList<>();
    static long epoch;
    static Owner activeLocal;
    private CenterTaskState() { }

    public static boolean enabled() { return MODE != Mode.OFF; }
    static boolean scalar() { return enabled() && MODE != Mode.OWNER_PDDR; }
    static void count(String key) { COUNTS.put(key, COUNTS.getOrDefault(key, 0L) + 1); }

    static void paid(PermutationSolution<Integer> point) {
        if (!enabled()) return;
        for (int objective = 0; objective < 3; objective++) {
            double value = point.getObjective(objective);
            if (!Double.isFinite(value)) throw new AssertionError("Unpaid/nonfinite ideal update");
            IDEAL[objective] = Math.min(IDEAL[objective], value);
        }
        count("successfulPaidIdealUpdates");
    }

    static Owner owner(PermutationSolution<Integer> point) {
        Object value = point.getAttribute(KEY);
        if (!(value instanceof Owner)) throw new AssertionError("Missing task owner");
        return (Owner) value;
    }

    static double score(PermutationSolution<Integer> point, Owner owner, double[] ideal) {
        double answer = Double.NEGATIVE_INFINITY;
        for (int objective = 0; objective < 3; objective++) {
            double weight = MODE == Mode.EQUAL ? 1.0 / 3 : WEIGHTS[owner.weight][objective];
            answer = Math.max(answer, weight * (point.getObjective(objective) - ideal[objective]) / SCALE[objective]);
        }
        if (!Double.isFinite(answer)) throw new AssertionError("Invalid task scalar value");
        return answer;
    }

    static double[] ideal() {
        for (double value : IDEAL) if (!Double.isFinite(value)) throw new AssertionError("No paid ideal");
        return IDEAL.clone();
    }

    static void requireSameOwner(Owner first, Owner second) {
        if (first.epoch != second.epoch || first.role != second.role || first.slot != second.slot
                || first.weight != second.weight) throw new AssertionError("Task ownership crossed slots/phases");
    }

    static final class Owner implements Serializable {
        private static final long serialVersionUID = 1L;
        final long epoch;
        final Direction role;
        final int slot, weight;
        Owner(long generation, Direction physicalRole, int position, int target) {
            epoch = generation; role = physicalRole; slot = position; weight = target;
        }
    }

    static void event(String phase, List<Particle> center) {
        List<Integer> slots = new ArrayList<>(), weights = new ArrayList<>(), categories = new ArrayList<>();
        for (Particle particle : center) {
            Owner owner = owner(particle.current);
            if (owner.epoch != epoch || owner.role != Direction.CENTER) throw new AssertionError("Stale CENTER task");
            slots.add(owner.slot); weights.add(MODE == Mode.EQUAL ? -1 : MODE == Mode.OWNER_PDDR ? -2 : owner.weight);
            Object family = particle.current.getAttribute("cooperation.family");
            categories.add(family == null ? 0 : (Integer) family + 1);
        }
        Map<String,Object> record = new LinkedHashMap<>();
        record.put("epoch", epoch); record.put("phase", phase); record.put("slots", slots);
        record.put("weights", weights); record.put("categories", categories);
        EVENTS.add(record);
    }

    public static Map<String,Object> diagnostics() {
        Map<String,Object> out = new LinkedHashMap<>();
        out.put("mode", MODE.name()); out.put("counts", new LinkedHashMap<>(COUNTS));
        out.put("taskLifetime", "One complete generation; rebuilt after native next-generation regrouping");
        boolean hasPaid = COUNTS.getOrDefault("successfulPaidIdealUpdates", 0L) > 0;
        out.put("scale", SCALE.clone()); out.put("ideal", hasPaid ? ideal() : new double[0]);
        out.put("activeLocalCleared", activeLocal == null); out.put("events", EVENTS);
        return out;
    }

    private static double[][] weights() {
        double[][] out = new double[55][3]; int index = 0;
        for (int a = 1; a <= 10; a++) for (int b = 1; b < 12 - a; b++)
            out[index++] = new double[] {a / 12., b / 12., (12 - a - b) / 12.};
        if (index != 55) throw new AssertionError("Wrong task lattice");
        return out;
    }

    private static double[] parseScale() {
        String value = System.getProperty("research.centerTasks.scale");
        if (value == null) throw new IllegalArgumentException("Frozen task scale required");
        double[] values = Arrays.stream(value.split(",")).mapToDouble(Double::parseDouble).toArray();
        if (values.length != 3) throw new IllegalArgumentException("Three task scales required");
        for (double scale : values) if (!Double.isFinite(scale) || scale <= 0)
            throw new IllegalArgumentException("Positive finite task scales required");
        return values;
    }
}
