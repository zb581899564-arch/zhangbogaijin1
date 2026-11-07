package research.dynamic;

import java.security.*;
import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.search.GomRecords;

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
        digest.update(GomRecords.paidBytes(point,fe));
        if (wanted.contains(fe)) prefixes.put(Long.toString(fe), snapshot());
    }
    String snapshot() {
        try {
            byte[] bytes = ((MessageDigest)digest.clone()).digest(); StringBuilder result = new StringBuilder(64);
            for (byte value : bytes) result.append(Character.forDigit((value >>> 4)&15,16)).append(Character.forDigit(value&15,16)); return result.toString();
        } catch (CloneNotSupportedException error) { throw new IllegalStateException(error); }
    }
}
