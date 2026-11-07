package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.util.research.modelglobal.FirstStageCatalog;
import org.uma.jmetal.util.research.modelglobal.TypedScheduleGenome;

/** Joint two-job proposals from the complete legal domain or its frozen initial-support complement. */
final class DomainJointMove {
    private final FirstStageCatalog catalog;
    private final long randomSeed;
    private final Random random;
    private final int[][] legal, jobs, support, complement;
    private final int[] factoryByJob, eligible;
    private long proposals, noEligible, unavailable, novelFirst;

    DomainJointMove(FirstStageCatalog domain, List<TypedScheduleGenome> initial, long seed) {
        if (initial.size() != 5) throw new IllegalArgumentException("Exactly five initial family donors required");
        catalog = domain; randomSeed = seed ^ 0x4f2a91L; random = new Random(randomSeed);
        legal = completeLegalDomain(); factoryByJob = assignments(initial.get(0));
        jobs = factoryJobs(); support = initialSupport(initial); complement = complements();
        List<Integer> available = new ArrayList<>();
        for (int f = 0; f < jobs.length; f++) if (jobs[f].length >= 2) available.add(f);
        eligible = array(available);
    }

    Result propose(TypedScheduleGenome parent, boolean novel) {
        proposals++;
        if (eligible.length == 0) {
            noEligible++; if (novel) unavailable++;
            return new Result(parent, new int[0], false, GomRecords.row("generator", novel ? "NOVEL" : "LEGAL",
                "factory", -1, "jobs", new int[0], "rank1", null, "rank2", null, "key1", null, "key2", null,
                "complementSize", 0, "noveltyUnavailable", novel, "noEligibleFactory", true,
                "noOp", true, "randomDraws", 0));
        }
        int factory = eligible[random.nextInt(eligible.length)];
        int firstIndex = random.nextInt(jobs[factory].length);
        int secondIndex = random.nextInt(jobs[factory].length - 1);
        if (secondIndex >= firstIndex) secondIndex++;
        int first = jobs[factory][firstIndex], second = jobs[factory][secondIndex];
        double rank1 = random.nextDouble(), rank2 = random.nextDouble();
        double key1 = random.nextDouble(), key2 = random.nextDouble();
        boolean missing = novel && complement[first].length == 0;
        int[] firstDomain = novel && !missing ? complement[first] : legal[factory];
        int resource1 = firstDomain[(int) (rank1 * firstDomain.length)];
        int resource2 = legal[factory][(int) (rank2 * legal[factory].length)];
        int[] resources = parent.allocations(); double[] keys = parent.priorities();
        boolean noOp = resources[first] == resource1 && resources[second] == resource2
            && keys[first] == key1 && keys[second] == key2;
        resources[first] = resource1; resources[second] = resource2; keys[first] = key1; keys[second] = key2;
        if (missing) unavailable++; else if (novel) novelFirst++;
        Map<String,Object> metadata = GomRecords.row("generator", novel ? "NOVEL" : "LEGAL", "factory", factory,
            "jobs", new int[]{first, second}, "rank1", rank1, "rank2", rank2, "key1", key1, "key2", key2,
            "resource1", resource1, "resource2", resource2, "firstDomainSize", firstDomain.length,
            "secondDomainSize", legal[factory].length, "complementSize", complement[first].length,
            "noveltyUnavailable", missing, "noEligibleFactory", false, "noOp", noOp,
            "randomDraws", 7);
        return new Result(TypedScheduleGenome.of(catalog, resources, keys), new int[]{first, second}, false, metadata);
    }

    private int[][] completeLegalDomain() {
        List<List<Integer>> byFactory = lists(catalog.factories());
        for (int id = 0; id < catalog.size(); id++) byFactory.get(catalog.factory(id)).add(id);
        int[][] result = arrays(byFactory);
        for (int[] values : result) if (values.length == 0) throw new AssertionError("Empty complete legal resource domain");
        return result;
    }

