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
        writeTrace(output, "semantic-trace.jsonl", audit.finish());
        summary.put("semanticAudit", audit.diagnostics());
        writeTrace(output, "feedback-trace.jsonl", audit.feedbackTrace());
        if (cooperation != null) {
            writeTrace(output, "composition-trace.jsonl", cooperation.compositionTrace());
            writeTrace(output, "cooperation-evidence.jsonl", cooperation.poolEvidenceTrace());
            writeTrace(output, "demand-trace.jsonl", cooperation.demandTrace());
            writeTrace(output, "context-renewal.jsonl", cooperation.contextRenewalTrace());
            writeTrace(output, "factory-transfer.jsonl", cooperation.factoryTransferTrace());
        }
    }
    private static void writeTrace(Path output, String name, List<Map<String, Object>> rows) throws Exception {
        if (rows == null) return;
        Files.createDirectories(output); List<String> lines = new ArrayList<>();
        for (Map<String, Object> row : rows) lines.add(DynamicJson.encode(row));
        Files.write(output.resolve(name), lines, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
    }
}
