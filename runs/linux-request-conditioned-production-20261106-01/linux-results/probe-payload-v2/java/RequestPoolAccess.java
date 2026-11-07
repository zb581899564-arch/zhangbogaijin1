package org.uma.jmetal.util.research.cooperation;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.search.GomRecords;
import org.uma.jmetal.util.research.search.RequestInputs;
import org.uma.jmetal.util.research.search.RequestSpec;

/** Import-only bridge to the unchanged production FactoryPool, including its exact tie rules. */
public final class RequestPoolAccess {
    private final FactoryPool[] pools;
    private final Instance instance;
    private long importDecodes, importNanos;
    private long productionOffers;

    public RequestPoolAccess(Instance in, DynamicParameters params, RequestSpec request, Path input) throws IOException {
        instance = in; pools = new FactoryPool[in.factories()];
        for (int f = 0; f < pools.length; f++) pools[f] = new FactoryPool();
        long start = System.nanoTime();
        for (String line : Files.readAllLines(input, StandardCharsets.UTF_8)) {
            String[] fields = line.split("\t", -1);
            if (fields.length != 6) throw new IllegalArgumentException("Expected six retained-pool columns");
            int factory = Integer.parseInt(fields[0]); long sourceFE = Long.parseLong(fields[1]);
            if (factory < 0 || factory >= pools.length || sourceFE < -1) throw new IllegalArgumentException("Invalid imported pool identity");
            double[] objectives = RequestInputs.doubles(fields[2]);
            int[] jobs = RequestInputs.ints(fields[3]), machines = RequestInputs.ints(fields[4]), workers = RequestInputs.ints(fields[5]);
            requireJobSet(request.parent, factory, jobs);
            PermutationSolution<Integer> qaPoint = replaceFactory(request.parent, factory, jobs, machines, workers);
            DynamicSchedule schedule = RequestInputs.full(in, params, qaPoint); importDecodes++;
            FactoryRecord record = new FactoryRecord(schedule, factory, sourceFE, -1, "IMPORTED_RETAINED", "SOURCE");
            if (!Arrays.equals(record.objectives, objectives) || !Arrays.equals(record.jobs, jobs)
                    || !Arrays.equals(record.machines, machines) || !Arrays.equals(record.workers, workers))
                throw new AssertionError("Imported retained factory does not reproduce its paid values");
            int size = pools[factory].size(); pools[factory].offer(record);
            if (pools[factory].size() != size + 1 || pools[factory].truncated != 0)
                throw new AssertionError("Source retained list changed under original pool rules");
        }
        for (FactoryPool pool : pools) if (pool.size() == 0) throw new AssertionError("Missing source factory pool");
        importNanos = System.nanoTime() - start;
    }

    public void observe(PermutationSolution<Integer> point, long fee, String producer) {
        DynamicSchedule paid = (DynamicSchedule) point.getAttribute(DynamicEvaluation.KEY);
        if (paid == null) throw new AssertionError("Pool observation requires a paid full schedule");
        for (int f = 0; f < pools.length; f++) pools[f].offer(new FactoryRecord(paid, f, fee, -1, "PROBE_PAID", producer));
        productionOffers++;
    }

    public Assembly compose(RequestSpec actual) {
        FactoryRecord[] chosen = choose(actual); boolean feasible = feasible(chosen);
        if (!feasible) return new Assembly(copy(actual.parent), false, false, null, chosenRecords(chosen));
        PermutationSolution<Integer> point = copy(actual.parent);
        @SuppressWarnings("unchecked") List<Integer> machines = (List<Integer>) point.getAttribute("machine");
        double[] prediction = new double[3]; int at = 0; boolean same = true;
        DynamicSchedule parent = (DynamicSchedule) actual.parent.getAttribute(DynamicEvaluation.KEY);
        for (int f = 0; f < pools.length; f++) {
            FactoryRecord record = chosen[f];
            same &= record.same(new FactoryRecord(parent, f));
            prediction[0] = Math.max(prediction[0], record.objectives[0]);
            prediction[1] += record.objectives[1]; prediction[2] += record.objectives[2];
            for (int i = 0; i < record.jobs.length; i++) {
                point.setVariableValue(at, record.jobs[i]); point.setVariableValueid(at, f);
                machines.set(at, record.machines[i]); point.setVariableValueworker(at++, record.workers[i]);
            }
        }
        point.setAttribute("worker", point.getVariablesworker());
        if (SchedulingEncoding.repair(point, instance) != 0) throw new AssertionError("Composition required repair");
        return new Assembly(point, true, same, prediction, chosenRecords(chosen));
    }

