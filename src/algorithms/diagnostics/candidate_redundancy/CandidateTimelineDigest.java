package org.uma.jmetal.util.research.search;

import java.nio.ByteBuffer;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import org.uma.jmetal.util.research.model.DynamicSchedule;
import org.uma.jmetal.util.research.model.DynamicStep;

/** Full operation fields in canonical factory order; no cached schedule is returned to search. */
final class CandidateTimelineDigest {
    private final MessageDigest digest;
    private final ByteBuffer buffer = ByteBuffer.allocate(100);
    CandidateTimelineDigest() {
        try { digest = MessageDigest.getInstance("SHA-256"); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
    byte[] of(DynamicSchedule schedule, int factories) {
        digest.reset();
        for (int f = 0; f < factories; f++) for (DynamicStep op : schedule.steps()) if (op.factory() == f) {
            buffer.clear();
            buffer.putInt(op.job()).putInt(op.factory()).putInt(op.stage()).putInt(op.machine()).putInt(op.worker());
            put(op.start()); put(op.base()); put(op.duration()); put(op.setupDuration()); put(op.completion());
            put(op.u()); put(op.v()); put(op.energy()); put(op.labor()); put(op.exposure());
            digest.update(buffer.array(), 0, buffer.position());
        }
        return digest.digest();
    }
    private void put(double value) { buffer.putLong(Double.doubleToLongBits(value)); }
}
