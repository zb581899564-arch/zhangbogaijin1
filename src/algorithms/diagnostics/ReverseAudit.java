package org.uma.jmetal.util.research.search;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectOutputStream;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import org.uma.jmetal.util.research.runtime.ThreeObjectiveArchive;
import research.dynamic.DynamicJson;

/** Used only by the reverse-ledger shadow classes. No search draws or candidate evaluations. */
public final class ReverseAudit {
    private static final ReverseAudit RUN = new ReverseAudit();
    private static final String PAID = "diagnostic.reverse.paidFE", ADMITTED = "diagnostic.reverse.admitted";
    private final MessageDigest stream = digest();
    private final ByteBuffer buffer = ByteBuffer.allocate(32);
    private final List<Map<String, Object>> phases = new ArrayList<>();
    private final List<Map<String, Object>> selection = new ArrayList<>();
    private ThreeObjectiveArchive<?> archive;
    private long fe, timedNanos, pbestCount, pbestMulti, pbestMissing, pbestAgeSum, pbestAgeMax;
    private long localComparisons, ties, rejectedAdmitted, tiedAdmitted;
    private final java.util.Set<Long> rejectedIds = new java.util.HashSet<>(), tiedIds = new java.util.HashSet<>();
    private int generation;
    private boolean inLocal;

    public static ReverseAudit run() { return RUN; }
    public long fe() { return fe; }
    public int generation() { return generation; }
    public long observedNanos() { return timedNanos; }
    public void chargedTime(long nanos) { timedNanos += nanos; }
    public double[][] archive() { return archive == null ? new double[0][3] : archive.objectiveSnapshot(); }
    void begin() { generation++; }

    public void paid(PermutationSolution<?> s, long number, boolean changed, ThreeObjectiveArchive<?> result) {
        long start = System.nanoTime();
        fe = number; archive = result;
        if (number == 1) checkPddr(s);
        s.setAttribute(PAID, fe);
        s.setAttribute(ADMITTED, changed);
        put(stream, fe);
        encode(stream, s);
        chargedTime(System.nanoTime() - start);
    }

    static long birth(PermutationSolution<?> s) {
        Object v = s.getAttribute(PAID);
        return v instanceof Long ? (Long) v : -1;
    }

    void pbest(Direction direction, PermutationSolution<Integer> chosen, int historySize) {
        if (direction != Direction.CENTER) return;
        long start = System.nanoTime();
        pbestCount++;
        if (historySize > 1) pbestMulti++;
        long birth = birth(chosen);
        if (birth < 0) pbestMissing++;
        else {
            long age = fe - birth;
            pbestAgeSum += age; pbestAgeMax = Math.max(pbestAgeMax, age);
        }
        chargedTime(System.nanoTime() - start);
    }

    boolean better(Direction direction, PermutationSolution<Integer> candidate,
            PermutationSolution<Integer> incumbent, List<PermutationSolution<Integer>> reference) {
        inLocal = true;
        try { return direction.better(candidate, incumbent, reference); }
        finally { inLocal = false; }
    }

    void pddr(PermutationSolution<Integer> candidate, double trial, double incumbent) {
        if (!inLocal) return;
        long start = System.nanoTime();
        localComparisons++;
        if (trial == incumbent) ties++;
        if (!(trial < incumbent) && Boolean.TRUE.equals(candidate.getAttribute(ADMITTED))) {
            rejectedAdmitted++;
            rejectedIds.add(birth(candidate));
            if (trial == incumbent) { tiedAdmitted++; tiedIds.add(birth(candidate)); }
        }
        chargedTime(System.nanoTime() - start);
    }

    void phase(String event, List<Particle> center, List<PermutationSolution<Integer>> reference) {
        if (generation != 1) return;
        long start = System.nanoTime();
        MessageDigest c = digest(), r = digest(), p = digest(), a = digest();
        for (Particle particle : center) encode(c, particle.current);
        for (PermutationSolution<Integer> value : reference) encode(r, value);
        for (double[] point : archive()) for (double value : point) put(a, Double.doubleToLongBits(value));
        try {
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            try (ObjectOutputStream out = new ObjectOutputStream(bytes)) { out.writeObject(SeededRandom.current()); }
            p.update(bytes.toByteArray());
        } catch (IOException e) { throw new IllegalStateException("Cannot serialize RNG state without a draw", e); }
        phases.add(row("event", event, "paidFE", fe, "centerSHA256", hex(c.digest()), "referenceSHA256", hex(r.digest()),
                "rngSHA256", hex(p.digest()), "archiveSHA256", hex(a.digest())));
        chargedTime(System.nanoTime() - start);
    }

