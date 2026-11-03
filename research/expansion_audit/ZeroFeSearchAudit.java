package org.uma.jmetal.util.research.search;

import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Executes frozen selection and JS guidance on synthetic immutable costs: no Problem/evaluate/decoder. */
public final class ZeroFeSearchAudit {
    private ZeroFeSearchAudit() { }

    @SuppressWarnings("unchecked")
    private static PermutationSolution<Integer> solution(double[] objectives, List<Integer> jobs) {
        return (PermutationSolution<Integer>) Proxy.newProxyInstance(
                PermutationSolution.class.getClassLoader(), new Class<?>[] {PermutationSolution.class},
                (proxy, method, args) -> {
                    switch (method.getName()) {
                    case "getObjective": return objectives[(Integer) args[0]];
                    case "getNumberOfObjectives": return 3;
                    case "copy": return proxy; // Costs are immutable; no copy mutation in these probes.
                    case "getVariables": return jobs;
                    case "getVariableValue": return jobs.get((Integer) args[0]);
                    case "equals": return proxy == args[0];
                    case "hashCode": return System.identityHashCode(proxy);
                    default: throw new UnsupportedOperationException(method.getName());
                    }
                });
    }

    @SuppressWarnings("unchecked")
    private static void selection() throws Exception {
        List<Particle> current = new ArrayList<>();
        List<PermutationSolution<Integer>> front = new ArrayList<>();
        for (int i = 0; i < 100; i++) {
            PermutationSolution<Integer> s = solution(new double[] {i + 1, 100 - i, 1}, null);
            front.add(s); current.add(new Particle(s));
        }
        Method select = CanonicalHmopso.class.getDeclaredMethod("select", List.class, int.class);
        select.setAccessible(true);
        List<Particle> selected = (List<Particle>) select.invoke(null, current, 100);
        if (!new HashSet<>(selected).equals(new HashSet<>(current))) throw new AssertionError("Identity loss");
        double[] fitness = ParetoTools.fitness(front);
        for (double value : fitness) if (value != 1) throw new AssertionError("Unexpected PDDR tie");
        List<Particle> union = new ArrayList<>();
        for (int i = 0; i < 100; i++) union.add(new Particle(solution(new double[] {1, 1, 1}, null)));
        for (int i = 0; i < 100; i++) union.add(new Particle(solution(new double[] {2, 2, 2}, null)));
        selected = (List<Particle>) select.invoke(null, union, 100);
        for (Particle p : selected) if (p.current.getObjective(0) != 1) throw new AssertionError("Union selection");
        System.out.println("SELECT100_OF100_KEEP_ALL; ND_FRONT100_PDDR_ALL1; SELECT100_OF200_FILTERS_DOMINATED");
    }

    private static void guidance() throws Exception {
        List<Integer> jobs = new ArrayList<>(Arrays.asList(0, 1, 2, 3));
        PermutationSolution<Integer> child = solution(new double[] {1, 1, 1}, jobs);
        PermutationSolution<Integer> guide = solution(new double[] {1, 1, 1}, Arrays.asList(1, 2, 3, 0));
        ParticleOperators op = new ParticleOperators(null, new SearchConfig().resolved(4));
        Method move = ParticleOperators.class.getDeclaredMethod("moveJobSequence", PermutationSolution.class, PermutationSolution.class);
        move.setAccessible(true); SeededRandom.reset(0); move.invoke(op, child, guide);
        int[] positionFactory = {0, 1, 0, 1};
        int changes = 0;
        for (int p = 0; p < 4; p++) if (positionFactory[p] != positionFactory[jobs.get(p)]) changes++;
        if (changes != 2) throw new AssertionError("Expected two rebound job-factory relations");
        System.out.println("JS_GUIDANCE=" + jobs + ";POSITION_FA_UNCHANGED=[0,1,0,1];JOB_FA_REBOUND=" + changes);
    }

    public static void main(String[] args) throws Exception {
        selection(); guidance();
        System.out.println("ZERO_FE_SEARCH_AUDIT_PASS newFE=0 optimizerRuns=0");
    }
}
