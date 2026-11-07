package research.dynamic;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.util.research.modelglobal.*;

/** Engineering observation never supplies a score, donor, RNG draw or acceptance decision. */
final class QpaEvidence implements QpaPopulation.Observer, AutoCloseable {
    private final BufferedWriter events, initials;
    private final PaRunChecks checks;
    final Map<String,Long> fees = new LinkedHashMap<>();
    long accepted, fallbacks, unchanged;

    QpaEvidence(Path out, PaRunChecks validation) throws IOException {
        checks = validation;
        events = Files.newBufferedWriter(out.resolve("events.jsonl"), StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        initials = Files.newBufferedWriter(out.resolve("initial-population.jsonl"), StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
    }
    private static void emit(BufferedWriter writer, Map<String,Object> record) {
        try { writer.write(DynamicJson.encode(record)); writer.newLine(); }
        catch (IOException error) { throw new UncheckedIOException(error); }
    }
    private void count(String key) { fees.put(key, fees.getOrDefault(key, 0L) + 1); }
    public void initial(int slot, QpaIndividual value, PaInternalArchive.Flags flags) {
        value.verifyStoredView(); count("initialization"); count("role." + value.role.name());
        Map<String,Object> record = QpaStateRecords.state(value, true);
        record.putAll(NeutralProbeSupport.row("kind", "initial", "slot", slot, "rawPaidHash", checks.lastRawHash));
        QpaStateRecords.flags(record, flags); emit(events, record); emit(initials, QpaStateRecords.raw(value));
    }
    public void model(int generation, List<QpaIndividual> parents, QpaLinkageModel model, long nanos) {
        for (QpaIndividual value : parents) value.verifyStoredView();
        emit(events, NeutralProbeSupport.row("kind", "model", "generation", generation,
            "parents", QpaStateRecords.population(parents), "affinity", model.affinity, "fullSubsets", model.fullSubsets,
            "activeSubsets", model.activeSubsets, "cutoff", model.cutoff, "modelNanos", nanos));
    }
    public void step(int generation, int slot, int step, int subset, int phase, int donorSlot, int reference,
            QpaIndividual parent, QpaIndividual donor, QpaIndividual child, boolean fallback, PaInternalArchive.Flags flags, boolean keep) {
        parent.verifyStoredView(); donor.verifyStoredView(); child.verifyStoredView();
        count("mixing"); count("phase." + phase); count("role." + parent.role.name());
        if (keep) accepted++; if (fallback) fallbacks++; if (child.hash.equals(parent.hash)) unchanged++;
        Map<String,Object> record = QpaStateRecords.state(child, false);
        record.putAll(NeutralProbeSupport.row("kind", "step", "generation", generation, "slot", slot, "step", step,
            "subset", subset, "phase", phase, "donorSlot", donorSlot, "reference", reference, "parentId", parent.id,
            "parentHash", parent.hash, "parentObjectives", parent.objectives(), "donorId", donor.id, "donorHash", donor.hash,
            "fallback", fallback, "accepted", keep, "rawPaidHash", checks.lastRawHash));
        QpaStateRecords.flags(record, flags); emit(events, record);
    }
    public void programEnd(int generation, int slot, QpaIndividual value) {
        emit(events, NeutralProbeSupport.row("kind", "programEnd", "generation", generation, "slot", slot,
            "result", QpaStateRecords.state(value, false)));
    }
    public void generationEnd(int generation, List<QpaIndividual> population) {
        for (QpaIndividual value : population) value.verifyStoredView();
        emit(events, NeutralProbeSupport.row("kind", "generationEnd", "generation", generation,
            "population", QpaStateRecords.population(population)));
        try { events.flush(); } catch (IOException error) { throw new UncheckedIOException(error); }
    }
    public void close() throws IOException { try { events.close(); } finally { initials.close(); } }
}
