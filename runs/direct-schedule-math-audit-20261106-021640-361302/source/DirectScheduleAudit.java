package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.modelglobal.*;

/** Known-source timeline checks and unscored structural fixtures; no optimizer or search archive. */
public final class DirectScheduleAudit {
    private final Instance instance;
    private final DynamicParameters parameters;
    private final FirstStageCatalog catalog;
    private long sources, fullQA, fixtures, fallbacks, rejected;

    private DirectScheduleAudit(Instance value, DynamicParameters params) {
        instance = value; parameters = params; catalog = new FirstStageCatalog(value);
    }

    private DynamicSchedule full(FourVectors value) {
        fullQA++;
        DynamicSchedule schedule = DynamicDecoder.full(instance, parameters, value.jobs(), value.factories(),
                value.machines(), value.workers(), null);
        DynamicValidator.validate(instance, parameters, schedule); return schedule;
    }

    private static void same(FourVectors a, FourVectors b) {
        if (!Arrays.equals(a.jobs(), b.jobs()) || !Arrays.equals(a.factories(), b.factories())
                || !Arrays.equals(a.machines(), b.machines()) || !Arrays.equals(a.workers(), b.workers()))
            throw new AssertionError("Four-vector view changed");
    }

    private List<DirectScheduleGenome> sources(Path path) throws Exception {
        List<DirectScheduleGenome> result = new ArrayList<>();
        for (String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            String[] fields = line.split("\t");
            FourVectors raw = new FourVectors(ProbeData.integers(fields[2]), ProbeData.integers(fields[3]),
                    ProbeData.integers(fields[4]), ProbeData.integers(fields[5]));
            DirectScheduleGenome genome = DirectScheduleGenome.fromVectors(catalog, raw);
            FourVectors roundtrip = genome.toVectors(); same(raw, roundtrip);
            same(raw, TypedScheduleGenome.fromVectors(catalog, roundtrip).toVectors());
            DynamicSchedule before = full(raw), after = full(roundtrip);
            NeutralProbeSupport.sameTimeline(before, after);
            String[] expected = fields[1].split(",");
            for (int k = 0; k < 3; k++) if (Double.doubleToLongBits(before.objectives()[k]) != Double.doubleToLongBits(Double.parseDouble(expected[k])))
                throw new AssertionError("Known paid source objective differs");
            int[] scratch = genome.positions(); scratch[0] = -1;
            scratch = genome.resources(); scratch[0] = -1; same(raw, genome.toVectors());
            result.add(genome); sources++;
        }
        return result;
    }

    private static int[][] byJob(FourVectors vectors) {
        int[] js = vectors.jobs(), fa = vectors.factories(), ma = vectors.machines(), wa = vectors.workers();
        int[][] result = new int[js.length][3];
        for (int p = 0; p < js.length; p++) result[js[p]] = new int[]{fa[p], ma[p], wa[p]};
        return result;
    }

    private void binding(DirectScheduleGenome parent, DirectScheduleGenome donor, int[] mask, int reference, DirectJointMove.Kind kind) {
        DirectJointMove move = DirectJointMove.apply(catalog, parent, donor, mask, reference, kind);
        fixtures++;
        if (move.emptyFactoryFallback) { fallbacks++; same(parent.toVectors(), move.genome.toVectors()); return; }
        FourVectors child = move.genome.toVectors(); int[][] actual = byJob(child), before = byJob(parent.toVectors()), incoming = byJob(donor.toVectors());
        Set<Integer> selected = new HashSet<>(); for (int job : mask) selected.add(job);
        for (int job = 0; job < actual.length; job++) if (!Arrays.equals(actual[job], selected.contains(job) ? incoming[job] : before[job]))
            throw new AssertionError("Resource tuple no longer attached to job");
        same(child, TypedScheduleGenome.fromVectors(catalog, child).toVectors());
        if (mask.length == catalog.jobs() && kind == DirectJointMove.Kind.ORDER) same(child, donor.toVectors());
        if (mask.length == catalog.jobs() && kind == DirectJointMove.Kind.POSITION
                && !Arrays.equals(child.jobs(), parent.toVectors().jobs())) throw new AssertionError("Position root order changed");
    }

