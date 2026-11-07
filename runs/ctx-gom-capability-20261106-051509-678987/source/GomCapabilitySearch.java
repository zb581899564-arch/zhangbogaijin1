package research.dynamic;

import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.util.research.search.*;

/** Explicit isolated local integration; frozen ordinary controls retain their complete original search. */
final class GomCapabilitySearch implements Algorithm<Object> {
    private static final long serialVersionUID = 1L;
    private final String arm;
    private final RunContext<PermutationSolution<Integer>> run;
    private final Instance in;
    private final DynamicParameters fatigue;
    private final DynamicEvaluation decoder;
    private GomRunScope scope;
    private DynamicSearch dynamic;
    private PaCapabilitySearch frozen;
    GomCapabilitySearch(String label, RunContext<PermutationSolution<Integer>> context, Instance input,
            DynamicParameters params, DynamicEvaluation raw) { arm=label; run=context; in=input; fatigue=params; decoder=raw; }
    static boolean contextArm(String label) { return label.endsWith("_CTX_GOM"); }
    public void run() {
        if (!contextArm(arm)) {
            frozen = new PaCapabilitySearch(arm.equals("PA_EQUAL") ? "PA_JOINT" : arm,run,in,fatigue,decoder); frozen.run(); return;
        }
        GomRunScope.Evidence silent = new GomRunScope.Evidence() {
            public boolean recording() { return false; }
            public void record(Map<String,Object> event) { throw new AssertionError("Unnecessary detailed event"); }
            public void view(PermutationSolution<Integer> before, PermutationSolution<Integer> after) { throw new AssertionError("Unnecessary view QA"); }
        };
        scope = new GomRunScope(run,silent,phase -> { });
        String mode = arm.equals("SHARE_CTX_GOM") ? "SHARE_JOB_ALIGNED" : arm.equals("SYNC_CTX_GOM") ? "SYNC_JOB_ALIGNED"
            : arm.equals("UNIFORM_CTX_GOM") ? "SHARE_JOB_ALIGNED_UNIFORM" : "NSGA2_4V";
        SearchConfig cfg = new SearchConfig(); cfg.mergeGlobalLocal = cfg.paperResourceOperators = !DynamicSearch.isClassic(mode);
        dynamic = DynamicSearch.create(mode,in,fatigue,decoder,run,cfg,false,0,0); dynamic.algorithm.run();
    }
    void observed(PermutationSolution<Integer> point,long fe) { if (scope != null) scope.observed(point,fe,null); }
    Map<String,Object> diagnostics() {
        Map<String,Object> result = new LinkedHashMap<>();
        if (frozen != null) result.putAll(frozen.diagnostics());
        if (dynamic != null) result.putAll(dynamic.diagnostics());
        if (scope != null) result.put("contextGom",scope.diagnostics());
        if (dynamic != null && dynamic.cooperation != null) result.put("cooperation",dynamic.cooperation.diagnostics());
        return result;
    }
    public Object getResult() { return null; }
    public String getName() { return arm; }
    public String getDescription() { return "Isolated context-local GOM and explicitly frozen complete controls"; }
}
