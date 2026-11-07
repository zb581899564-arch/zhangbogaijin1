package org.uma.jmetal.util.research.cooperation;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.*;
import java.util.function.LongSupplier;
import java.util.function.Supplier;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.search.SwarmSupport;

/** Isolated finite-pool certificate and irreversible protection release; no assertion about future search. */
public final class ContextRelease {
    private static final String MODE = System.getProperty("research.release.mode", "KEEP");
    private static final boolean COMPOSE = Boolean.parseBoolean(System.getProperty("research.release.compose", "true"));
    private static final boolean[] released = new boolean[4];
    private static final List<Map<String,Object>> events = new ArrayList<>();
    private static final Map<Integer,Integer> plan = new LinkedHashMap<>();
    private static Supplier<List<PermutationSolution<Integer>>> archive;
    private static LongSupplier successful;
    private static Random random;
    private static int generation;
    private static long nanos, compatibleFreeObservations, compatibleFreeRequests;
    private ContextRelease() { }

    public static void configure(Supplier<List<PermutationSolution<Integer>>> known, LongSupplier paid, long seed) throws Exception {
        if (!Arrays.asList("KEEP", "BOUND", "ALL", "RANDOM_MATCHED").contains(MODE))
            throw new IllegalArgumentException("Unknown release mode " + MODE);
        archive = known; successful = paid; random = new Random(seed ^ 0x24AB731L);
        if (MODE.equals("RANDOM_MATCHED")) for (String line : Files.readAllLines(
                Paths.get(System.getProperty("research.release.plan")), StandardCharsets.UTF_8)) {
            if (line.startsWith("generation") || line.trim().isEmpty()) continue;
            String[] c = line.split(","); plan.put(Integer.parseInt(c[0]), Integer.parseInt(c[1]));
        }
    }
    static boolean released(int family) { return family >= 0 && released[family]; }
    static int protectedCount() { int n=0; for (boolean r:released) if(!r)n++; return n; }
    static void releaseForCheck(int family) { released[family]=true; }
    static void normalize(PermutationSolution<Integer> s) {
        Object f=s.getAttribute(FamilyContexts.FAMILY);
        if(f!=null && released((Integer)f)) {
            s.getAttributes().remove(FamilyContexts.FAMILY); s.getAttributes().remove(FamilyContexts.FIXED);
        }
    }
    static int[] quotas() {
        int[] q={100-5*protectedCount(),0,0,0,0};
        for(int f=0;f<4;f++)if(!released[f])q[f+1]=5; return q;
    }
    static int category(PermutationSolution<Integer> s) { normalize(s); return FamilyContexts.family(s)+1; }
    static int poolFamily(PermutationSolution<Integer> s,FamilyContexts contexts,boolean request) {
        int f=FamilyContexts.family(s); if(f>=0 && !released[f])return f;
        if(MODE.equals("KEEP"))return -1;
        int[] assignment=FamilyContexts.byJob(s);
        for(int i=0;i<4;i++)if(released[i] && Arrays.equals(assignment,contexts.assignment(i))) {
            if(request)compatibleFreeRequests++;else compatibleFreeObservations++;return i;
        }
        return -1;
    }
    static boolean compositionEnabled() { return COMPOSE; }

    /** Bound for the Cartesian product of retained compatible per-factory records, in minimization form. */
    static double[] lowerBound(List<List<double[]>> factories) {
        double[] result=new double[3];
        for(List<double[]> records:factories) {
            if(records.isEmpty())return null;
            double[] low={Double.POSITIVE_INFINITY,Double.POSITIVE_INFINITY,Double.POSITIVE_INFINITY};
            for(double[] r:records)for(int k=0;k<3;k++)low[k]=Math.min(low[k],r[k]);
            result[0]=Math.max(result[0],low[0]);result[1]+=low[1];result[2]+=low[2];
        }
        // Conservative slack makes roundoff less likely to certify coverage; never relax dominance.
        for(int k=0;k<3;k++)result[k]-=32*Math.ulp(result[k]);return result;
    }
    static boolean covered(double[] bound,List<PermutationSolution<Integer>> known) {
        if(bound==null)return false;
        for(PermutationSolution<Integer> p:known) {
            boolean yes=true;for(int k=0;k<3;k++)yes &= p.getObjective(k)<=bound[k];if(yes)return true;
        }
        return false;
    }
    public static void afterGlobal(SwarmSupport support,List<PermutationSolution<Integer>> population) {
        if(MODE.equals("KEEP"))return;
        if(!(support instanceof CooperationSupport))throw new IllegalArgumentException("Release requires sharing support");
        long start=System.nanoTime();generation++;
        double[][] bounds=((CooperationSupport)support).retainedPoolLowerBounds();
        List<PermutationSolution<Integer>> known=archive.get();List<Integer> certified=new ArrayList<>(),chosen=new ArrayList<>();
        for(int f=0;f<4;f++)if(!released[f] && covered(bounds[f],known))certified.add(f);
        if(MODE.equals("BOUND"))chosen.addAll(certified);
        else if(MODE.equals("ALL"))for(int f=0;f<4;f++)if(!released[f])chosen.add(f);
        else {
            List<Integer> remaining=new ArrayList<>();for(int f=0;f<4;f++)if(!released[f])remaining.add(f);
            Collections.shuffle(remaining,random);int n=plan.getOrDefault(generation,0);
            if(n<0 || n>remaining.size())throw new IllegalArgumentException("Invalid matched release count");
            chosen.addAll(remaining.subList(0,n));
        }
        for(int f:chosen)released[f]=true;
        for(PermutationSolution<Integer> s:population)normalize(s);
        Map<String,Object> e=new LinkedHashMap<>();e.put("generation",generation);e.put("paidFE",successful.getAsLong());
        e.put("bounds",bounds);e.put("certified",certified);e.put("releasedNow",chosen);e.put("quotas",quotas());events.add(e);
        nanos+=System.nanoTime()-start;
    }
    public static Map<String,Object> diagnostics() {
        Map<String,Object> out=new LinkedHashMap<>();out.put("mode",MODE);out.put("composition",COMPOSE);
        out.put("events",events);out.put("protectedFamilies",protectedCount());out.put("decisionSeconds",nanos/1e9);
        out.put("compatibleFreeObservations",compatibleFreeObservations);out.put("compatibleFreeRequests",compatibleFreeRequests);
        return out;
    }
}
