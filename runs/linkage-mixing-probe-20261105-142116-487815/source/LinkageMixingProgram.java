package research.dynamic;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Random;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.classic.ClassicKernelBridge;
import org.uma.jmetal.util.research.model.DynamicSchedule;
import org.uma.jmetal.util.research.search.LinkageSearchBridge;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** One fixed-budget mixing walk; only its accepted current state feeds the next step. */
final class LinkageMixingProgram {
    static final String[] METHODS = {"FA_LINKAGE", "RELABEL_TREE", "SINGLE_JOB", "CLASSIC_KERNEL"};
    private final LinkageMixingRun.Probe probe;
    private final ClassicKernelBridge kernel;
    LinkageMixingProgram(LinkageMixingRun.Probe value) { probe = value;kernel = new ClassicKernelBridge(value.in, value.context::checkpoint); }

    void run(String role, int rank, int parentOrdinal, int sourceIndex, int methodOffset) {
        PermutationSolution<Integer> receiver = probe.sources.get(sourceIndex);
        List<Integer> group = probe.groups.get(role);int steps = probe.subsets.size(), n = probe.in.jobs();
        long seed = NeutralProbeSupport.mixed(probe.noiseSeed + parentOrdinal * 100003L);
        Random draw = new Random(seed);int[] donors = new int[steps];
        for (int k = 0; k < steps; k++) donors[k] = group.get(draw.nextInt(group.size()));
        List<Integer> order = order(steps, seed ^ 0x71ac3L), single = order(n, seed ^ 0x8b2d5L);
        for (int turn = 0; turn < METHODS.length; turn++) {
            String method = METHODS[(turn + methodOffset) % METHODS.length];
            one(role, rank, sourceIndex, receiver, method, donors, order, single, seed);
        }
    }

    private void one(String role, int rank, int sourceIndex, PermutationSolution<Integer> receiver, String method,
            int[] donors, List<Integer> order, List<Integer> single, long seed) {
        PermutationSolution<Integer> current = receiver;long started = System.nanoTime(), generation = 0, evaluation = 0, decisions = 0, qa = 0;
        int acceptedCount = 0, fallbacks = 0, steps = donors.length;
        for (int k = 0; k < steps; k++) {
            PermutationSolution<Integer> donor = probe.sources.get(donors[k]);
            String before = ProbeData.key(current), other = ProbeData.key(donor);
            double[] parentObjectives = current.getObjectives().clone();int subsetIndex = order.get(k);int[] subset = null;
            long noise = NeutralProbeSupport.mixed(seed + k * 997L);SeededRandom.reset(noise);
            long time = System.nanoTime();PermutationSolution<Integer> child;boolean fallback = false;
            if (method.equals("CLASSIC_KERNEL")) child = kernel.child(current, donor);
            else {
                subset = method.equals("SINGLE_JOB") ? new int[]{single.get(k % single.size())}
                    : (method.equals("FA_LINKAGE") ? probe.subsets : probe.relabeled).get(subsetIndex);
                LinkageGenome.Proposal result = LinkageGenome.donate(current, donor, subset, probe.in.factories());
                child = result.point;fallback = result.fallback;
            }
            int edits = SchedulingEncoding.repair(child, probe.in);generation += System.nanoTime() - time;
            if (edits != 0 && !method.equals("CLASSIC_KERNEL")) throw new AssertionError("Physical mixing needs repair");
            if (!before.equals(ProbeData.key(current)) || !other.equals(ProbeData.key(donor))) throw new AssertionError("Generation mutated paid input");
            time = System.nanoTime();probe.context.problem().evaluate(child);evaluation += System.nanoTime() - time;
            probe.digest.update(probe.context.budget().successful(), child);
            time = System.nanoTime();probe.check(child);qa += System.nanoTime() - time;
            if (fallback && !java.util.Arrays.equals(child.getObjectives(), parentObjectives)) throw new AssertionError("Fallback objective differs");
            if (subset != null && subset.length == probe.in.jobs() && !java.util.Arrays.equals(child.getObjectives(), donor.getObjectives()))
                throw new AssertionError("Full physical donation objective differs");
            time = System.nanoTime();boolean accepted = LinkageSearchBridge.better(role, child, current, probe.reference);decisions += System.nanoTime() - time;
            if (accepted) { current = child;acceptedCount++; }if (fallback) fallbacks++;
            Map<String,Object> record = NeutralProbeSupport.row("role", role, "receiverRank", rank, "sourceIndex", sourceIndex,
                "method", method, "step", k, "paidFE", probe.context.budget().successful(), "donorIndex", donors[k],
                "subsetIndex", subsetIndex, "subsetSize", subset == null ? -1 : subset.length, "noise", noise,
                "fallback", fallback, "postRepairEdits", edits, "parentObjectives", parentObjectives,
                "objectives", child.getObjectives().clone(), "accepted", accepted);
            if (probe.context.budget().successful() % 257 == 1 || k == steps - 1) record.put("sampledGenome", ProbeData.encoding(child));
            NeutralProbeSupport.append(probe.out.resolve("outcomes.jsonl"), record);
        }
        NeutralProbeSupport.append(probe.out.resolve("programs.jsonl"), NeutralProbeSupport.row("role", role,
            "receiverRank", rank, "sourceIndex", sourceIndex, "method", method, "successfulChildFE", steps,
            "acceptedSteps", acceptedCount, "emptyFactoryFallbacks", fallbacks, "finalGenome", ProbeData.encoding(current),
            "wholeProgramIncludingQAEvidenceSeconds", (System.nanoTime() - started) / 1e9,
            "generationSeconds", generation / 1e9, "paidEvaluationSeconds", evaluation / 1e9,
            "acceptanceSeconds", decisions / 1e9, "fullQASeconds", qa / 1e9));
    }

    private static List<Integer> order(int size, long seed) {
        List<Integer> result = new ArrayList<>();for (int i = 0; i < size; i++) result.add(i);
        Collections.shuffle(result, new Random(seed));return result;
    }
}