    private int[] assignments(TypedScheduleGenome genome) {
        int[] resources = genome.allocations(), result = new int[resources.length];
        for (int job = 0; job < result.length; job++) result[job] = catalog.factory(resources[job]);
        return result;
    }

    private int[][] factoryJobs() {
        List<List<Integer>> result = lists(catalog.factories());
        for (int job = 0; job < catalog.jobs(); job++) result.get(factoryByJob[job]).add(job);
        return arrays(result);
    }

    private int[][] initialSupport(List<TypedScheduleGenome> initial) {
        List<SortedSet<Integer>> values = new ArrayList<>();
        for (int job = 0; job < catalog.jobs(); job++) values.add(new TreeSet<>());
        for (TypedScheduleGenome member : initial) {
            if (!Arrays.equals(factoryByJob, assignments(member))) throw new AssertionError("Initial family assignments differ");
            int[] resources = member.allocations();
            for (int job = 0; job < catalog.jobs(); job++) values.get(job).add(resources[job]);
        }
        int[][] result = new int[catalog.jobs()][];
        for (int job = 0; job < result.length; job++) result[job] = array(values.get(job));
        return result;
    }

    private int[][] complements() {
        int[][] result = new int[catalog.jobs()][];
        for (int job = 0; job < result.length; job++) {
            List<Integer> missing = new ArrayList<>();
            for (int id : legal[factoryByJob[job]]) if (Arrays.binarySearch(support[job], id) < 0) missing.add(id);
            result[job] = array(missing);
        }
        return result;
    }

    Map<String,Object> domain() {
        List<Map<String,Object>> tuples = new ArrayList<>(), factories = new ArrayList<>(), initial = new ArrayList<>();
        for (int id = 0; id < catalog.size(); id++) {
            int[] tuple = catalog.tuple(id);
            tuples.add(GomRecords.row("id", id, "factory", tuple[0], "machine", tuple[1], "worker", tuple[2]));
        }
        for (int f = 0; f < catalog.factories(); f++) factories.add(GomRecords.row("factory", f,
            "jobs", jobs[f], "legalResourceIds", legal[f], "eligible", jobs[f].length >= 2));
        for (int job = 0; job < catalog.jobs(); job++) initial.add(GomRecords.row("job", job,
            "factory", factoryByJob[job], "support", support[job], "complement", complement[job]));
        return GomRecords.row("catalog", tuples, "factories", factories, "initialSupport", initial,
            "eligibleFactories", eligible, "rng", "java.util.Random", "rngSeed", randomSeed,
            "supportRule", "Frozen resources of this job in the five initial family receivers; never updated",
            "drawOrder", "nextInt(eligible), nextInt(n), nextInt(n-1), nextDouble rank1, rank2, key1, key2",
            "domainRule", "All FirstStageCatalog IDs in increasing order, restricted only to the fixed factory");
    }

    Map<String,Object> receipt() {
        return GomRecords.row("rngSeed", randomSeed, "proposalsGenerated", proposals, "noEligibleFactory", noEligible,
            "noveltyUnavailable", unavailable, "novelFirstJobGenerated", novelFirst,
            "counterScope", "Generated proposals, including a subsequently failed paid attempt");
    }

    private static List<List<Integer>> lists(int count) {
        List<List<Integer>> result = new ArrayList<>();
        for (int i = 0; i < count; i++) result.add(new ArrayList<>()); return result;
    }
    private static int[][] arrays(List<List<Integer>> values) {
        int[][] result = new int[values.size()][];
        for (int i = 0; i < result.length; i++) result[i] = array(values.get(i)); return result;
    }
    private static int[] array(Collection<Integer> values) {
        int[] result = new int[values.size()]; int at = 0;
        for (int value : values) result[at++] = value; return result;
    }

    static final class Result {
        final TypedScheduleGenome genome;
        final int[] mask;
        final boolean fallback;
        final Map<String,Object> metadata;
        Result(TypedScheduleGenome value, int[] selected, boolean unchanged, Map<String,Object> record) {
            genome = value; mask = selected.clone(); fallback = unchanged; metadata = record;
        }
    }
}
