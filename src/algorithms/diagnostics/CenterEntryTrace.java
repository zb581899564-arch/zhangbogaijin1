package org.uma.jmetal.util.research.search;

import java.io.*;
import java.nio.ByteBuffer;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Snapshot and per-slot Java Random bank for the isolated CENTER experiment. */
public final class CenterEntryTrace {
    public static final class Entry implements Serializable {
        private static final long serialVersionUID = 1L;
        final List<Particle> particles;
        final List<PermutationSolution<Integer>> reference;
        final double[][] paidFront;
        final long paid;
        Entry(List<Particle> particles, List<PermutationSolution<Integer>> reference, double[][] paidFront, long paid) {
            this.particles = new ArrayList<>(particles);
            this.reference = new ArrayList<>(reference);
            this.paidFront = paidFront;
            this.paid = paid;
        }
    }
    private static final class Slot implements Serializable {
        private static final long serialVersionUID = 1L;
        final int visit, round;
        final byte[] rng;
        Slot(int visit, int round, byte[] rng) { this.visit = visit; this.round = round; this.rng = rng; }
    }
    private static CenterEntryTrace trace;
    private final Path out;
    private final boolean replay;
    private final List<Slot> bank;
    private final MessageDigest digest = sha();
    private final ByteBuffer buffer = ByteBuffer.allocate(8);
    private final List<Map<String, Object>> endpoints = new ArrayList<>();
    private long paid;
    private final long offset;
    private int visit, index;
    private final CenterReferenceProbe probe;

    private CenterEntryTrace(Path out, boolean replay, List<Slot> bank, long offset, CenterReferenceProbe probe) {
        this.out = out; this.replay = replay; this.bank = bank; this.offset = offset; this.probe = probe;
    }

    static void capture(List<Particle> particles, List<PermutationSolution<Integer>> reference) {
        String directory = System.getProperty("research.center.capture");
        if (directory == null || ReverseAudit.run().generation() != 1) return;
        Path out = Paths.get(directory);
        Entry value = new Entry(particles, reference, ReverseAudit.run().archive(), ReverseAudit.run().fe());
        trace = new CenterEntryTrace(out, false, new ArrayList<>(), value.paid, null);
        writeObject(out.resolve("entry.bin"), value);
        writeRows(out.resolve("entry.jsonl"), Collections.singletonList(ReverseAudit.row(
                "paidFE", value.paid, "center", genomeRows(value.particles), "reference", solutionRows(value.reference),
                "background", value.paidFront)));
    }

    @SuppressWarnings("unchecked")
    static void prepare(Path out, Path rng, List<PermutationSolution<Integer>> alternate) {
        List<Slot> bank = (List<Slot>) readObject(rng);
        trace = new CenterEntryTrace(out, true, bank, 0, new CenterReferenceProbe(alternate));
    }

    static Entry load(Path path) { return (Entry) readObject(path); }

    static void slot(int physical, int round) {
        CenterEntryTrace t = trace;
        if (t == null) return;
        if (physical != Direction.CENTER.id()) throw new IllegalStateException("Cross replay entered another group");
        if (round == -1) t.visit++;
        if (t.replay) {
            Slot s = t.bank.get(t.index++);
            if (s.visit != t.visit || s.round != round) throw new IllegalStateException("RNG slot does not match ledger");
            SeededRandom.restoreForCenterReplay((Random) decode(s.rng));
        } else t.bank.add(new Slot(t.visit, round, encode(SeededRandom.current())));
    }

    public static void paid(PermutationSolution<?> value, long absolute) {
        CenterEntryTrace t = trace;
        if (t == null) return;
        long relative = absolute - t.offset;
        if (relative != ++t.paid) throw new IllegalStateException("Unexpected paid index in CENTER trace");
        t.put(relative, 8);
        t.ints(value.getVariables()); t.ints(value.getVariablesid());
        t.ints((List<?>) value.getAttribute("machine")); t.ints(value.getVariablesworker());
        for (double x : value.getObjectives()) t.put(Double.doubleToLongBits(x), 8);
    }

