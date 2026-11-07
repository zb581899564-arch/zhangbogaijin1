package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.util.research.search.SearchConfig;
import org.uma.jmetal.util.research.search.SemanticAudit;
import org.uma.jmetal.util.research.cooperation.CooperationSupport;

/** Explicit S/O flags and bounded evidence export, separate from the physical model. */
final class DynamicSemantics {
    final String profile;
    final SemanticAudit audit;
    private DynamicSemantics(String profile, SemanticAudit audit) { this.profile = profile; this.audit = audit; }
    static DynamicSemantics configure(String[] args, SearchConfig cfg, RunContext<PermutationSolution<Integer>> context) {
        String profile = args.length > 15 ? args[15] : "V2";
        if (!profile.equals("V2") && !profile.equals("S") && !profile.equals("O") && !profile.equals("SO"))
            throw new IllegalArgumentException("Semantic profile must be V2/S/O/SO");
        if (DynamicSearch.isClassic(args[4]) && !profile.equals("V2"))
            throw new IllegalArgumentException("Classic controls cannot use S/O");
        cfg.mergeGlobalLocal = profile.equals("S") || profile.equals("SO");
        cfg.paperResourceOperators = profile.equals("O") || profile.equals("SO");
        SemanticAudit audit = args.length > 16 && Boolean.parseBoolean(args[16])
                ? new SemanticAudit(context.clock()::elapsedSeconds, Double.parseDouble(args[7]),
                        args.length > 19 && Boolean.parseBoolean(args[19])) : null;
        context.problem().setAudit(audit);
        return new DynamicSemantics(profile, audit);
    }
    void finish(Path output, Map<String, Object> summary, CooperationSupport cooperation) throws Exception {
        summary.put("semanticProfile", profile);
        if (audit == null) return;
        List<String> lines = new ArrayList<>();
        for (Map<String, Object> row : audit.finish()) lines.add(DynamicJson.encode(row));
        summary.put("semanticAudit", audit.diagnostics());
        Files.createDirectories(output);
        Files.write(output.resolve("semantic-trace.jsonl"), lines, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        List<Map<String, Object>> feedback = audit.feedbackTrace();
        if (feedback != null) {
            List<String> evidence = new ArrayList<>();
            for (Map<String, Object> row : feedback) evidence.add(DynamicJson.encode(row));
            Files.write(output.resolve("feedback-trace.jsonl"), evidence, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        }
        List<Map<String, Object>> composition = cooperation == null ? null : cooperation.compositionTrace();
        if (composition != null) {
            List<String> evidence = new ArrayList<>();
            for (Map<String, Object> row : composition) evidence.add(DynamicJson.encode(row));
            Files.write(output.resolve("composition-trace.jsonl"), evidence, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        }
        if (cooperation != null && cooperation.poolEvidenceTrace() != null) {
            List<String> evidence = new ArrayList<>();
            for (Map<String, Object> row : cooperation.poolEvidenceTrace()) evidence.add(DynamicJson.encode(row));
            Files.write(output.resolve("cooperation-evidence.jsonl"), evidence, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        }
        if (cooperation != null && cooperation.demandTrace() != null) {
            List<String> evidence = new ArrayList<>();
            for (Map<String, Object> row : cooperation.demandTrace()) evidence.add(DynamicJson.encode(row));
            Files.write(output.resolve("demand-trace.jsonl"), evidence, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        }
    }
}
