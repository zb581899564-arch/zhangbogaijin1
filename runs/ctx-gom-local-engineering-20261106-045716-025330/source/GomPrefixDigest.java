package research.dynamic;

import java.nio.ByteBuffer;
import java.security.*;
import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;

/** Cloneable diagnostic digest. It is checked against the unchanged common paid digest at completion. */
final class GomPrefixDigest {
    private final MessageDigest digest;
    private final Set<Long> wanted = new HashSet<>();
    final Map<String,String> prefixes = new LinkedHashMap<>();
    GomPrefixDigest() throws Exception {
        digest = MessageDigest.getInstance("SHA-256");
        String value = System.getProperty("research.ctxGom.prefixFE", "");
        if (!value.isEmpty()) for (String text : value.split(",")) wanted.add(Long.parseLong(text));
    }
    void update(PermutationSolution<Integer> point, long fe) {
        int[][] vectors = {SchedulingEncoding.integers(point.getVariables()), SchedulingEncoding.integers(point.getVariablesid()),
            SchedulingEncoding.machineIntegers(point), SchedulingEncoding.integers(point.getVariablesworker())};
        ByteBuffer data = ByteBuffer.allocate(48+16*vectors[0].length); data.putLong(fe);
        for (int[] vector : vectors) { data.putInt(vector.length); for (int value : vector) data.putInt(value); }
        for (double value : point.getObjectives()) data.putDouble(value); digest.update(data.array());
        if (wanted.contains(fe)) prefixes.put(Long.toString(fe), snapshot());
    }
    String snapshot() {
        try {
            byte[] bytes = ((MessageDigest)digest.clone()).digest(); StringBuilder result = new StringBuilder(64);
            for (byte value : bytes) result.append(Character.forDigit((value >>> 4)&15,16)).append(Character.forDigit(value&15,16)); return result.toString();
        } catch (CloneNotSupportedException error) { throw new IllegalStateException(error); }
    }
}
