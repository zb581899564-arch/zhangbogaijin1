package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.modelglobal.*;

/** Model mathematics and physically neutral reencoding; no candidate search or results archive. */
public final class PaModelAuditRun {
    private final Instance instance;
    private final DynamicParameters parameters;
    private final FirstStageCatalog catalog;
    private final Path out;
    private long decoderCalls, sources, rawOrderChanges, neutralKeyMatches, componentPairs;

    private PaModelAuditRun(Instance value, DynamicParameters fatigue, Path output) {
        instance = value; parameters = fatigue; catalog = new FirstStageCatalog(value); out = output;
    }

    private DynamicSchedule full(FourVectors vectors) {
        decoderCalls++; DynamicSchedule result = DynamicDecoder.full(instance, parameters, vectors.jobs(), vectors.factories(),
                vectors.machines(), vectors.workers(), null); DynamicValidator.validate(instance, parameters, result); return result;
    }

    private List<TypedScheduleGenome> reencode(Path source, long seed) throws Exception {
        List<TypedScheduleGenome> genomes = new ArrayList<>(); Random random = new Random(seed);
        for (String line : Files.readAllLines(source, StandardCharsets.UTF_8)) {
            String[] fields = line.split("\t"); if (Integer.parseInt(fields[2]) != 0) continue;
            FourVectors raw = new FourVectors(ProbeData.integers(fields[4]), ProbeData.integers(fields[5]),
                    ProbeData.integers(fields[6]), ProbeData.integers(fields[7]));
            TypedScheduleGenome genome = TypedScheduleGenome.fromVectors(catalog, raw); long localSeed = random.nextLong();
            TypedScheduleGenome reencoded = FactoryKeyReencoder.apply(catalog, genome, new Random(localSeed));
            TypedScheduleGenome neutral = FactoryKeyReencoder.apply(catalog,
                    TypedScheduleGenome.fromVectors(catalog, reverseFactoryView(raw, instance.factories())), new Random(localSeed));
            if (!Arrays.equals(reencoded.priorities(), neutral.priorities())
                    || !Arrays.equals(reencoded.allocations(), neutral.allocations())) throw new AssertionError("Neutral view changed model keys");
            neutralKeyMatches++; FourVectors child = reencoded.toVectors();
            if (!Arrays.equals(raw.jobs(), child.jobs())) rawOrderChanges++;
            DynamicSchedule before = full(raw), after = full(child); NeutralProbeSupport.sameTimeline(before, after);
            String[] expected = fields[3].split(",");
            for (int k = 0; k < 3; k++) if (Double.doubleToLongBits(before.objectives()[k])
                    != Double.doubleToLongBits(Double.parseDouble(expected[k]))) throw new AssertionError("Source objective mismatch");
            int[] factories = new int[instance.jobs()], resources = reencoded.allocations();
            for (int j = 0; j < factories.length; j++) factories[j] = catalog.factory(resources[j]);
            NeutralProbeSupport.append(out.resolve("genomes.jsonl"), NeutralProbeSupport.row("sourceIndex", Integer.parseInt(fields[0]),
                "role", fields[1], "factoryByJob", factories, "keysByJob", reencoded.priorities(),
                "rawGlobalOrderChanged", !Arrays.equals(raw.jobs(), child.jobs()), "sameFullPhysicalTimeline", true));
            genomes.add(reencoded); sources++;
        }
        if (sources != 80 || decoderCalls != 160 || neutralKeyMatches != 80) throw new AssertionError("Incomplete source QA");
        return genomes;
    }

