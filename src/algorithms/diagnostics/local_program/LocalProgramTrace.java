package org.uma.jmetal.util.research.search;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.Solution;
import research.dynamic.DynamicJson;

/** Observe one original VNS outer iteration as a complete shake-descent-accept program. */
public final class LocalProgramTrace {
    private static ProgramPaidHistory history;
    private static ProgramGenomeEvidence genomes;
    private static int factories;
    private static long nextId, completed, partial, insidePaid;
    private static Episode active;
    private static final List<Map<String,Object>> EPISODES = new ArrayList<>();
    private LocalProgramTrace() { }
    public static void configure(int count) { factories = count;history = new ProgramPaidHistory(count);genomes = new ProgramGenomeEvidence(history); }

    public static void paid(Solution<?> value, long fe, boolean changed) {
        String phase = active == null ? "OUTSIDE" : active.shakeFE == null ? "SHAKE" : "DESCENT";
        history.paid((PermutationSolution<?>)value, fe, active == null ? 0 : active.id, phase, changed);
        if (active != null) insidePaid++;
    }
    static void begin(PermutationSolution<Integer> parent, int factory, int operator, Direction preference,
            int physicalGroup, List<PermutationSolution<Integer>> reference) {
        if (active != null) throw new AssertionError("Nested VNS program");
        active = new Episode(++nextId, factory, operator, preference, physicalGroup, genomes.reference(reference), parent);
    }
    static void shaken(PermutationSolution<Integer> point) {
        if (active == null || active.shakeFE != null || history.paid() != active.startFE + 1)
            throw new AssertionError("A VNS shake must cost exactly one successful evaluation");
        active.shakeFE = history.paid();active.shake = point.getObjectives().clone();
        active.identity = active.entryKey.equals(CandidatePhysicalKey.of(point, factories));
        if (active.sample != null) active.sample.put("shaken", genomes.genome(point));
    }
    static void finished(PermutationSolution<Integer> improved, boolean accepted) {
        if (active == null || active.shakeFE == null) throw new AssertionError("Missing VNS shake");
        active.exit = improved.getObjectives().clone();active.accepted = accepted;
        if (active.sample != null) active.sample.put("improved", genomes.genome(improved));
    }
    static void end(boolean complete) {
        if (active == null) throw new AssertionError("No VNS program to close");
        Map<String,Object> row = active.row(complete);EPISODES.add(row);
        if (active.sample != null) {
            active.sample.put("completed", complete);active.sample.put("endFE", history.paid());
            genomes.samples.add(active.sample);
        }
        if (complete) completed++;else partial++;
        active = null;
    }

    public static void write(Path out) throws Exception {
        history.write(out);lines(out.resolve("local-programs.jsonl"), EPISODES);
        lines(out.resolve("program-references.jsonl"), genomes.references);
        lines(out.resolve("program-samples.jsonl"), genomes.samples);
        Map<String,Object> receipt = new LinkedHashMap<>();receipt.put("paidObservations", history.paid());
        receipt.put("physicalKeysStored", history.distinctKeys());receipt.put("programsStarted", nextId);
        receipt.put("programsCompleted", completed);receipt.put("programsPartial", partial);
        receipt.put("programSuccessfulFE", insidePaid);receipt.put("activeProgramCleared", active == null);
        receipt.put("samplePolicy", "Every257th outer VNS iteration starting at1; no RNG or outcome filtering");
        lines(out.resolve("local-program-receipt.json"), java.util.Collections.singletonList(receipt));
    }
    private static void lines(Path path, List<Map<String,Object>> values) throws Exception {
        List<String> text = new ArrayList<>();for (Map<String,Object> row : values) text.add(DynamicJson.encode(row));
        Files.write(path, text, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
    }

    private static final class Episode {
        final long id, startFE;
        final int factory, operator, group, reference;
        final String preference;
        final double[] entry;
        final CandidatePhysicalKey entryKey;
        final Map<String,Object> sample;
        Long shakeFE;double[] shake, exit;boolean identity, accepted;
        Episode(long index, int f, int op, Direction d, int g, int ref, PermutationSolution<Integer> parent) {
            id = index;startFE = history.paid();factory = f;operator = op;group = g;reference = ref;preference = d.name();
            history.physicalBirth(parent);entry = parent.getObjectives().clone();entryKey = CandidatePhysicalKey.of(parent, factories);
            sample = id % 257 == 1 ? new LinkedHashMap<>() : null;
            if (sample != null) { sample.put("episode", id);sample.put("startFE", startFE);sample.put("reference", ref);sample.put("entry", genomes.genome(parent)); }
        }
        Map<String,Object> row(boolean complete) {
            if (complete && (exit == null || shakeFE == null)) throw new AssertionError("Incomplete program labeled complete");
            Map<String,Object> out = new LinkedHashMap<>();
            out.put("episode", id);out.put("factory", factory);out.put("operator", operator);out.put("physicalGroup", group);
            out.put("preference", preference);out.put("reference", reference);out.put("startFE", startFE);
            out.put("shakeFE", shakeFE);out.put("endFE", history.paid());out.put("completed", complete);
            out.put("identityShake", shakeFE == null ? null : identity);out.put("entry", entry);out.put("shaken", shake);
            out.put("improved", exit);out.put("accepted", complete ? accepted : null);return out;
        }
    }
}
