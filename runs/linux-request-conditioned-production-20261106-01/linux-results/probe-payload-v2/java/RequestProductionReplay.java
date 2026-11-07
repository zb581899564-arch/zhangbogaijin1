package org.uma.jmetal.util.research.search;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.cooperation.RequestPoolAccess;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.modelglobal.*;
import org.uma.jmetal.util.research.runtime.*;
import research.dynamic.DynamicJson;

/** A fixed-model, five-receiver conditional production probe; never a resumed full algorithm. */
public final class RequestProductionReplay implements Algorithm<Object> {
    private static final long serialVersionUID = 1L;
    private static final int PRODUCTION_FE = 511;
    private final RunContext<PermutationSolution<Integer>> run;
    private final Instance instance;
    private final RequestInputs input;
    private final RequestAcceptance acceptance;
    private final GomRunScope scope;
    private final Path output;
    private final String arm;
    private final boolean recording;
    private final BufferedWriter paidLog, stepLog;
    private final List<List<Integer>> orders = new ArrayList<>();
    private final int[] cursors = new int[5], rounds = new int[5];
    private final long[] produced = new long[5];
    private List<Integer> slots;
    private GomWorkspace work;
    private long paidRows, productionPaid, assemblyPaid;
    private long paidEvidenceNanos, stepEvidenceNanos;
    private String stage = "PREPARED", producer = "NONE";
    private Map<String,Object> pending, assembly = GomRecords.row("performed", false);

