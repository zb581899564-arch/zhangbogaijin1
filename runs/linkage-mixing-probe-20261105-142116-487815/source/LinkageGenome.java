package research.dynamic;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.search.LinkageSearchBridge;

/** Complete job tuples and physical within-factory ranks; neutral global interleavings are ignored. */
final class LinkageGenome {
    static final class Proposal {
        final PermutationSolution<Integer> point;final boolean fallback;
        Proposal(PermutationSolution<Integer> value, boolean empty) { point = value;fallback = empty; }
    }
    private final int[] factory, machine, worker;
    private final double[] rank;
    private final int factories;
    private LinkageGenome(PermutationSolution<Integer> value, int count) {
        factories = count;int n = value.getNumberOfVariables();factory = new int[n];machine = new int[n];worker = new int[n];rank = new double[n];
        int[] sizes = new int[count], seen = new int[count];
        for (int i = 0; i < n; i++) sizes[value.getVariableValueid(i)]++;
        List<Integer> machines = machines(value);
        for (int i = 0; i < n; i++) {
            int job = value.getVariableValue(i), f = value.getVariableValueid(i);
            factory[job] = f;machine[job] = machines.get(i);worker[job] = value.getVariableValueworker(i);
            rank[job] = (seen[f]++ + .5) / sizes[f];
        }
    }
    private LinkageGenome(LinkageGenome value) {
        factories = value.factories;factory = value.factory.clone();machine = value.machine.clone();
        worker = value.worker.clone();rank = value.rank.clone();
    }

    static Proposal donate(PermutationSolution<Integer> recipient, PermutationSolution<Integer> donor,
            int[] subset, int factories) {
        LinkageGenome result = new LinkageGenome(new LinkageGenome(recipient, factories));
        LinkageGenome source = new LinkageGenome(donor, factories);
        for (int job : subset) {
            result.factory[job] = source.factory[job];result.machine[job] = source.machine[job];
            result.worker[job] = source.worker[job];result.rank[job] = source.rank[job];
        }
        boolean[] present = new boolean[factories];for (int f : result.factory) present[f] = true;
        for (boolean value : present) if (!value) return new Proposal(copy(recipient), true);
        return new Proposal(result.solution(recipient), false);
    }

    private PermutationSolution<Integer> solution(PermutationSolution<Integer> template) {
        Integer[] jobs = new Integer[factory.length];for (int j = 0; j < jobs.length; j++) jobs[j] = j;
        Arrays.sort(jobs, Comparator.comparingInt((Integer j) -> factory[j]).thenComparingDouble(j -> rank[j]).thenComparingInt(j -> j));
        PermutationSolution<Integer> result = copy(template);List<Integer> machines = machines(result);
        for (int position = 0; position < jobs.length; position++) {
            int job = jobs[position];result.setVariableValue(position, job);result.setVariableValueid(position, factory[job]);
            machines.set(position, machine[job]);result.setVariableValueworker(position, worker[job]);
        }
        return result;
    }

    static String physical(PermutationSolution<Integer> value, int factories) {
        StringBuilder result = new StringBuilder();List<Integer> machines = machines(value);
        for (int f = 0; f < factories; f++) {
            result.append(f).append(':');
            for (int p = 0; p < value.getNumberOfVariables(); p++) if (value.getVariableValueid(p) == f)
                result.append(value.getVariableValue(p)).append(',').append(machines.get(p)).append(',').append(value.getVariableValueworker(p)).append(';');
            result.append('|');
        }
        return result.toString();
    }
    static PermutationSolution<Integer> neutral(PermutationSolution<Integer> value, int factories) {
        List<Integer> positions = new ArrayList<>();
        for (int f = factories - 1; f >= 0; f--) for (int p = 0; p < value.getNumberOfVariables(); p++)
            if (value.getVariableValueid(p) == f) positions.add(p);
        PermutationSolution<Integer> result = copy(value);List<Integer> sourceMachines = machines(value), targetMachines = machines(result);
        for (int p = 0; p < positions.size(); p++) {
            int q = positions.get(p);result.setVariableValue(p, value.getVariableValue(q));result.setVariableValueid(p, value.getVariableValueid(q));
            targetMachines.set(p, sourceMachines.get(q));result.setVariableValueworker(p, value.getVariableValueworker(q));
        }
        return result;
    }
    static PermutationSolution<Integer> copy(PermutationSolution<Integer> value) { return LinkageSearchBridge.copy(value); }
    @SuppressWarnings("unchecked")
    private static List<Integer> machines(PermutationSolution<Integer> value) { return (List<Integer>)value.getAttribute("machine"); }
}