    private void structuralFixtures(List<DirectScheduleGenome> genomes) {
        Random random = new Random(2026110603L); int n = catalog.jobs();
        for (int i = 0; i < 1000; i++) {
            DirectScheduleGenome parent = genomes.get(random.nextInt(genomes.size())), donor = genomes.get(random.nextInt(genomes.size()));
            List<Integer> jobs = new ArrayList<>(); for (int j = 0; j < n; j++) jobs.add(j);
            Collections.shuffle(jobs, random); int size = i % 20 == 0 ? n : 1 + random.nextInt(Math.min(n, 8));
            int[] mask = new int[size]; for (int j = 0; j < size; j++) mask[j] = jobs.get(j);
            for (DirectJointMove.Kind kind : DirectJointMove.Kind.values()) binding(parent, donor, mask, mask[0], kind);
        }
    }

    private void rejects(Runnable operation) {
        try { operation.run(); } catch (IllegalArgumentException expected) { rejected++; return; }
        throw new AssertionError("Malformed view was accepted");
    }

    private void malformed(DirectScheduleGenome value) {
        int[] repeated = value.positions(); repeated[0] = repeated[1];
        rejects(() -> DirectScheduleGenome.of(catalog, value.resources(), repeated));
        int[] invalid = value.resources(); invalid[0] = -1;
        rejects(() -> DirectScheduleGenome.of(catalog, invalid, value.positions()));
        int[] empty = value.resources(); Arrays.fill(empty, catalog.id(0, 0, 0));
        rejects(() -> DirectScheduleGenome.of(catalog, empty, value.positions()));
        rejects(() -> DirectJointMove.apply(catalog, value, value, new int[]{0,0}, 0, DirectJointMove.Kind.POSITION));
        rejects(() -> DirectJointMove.apply(catalog, value, value, new int[]{0}, 1, DirectJointMove.Kind.POSITION));
        rejects(() -> DirectJointMove.apply(catalog, value, value, new int[0], 0, DirectJointMove.Kind.ORDER));
        rejects(() -> DirectJointMove.apply(new FirstStageCatalog(instance), value, value, new int[]{0}, 0, DirectJointMove.Kind.ORDER));
    }

    public static void main(String[] args) throws Exception {
        Path input = Paths.get(args[0]), out = Paths.get(args[4]); Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir", input.getParent().toString()); System.setProperty("dhfsp.setupFile", args[1]);
        System.setProperty("dhfsp.standbyPower", "1"); String[] parts = input.getFileName().toString().replace(".txt", "").split("_");
        EDHHFSPW raw = new EDHHFSPW(Integer.parseInt(parts[0]), Integer.parseInt(parts[1]), Integer.parseInt(parts[2]), Integer.parseInt(parts[3]));
        Instance instance = raw.getSchedulingInstance(); DirectScheduleAudit audit = new DirectScheduleAudit(instance, DynamicInputs.fatigue(instance, Paths.get(args[2])));
        List<DirectScheduleGenome> sources = audit.sources(Paths.get(args[3])); audit.structuralFixtures(sources); audit.malformed(sources.get(0));
        NeutralProbeSupport.append(out.resolve("receipt.jsonl"), NeutralProbeSupport.row("status", "passed", "knownPaidSources", audit.sources,
            "fullTimelineQA", audit.fullQA, "unscoredJointFixtures", audit.fixtures, "emptyFactoryFallbacks", audit.fallbacks,
            "malformedFixturesRejected", audit.rejected, "newDynamicSearchFE", 0, "defaultMainlineChanged", false, "goalAchieved", false));
        NeutralProbeSupport.append(out.resolve("loaded-identity.jsonl"), ClassResolutionProbe.capture("research.dynamic.DirectScheduleAudit",
            "org.uma.jmetal.util.research.modelglobal.DirectScheduleGenome", "org.uma.jmetal.util.research.modelglobal.DirectPositionMixing",
            "org.uma.jmetal.util.research.modelglobal.DirectJointMove", "org.uma.jmetal.util.research.model.DynamicDecoder"));
    }
}
