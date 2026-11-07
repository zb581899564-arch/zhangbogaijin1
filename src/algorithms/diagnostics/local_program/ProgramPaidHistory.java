package org.uma.jmetal.util.research.search;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;

/** Numeric paid stream and exact physical birth membership; no decisions or stored mutable solutions. */
final class ProgramPaidHistory {
    private final int factories;
    private final Map<CandidatePhysicalKey,Long> births = new HashMap<>();
    private final List<String> rows = new ArrayList<>();
    private long paid;
    ProgramPaidHistory(int count) {
        factories = count;rows.add("fe,episode,phase,archiveChanged,C,E,W");
    }
    void paid(PermutationSolution<?> point, long fe, long episode, String phase, boolean changed) {
        if (fe != paid + 1) throw new AssertionError("Program paid history is not contiguous");
        births.putIfAbsent(CandidatePhysicalKey.of(point, factories), fe);
        rows.add(fe + "," + episode + "," + phase + "," + (changed ? 1 : 0) + ","
                + point.getObjective(0) + "," + point.getObjective(1) + "," + point.getObjective(2));
        paid = fe;
    }
    long physicalBirth(PermutationSolution<?> point) {
        Long value = births.get(CandidatePhysicalKey.of(point, factories));
        if (value == null || value > paid) throw new AssertionError("Unpaid program snapshot");
        return value;
    }
    long paid() { return paid; }
    int distinctKeys() { return births.size(); }
    void write(Path out) throws IOException {
        Files.write(out.resolve("program-paid-objectives.csv"), rows, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
    }
}
