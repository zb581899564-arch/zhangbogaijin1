package org.uma.jmetal.util.research.search;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.List;

/** Per-visit physical FE and factory schedule for the isolated static guidance diagnostic. */
public final class QgsLocalLedger {
    private static QgsLocalLedger active;
    private static final String HEADER = "visit,group,round,factory,paid,restarts";
    private final boolean replay;
    private final List<String> expected;
    private final List<String> actual = new ArrayList<>();
    private int index, visit;

    private QgsLocalLedger() throws IOException {
        String mode = System.getProperty("research.qgsAudit.mode");
        if (!"record".equals(mode) && !"replay".equals(mode)) throw new IllegalStateException("Missing audit mode");
        replay = "replay".equals(mode);
        actual.add(HEADER);
        if (replay) {
            expected = Files.readAllLines(Paths.get(System.getProperty("research.qgsAudit.ledger")), StandardCharsets.UTF_8);
            if (!expected.get(0).equals(HEADER)) throw new IllegalArgumentException("Invalid replay ledger");
            index = 1;
        } else expected = null;
    }

    static QgsLocalLedger instance() {
        if (active != null) return active;
        try { active = new QgsLocalLedger(); return active; }
        catch (IOException ex) { throw new UncheckedIOException(ex); }
    }

    static int choose(QTable table, int observation, double exploration) {
        String policy = System.getProperty("research.qgsAudit.guidance");
        if ("Q".equals(policy)) return table.choose(observation, exploration);
        if (!"UNIFORM".equals(policy)) throw new IllegalStateException("Unknown guidance policy");
        // Same action set; retain the exploration draw, ignore reward when selecting.
        org.uma.jmetal.util.research.runtime.SeededRandom.current().nextDouble();
        return org.uma.jmetal.util.research.runtime.SeededRandom.current().nextInt(3);
    }

    Slot inter(int group) { visit++; return begin(group, -1, -1); }
    boolean hasRound() {
        return !replay || index < expected.size() && Integer.parseInt(expected.get(index).split(",")[0]) == visit;
    }
    Slot round(int group, int round, int factory) { return begin(group, round, factory); }
    private Slot begin(int group, int round, int factory) {
        if (!replay) return new Slot(group, round, factory, Integer.MAX_VALUE, false);
        if (index >= expected.size()) throw new IllegalStateException("Too many local visits");
        String[] v = expected.get(index++).split(",");
        if (v.length != 6 || Integer.parseInt(v[0]) != visit || Integer.parseInt(v[1]) != group
                || Integer.parseInt(v[2]) != round) throw new IllegalStateException("Local schedule mismatch at " + index);
        return new Slot(group, round, Integer.parseInt(v[3]), Integer.parseInt(v[4]), true);
    }
    void end(Slot slot) {
        if (slot.fixed && slot.paid != slot.limit) throw new IllegalStateException("Unspent replay quota");
        actual.add(visit + "," + slot.group + "," + slot.round + "," + slot.factory + "," + slot.paid + "," + slot.restarts);
    }
    public static void finish(Path out) throws IOException {
        QgsLocalLedger self = instance();
        if (self.replay && self.index != self.expected.size()) throw new IllegalStateException("Incomplete local replay");
        Files.write(out.resolve("local-ledger.csv"), self.actual, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
    }
    static final class Slot {
        final int group, round, factory, limit;
        final boolean fixed;
        int paid, restarts;
        Slot(int group, int round, int factory, int limit, boolean fixed) {
            if (limit < 0) throw new IllegalArgumentException("Negative local quota");
            this.group = group; this.round = round; this.factory = factory; this.limit = limit; this.fixed = fixed;
        }
    }
}
