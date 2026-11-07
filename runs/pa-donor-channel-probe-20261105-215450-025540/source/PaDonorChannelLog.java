package org.uma.jmetal.util.research.modelglobal;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import research.dynamic.DynamicJson;

/** Optional read-only channel evidence, closed before the receipt is emitted. */
final class PaDonorChannelLog {
    private final BufferedWriter writer;
    PaDonorChannelLog() {
        String path = System.getProperty("research.pa.donorAuditPath");
        try {
            writer = path == null ? null : Files.newBufferedWriter(Paths.get(path), StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        } catch (IOException error) { throw new UncheckedIOException(error); }
    }
    boolean enabled() { return writer != null; }
    void emit(Map<String,Object> row) {
        if (writer == null) return;
        try { writer.write(DynamicJson.encode(row)); writer.newLine(); }
        catch (IOException error) { throw new UncheckedIOException(error); }
    }
    void close() {
        if (writer == null) return;
        try { writer.close(); } catch (IOException error) { throw new UncheckedIOException(error); }
    }
    static Map<String,Object> row(Object... pairs) {
        Map<String,Object> values = new LinkedHashMap<>();
        for (int i=0; i<pairs.length; i+=2) values.put((String)pairs[i], pairs[i+1]);
        return values;
    }
    static Map<String,Object> state(PaIndividual point, boolean full) {
        Map<String,Object> value = row("id",point.id,"paidFE",point.paidFE,"role",point.role.name(),
            "hash",point.hash,"objectives",point.objectives());
        if (full) { value.put("resources",point.genome.allocations()); value.put("keys",point.genome.priorities()); }
        return value;
    }
    static void flags(Map<String,Object> row, PaInternalArchive.Flags flags) {
        row.put("archiveDominated",flags.dominated); row.put("archiveEqual",flags.equal);
        row.put("archiveFresh",flags.fresh); row.put("archiveSizeBefore",flags.before); row.put("archiveSizeAfter",flags.after);
    }
}