    static boolean better(Direction direction, PermutationSolution<Integer> candidate,
            PermutationSolution<Integer> incumbent, List<PermutationSolution<Integer>> reference) {
        boolean accepted = ReverseAudit.run().better(direction, candidate, incumbent, reference);
        if (trace != null && trace.probe != null)
            trace.probe.observe(direction, candidate, incumbent, reference, accepted);
        return accepted;
    }

    static void retained(Particle p) {
        if (trace != null) trace.endpoints.add(solutionRow(p.current, trace.paid));
    }

    static void finish() {
        CenterEntryTrace t = trace;
        if (t == null) return;
        if (t.replay && t.index != t.bank.size()) throw new IllegalStateException("Unused RNG slots");
        if (t.endpoints.size() != 55 || t.visit != 55) throw new IllegalStateException("Incomplete CENTER visits");
        if (!t.replay) writeObject(t.out.resolve("rng-slots.bin"), t.bank);
        writeRows(t.out.resolve("endpoints.jsonl"), t.endpoints);
        writeRows(t.out.resolve("center-trace.jsonl"), Collections.singletonList(ReverseAudit.row(
                "paidFE", t.paid, "slots", t.bank.size(), "paidSHA256", hex(t.digest.digest()),
                "referenceProbe", t.probe == null ? null : t.probe.summary())));
        trace = null;
    }

    private static List<Map<String, Object>> genomeRows(List<Particle> p) {
        List<Map<String, Object>> rows = new ArrayList<>();
        for (Particle value : p) rows.add(solutionRow(value.current, ReverseAudit.birth(value.current)));
        return rows;
    }
    private static List<Map<String, Object>> solutionRows(List<PermutationSolution<Integer>> p) {
        List<Map<String, Object>> rows = new ArrayList<>();
        for (PermutationSolution<Integer> value : p) rows.add(solutionRow(value, ReverseAudit.birth(value)));
        return rows;
    }
    private static Map<String, Object> solutionRow(PermutationSolution<Integer> value, long paid) {
        return ReverseAudit.row("genome", ReverseAudit.genome(value), "objectives", value.getObjectives().clone(),
                "family", value.getAttribute("cooperation.family"), "paid", paid);
    }
    private void ints(List<?> values) {
        put(values.size(), 4);
        for (Object v : values) put((Integer) v, 4);
    }
    private void put(long value, int bytes) {
        buffer.clear();
        if (bytes == 8) buffer.putLong(value); else buffer.putInt((int) value);
        digest.update(buffer.array(), 0, bytes);
    }
    private static MessageDigest sha() {
        try { return MessageDigest.getInstance("SHA-256"); }
        catch (Exception e) { throw new AssertionError(e); }
    }
    private static String hex(byte[] bytes) {
        StringBuilder s = new StringBuilder();
        for (byte b : bytes) s.append(Character.forDigit((b >>> 4) & 15, 16)).append(Character.forDigit(b & 15, 16));
        return s.toString();
    }
    private static byte[] encode(Object value) {
        try (ByteArrayOutputStream bytes = new ByteArrayOutputStream()) {
            try (ObjectOutputStream o = new ObjectOutputStream(bytes)) { o.writeObject(value); }
            return bytes.toByteArray();
        } catch (IOException e) { throw new UncheckedIOException(e); }
    }
    private static Object decode(byte[] bytes) {
        try (ObjectInputStream i = new ObjectInputStream(new ByteArrayInputStream(bytes))) { return i.readObject(); }
        catch (IOException e) { throw new UncheckedIOException(e); }
        catch (ClassNotFoundException e) { throw new IllegalStateException(e); }
    }
    private static void writeObject(Path path, Object value) {
        try { Files.write(path, encode(value), StandardOpenOption.CREATE_NEW); }
        catch (IOException e) { throw new UncheckedIOException(e); }
    }
    private static Object readObject(Path path) {
        try { return decode(Files.readAllBytes(path)); }
        catch (IOException e) { throw new UncheckedIOException(e); }
    }
    private static void writeRows(Path path, List<Map<String, Object>> rows) {
        try { ReverseAudit.writeRows(path, rows); }
        catch (IOException e) { throw new UncheckedIOException(e); }
    }
}
