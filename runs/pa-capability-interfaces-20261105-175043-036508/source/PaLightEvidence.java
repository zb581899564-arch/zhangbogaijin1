package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.solution.*;
import org.uma.jmetal.util.research.runtime.*;
import org.uma.jmetal.util.research.model.*;

/** Same checkpoint capture for all six arms; full replay occurs after the search clock stops. */
final class PaLightEvidence implements EvaluationObserver {
    final AnytimeRecorder recorder;
    final CheckpointGenomes genomes;
    final List<Map<String,Object>> initial = new ArrayList<>();
    final NaturalRunEvidence last = new NaturalRunEvidence();
    final PddrPaidDigest digest;

    PaLightEvidence(long limit, double seconds) throws Exception {
        recorder = new AnytimeRecorder(limit, seconds, new double[]{.5,1}, NaturalRunEvidence.checkpoints(limit));
        genomes = new CheckpointGenomes(recorder, seconds);
        digest = Boolean.getBoolean("research.pa.auditPaid") ? new PddrPaidDigest() : null;
    }
    public void completed(long fe, double seconds, boolean changed, ThreeObjectiveArchive<?> archive) {
        throw new IllegalStateException("Paid point required");
    }
    public void completedSolution(Solution<?> point, long fe, double seconds, boolean changed, ThreeObjectiveArchive<?> archive) {
        last.observed(archive, fe);
        if (digest != null) digest.update(fe, (PermutationSolution<?>)point);
        if (fe <= 100) {
            @SuppressWarnings("unchecked") PermutationSolution<Integer> value = (PermutationSolution<Integer>)point;
            Map<String,Object> record = ProbeData.encoding(value); record.put("fe", fe); initial.add(record);
        }
        genomes.completedSolution(point, fe, seconds, changed, archive);
    }
    void write(Path out, Instance instance, DynamicParameters fatigue) throws Exception {
        writeRows(out.resolve("initial-population.jsonl"), initial);
        writeRows(out.resolve("anytime.jsonl"), recorder.finish()); genomes.validateAndWrite(out, instance, fatigue);
    }
    static void writeRows(Path path, List<Map<String,Object>> values) throws Exception {
        List<String> lines = new ArrayList<>(); for (Map<String,Object> row : values) lines.add(DynamicJson.encode(row));
        Files.write(path, lines, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
    }
}
