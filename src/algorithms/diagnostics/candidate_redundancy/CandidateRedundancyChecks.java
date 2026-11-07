package org.uma.jmetal.util.research.search;

import java.util.Collections;
import java.util.List;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Synthetic encoding/proof checks only. No evaluator or DynamicDecoder is called. */
public final class CandidateRedundancyChecks {
    private CandidateRedundancyChecks() { }
    public static void main(String[] args) throws Exception {
        System.setProperty("dhfsp.dataDir", args[0]); System.setProperty("dhfsp.setupFile", args[1]);
        System.setProperty("dhfsp.standbyPower", "1"); SeededRandom.reset(0);
        EDHHFSPW problem = new EDHHFSPW(20, 8, 5, 1); Instance in = problem.getSchedulingInstance();
        PermutationSolution<Integer> a = problem.createSolution();
        List<Integer> ma = ParticleOperators.machines(a);
        for (int p = 0; p < 20; p++) {
            a.setVariableValue(p, p);a.setVariableValueid(p, p % in.factories());ma.set(p, 0);a.getVariablesworker().set(p, 0);
        }
        PermutationSolution<Integer> b = ParetoTools.copy(a);
        Collections.swap(b.getVariables(), 0, 1);Collections.swap(b.getVariablesid(), 0, 1);
        if (!CandidatePhysicalKey.of(a, in.factories()).equals(CandidatePhysicalKey.of(b, in.factories())))
            throw new AssertionError("Neutral inter-factory interleaving changed full physical key");
        if (!EmptyNeighborhoodCertificate.empty(in, a, 0, 5) || !EmptyNeighborhoodCertificate.empty(in, a, 0, 8)
                || EmptyNeighborhoodCertificate.empty(in, a, 0, 0)) throw new AssertionError("Known permutation certificates failed");
        int changedFactory = -1;
        for (int f = 0; f < in.factories(); f++) if (in.machines(f, 0) > 1) { changedFactory = f;break; }
        if (changedFactory < 0) throw new AssertionError("Fixture needs a two-machine factory");
        int position = EmptyNeighborhoodCertificate.positions(b, changedFactory).get(0);
        ParticleOperators.machines(b).set(position, 1);
        if (CandidatePhysicalKey.of(a, in.factories()).equals(CandidatePhysicalKey.of(b, in.factories())))
            throw new AssertionError("Resource change disappeared from full physical key");
        if (EmptyNeighborhoodCertificate.empty(in, b, changedFactory, 5)) throw new AssertionError("Mixed resources called empty");
        System.out.println("CANDIDATE_REDUNDANCY_FIXTURES_PASS canonical key; resource identity; exact empty permutation; zeroFE zeroDecoder");
    }
}