    public RequestProductionReplay(RunContext<PermutationSolution<Integer>> context, Instance in, DynamicParameters params,
            Path directory, Path out, String mode, long seed) throws IOException {
        run = context; instance = in; output = out; arm = mode;
        if (!RequestAcceptance.ARMS.contains(mode)) throw new IllegalArgumentException("Unknown arm " + mode);
        recording = Boolean.parseBoolean(System.getProperty("research.request.observer", "true"));
        input = new RequestInputs(directory, run.problem(), in, params, mode);
        acceptance = new RequestAcceptance(mode, input.effective);
        SeededRandom.reset(seed);
        scope = new GomRunScope(run, new GomRunScope.Evidence() {
            public boolean recording() { return false; }
            public void record(Map<String,Object> row) { throw new AssertionError("Unused scope recorder"); }
            public void view(PermutationSolution<Integer> a, PermutationSolution<Integer> b) { throw new AssertionError("Unused scope view"); }
        }, phase -> {});
        for (double[] objectives : input.background) scope.archive.offer(objectives);
        paidLog = Files.newBufferedWriter(out.resolve("paid.jsonl"), StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        stepLog = Files.newBufferedWriter(out.resolve("steps.jsonl"), StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
    }

    /** Always runs: archive/pool notifications are algorithm semantics, independent of the evidence switch. */
    public void observed(PermutationSolution<Integer> point, long fe) {
        scope.observed(point, fe, null);
        input.pools.observe(point, fe, producer);
        if (stage.equals("PRODUCTION")) productionPaid++; else if (stage.equals("ASSEMBLY")) assemblyPaid++;
        else throw new AssertionError("Paid evaluation outside a declared stage");
        if (recording) {
            long evidenceStart = System.nanoTime();
            Map<String,Object> row = GomRecords.raw(point);
            DynamicSchedule paid = schedule(point);
            if (pending != null) row.putAll(pending);
            row.putAll(GomRecords.row("fe", fe, "stage", stage, "producer", producer, "dominated", scope.lastFlags.dominated,
                "equal", scope.lastFlags.equal, "fresh", scope.lastFlags.fresh, "archiveBefore", scope.lastFlags.before,
                "archiveAfter", scope.lastFlags.after, "factoryMakespan", paid.factoryMakespan(),
                "factoryEnergy", paid.factoryEnergy(), "factoryCost", paid.factoryCost()));
            append(paidLog, row); paidRows++; paidEvidenceNanos += System.nanoTime() - evidenceStart;
        }
    }

    public void run() {
        prepare(); stage = "PRODUCTION";
        for (int fee = 0; fee < PRODUCTION_FE; fee++) proposal(fee % 5);
        run.problem().checkpoint(); // A cutoff of 511 never even constructs a final assembly.
        compose(); stage = "COMPLETE";
    }

    private void prepare() {
        GomRunScope.begin(input.receivers, instance); work = scope.workspace;
        slots = new ArrayList<>(work.domains.get(input.actual.family));
        if (slots.size() != 5) throw new AssertionError("Expected five mature fixed-family receivers");
        List<int[]> masks = work.masks.get(input.actual.family);
        if (masks.size() != 2 * instance.jobs() - instance.factories()) throw new AssertionError("Original factory-block FOS changed");
        for (int i = 0; i < 5; i++) orders.add(shuffled(masks.size()));
        write(output.resolve("before.json"), population());
        write(output.resolve("models.json"), GomRecords.row("family", input.actual.family, "slots", slots, "masks", masks,
            "initialOrders", orders, "domain", work.domains.get(input.actual.family), "model", "Original GomDomainModels"));
        Map<String,Object> pools = input.pools.snapshot();
        pools.put("initialSelection", input.pools.inspectChoice(input.actual));
        write(output.resolve("initial-pools.json"), pools);
    }

    private void proposal(int receiver) {
        run.problem().checkpoint(); int slot = slots.get(receiver);
        if (cursors[receiver] == orders.get(receiver).size()) {
            orders.set(receiver, shuffled(orders.get(receiver).size())); cursors[receiver] = 0; rounds[receiver]++;
        }
        int subset = orders.get(receiver).get(cursors[receiver]);
        List<Integer> donors = new ArrayList<>(slots); donors.remove(Integer.valueOf(slot));
        int donorSlot = donors.get(SeededRandom.current().nextInt(donors.size()));
        GomRecords.State parent = work.values.get(slot), donor = work.values.get(donorSlot);
        int[] mask = work.masks.get(input.actual.family).get(subset);
        PaMixingMove move = PaMixingMove.apply(work.catalog, parent.genes, donor.genes, mask);
        PermutationSolution<Integer> child = GomRecords.copy(parent.point, move.genome);
        if (SchedulingEncoding.repair(child, instance) != 0) throw new AssertionError("Original GOM proposal required repair");
        Direction role = input.roles.get(slot); producer = role.name();
        pending = GomRecords.row("stage", stage, "receiver", receiver, "slot", slot, "role", producer,
            "round", rounds[receiver], "step", cursors[receiver], "subset", subset, "donorSlot", donorSlot,
            "mask", mask, "parentId", parent.id, "donorId", donor.id, "parentPaidFE", parent.paidFE, "donorPaidFE", donor.paidFE,
            "parentSourcePaidByFE", input.receiverSourceFE.get(slot), "donorSourcePaidByFE", input.receiverSourceFE.get(donorSlot));
        run.problem().evaluate(child); GomRecords.sameView(child, move.genome);
        if (scope.lastPaid != child) throw new AssertionError("Paid child missed common archive");
        RequestAcceptance.Decision decision = acceptance.decide(role, child.getObjectives(), parent.objectives,
            schedule(child).factoryMakespan(), schedule(parent.point).factoryMakespan(), scope.lastFlags);
        GomRecords.State candidate = new GomRecords.State(++scope.states, run.budget().successful(), move.genome, child);
        if (decision.keep) work.values.set(slot, candidate);
        produced[receiver]++; cursors[receiver]++;
        if (recording) {
            long evidenceStart = System.nanoTime();
            Map<String,Object> row = GomRecords.raw(child); row.putAll(pending); row.putAll(decision.record());
            row.putAll(GomRecords.row("fe", run.budget().successful(), "mask", mask, "parentObjectives", parent.objectives,
                "fallback", move.fallback, "resources", move.genome.allocations(), "keys", move.genome.priorities(),
                "candidateId", candidate.id, "dominated", scope.lastFlags.dominated, "equal", scope.lastFlags.equal,
                "fresh", scope.lastFlags.fresh, "archiveBefore", scope.lastFlags.before, "archiveAfter", scope.lastFlags.after));
            append(stepLog, row); stepEvidenceNanos += System.nanoTime() - evidenceStart;
        }
        pending = null;
    }

    private void compose() {
        stage = "ASSEMBLY"; producer = "ORIGINAL_SHARED_SELECTOR";
        RequestPoolAccess.Assembly choice = input.pools.compose(input.actual);
        pending = GomRecords.row("stage", stage, "actualRequest", input.actual.record(), "feasible", choice.feasible);
        assembly = GomRecords.row("performed", false, "attempted", true, "fe", 512, "request", input.actual.record(),
            "feasible", choice.feasible, "fallbackPaidParent", !choice.feasible, "duplicateParent", choice.duplicateParent,
            "predicted", choice.predicted, "chosen", choice.chosen);
        run.problem().evaluate(choice.point); choice.validate();
        assembly.put("performed", true); assembly.put("result", GomRecords.raw(choice.point)); pending = null;
    }

    private static List<Integer> shuffled(int size) {
        List<Integer> order = new ArrayList<>(); for (int i = 0; i < size; i++) order.add(i);
        Collections.shuffle(order, SeededRandom.current()); return order;
    }

    private static DynamicSchedule schedule(PermutationSolution<Integer> point) {
        DynamicSchedule result = (DynamicSchedule) point.getAttribute(DynamicEvaluation.KEY);
        if (result == null) throw new AssertionError("Missing paid or restored source schedule"); return result;
    }

    public List<Map<String,Object>> population() {
        List<Map<String,Object>> result = new ArrayList<>(); if (work == null) return result;
        for (int slot : slots) {
            GomRecords.State state = work.values.get(slot);
            DynamicSchedule paid = schedule(state.point);
            Map<String,Object> row = GomRecords.raw(GomRecords.copy(state.point, state.genes));
            row.putAll(GomRecords.row("slot", slot, "family", input.actual.family, "role", input.roles.get(slot).name(),
                "resources", state.genes.allocations(), "keys", state.genes.priorities(), "paidFE", state.paidFE,
                "stateId", state.id, "sourcePaidByFE", input.receiverSourceFE.get(slot),
                "factoryMakespan", paid.factoryMakespan(), "factoryEnergy", paid.factoryEnergy(),
                "factoryCost", paid.factoryCost())); result.add(row);
        }
        return result;
    }

    public Map<String,Object> receipt() {
        return GomRecords.row("arm", arm, "stage", stage, "actualRequest", input.actual.record(), "effectiveRequest", input.effective.record(),
            "productionPaid", productionPaid, "assemblyPaid", assemblyPaid, "perReceiverFE", produced, "acceptance", acceptance.receipt(),
            "pending", pending, "observer", recording, "paidLogRows", paidRows, "backgroundPoints", input.background.size(),
            "paidEvidenceSeconds", paidEvidenceNanos / 1e9, "stepEvidenceSeconds", stepEvidenceNanos / 1e9,
            "evidenceTimingScope", "Detailed paid/step record construction and append only; archive/pool semantics excluded; final file close and snapshot IO excluded",
            "importQA", input.receipt(), "plannedProductionFE", PRODUCTION_FE, "plannedTotalFE", 512,
            "productionEtaUsage", arm.equals("ORDINARY") ? "Equal-violation weighted acceptance" : "None; role semantics preserved",
            "scope", "Fixed-model five-receiver conditional probe; not full four-group algorithm performance");
    }

    public void finish() {
        try { paidLog.close(); stepLog.close(); } catch (IOException error) { throw new UncheckedIOException(error); }
        write(output.resolve("after.json"), population()); write(output.resolve("front.json"), scope.archive());
        write(output.resolve("assembly.json"), assembly); write(output.resolve("final-pools.json"), input.pools.snapshot());
    }

    private static void append(BufferedWriter writer, Object value) {
        try { writer.write(DynamicJson.encode(value)); writer.newLine(); } catch (IOException error) { throw new UncheckedIOException(error); }
    }
    public static void write(Path file, Object value) {
        try { Files.write(file, DynamicJson.encode(value).getBytes(StandardCharsets.UTF_8), StandardOpenOption.CREATE_NEW); }
        catch (IOException error) { throw new UncheckedIOException(error); }
    }
    public Object getResult() { return scope.archive(); }
    public String getName() { return "REQUEST_CONDITIONED_PRODUCTION_" + arm; }
    public String getDescription() { return "Matched factory-block GOM proposals; experimental acceptance only"; }
}
