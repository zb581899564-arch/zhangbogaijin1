package org.uma.jmetal.util.research.classic;

import java.lang.reflect.Proxy;
import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Zero-decoder fixture: inherited union scores, category restriction and original tournament RNG. */
public final class CenterPopulationChecks {
    private CenterPopulationChecks() { }
    @SuppressWarnings("unchecked")
    private static PermutationSolution<Integer> point(double... objectives) {
        return (PermutationSolution<Integer>)Proxy.newProxyInstance(PermutationSolution.class.getClassLoader(),
            new Class<?>[]{PermutationSolution.class},(proxy,method,args)->{
                switch(method.getName()) {
                    case "getObjectives": return objectives.clone();
                    case "getObjective": return objectives[(Integer)args[0]];
                    case "getNumberOfObjectives": return 3;
                    case "toString": return Arrays.toString(objectives);
                    case "hashCode": return System.identityHashCode(proxy);
                    case "equals": return proxy==args[0];
                    default: throw new UnsupportedOperationException(method.getName());
                }
            });
    }
    public static void main(String[] args) {
        List<PermutationSolution<Integer>> union=Arrays.asList(point(0,4,4),point(1,3,3),
            point(2,1.5,2),point(3,1,1),point(4,0,0),point(4,4,4));
        List<PermutationSolution<Integer>> retained=Arrays.asList(union.get(1),union.get(2),union.get(3));
        NsgaSelection selection=new NsgaSelection(()->{});
        NsgaSelection.Scores scores=selection.score(union);
        if(scores.rank[5]!=1 || scores.rank[1]!=0) throw new AssertionError("Dominance fixture");
        NsgaSelection.Scores expected=new NsgaSelection.Scores(3,new ArrayList<>());
        for(int i=0;i<3;i++) { expected.rank[i]=scores.rank[i+1]; expected.crowding[i]=scores.crowding[i+1]; }
        NsgaSelection.Scores fresh=selection.score(retained);
        CenterMatingScores bridge=new CenterMatingScores(union,()->{}); int changed=0;
        for(int seed=1;seed<=128;seed++) {
            SeededRandom.reset(seed); int actual=bridge.draw(retained,Arrays.asList(0,1,2));
            SeededRandom.reset(seed); int old=selection.tournament(expected);
            SeededRandom.reset(seed); int wrong=selection.tournament(fresh);
            if(actual!=old) throw new AssertionError("Union score or RNG drift");
            if(actual!=wrong) changed++;
            if(bridge.draw(retained,Collections.singletonList(1))!=1) throw new AssertionError("Category escape");
        }
        if(changed==0) throw new AssertionError("Fixture did not distinguish truncated rescoring");
        System.out.println("CENTER_POPULATION_CHECKS_PASS seeds=128 truncationDifferences="+changed+" searchFE=0 decodes=0");
    }
}
