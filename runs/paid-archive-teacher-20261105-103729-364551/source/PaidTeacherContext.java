package research.dynamic;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.mechanism.KernelVariants;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;
import org.uma.jmetal.util.research.search.SearchConfig;

/** One fixed paid background, with no candidate or teacher feedback between comparison arms. */
final class PaidTeacherContext {
    static final int RECIPIENTS = 8, REPS = 16;
    final Instance instance;
    final DynamicParameters parameters;
    final Path output;
    final long seed;
    final int contextIndex;
    final DynamicEvaluation decoder;
    final RunContext<PermutationSolution<Integer>> context;
    long fullQA;
    double qaSeconds;

    PaidTeacherContext(EDHHFSPW raw, DynamicParameters params, Path out, long baseSeed, int index, int inputs) {
        instance = raw.getSchedulingInstance(); parameters = params; output = out; seed = baseSeed; contextIndex = index;
        decoder = new DynamicEvaluation(raw, instance, params, true);
        long limit = inputs + (long) RECIPIENTS * REPS * PaidGuidePools.METHODS.length;
        context = new RunContext<>(decoder, limit, seed + index); decoder.setCheckpoint(context::checkpoint);
    }

    void run(String id, List<String[]> inputs, List<String[]> recipients) {
        if (recipients.size() != RECIPIENTS) throw new AssertionError("Wrong recipient count");
        boolean completed = false;
        try {
            context.run(new Algorithm<Object>() {
                private static final long serialVersionUID = 1L;
                public void run() { trials(id, inputs, recipients); }
                public Object getResult() { return null; }
                public String getName() { return "PAID_ARCHIVE_TEACHER_VALUE"; }
                public String getDescription() { return getName(); }
            });
            if (context.budget().successful() != context.budget().limit() || context.budget().failed() != 0)
                throw new AssertionError("Incomplete teacher-value context");
            completed = true;
        } finally {
            List<Map<String,Object>> last = new ArrayList<>();
            for (PermutationSolution<Integer> point : context.result()) last.add(ProbeData.encoding(point));
            NeutralProbeSupport.append(output.resolve("context-receipts.jsonl"), NeutralProbeSupport.row(
                    "context", id, "status", completed ? "COMPLETE" : "INCOMPLETE_RETAINED",
                    "successfulFE", context.budget().successful(), "attemptedFE", context.budget().attempted(),
                    "failedFE", context.budget().failed(), "expectedFE", context.budget().limit(),
                    "inputs", inputs.size(), "fullDecoderQA", fullQA, "offlineQASeconds", qaSeconds,
                    "decoder", decoder.diagnostics(), "lastValidFront", last));
            decoder.clearPrepared();
        }
    }

