package org.uma.jmetal.util.research.mechanism;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.Instance;

/** Proposal-local views: retain every factory's ordered (job,machine,worker) chain. */
public final class NeutralInterleavings {
    private NeutralInterleavings() { }

    @SuppressWarnings("unchecked")
    public static PermutationSolution<Integer> view(PermutationSolution<Integer> donor,
            PermutationSolution<Integer> recipient, Instance in, Random random, boolean aligned) {
        List<List<Integer>> queues = new ArrayList<>();
        for (int f = 0; f < in.factories(); f++) queues.add(new ArrayList<>());
        for (int p = 0; p < in.jobs(); p++) queues.get(donor.getVariableValueid(p)).add(p);
        int[] head = new int[in.factories()], rank = new int[in.jobs()];
        for (int p = 0; p < in.jobs(); p++) rank[recipient.getVariableValue(p)] = p;
        PermutationSolution<Integer> result = (PermutationSolution<Integer>) donor.copy();
        for (int p = 0; p < in.jobs(); p++) {
            int chosen = aligned ? firstByRank(donor, queues, head, rank)
                    : randomFactory(queues, head, random.nextInt(in.jobs() - p));
            int old = queues.get(chosen).get(head[chosen]++);
            result.setVariableValue(p, donor.getVariableValue(old));
            result.setVariableValueid(p, donor.getVariableValueid(old));
            machines(result).set(p, machines(donor).get(old));
            result.setVariableValueworker(p, donor.getVariableValueworker(old));
        }
        if (!physicalKey(donor, in).equals(physicalKey(result, in)))
            throw new AssertionError("Neutral view changed a factory chain");
        return result;
    }

    private static int firstByRank(PermutationSolution<Integer> donor,
            List<List<Integer>> queues, int[] head, int[] rank) {
        int best = -1, value = Integer.MAX_VALUE;
        for (int f = 0; f < head.length; f++) if (head[f] < queues.get(f).size()) {
            int candidate = rank[donor.getVariableValue(queues.get(f).get(head[f]))];
            if (candidate < value) { value = candidate; best = f; }
        }
        return best;
    }

    private static int randomFactory(List<List<Integer>> queues, int[] head, int ticket) {
        // Remaining-count weights give a uniform draw over all chain interleavings.
        for (int f = 0; f < head.length; f++) {
            ticket -= queues.get(f).size() - head[f];
            if (ticket < 0) return f;
        }
        throw new AssertionError("Invalid interleaving ticket");
    }

    public static String physicalKey(PermutationSolution<Integer> value, Instance in) {
        StringBuilder out = new StringBuilder();
        for (int f = 0; f < in.factories(); f++) {
            out.append('|').append(f).append(':');
            for (int p = 0; p < in.jobs(); p++) if (value.getVariableValueid(p) == f)
                out.append(value.getVariableValue(p)).append(',').append(machines(value).get(p))
                        .append(',').append(value.getVariableValueworker(p)).append(';');
        }
        return out.toString();
    }

    /** Untruncated input-to-donor swap path; not the post-mutation live QGS path. */
    @SuppressWarnings("unchecked")
    public static int[] path(PermutationSolution<Integer> parent,
            PermutationSolution<Integer> donor, Instance in) {
        PermutationSolution<Integer> current = (PermutationSolution<Integer>) parent.copy();
        int swaps = 0, neutral = 0;
        for (int p = 0; p < in.jobs(); p++) if (!current.getVariableValue(p).equals(donor.getVariableValue(p))) {
            int other = current.getVariables().indexOf(donor.getVariableValue(p));
            String before = physicalKey(current, in);
            Collections.swap(current.getVariables(), p, other);
            Collections.swap(current.getVariablesid(), p, other);
            Collections.swap(machines(current), p, other);
            Collections.swap(current.getVariablesworker(), p, other);
            swaps++; if (before.equals(physicalKey(current, in))) neutral++;
        }
        return new int[] {swaps, neutral};
    }

    @SuppressWarnings("unchecked")
    private static List<Integer> machines(PermutationSolution<Integer> s) {
        return (List<Integer>) s.getAttribute("machine");
    }
}
