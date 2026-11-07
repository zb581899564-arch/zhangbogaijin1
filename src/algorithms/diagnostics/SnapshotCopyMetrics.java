package org.uma.jmetal.util.research.runtime;

import java.util.*;

/** Optional per-process accounting; disabled for any subsequent timing experiment. */
public final class SnapshotCopyMetrics {
    private static final boolean ENABLED = Boolean.getBoolean("research.snapshot.audit");
    private static boolean searching;
    private static long copies, searchCopies, bytes, searchBytes, anchors, nanos, searchNanos;
    private SnapshotCopyMetrics() { }
    public static void searchStarted() { searching = true; }
    public static void searchEnded() { searching = false; }
    static long begin() {
        if (!ENABLED) return 0;
        copies++; if (searching) searchCopies++;
        return System.nanoTime();
    }
    static void serialized(long size, long count) {
        if (!ENABLED) return;
        bytes += size; anchors += count; if (searching) searchBytes += size;
    }
    static void end(long start) {
        if (!ENABLED) return;
        long elapsed = System.nanoTime()-start; nanos += elapsed; if (searching) searchNanos += elapsed;
    }
    public static Map<String,Object> snapshot() {
        Map<String,Object> out = new LinkedHashMap<>();
        out.put("enabled", ENABLED); out.put("mode", System.getProperty("research.snapshot.mode", "SERIAL"));
        out.put("copyAttempts", copies); out.put("searchCopyAttempts", searchCopies);
        out.put("serializedBytes", bytes); out.put("searchSerializedBytes", searchBytes); out.put("immutableAnchors", anchors);
        out.put("copySeconds", nanos/1e9); out.put("searchCopySeconds", searchNanos/1e9);
        return out;
    }
}
