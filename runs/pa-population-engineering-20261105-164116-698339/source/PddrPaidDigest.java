package research.dynamic;

import java.nio.ByteBuffer;
import java.security.MessageDigest;
import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;

/** Same paid-trace byte convention as the frozen ReverseAudit observer. */
final class PddrPaidDigest {
    private final MessageDigest digest;
    private final ByteBuffer buffer = ByteBuffer.allocate(8);
    PddrPaidDigest() throws Exception { digest = MessageDigest.getInstance("SHA-256"); }

    void update(long paid, PermutationSolution<?> s) {
        put(paid, 8);
        ints(s.getVariables()); ints(s.getVariablesid());
        ints((List<?>) s.getAttribute("machine")); ints(s.getVariablesworker());
        for (double x : s.getObjectives()) put(Double.doubleToLongBits(x), 8);
    }
    String finish() {
        StringBuilder out = new StringBuilder(64);
        for (byte b : digest.digest()) out.append(Character.forDigit((b >>> 4) & 15, 16)).append(Character.forDigit(b & 15, 16));
        return out.toString();
    }
    private void ints(List<?> values) {
        put(values.size(), 4);
        for (Object value : values) put((Integer) value, 4);
    }
    private void put(long value, int bytes) {
        buffer.clear();
        if (bytes == 4) buffer.putInt((int) value); else buffer.putLong(value);
        digest.update(buffer.array(), 0, bytes);
    }
}
