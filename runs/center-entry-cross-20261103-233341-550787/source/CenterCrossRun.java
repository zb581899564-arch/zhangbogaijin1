package research.dynamic;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.Solution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.DynamicParameters;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.runtime.EvaluationObserver;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.util.research.runtime.ThreeObjectiveArchive;
import org.uma.jmetal.util.research.search.CenterCrossSearch;
import org.uma.jmetal.util.research.search.CenterEntryTrace;
import org.uma.jmetal.util.research.search.QgsLocalLedger;
import org.uma.jmetal.util.research.search.ReverseAudit;

/** Replays a single factorial cell with genuine guarded dynamic evaluations. */
public final class CenterCrossRun {
    private CenterCrossRun() {}
    public static void main(String[] args) throws Exception {
        Path out = Paths.get(args[3]);
        long limit = Long.parseLong(args[9]), seed = Long.parseLong(args[10]);
        System.setProperty("research.qgsAudit.mode", "replay");
        System.setProperty("research.qgsAudit.ledger", args[4]);
        EDHHFSPW raw = LongBudgetRun.load(Paths.get(args[0]), Paths.get(args[1]));
        Instance instance = raw.getSchedulingInstance();
        DynamicParameters params = DynamicInputs.fatigue(instance, Paths.get(args[2]));
        DynamicEvaluation dynamic = new DynamicEvaluation(raw, instance, params, true);
        RunContext<PermutationSolution<Integer>> context = new RunContext<>(dynamic, limit, seed);
        dynamic.setCheckpoint(context::checkpoint);
        CenterCrossSearch search = new CenterCrossSearch(context, instance, params, out,
                Paths.get(args[5]), Paths.get(args[6]), Paths.get(args[7]), Paths.get(args[8]));
        List<Map<String, Object>> admitted = new ArrayList<>();
        context.problem().setObserver(new EvaluationObserver() {
            @Override public void completed(long paid, double seconds, boolean changed, ThreeObjectiveArchive<?> a) {}
            @Override public void completedSolution(Solution<?> s, long paid, double seconds, boolean changed,
                    ThreeObjectiveArchive<?> a) {
                PermutationSolution<?> p = (PermutationSolution<?>) s;
                ReverseAudit.run().paid(p, paid, changed, a);
                CenterEntryTrace.paid(p, paid);
                if (changed) admitted.add(ReverseAudit.row("FE", paid, "objectives", p.getObjectives().clone()));
            }
        });
        try { context.run(search); }
        catch (RuntimeException | Error e) {
            Map<String, Object> failure = ReverseAudit.row("error", e.toString(), "attempted", context.budget().attempted(),
                    "successful", context.budget().successful(), "lastFront", ReverseAudit.run().archive());
            ReverseAudit.writeRows(out.resolve("failure.jsonl"), java.util.Collections.singletonList(failure));
            throw e;
        }
        if (!"FE_LIMIT".equals(context.stopReason()) || context.budget().attempted() != limit
                || context.budget().successful() != limit || context.budget().failed() != 0)
            throw new IllegalStateException("Invalid crossed stage FE receipt");
        QgsLocalLedger.finish(out);
        Map<String, Object> receipt = ReverseAudit.row("seed", seed, "attempted", context.budget().attempted(),
                "successful", context.budget().successful(), "failed", context.budget().failed(),
                "stopReason", context.stopReason(), "searchSeconds", context.clock().elapsedSeconds(),
                "search", search.diagnostics(), "decoder", dynamic.diagnostics());
        ReverseAudit.writeRows(out.resolve("run-receipt.jsonl"), java.util.Collections.singletonList(receipt));
        ReverseAudit.writeRows(out.resolve("admissions.jsonl"), admitted);
        DynamicOutput.write(out, instance, params, context.result(), receipt, false);
    }
}