    /** Selection evidence only: unlike compose(), this never constructs a candidate. */
    public Map<String,Object> inspectChoice(RequestSpec actual) {
        FactoryRecord[] chosen = choose(actual); boolean possible = feasible(chosen);
        double[] predicted = new double[3];
        if (possible) for (FactoryRecord record : chosen) {
            predicted[0] = Math.max(predicted[0], record.objectives[0]);
            predicted[1] += record.objectives[1]; predicted[2] += record.objectives[2];
        }
        return GomRecords.row("chosen", chosenRecords(chosen), "feasible", possible, "predicted", possible ? predicted : null);
    }

    private FactoryRecord[] choose(RequestSpec actual) {
        FactoryRecord[] result = new FactoryRecord[pools.length];
        for (int f = 0; f < pools.length; f++) result[f] = pools[f].choose(actual.cap, actual.eta, actual.energyScale, actual.wageScale);
        return result;
    }

    private static boolean feasible(FactoryRecord[] chosen) {
        for (FactoryRecord record : chosen) if (record == null) return false;
        return true;
    }

    public Map<String,Object> importReceipt() {
        return GomRecords.row("retainedRecordFullDecodes", importDecodes, "retainedRecordQASeconds", importNanos / 1e9,
            "qaCombinationsOfferedToArchive", 0, "poolImplementation", FactoryPool.class.getName());
    }

    public Map<String,Object> snapshot() {
        List<Map<String,Object>> all = new ArrayList<>();
        long accepted = 0, rejected = 0, truncated = 0;
        for (int f = 0; f < pools.length; f++) {
            List<Map<String,Object>> records = new ArrayList<>();
            for (FactoryRecord record : pools[f].records()) records.add(record(record));
            all.add(GomRecords.row("factory", f, "records", records));
            accepted += pools[f].accepted; rejected += pools[f].rejected; truncated += pools[f].truncated;
        }
        return GomRecords.row("factories", all, "paidObservations", productionOffers, "accepted", accepted,
            "rejected", rejected, "truncated", truncated);
    }

    private static List<Map<String,Object>> chosenRecords(FactoryRecord[] records) {
        List<Map<String,Object>> result = new ArrayList<>();
        for (FactoryRecord record : records) result.add(record == null ? null : record(record));
        return result;
    }

    private static Map<String,Object> record(FactoryRecord value) {
        return GomRecords.row("jobs", value.jobs, "machines", value.machines, "workers", value.workers,
            "objectives", value.objectives, "paidFE", value.paidFE, "stage", value.stage);
    }

    private static void requireJobSet(PermutationSolution<Integer> parent, int factory, int[] jobs) {
        int[] expected = GomRecords.vectors(parent).jobs(), fa = GomRecords.vectors(parent).factories();
        List<Integer> selected = new ArrayList<>();
        for (int i = 0; i < expected.length; i++) if (fa[i] == factory) selected.add(expected[i]);
        int[] actual = jobs.clone(); Arrays.sort(actual); Collections.sort(selected);
        if (actual.length != selected.size()) throw new AssertionError("Imported factory job count differs");
        for (int i = 0; i < actual.length; i++) if (actual[i] != selected.get(i)) throw new AssertionError("Imported factory job set differs");
    }

    private static PermutationSolution<Integer> replaceFactory(PermutationSolution<Integer> parent, int factory,
            int[] jobs, int[] machines, int[] workers) {
        if (jobs.length != machines.length || jobs.length != workers.length) throw new IllegalArgumentException("Malformed local encoding");
        PermutationSolution<Integer> point = copy(parent);
        @SuppressWarnings("unchecked") List<Integer> ma = (List<Integer>) point.getAttribute("machine");
        int at = 0;
        for (int i = 0; i < point.getNumberOfVariables(); i++) if (point.getVariableValueid(i) == factory) {
            point.setVariableValue(i, jobs[at]); ma.set(i, machines[at]); point.setVariableValueworker(i, workers[at++]);
        }
        return point;
    }

    @SuppressWarnings("unchecked") private static PermutationSolution<Integer> copy(PermutationSolution<Integer> point) {
        return (PermutationSolution<Integer>) point.copy();
    }

    public static final class Assembly {
        public final PermutationSolution<Integer> point;
        public final boolean feasible, duplicateParent;
        public final double[] predicted;
        public final List<Map<String,Object>> chosen;
        Assembly(PermutationSolution<Integer> value, boolean possible, boolean duplicate, double[] prediction,
                List<Map<String,Object>> records) {
            point = value; feasible = possible; duplicateParent = duplicate; predicted = prediction; chosen = records;
        }
        public void validate() {
            if (predicted == null) return;
            for (int k = 0; k < 3; k++) if (Math.abs(predicted[k] - point.getObjective(k)) > 1e-9 * Math.max(1, Math.abs(predicted[k])))
                throw new AssertionError("Original pool composition prediction differs from charged decode");
        }
    }
}
