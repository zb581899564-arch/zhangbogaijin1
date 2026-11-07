package org.uma.jmetal.util.research.modelglobal;

import java.util.*;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.util.research.search.Direction;

/** Model API checkpoint carrier with an explicitly forbidden objective backend. */
final class GeometryWorld {
    final Instance in;
    final FirstStageCatalog catalog;
    final RunContext<PermutationSolution<Integer>> guard;
    final QpaPaidEvaluation evaluation;
    private final ForbiddenProblem backend;
    long proxies;

    GeometryWorld(EDHHFSPW raw,long seed) {
        in=raw.getSchedulingInstance();catalog=new FirstStageCatalog(in);backend=new ForbiddenProblem(raw);
        guard=new RunContext<>(backend,1,seed);evaluation=new QpaPaidEvaluation(guard,in,new PaPaidEvaluation.Checks() {
            public void paid(PermutationSolution<Integer> point,long fe) {throw new AssertionError("Unpaid model audit attempted evaluation");}
            public void neutral(PermutationSolution<Integer> a,PermutationSolution<Integer> b) {throw new AssertionError("Unexpected evaluator reencode");}
        });
    }

    QpaIndividual carrier(String[] fields) {
        int slot=Integer.parseInt(fields[2]);long paid=Long.parseLong(fields[3]);
        int[] js=ints(fields[6]),fa=ints(fields[7]),ma=ints(fields[8]),wa=ints(fields[9]);
        FourVectors vectors=new FourVectors(js,fa,ma,wa);DirectScheduleGenome genes=DirectScheduleGenome.fromVectors(catalog,vectors);
        PermutationSolution<Integer> point=guard.problem().createSolution();proxies++;
        @SuppressWarnings("unchecked") List<Integer> machines=(List<Integer>)point.getAttribute("machine");
        for (int p=0;p<js.length;p++) {point.setVariableValue(p,js[p]);point.setVariableValueid(p,fa[p]);machines.set(p,ma[p]);point.setVariableValueworker(p,wa[p]);}
        double[] objectives=Arrays.stream(fields[5].split(",")).mapToDouble(Double::parseDouble).toArray();
        for (int k=0;k<3;k++) point.setObjective(k,objectives[k]);
        return new QpaIndividual(slot+1,paid,Direction.valueOf(fields[4]),genes,point);
    }

    static int[] ints(String value) {return Arrays.stream(value.split(",")).mapToInt(Integer::parseInt).toArray();}

    void requireZeroEvaluation() {
        if (backend.calls!=0||guard.budget().attempted()!=0||guard.budget().successful()!=0||guard.budget().failed()!=0)
            throw new AssertionError("Structural-only audit consumed evaluation");
    }

    long objectiveCalls() {return backend.calls;}

    private static final class ForbiddenProblem implements Problem<PermutationSolution<Integer>> {
        private static final long serialVersionUID=1L;
        private final EDHHFSPW raw;
        long calls;
        ForbiddenProblem(EDHHFSPW value) {raw=value;}
        public void evaluate(PermutationSolution<Integer> point) {calls++;throw new AssertionError("Objective evaluation forbidden");}
        public PermutationSolution<Integer> createSolution() {return raw.createSolution();}
        public int getNumberOfVariables() {return raw.getNumberOfVariables();}
        public int getNumberOfObjectives() {return raw.getNumberOfObjectives();}
        public int getNumberOfConstraints() {return raw.getNumberOfConstraints();}
        public String getName() {return raw.getName();}
    }
}
