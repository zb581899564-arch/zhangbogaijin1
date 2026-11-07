package research.dynamic;

import java.util.Map;
import java.util.function.Supplier;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.classic.ClassicAlgorithm;
import org.uma.jmetal.util.research.classic.ClassicConfig;
import org.uma.jmetal.util.research.cooperation.CooperationSupport;
import org.uma.jmetal.util.research.joint.JointPolicy;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.util.research.search.*;

/** Assembles a search strategy without changing the common physical evaluator. */
final class DynamicSearch {
    final Algorithm<?> algorithm;
    final JointPolicy joint;
    final CooperationSupport cooperation;
    final String configuration;
    private final Supplier<Map<String, ?>> diagnostics;

    private DynamicSearch(Algorithm<?> algorithm, JointPolicy joint, CooperationSupport cooperation,
            String configuration, Supplier<Map<String, ?>> diagnostics) {
        this.algorithm = algorithm; this.joint = joint; this.cooperation = cooperation;
        this.configuration = configuration; this.diagnostics = diagnostics;
    }
    static DynamicSearch create(String mode, Instance in, DynamicParameters parameters,
            DynamicEvaluation raw, RunContext<PermutationSolution<Integer>> context,
            SearchConfig cfg, boolean small, int traceLimit, int classicSetting) {
        return create(mode, in, parameters, raw, context, cfg, small, traceLimit, classicSetting, null);
    }
    static DynamicSearch create(String mode, Instance in, DynamicParameters parameters,
            DynamicEvaluation raw, RunContext<PermutationSolution<Integer>> context,
            SearchConfig cfg, boolean small, int traceLimit, int classicSetting, SemanticAudit audit) {
        return create(mode, in, parameters, raw, context, cfg, small, traceLimit, classicSetting, audit, null);
    }
    static DynamicSearch create(String mode, Instance in, DynamicParameters parameters,
            DynamicEvaluation raw, RunContext<PermutationSolution<Integer>> context,
            SearchConfig cfg, boolean small, int traceLimit, int classicSetting, SemanticAudit audit,
            MechanismCapture mechanism) {
        if (isClassic(mode)) {
            if (small) throw new IllegalArgumentException("Classic comparison requires its registered population configuration");
            ClassicAlgorithm search = new ClassicAlgorithm(context.problem(), in,
                    new ClassicConfig(mode, classicSetting), context::checkpoint, audit, mechanism);
            return new DynamicSearch(search, null, null, search.configuration(), search::diagnostics);
        }
        boolean cooperative = mode.contains("SHARE") || mode.contains("SYNC");
        String jointMode = mode.startsWith("VALUE_") ? "VALUE" : mode;
        JointPolicy joint = (mode.equals("BASELINE") || mode.equals("SYNC") || mode.equals("SHARE"))
                ? null : new JointPolicy(in, parameters, new ParticleOperators(in, cfg.resolved(4)),
                        JointPolicy.Mode.valueOf(jointMode), raw::prepare, context::checkpoint, traceLimit);
        CooperationSupport support = cooperative
                ? new CooperationSupport(in, parameters, mode.contains("SHARE")) : null;
        CanonicalHmopso search = new CanonicalHmopso(context.problem(), in, 4, cfg, joint, support, audit, mechanism);
        return new DynamicSearch(search, joint, support, cfg.describe(4), search::diagnostics);
    }
    static boolean isClassic(String mode) {
        return mode.equals("NSGA2_4V") || mode.equals("SPEA2_4V") || mode.equals("MOEAD_4V") || mode.equals("NSGA2_VNS_4V");
    }
    Map<String, ?> diagnostics() { return diagnostics.get(); }
}