    private void model(List<TypedScheduleGenome> genomes) throws Exception {
        int[][] factories = new int[genomes.size()][instance.jobs()]; double[][] keys = new double[genomes.size()][];
        for (int k = 0; k < genomes.size(); k++) {
            int[] ids = genomes.get(k).allocations(); keys[k] = genomes.get(k).priorities();
            for (int j = 0; j < ids.length; j++) factories[k][j] = catalog.factory(ids[j]);
        }
        long started = System.nanoTime(); PaDependencyModel model = new PaDependencyModel(factories, keys, instance.factories());
        double[][] matrix = model.matrix(); long modelNanos = System.nanoTime() - started; List<String> lines = new ArrayList<>();
        for (int a = 0; a < instance.jobs(); a++) for (int b = a + 1; b < instance.jobs(); b++) {
            double[] values = model.components(a, b); StringBuilder line = new StringBuilder(a + "\t" + b);
            for (double value : values) line.append('\t').append(value); lines.add(line.toString()); componentPairs++;
            if (matrix[a][b] != values[0] || matrix[b][a] != values[0]) throw new AssertionError("Asymmetric model");
        }
        Files.write(out.resolve("components.tsv"), lines, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        started = System.nanoTime(); List<int[]> subsets = new LinkageHierarchy(matrix).subsets(); long hierarchyNanos = System.nanoTime() - started;
        if (subsets.size() != 2 * instance.jobs() - 1 || subsets.get(subsets.size() - 1).length != instance.jobs())
            throw new AssertionError("Incomplete linkage hierarchy");
        NeutralProbeSupport.append(out.resolve("model.jsonl"), NeutralProbeSupport.row("subsets", subsets,
            "modelNanos", modelNanos, "hierarchyNanos", hierarchyNanos, "weight", PaDependencyModel.WEIGHT,
            "population", genomes.size(), "factories", instance.factories(), "jobs", instance.jobs()));
    }

    private static FourVectors reverseFactoryView(FourVectors original, int count) {
        int[] js = original.jobs(), fa = original.factories(), ma = original.machines(), wa = original.workers();
        int n = js.length, q = 0; int[] jobs = new int[n], factories = new int[n], machines = new int[n], workers = new int[n];
        for (int f = count - 1; f >= 0; f--) for (int p = 0; p < n; p++) if (fa[p] == f) {
            jobs[q] = js[p]; factories[q] = fa[p]; machines[q] = ma[p]; workers[q++] = wa[p];
        }
        return new FourVectors(jobs, factories, machines, workers);
    }

    public static void main(String[] args) throws Exception {
        Path input = Paths.get(args[0]), out = Paths.get(args[4]); Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir", input.getParent().toString()); System.setProperty("dhfsp.setupFile", args[1]);
        System.setProperty("dhfsp.standbyPower", "1"); String[] d = input.getFileName().toString().replace(".txt", "").split("_");
        EDHHFSPW raw = new EDHHFSPW(Integer.parseInt(d[0]), Integer.parseInt(d[1]), Integer.parseInt(d[2]), Integer.parseInt(d[3]));
        Instance instance = raw.getSchedulingInstance();
        PaModelAuditRun audit = new PaModelAuditRun(instance, DynamicInputs.fatigue(instance, Paths.get(args[2])), out); boolean complete = false;
        try {
            NeutralProbeSupport.append(out.resolve("loaded-identity.jsonl"), ClassResolutionProbe.capture("research.dynamic.PaModelAuditRun",
                "org.uma.jmetal.util.research.modelglobal.PaDependencyModel", "org.uma.jmetal.util.research.modelglobal.BinomialAttraction",
                "org.uma.jmetal.util.research.modelglobal.LinkageHierarchy", "org.uma.jmetal.util.research.modelglobal.FactoryKeyReencoder",
                "org.uma.jmetal.util.research.model.DynamicDecoder", "org.uma.jmetal.util.research.model.DynamicValidator"));
            audit.model(audit.reencode(Paths.get(args[3]), Long.parseLong(args[5]))); PaModelFixtures.write(out); complete = true;
        } finally {
            NeutralProbeSupport.append(out.resolve("receipt.jsonl"), NeutralProbeSupport.row("status", complete ? "COMPLETE" : "INCOMPLETE_RETAINED",
                "optimizationFE", 0, "decoderCalls", audit.decoderCalls, "sourceGenomes", audit.sources,
                "neutralViewExactKeyMatches", audit.neutralKeyMatches, "rawGlobalOrderChanges", audit.rawOrderChanges,
                "componentPairs", audit.componentPairs, "defaultMainlineChanged", false, "goalAchieved", false));
        }
    }
}
