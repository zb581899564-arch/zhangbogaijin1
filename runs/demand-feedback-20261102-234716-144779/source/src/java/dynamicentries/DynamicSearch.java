package research.dynamic;

import java.util.Map;
import java.util.LinkedHashMap;
import java.util.function.Supplier;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.classic.ClassicAlgorithm;
import org.uma.jmetal.util.research.classic.ClassicConfig;
import org.uma.jmetal.util.research.cooperation.CooperationSupport;
import org.uma.jmetal.util.research.joint.JointPolicy;
import org.uma.jmetal.util.research.mechanism.JobAlignedPolicy;
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
        return create(mode, in, parameters, raw, context, cfg, small, traceLimit, classicSetting, audit, mechanism, false);
    }
    static DynamicSearch create(String mode, Instance in, DynamicParameters parameters,
            DynamicEvaluation raw, RunContext<PermutationSolution<Integer>> context,
            SearchConfig cfg, boolean small, int traceLimit, int classicSetting, SemanticAudit audit,
            MechanismCapture mechanism, boolean captureCooperation) {
        if (isClassic(mode)) {
            if (small) throw new IllegalArgumentException("Classic comparison requires its registered population configuration");
            ClassicAlgorithm search = new ClassicAlgorithm(context.problem(), in,
                    new ClassicConfig(mode, classicSetting), context::checkpoint, audit, mechanism);
            return new DynamicSearch(search, null, null, search.configuration(), search::diagnostics);
        }
        String demandMode = mode.endsWith("_DEMAND") ? "DEMAND" : mode.endsWith("_SHAM") ? "SHAM" : "NONE";
        String preferenceMode = demandMode.equals("NONE") ? mode : mode.substring(0, mode.length() - demandMode.length() - 1);
        if (!demandMode.equals("NONE") && !preferenceMode.equals("SHARE_JOB_ALIGNED"))
            throw new IllegalArgumentException("Demand validation is registered only for SHARE_JOB_ALIGNED");
        boolean uniform = preferenceMode.endsWith("_UNIFORM");
        String orderMode = uniform ? preferenceMode.substring(0, preferenceMode.length() - "_UNIFORM".length()) : preferenceMode;
        boolean centerLast = orderMode.endsWith("_CENTER_LAST");
        String kernelMode = centerLast ? orderMode.substring(0, orderMode.length() - "_CENTER_LAST".length()) : orderMode;
        if (uniform && (centerLast || (!kernelMode.equals("SYNC_JOB_ALIGNED") && !kernelMode.equals("SHARE_JOB_ALIGNED"))))
            throw new IllegalArgumentException("Uniform preference is registered only for original-order SYNC/SHARE JOB_ALIGNED");
        if (centerLast && !kernelMode.equals("SYNC_JOB_ALIGNED") && !kernelMode.equals("SHARE_JOB_ALIGNED"))
            throw new IllegalArgumentException("Center-last is registered only for SYNC/SHARE JOB_ALIGNED");
        boolean aligned = kernelMode.equals("BASELINE_JOB_ALIGNED") || kernelMode.equals("SHARE_JOB_ALIGNED") || kernelMode.equals("SYNC_JOB_ALIGNED");
        String baseMode = aligned ? kernelMode.substring(0, kernelMode.length() - "_JOB_ALIGNED".length()) : kernelMode;
        boolean cooperative = baseMode.contains("SHARE") || baseMode.contains("SYNC");
        String jointMode = baseMode.startsWith("VALUE_") ? "VALUE" : baseMode;
        JointPolicy joint = (baseMode.equals("BASELINE") || baseMode.equals("SYNC") || baseMode.equals("SHARE"))
                ? null : new JointPolicy(in, parameters, new ParticleOperators(in, cfg.resolved(4)),
                        JointPolicy.Mode.valueOf(jointMode), raw::prepare, context::checkpoint, traceLimit);
        CooperationSupport support = cooperative
                ? new CooperationSupport(in, parameters, baseMode.contains("SHARE"), centerLast, uniform, audit, captureCooperation, demandMode) : null;
        JobAlignedPolicy alignedPolicy = aligned ? new JobAlignedPolicy(in, cfg) : null;
        GlobalUpdatePolicy policy = aligned ? alignedPolicy : joint;
        CanonicalHmopso search = new CanonicalHmopso(context.problem(), in, 4, cfg, policy, support, audit, mechanism);
        if (!aligned) return new DynamicSearch(search, joint, support, cfg.describe(4), search::diagnostics);
        String description = cfg.describe(4) + ";globalKernel=JOB_ALIGNED"
                + (centerLast ? ";globalOrder=MAKESPAN,ENERGY,WORKER_COST,CENTER" : "")
                + (uniform ? ";allPhysicalGroupsPreference=CENTER" : "")
                + (demandMode.equals("NONE") ? "" : ";fixedDemandFactoryRouting=" + demandMode);
        return new DynamicSearch(search, joint, support, description, () -> {
            Map<String, Object> counts = new LinkedHashMap<>(); counts.putAll(search.diagnostics());
            counts.put("globalKernel", "JOB_ALIGNED"); counts.put("alignedKernelProposals", alignedPolicy.proposals());
            return counts;
        });
    }
    static boolean isClassic(String mode) {
        return mode.equals("NSGA2_4V") || mode.equals("SPEA2_4V") || mode.equals("MOEAD_4V") || mode.equals("NSGA2_VNS_4V");
    }
    Map<String, ?> diagnostics() { return diagnostics.get(); }
}
