package org.uma.jmetal.util.research.search;

import java.util.*;
import java.util.function.Supplier;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.mechanism.KernelVariants;
import org.uma.jmetal.util.research.model.Instance;

/** Paid two-proposal competition for MAKESPAN; halve its update count to preserve its FE quota. */
public final class GlobalProposalPack {
    private static final String MODE = System.getProperty("research.pack.mode", "BASE");
    private static KernelVariants kernels;
    private static final Map<String,Long> counts = new LinkedHashMap<>();
    private GlobalProposalPack() { }
    static void initialize(Instance instance, SearchConfig config, Runnable checkpoint) {
        if (!MODE.equals("BASE")) kernels = new KernelVariants(instance, config, checkpoint);
    }
    private static boolean paired(Direction role) { return role == Direction.MAKESPAN && MODE.endsWith("PAIR"); }
    static int steps(Direction role, int iterations) {
        if (paired(role) && iterations % 2 != 0) throw new IllegalArgumentException("Uneven pair budget");
        return paired(role) ? iterations / 2 : iterations;
    }
    private static void count(String key) { counts.put(key, counts.getOrDefault(key,0L)+1); }
    static PermutationSolution<Integer> first(PermutationSolution<Integer> parent,
            PermutationSolution<Integer> personal, PermutationSolution<Integer> leader, Direction role,
            Supplier<PermutationSolution<Integer>> original) {
        if (MODE.equals("BASE") || role != Direction.MAKESPAN) return original.get();
        String kernel = MODE.startsWith("CG_") ? "CLASSIC_GLOBAL" : "JOB_ALIGNED";
        count("first."+kernel); return kernels.child(kernel,parent,personal,leader);
    }
    static PermutationSolution<Integer> second(PermutationSolution<Integer> parent,
            PermutationSolution<Integer> personal, PermutationSolution<Integer> leader, Direction role) {
        if (!paired(role)) return null;
        String kernel = MODE.equals("JA_PAIR") ? "JOB_ALIGNED" : "CLASSIC_GLOBAL";
        count("second."+kernel); return kernels.child(kernel,parent,personal,leader);
    }
    static PermutationSolution<Integer> choose(PermutationSolution<Integer> first, PermutationSolution<Integer> second) {
        if (second == null) return first;
        boolean takeSecond = second.getObjective(0) < first.getObjective(0);
        count(takeSecond ? "secondWon" : "firstWonOrTied"); return takeSecond ? second : first;
    }
    public static Map<String,Object> diagnostics() {
        Map<String,Object> out=new LinkedHashMap<>();out.put("mode",MODE);out.put("counts",counts);
        out.put("budget", "Paired M uses25 updates x15 particles x2 paid proposals; unpaired M uses50 x15 x1. Other roles unchanged.");
        return out;
    }
}