    private void trials(String id, List<String[]> fields, List<String[]> recipients) {
        List<PaidGuidePools.Entry> known = replay(id, fields);
        Map<String,PaidGuidePools.Entry> byId = new LinkedHashMap<>();
        List<String> original = new ArrayList<>();
        for (PaidGuidePools.Entry entry : known) { byId.put(entry.id, entry); original.add(ProbeData.key(entry.value)); }
        SearchConfig settings = new SearchConfig(); settings.mergeGlobalLocal = settings.paperResourceOperators = true;
        KernelVariants kernel = new KernelVariants(instance, settings, context::checkpoint);
        long started = System.nanoTime();
        List<PaidGuidePools.Entry> initial = PaidGuidePools.construct(known, "INITIAL_ND");
        long initialNanos = System.nanoTime() - started;
        poolRecord(id, -1, "INITIAL_ND", initial, initialNanos);
        for (int rep = 0; rep < REPS; rep++) {
            for (int turn = 0; turn < PaidGuidePools.METHODS.length; turn++) {
                String method = PaidGuidePools.METHODS[(turn + rep + contextIndex) % PaidGuidePools.METHODS.length];
                List<PaidGuidePools.Entry> pool;
                if (method.equals("INITIAL_ND")) pool = initial;
                else {
                    started = System.nanoTime(); pool = PaidGuidePools.construct(known, method);
                    poolRecord(id, rep, method, pool, System.nanoTime() - started);
                }
                for (String[] recipient : recipients) {
                    int parentIndex = Integer.parseInt(recipient[1]);
                    PaidGuidePools.Entry parent = byId.get(recipient[2]), personal = byId.get(recipient[3]);
                    if (parent == null || personal == null) throw new AssertionError("Unpaid parent or personal guide");
                    long selectSeed = NeutralProbeSupport.mixed(seed + contextIndex * 1009L + parentIndex * 117L + rep);
                    long noise = NeutralProbeSupport.mixed(selectSeed ^ 0x5a17c9e3L);
                    started = System.nanoTime();
                    int chosen = (int) (new Random(selectSeed).nextDouble() * pool.size());
                    PaidGuidePools.Entry guide = pool.get(chosen);
                    @SuppressWarnings("unchecked") PermutationSolution<Integer> copiedGuide =
                            (PermutationSolution<Integer>) guide.value.copy();
                    long selectionNanos = System.nanoTime() - started;
                    SeededRandom.reset(noise); started = System.nanoTime();
                    PermutationSolution<Integer> child = kernel.child(KernelVariants.JOB_ALIGNED,
                            parent.value, personal.value, copiedGuide);
                    int repair = SchedulingEncoding.repair(child, instance);
                    long generationNanos = System.nanoTime() - started;
                    started = System.nanoTime(); context.problem().evaluate(child);
                    long evaluationNanos = System.nanoTime() - started;
                    check(child);
                    NeutralProbeSupport.append(output.resolve("outcomes.jsonl"), NeutralProbeSupport.row(
                            "context", id, "recipient", parentIndex, "rep", rep, "method", method,
                            "parentId", parent.id, "personalId", personal.id, "guideId", guide.id,
                            "guideFirstRole", guide.firstRole, "selectSeed", selectSeed, "constructionSeed", noise,
                            "paidFE", context.budget().successful(), "child", ProbeData.encoding(child),
                            "selectionSeconds", selectionNanos / 1e9, "generationSeconds", generationNanos / 1e9,
                            "evaluationSeconds", evaluationNanos / 1e9, "commonRepairEdits", repair));
                }
            }
        }
        for (int index = 0; index < known.size(); index++)
            if (!original.get(index).equals(ProbeData.key(known.get(index).value)))
                throw new AssertionError("Teacher kernel mutated a paid source");
    }

    private List<PaidGuidePools.Entry> replay(String id, List<String[]> fields) {
        List<PaidGuidePools.Entry> known = new ArrayList<>();
        for (String[] row : fields) {
            long started = System.nanoTime();
            PermutationSolution<Integer> point = context.problem().createSolution();
            ProbeData.fill(point, row, 5, -1, null);
            long reconstructionNanos = System.nanoTime() - started;
            started = System.nanoTime(); context.problem().evaluate(point);
            long evaluationNanos = System.nanoTime() - started;
            ProbeData.expected(point, row[9]); check(point);
            PaidGuidePools.Entry entry = new PaidGuidePools.Entry(row, point); known.add(entry);
            NeutralProbeSupport.append(output.resolve("paid-inputs.jsonl"), NeutralProbeSupport.row(
                    "context", id, "id", entry.id, "membership", entry.membership,
                    "paidFE", context.budget().successful(), "firstPaidFE", entry.firstPaid,
                    "reconstructionSeconds", reconstructionNanos / 1e9, "evaluationSeconds", evaluationNanos / 1e9,
                    "genome", ProbeData.encoding(point)));
        }
        return known;
    }

    private void poolRecord(String id, int rep, String method, List<PaidGuidePools.Entry> pool, long nanos) {
        List<String> ids = new ArrayList<>(); for (PaidGuidePools.Entry entry : pool) ids.add(entry.id);
        NeutralProbeSupport.append(output.resolve("pools.jsonl"), NeutralProbeSupport.row(
                "context", id, "rep", rep, "method", method, "ids", ids, "buildSeconds", nanos / 1e9));
    }

    private void check(PermutationSolution<Integer> point) {
        long started = System.nanoTime(); fullQA++;
        NeutralProbeSupport.sameTimeline((DynamicSchedule) point.getAttribute(DynamicEvaluation.KEY),
                NeutralProbeSupport.full(instance, parameters, point));
        qaSeconds += (System.nanoTime() - started) / 1e9;
    }
}
