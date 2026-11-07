package research.dynamic;

import java.io.BufferedWriter;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.util.research.modelglobal.*;

/** Append-only state transition log; snapshots are immutable numeric copies, never search feedback. */
final class PaEvidence implements PaPopulation.Observer, AutoCloseable {
    private final BufferedWriter events;
    private final PaRunChecks checks;
    final Map<String,Long> fees = new LinkedHashMap<>();
    long accepted, fallbacks, unchanged, currentGenerationDonorReads, changedCurrentGenerationDonorReads;
    private final Set<Long> acceptedInGeneration = new HashSet<>();
    private final Set<Long> changedInGeneration = new HashSet<>();

    PaEvidence(Path out, PaRunChecks validation) throws IOException {
        checks = validation; events = Files.newBufferedWriter(out.resolve("events.jsonl"), StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
    }
    private void emit(Map<String,Object> record) {
        try { events.write(DynamicJson.encode(record)); events.newLine(); }
        catch (IOException e) { throw new UncheckedIOException(e); }
    }
    private void count(String key) { fees.put(key, fees.getOrDefault(key, 0L) + 1); }
    public void initial(int slot, PaIndividual point, PaInternalArchive.Flags flags) {
        count("initialization"); count("role." + point.role.name());
        Map<String,Object> record = PaStateRecords.state(point, true);
        record.putAll(NeutralProbeSupport.row("kind", "initial", "slot", slot, "rawPaidHash", checks.lastRawHash));
        flags(record, flags); emit(record);
    }
    public void reencoded(int generation, int slot, PaIndividual before, PaIndividual after) {
        if (slot == 0) { acceptedInGeneration.clear(); changedInGeneration.clear(); }
        Map<String,Object> record = PaStateRecords.state(after, true);
        record.putAll(NeutralProbeSupport.row("kind", "reencode", "generation", generation, "slot", slot, "beforeId", before.id,
            "beforeHash", before.hash)); emit(record);
    }
    public void model(int generation, List<PaIndividual> population, double[][] dependency, List<int[]> subsets, long nanos) {
        emit(NeutralProbeSupport.row("kind", "model", "generation", generation, "population", PaStateRecords.population(population),
            "dependency", dependency, "subsets", subsets, "modelAndHierarchyNanos", nanos));
    }
    public void step(int generation, int slot, int step, int subset, int donorSlot, PaIndividual parent, PaIndividual donor,
            PaIndividual child, boolean fallback, PaInternalArchive.Flags flags, boolean accept) {
        count("mixing"); count("role." + parent.role.name());
        if (accept) { accepted++; acceptedInGeneration.add(child.id); if (!child.hash.equals(parent.hash)) changedInGeneration.add(child.id); }
        if (fallback) fallbacks++; if (child.hash.equals(parent.hash)) unchanged++;
        boolean freshDonor = acceptedInGeneration.contains(donor.id); if (freshDonor) currentGenerationDonorReads++;
        boolean changedDonor = changedInGeneration.contains(donor.id); if (changedDonor) changedCurrentGenerationDonorReads++;
        Map<String,Object> record = PaStateRecords.state(child, false);
        record.putAll(NeutralProbeSupport.row("kind", "step", "generation", generation, "slot", slot, "step", step,
            "subset", subset, "donorSlot", donorSlot, "parentId", parent.id, "parentHash", parent.hash,
            "donorId", donor.id, "donorHash", donor.hash, "donorAcceptedThisGeneration", freshDonor,
            "donorChangedThisGeneration", changedDonor,
            "parentObjectives", parent.objectives(), "fallback", fallback, "accepted", accept, "rawPaidHash", checks.lastRawHash));
        flags(record, flags); emit(record);
    }
    public void programEnd(int generation, int slot, PaIndividual result) {
        emit(NeutralProbeSupport.row("kind", "programEnd", "generation", generation, "slot", slot, "result", PaStateRecords.state(result, false)));
    }
    public void generationEnd(int generation, List<PaIndividual> population) {
        emit(NeutralProbeSupport.row("kind", "generationEnd", "generation", generation, "population", PaStateRecords.population(population)));
        try { events.flush(); } catch (IOException e) { throw new UncheckedIOException(e); }
    }
    private static void flags(Map<String,Object> record, PaInternalArchive.Flags flags) {
        record.putAll(NeutralProbeSupport.row("archiveDominated", flags.dominated, "archiveEqual", flags.equal,
            "archiveFresh", flags.fresh, "archiveSizeBefore", flags.before, "archiveSizeAfter", flags.after));
    }
    public void close() throws IOException { events.close(); }
}
