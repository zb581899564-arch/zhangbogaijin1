package org.uma.jmetal.util.research.search;

import java.util.*;
import java.util.function.Consumer;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.modelglobal.*;
import org.uma.jmetal.util.research.runtime.RunContext;

/** Per-JVM paid archive, evidence and cooperative stopping; no default/mainline state replacement. */
public final class GomRunScope {
    public interface Evidence {
        default boolean recording() { return true; }
        void record(Map<String,Object> event);
        void view(PermutationSolution<Integer> before, PermutationSolution<Integer> after);
    }
    private static GomRunScope current;
    final RunContext<PermutationSolution<Integer>> run;
    final Evidence evidence;
    final Consumer<String> clockProbe;
    final PaInternalArchive archive = new PaInternalArchive();
    final GomPaidRegistry registry = new GomPaidRegistry();
    GomWorkspace workspace;
    PaInternalArchive.Flags lastFlags;
    PermutationSolution<Integer> lastPaid;
    long states, localFees, views, completedPasses, completedPrograms;
    int passes;
    String stage = "GLOBAL_OR_INITIAL";
    public GomRunScope(RunContext<PermutationSolution<Integer>> context, Evidence sink, Consumer<String> synthetic) {
        if (current != null) throw new IllegalStateException("One GOM scope per JVM");
        run = context; evidence = sink; clockProbe = synthetic; current = this;
    }
    public static boolean enabled() { return Boolean.getBoolean("research.ctxGom.enabled"); }
    public static void begin(List<PermutationSolution<Integer>> population, Instance instance) {
        if (!enabled()) return;
        GomRunScope scope = require(); scope.guard("PASS_START"); scope.passes++; scope.stage = "VIEWS";
        scope.workspace = new GomWorkspace(scope, instance); scope.workspace.prepare(population);
    }
    static GomRunScope require() { if (current == null) throw new IllegalStateException("Missing paid GOM scope"); return current; }
    void guard(String phase) { run.problem().checkpoint(); clockProbe.accept(phase); }
    public void observed(PermutationSolution<Integer> point, long fe, String rawHash) {
        lastFlags = archive.offer(point.getObjectives()); lastPaid = point;
        if (!recording()) return;
        registry.put(point, fe, rawHash);
        evidence.record(GomRecords.row("kind", "paid", "fe", fe, "objectives", point.getObjectives().clone(), "rawHash", rawHash,
            "dominated", lastFlags.dominated, "equal", lastFlags.equal, "fresh", lastFlags.fresh, "before", lastFlags.before, "after", lastFlags.after));
    }
    public double[][] archive() { return archive.snapshot(); }
    boolean recording() { return evidence.recording(); }
    long sourceFee(PermutationSolution<Integer> point) { return recording() ? registry.fee(point) : -1; }
    public Map<String,Object> diagnostics() {
        return GomRecords.row("enabled", enabled(), "passesStarted", passes, "completePasses", completedPasses,
            "completePrograms", completedPrograms, "localEvaluations", localFees, "preparedViews", views,
            "validatedViews", recording() ? views : 0, "detailedEvidence", recording(),
            "recoveredPaidCopies",registry.recoveredCopies,"stage", stage, "workspace", workspace == null ? null : workspace.receipt());
    }
    public long localFees() { return localFees; }
}
