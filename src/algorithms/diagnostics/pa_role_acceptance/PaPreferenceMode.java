package org.uma.jmetal.util.research.modelglobal;

import java.util.LinkedHashMap;
import java.util.Map;
import org.uma.jmetal.util.research.search.Direction;

/** Initial metadata-only ablation: generation, paid genes and all random draws are unchanged. */
public final class PaPreferenceMode {
    private static final String MODE = System.getProperty("research.pa.preferenceMode", "FOUR");
    private static final Map<Direction, Integer> counts = new java.util.EnumMap<>(Direction.class);

    private PaPreferenceMode() { }

    public static PaIndividual initial(PaIndividual point) {
        if (!MODE.equals("FOUR") && !MODE.equals("CENTER")) throw new IllegalArgumentException("Unknown preference mode: " + MODE);
        Direction effective = MODE.equals("CENTER") ? Direction.CENTER : point.role;
        counts.put(effective, counts.getOrDefault(effective, 0) + 1);
        return effective == point.role ? point : new PaIndividual(point.id, point.paidFE, effective, point.genome, point.point);
    }

    public static Map<String, Object> diagnostics() {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("preference.mode", MODE);
        for (Direction role : Direction.values()) result.put("preference.initial." + role.name(), counts.getOrDefault(role, 0));
        return result;
    }
}
