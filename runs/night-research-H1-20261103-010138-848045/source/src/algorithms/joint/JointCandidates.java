package org.uma.jmetal.util.research.joint;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import org.uma.jmetal.solution.PermutationSolution;

/** Fixed, objective-blind candidate sources, shared by all four controls. */
final class JointCandidates {
    private JointCandidates() { }
    static List<JointAction> propose(BlockContext block, PermutationSolution<Integer>[] teachers, Random random) {
        List<JointAction> result = new ArrayList<>();
        offer(result, block, block.witness().get(0));
        for (PermutationSolution<Integer> teacher : teachers) {
            JointAction[] byJob = BlockContext.byJob(block.instance, teacher, false);
            for (int job : BlockContext.sequence(teacher)) if (block.remaining(job)) {
                offer(result, block, byJob[job]); break;
            }
        }
        // Exactly two exploration draws. Feasible factories are selected before local resources.
        for (int draw = 0; draw < 2; draw++) {
            List<JointAction> remaining = block.witness();
            int job = remaining.get(random.nextInt(remaining.size())).job();
            List<Integer> factories = new ArrayList<>();
            for (int f = 0; f < block.instance.factories(); f++) {
                if (block.completable(new JointAction(job, f, 0, 0))) factories.add(f);
            }
            if (factories.isEmpty()) throw new IllegalStateException("Witness failed to supply a feasible exploration factory");
            int f = factories.get(random.nextInt(factories.size()));
            offer(result, block, new JointAction(job, f, random.nextInt(block.instance.machines(f, 0)),
                    random.nextInt(block.instance.workers(f, 0))));
        }
        if (result.size() > JointPolicy.CANDIDATE_LIMIT) throw new IllegalStateException("Candidate cap exceeded");
        return result;
    }
    private static void offer(List<JointAction> values, BlockContext block, JointAction a) {
        if (block.completable(a) && !values.contains(a)) values.add(a);
    }
}
