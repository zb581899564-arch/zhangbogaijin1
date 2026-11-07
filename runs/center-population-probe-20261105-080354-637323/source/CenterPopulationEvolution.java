package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.classic.ClassicKernelBridge;
import org.uma.jmetal.util.research.classic.CenterMatingScores;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Isolated central population lifecycle; boundary QGS, family quotas and compose rule are unchanged. */
public final class CenterPopulationEvolution {
    private static final String MODE=System.getProperty("research.center.population","OFF");
    private static final Map<String,Long> counts=new LinkedHashMap<>();
    private final SearchState state;
    private final SwarmSupport support;
    private final SemanticAudit audit;
    private final MechanismCapture mechanism;
    private final ClassicKernelBridge kernel;

    static boolean enabled() {
        if (!Arrays.asList("OFF","FIXED","UNIFORM","TOURNAMENT").contains(MODE))
            throw new IllegalArgumentException("Unknown central population lifecycle");
        return !MODE.equals("OFF");
    }
    CenterPopulationEvolution(Instance instance,SearchState state,SwarmSupport support,
            SemanticAudit audit,MechanismCapture mechanism) {
        this.state=state; this.support=support; this.audit=audit; this.mechanism=mechanism;
        kernel=new ClassicKernelBridge(instance,state::checkLocalSlot);
    }
    private static void add(String key,long n) { counts.put(key,counts.getOrDefault(key,0L)+n); }
    private static int category(PermutationSolution<Integer> value) {
        Object family=value.getAttribute("cooperation.family"); return family==null?0:(Integer)family+1;
    }
    private static List<PermutationSolution<Integer>> values(List<Particle> group) {
        List<PermutationSolution<Integer>> out=new ArrayList<>();
        for (Particle particle:group) out.add(particle.current); return out;
    }
    private static Map<Integer,List<Integer>> categories(List<Particle> group) {
        Map<Integer,List<Integer>> result=new LinkedHashMap<>();
        for (int i=0;i<group.size();i++) result.computeIfAbsent(category(group.get(i).current),x->new ArrayList<>()).add(i);
        return result;
    }
    private int draw(List<PermutationSolution<Integer>> current,List<Integer> allowed,CenterMatingScores scores) {
        return MODE.equals("TOURNAMENT")?scores.draw(current,allowed)
            :allowed.get(SeededRandom.current().nextInt(allowed.size()));
    }
    List<Particle> evolve(List<Particle> initial,int steps) {
        List<Particle> group=initial;
        CenterMatingScores scores=MODE.equals("TOURNAMENT")?new CenterMatingScores(values(group),state::checkLocalSlot):null;
        for (int step=0;step<steps;step++) {
            state.checkLocalSlot();
            List<PermutationSolution<Integer>> current=values(group);
            Map<Integer,List<Integer>> byCategory=categories(group);
            List<Particle> children=new ArrayList<>(); Set<Long> firstParents=new HashSet<>();
            for (int slot=0;slot<group.size();slot++) {
                state.checkLocalSlot();
                List<Integer> allowed=byCategory.get(category(group.get(slot).current));
                int first=MODE.equals("FIXED")?slot:draw(current,allowed,scores);
                Particle parent=group.get(first); firstParents.add(parent.branchId());
                children.add(propose(parent,current,allowed,scores));
            }
            List<PermutationSolution<Integer>> union=new ArrayList<>(current); union.addAll(values(children));
            group=GlobalGroupPolicy.select(group,children,Direction.CENTER);
            if (mechanism!=null) mechanism.batch(Direction.CENTER,step,group);
            add("completedBatches",1); add("firstParentsPerBatchTotal",firstParents.size());
            // Keep union-front scores for the surviving objects; never rescore only the truncated population.
            if (MODE.equals("TOURNAMENT") && step+1<steps)
                scores=new CenterMatingScores(union,state::checkLocalSlot);
        }
        return group;
    }
    private Particle propose(Particle parent,List<PermutationSolution<Integer>> current,
            List<Integer> allowed,CenterMatingScores scores) {
        add("composeCalls",1);
        PermutationSolution<Integer> child=support==null?null:support.compose(parent.current,Direction.CENTER);
        boolean composed=child!=null;
        PermutationSolution<Integer> donor=parent.current;
        if (!composed) {
            donor=current.get(draw(current,allowed,scores));
            if (category(donor)!=category(parent.current)) throw new AssertionError("Cross-family mating");
            child=kernel.child(parent.current,donor);
            if (audit!=null) {audit.teacherConsumed(parent.current); audit.teacherConsumed(donor);}
        }
        if (mechanism!=null) mechanism.proposal(parent.current,parent.current,donor,composed);
        if (audit!=null) audit.generated(child,parent.current,composed);
        state.evaluate(child,"global",Direction.CENTER);
        if (category(child)!=category(parent.current)) throw new AssertionError("Child family changed");
        add(composed?"composedPaid":"ordinaryPaid",1); add("paid",1);
        // An EA birth starts its own history; all three EA controls use this identical policy.
        return new Particle(child);
    }
    public static Map<String,Object> diagnostics() {
        Map<String,Object> result=new LinkedHashMap<>();result.put("mode",MODE);result.put("counts",new LinkedHashMap<>(counts));
        result.put("centerReplacementEnabled",!MODE.equals("OFF"));
        result.put("qPolicy","Unchanged original path when OFF; no CENTER Q agent in EA modes");return result;
    }
}
