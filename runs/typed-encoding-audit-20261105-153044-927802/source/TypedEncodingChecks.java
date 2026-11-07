package research.dynamic;

import java.util.Arrays;
import java.util.Random;
import org.uma.jmetal.util.research.modelglobal.FirstStageCatalog;
import org.uma.jmetal.util.research.modelglobal.FourVectors;
import org.uma.jmetal.util.research.modelglobal.TypedScheduleGenome;

/** Pure representation checks; every malformed value is rejected without evaluating a schedule. */
final class TypedEncodingChecks {
    long checks, rejected;

    void catalog(FirstStageCatalog domain) {
        for (int id = 0; id < domain.size(); id++) {
            int[] tuple = domain.tuple(id);
            require(domain.id(tuple[0], tuple[1], tuple[2]) == id, "Catalog inverse");
            tuple[0] = -1; require(domain.factory(id) >= 0, "Catalog defensive copy");
        }
    }

    TypedScheduleGenome source(FirstStageCatalog domain, FourVectors input, Random noise) {
        TypedScheduleGenome genome = TypedScheduleGenome.fromVectors(domain, input);
        same(input, genome.toVectors());
        int n = domain.jobs(); double[] keys = new double[n];
        for (int p = 0; p < n; p++) keys[p] = noise.nextDouble();
        Arrays.sort(keys); keys[0] = 0; keys[n - 1] = 1;
        same(input, genome.withOrderedKeys(keys).toVectors());
        int[] resources = genome.allocations(); resources[0] = -1;
        double[] priorities = genome.priorities(); priorities[0] = Double.NaN;
        int[] original = input.jobs(); original[0] = -1;
        same(input, genome.toVectors());
        malformed(domain, genome, input);
        orderEdges(domain, genome);
        return genome;
    }

    private void malformed(FirstStageCatalog domain, TypedScheduleGenome genome, FourVectors input) {
        int[] allocation = genome.allocations(); double[] keys = genome.priorities();
        bad(() -> TypedScheduleGenome.of(domain, new int[0], keys));
        bad(() -> TypedScheduleGenome.of(domain, allocation, new double[0]));
        for (int invalid : new int[]{-1, domain.size()}) {
            int[] changed = allocation.clone(); changed[0] = invalid;
            bad(() -> TypedScheduleGenome.of(domain, changed, keys));
        }
        for (double invalid : new double[]{Double.NaN, Double.POSITIVE_INFINITY, -1e-9, 1 + 1e-9}) {
            double[] changed = keys.clone(); changed[0] = invalid;
            bad(() -> TypedScheduleGenome.of(domain, allocation, changed));
        }
        int[] empty = new int[domain.jobs()]; bad(() -> TypedScheduleGenome.of(domain, empty, keys));
        double[] tied = new double[domain.jobs()]; bad(() -> genome.withOrderedKeys(tied));
        int[] repeated = input.jobs(); repeated[0] = repeated[1];
        bad(() -> TypedScheduleGenome.fromVectors(domain,
                new FourVectors(repeated, input.factories(), input.machines(), input.workers())));
        int[] invalidMachine = input.machines(); invalidMachine[0] = Integer.MAX_VALUE;
        bad(() -> TypedScheduleGenome.fromVectors(domain,
                new FourVectors(input.jobs(), input.factories(), invalidMachine, input.workers())));
        int[] invalidWorker = input.workers(); invalidWorker[0] = -1;
        bad(() -> TypedScheduleGenome.fromVectors(domain,
                new FourVectors(input.jobs(), input.factories(), input.machines(), invalidWorker)));
        same(input, genome.toVectors()); // Failed construction and reencoding cannot mutate the receiver.
    }

    private void orderEdges(FirstStageCatalog domain, TypedScheduleGenome genome) {
        for (int kind = 0; kind < 4; kind++) {
            double[] keys = new double[domain.jobs()];
            for (int j = 0; j < keys.length; j++) keys[j] = kind == 0 ? 0 : kind == 1 ? 1
                    : kind == 2 ? (j % 3) * .5 : (j % 2 == 0 ? -0.0 : 0.0);
            TypedScheduleGenome edge = TypedScheduleGenome.of(domain, genome.allocations(), keys);
            int[] jobs = edge.toVectors().jobs();
            for (int p = 1; p < jobs.length; p++) {
                int a = jobs[p - 1], b = jobs[p];
                require(keys[a] < keys[b] || (keys[a] == keys[b] && a > b), "Source key order");
            }
            require(Arrays.equals(genome.allocations(), edge.allocations()), "Keys cannot change resources");
        }
    }

    void same(FourVectors first, FourVectors second) {
        require(Arrays.equals(first.jobs(), second.jobs()) && Arrays.equals(first.factories(), second.factories())
                && Arrays.equals(first.machines(), second.machines()) && Arrays.equals(first.workers(), second.workers()),
                "Raw four-vector roundtrip, including global interleaving");
    }

    private void bad(Runnable action) {
        try { action.run(); } catch (IllegalArgumentException expected) { rejected++; checks++; return; }
        throw new AssertionError("Malformed representation was accepted");
    }

    private void require(boolean value, String message) {
        if (!value) throw new AssertionError(message); checks++;
    }
}
