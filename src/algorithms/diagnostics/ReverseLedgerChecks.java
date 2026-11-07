package org.uma.jmetal.util.research.search;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Collections;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.joint.JointCheckProblem;
import org.uma.jmetal.util.research.runtime.EvaluationObserver;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.util.research.runtime.ThreeObjectiveArchive;

/** Exercise the actual shadow local kernel, strict budget and ledger with a tiny fixture. */
public final class ReverseLedgerChecks {
    private ReverseLedgerChecks() {}
    public static void main(String[] args) throws Exception {
        Path out = Paths.get(args[0]);
        int limit = Integer.parseInt(args[1]);
        System.setProperty("research.qgsAudit.mode", args[2]);
        if (args.length > 3) System.setProperty("research.qgsAudit.ledger", args[3]);
        JointCheckProblem raw = new JointCheckProblem(7);
        DynamicEvaluation eval = new DynamicEvaluation(raw, raw.instance, raw.parameters, true);
        RunContext<PermutationSolution<Integer>> context = new RunContext<>(eval, limit, 19);
        eval.setCheckpoint(context::checkpoint);
        ReverseAudit audit = ReverseAudit.run();
        context.problem().setObserver(new EvaluationObserver() {
            @Override public void completed(long fe, double time, boolean changed, ThreeObjectiveArchive<?> archive) {}
            @Override public void completedSolution(org.uma.jmetal.solution.Solution<?> candidate, long fe, double time,
                    boolean changed, ThreeObjectiveArchive<?> archive) {
                audit.paid((PermutationSolution<?>) candidate, fe, changed, archive);
            }
        });
        SearchState state = new SearchState(context.problem(), raw.instance, null);
        LocalSearch local = new LocalSearch(raw.instance, 4, new SearchConfig().resolved(4), state);
        context.run(new Algorithm<Object>() {
            private static final long serialVersionUID = 1L;
            @Override public void run() {
                Particle particle = new Particle(state.evaluate(context.problem().createSolution(), "global", Direction.CENTER));
                while (true) {
                    context.problem().checkpoint();
                    particle = local.improve(particle, Direction.CENTER, Collections.singletonList(particle.current));
                }
            }
            @Override public Object getResult() { return null; }
            @Override public String getName() { return "ReverseLedgerChecks"; }
            @Override public String getDescription() { return getName(); }
        });
        if (!"FE_LIMIT".equals(context.stopReason()) || context.budget().attempted() != limit
                || context.budget().successful() != limit || context.budget().failed() != 0)
            throw new AssertionError("Guard did not stop on the exact paid limit");
        QgsLocalLedger.finish(out);
        audit.finish(out);
        System.out.println("REVERSE_BOUNDARY_OK " + limit + " " + args[2]);
    }
}
