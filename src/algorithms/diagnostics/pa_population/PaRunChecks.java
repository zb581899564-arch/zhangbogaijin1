package research.dynamic;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.modelglobal.PaPaidEvaluation;

/** Every paid candidate receives full timeline QA, including duplicates and unchanged fallbacks. */
final class PaRunChecks implements PaPaidEvaluation.Checks {
    private final Instance instance;
    private final DynamicParameters parameters;
    private final Set<String> seen = new HashSet<>();
    final PddrPaidDigest paidDigest = new PddrPaidDigest(), one = new PddrPaidDigest();
    long paidQA, neutralQA, rawDuplicates, paidQANanos, neutralQANanos;
    String lastRawHash;
    PaRunChecks(Instance value, DynamicParameters fatigue) throws Exception { instance = value; parameters = fatigue; }

    public void paid(PermutationSolution<Integer> value, long fe) {
        long started = System.nanoTime(); paidQA++;
        DynamicSchedule full = NeutralProbeSupport.full(instance, parameters, value);
        NeutralProbeSupport.sameTimeline((DynamicSchedule)value.getAttribute(DynamicEvaluation.KEY), full);
        if (!Arrays.equals(value.getObjectives(), full.objectives())) throw new AssertionError("Paid objective cache differs");
        paidDigest.update(fe, value); one.update(0, value); lastRawHash = one.finish();
        if (!seen.add(lastRawHash)) rawDuplicates++; paidQANanos += System.nanoTime() - started;
    }

    public void neutral(PermutationSolution<Integer> before, PermutationSolution<Integer> after) {
        long started = System.nanoTime(); neutralQA++;
        DynamicSchedule full = NeutralProbeSupport.full(instance, parameters, after);
        NeutralProbeSupport.sameTimeline((DynamicSchedule)before.getAttribute(DynamicEvaluation.KEY), full);
        if (!Arrays.equals(before.getObjectives(), after.getObjectives()) || !Arrays.equals(after.getObjectives(), full.objectives()))
            throw new AssertionError("Reencoding changed objective values");
        neutralQANanos += System.nanoTime() - started;
    }
}