    void selection(List<Particle> candidates, SurvivorSelection.Result chosen, int globals) {
        if (generation != 1) return;
        long start = System.nanoTime();
        int[] categories = chosen.categories(), kept = chosen.indices();
        double[] scores = chosen.fitness();
        for (int i = 0; i < candidates.size(); i++) {
            Particle item = candidates.get(i);
            PermutationSolution<Integer> s = item.current;
            selection.add(row("paidFE", fe, "index", i, "source", i < globals ? "global" : "local",
                    "familyCategory", categories[i], "pddr", scores[i], "kept", contains(kept, i),
                    "birthFE", birth(s), "admittedAtBirth", Boolean.TRUE.equals(s.getAttribute(ADMITTED)),
                    "objectives", s.getObjectives().clone(), "genome", genome(s)));
        }
        chargedTime(System.nanoTime() - start);
    }

    public void finish(Path out) throws IOException {
        writeRows(out.resolve("center-entry.jsonl"), phases);
        writeRows(out.resolve("selection-audit.jsonl"), selection);
        writeRows(out.resolve("observation.jsonl"), Arrays.asList(row("paidFE", fe, "paidSHA256", hex(stream.digest()),
                "observationSeconds", timedNanos / 1e9, "centerPbestCount", pbestCount, "centerPbestMulti", pbestMulti,
                "centerPbestMissingBirth", pbestMissing, "centerPbestAgeSumFE", pbestAgeSum,
                "centerPbestAgeMaxFE", pbestAgeMax, "pddrComparisons", localComparisons, "pddrTies", ties,
                "pddrRejectedAdmittedComparisons", rejectedAdmitted, "pddrTiedAdmittedComparisons", tiedAdmitted,
                "pddrRejectedAdmittedUniqueFE", rejectedIds.size(), "pddrTiedAdmittedUniqueFE", tiedIds.size())));
    }

    @SuppressWarnings("unchecked")
    private void checkPddr(PermutationSolution<?> s) {
        PermutationSolution<Integer> base = (PermutationSolution<Integer>) s;
        List<PermutationSolution<Integer>> values = new ArrayList<>();
        for (int i = 0; i < 3; i++) {
            PermutationSolution<Integer> item = ParetoTools.copy(base);
            item.setObjective(0, i); item.setObjective(1, 2 - i); item.setObjective(2, 1);
            values.add(item);
        }
        if (!Arrays.equals(ParetoTools.fitness(values), new double[] {1, 1, 1})
                || !ParetoTools.order(values, Direction.CENTER).equals(Arrays.asList(0, 1, 2))
                || Direction.CENTER.better(values.get(1), values.get(0), values))
            throw new IllegalStateException("Unexpected CENTER/PDDR tie behavior");
    }

    public static Map<String, Object> genome(PermutationSolution<?> s) {
        return row("JS", new ArrayList<>(s.getVariables()), "FA", new ArrayList<>(s.getVariablesid()),
                "MA", new ArrayList<>((List<?>) s.getAttribute("machine")), "WA", new ArrayList<>(s.getVariablesworker()));
    }
    public static Map<String, Object> row(Object... pairs) {
        Map<String, Object> row = new LinkedHashMap<>();
        for (int i = 0; i < pairs.length; i += 2) row.put((String) pairs[i], pairs[i + 1]);
        return row;
    }
    public static void writeRows(Path out, List<Map<String, Object>> data) throws IOException {
        List<String> lines = new ArrayList<>();
        for (Map<String, Object> row : data) lines.add(DynamicJson.encode(row));
        Files.write(out, lines, StandardCharsets.UTF_8, java.nio.file.StandardOpenOption.CREATE_NEW);
    }
    private void encode(MessageDigest d, PermutationSolution<?> s) {
        ints(d, s.getVariables()); ints(d, s.getVariablesid());
        ints(d, (List<?>) s.getAttribute("machine")); ints(d, s.getVariablesworker());
        for (double value : s.getObjectives()) put(d, Double.doubleToLongBits(value));
    }
    private void ints(MessageDigest d, List<?> values) {
        buffer.clear(); buffer.putInt(values.size()); d.update(buffer.array(), 0, 4);
        for (Object v : values) {
            buffer.clear(); buffer.putInt((Integer) v); d.update(buffer.array(), 0, 4);
        }
    }
    private void put(MessageDigest d, long value) {
        buffer.clear(); buffer.putLong(value); d.update(buffer.array(), 0, 8);
    }
    private static boolean contains(int[] values, int key) {
        for (int value : values) if (value == key) return true;
        return false;
    }
    private static MessageDigest digest() {
        try { return MessageDigest.getInstance("SHA-256"); }
        catch (NoSuchAlgorithmException e) { throw new AssertionError(e); }
    }
    private static String hex(byte[] data) {
        StringBuilder s = new StringBuilder(data.length * 2);
        for (byte b : data) s.append(Character.forDigit((b >>> 4) & 15, 16)).append(Character.forDigit(b & 15, 16));
        return s.toString();
    }
}
