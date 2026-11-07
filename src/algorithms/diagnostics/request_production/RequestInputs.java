package org.uma.jmetal.util.research.search;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.cooperation.RequestPoolAccess;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.modelglobal.FourVectors;

/** Frozen source inputs. Full import decodes restore already-paid caches, never create archive points. */
public final class RequestInputs {
    final List<PermutationSolution<Integer>> receivers = new ArrayList<>();
    final List<Direction> roles = new ArrayList<>();
    final List<Long> receiverSourceFE = new ArrayList<>();
    final List<double[]> background = new ArrayList<>();
    final RequestSpec actual, effective;
    final RequestPoolAccess pools;
    private long restored, restoreNanos;

    RequestInputs(Path folder, Problem<PermutationSolution<Integer>> problem, Instance in,
            DynamicParameters params, String arm) throws IOException {
        long start = System.nanoTime();
        for (String line : Files.readAllLines(folder.resolve("points.tsv"), StandardCharsets.UTF_8)) {
            String[] fields = line.split("\t", -1);
            if (fields.length != 10 || !fields[0].equals("P")) throw new IllegalArgumentException("Expected mature P100 only");
            if (Integer.parseInt(fields[1]) != receivers.size()) throw new AssertionError("Source receiver order differs");
            PermutationSolution<Integer> point = point(problem, in, Integer.parseInt(fields[4]), fields, 5);
            restore(point, in, params); receivers.add(point); roles.add(Direction.valueOf(fields[3]));
            receiverSourceFE.add(Long.parseLong(fields[2]));
        }
        if (receivers.size() != 100) throw new AssertionError("Expected mature P100");
        actual = request(folder.resolve("request.tsv"), problem, in, params);
        RequestSpec shuffled = request(folder.resolve("effective-request.tsv"), problem, in, params);
        if (actual.family != shuffled.family || !Arrays.equals(fixed(actual.parent), fixed(shuffled.parent)))
            throw new AssertionError("Shuffled request must have the same family job sets");
        effective = arm.equals("SHUFFLED") ? shuffled : actual;
        int[] count = new int[4]; int familyCount = 0;
        for (int i = 0; i < receivers.size(); i++) if (((Integer) receivers.get(i).getAttribute("cooperation.family")) == actual.family) {
            familyCount++; count[roles.get(i).ordinal()]++;
            if (!Arrays.equals(fixed(receivers.get(i)), fixed(actual.parent))) throw new AssertionError("Receiver request job sets differ");
        }
        if (familyCount != 5 || !Arrays.equals(count, new int[]{1, 2, 1, 1})) throw new AssertionError("Expected original M1/C2/E1/W1 family");
        for (String line : Files.readAllLines(folder.resolve("background.tsv"), StandardCharsets.UTF_8)) {
            double[] objective = doubles(line.replace('\t', ','));
            if (objective.length != 3) throw new IllegalArgumentException("Expected A0 objective triple");
            background.add(objective);
        }
        if (background.isEmpty()) throw new AssertionError("Common paid background is empty");
        restoreNanos = System.nanoTime() - start;
        pools = new RequestPoolAccess(in, params, actual, folder.resolve("pools.tsv"));
    }

    private RequestSpec request(Path path, Problem<PermutationSolution<Integer>> problem,
            Instance in, DynamicParameters params) throws IOException {
        List<String> lines = Files.readAllLines(path, StandardCharsets.UTF_8);
        if (lines.size() != 1) throw new IllegalArgumentException("Exactly one request per context file");
        String[] fields = lines.get(0).split("\t", -1);
        if (fields.length != 11) throw new IllegalArgumentException("Expected eleven request columns");
        PermutationSolution<Integer> parent = point(problem, in, Integer.parseInt(fields[1]), fields, 6);
        restore(parent, in, params); return new RequestSpec(fields, parent);
    }

    private void restore(PermutationSolution<Integer> point, Instance in, DynamicParameters params) {
        DynamicSchedule schedule = full(in, params, point); restored++;
        if (!Arrays.equals(schedule.objectives(), point.getObjectives())) throw new AssertionError("Source-paid objectives do not reproduce");
        point.setAttribute(DynamicEvaluation.KEY, schedule);
    }

    private static PermutationSolution<Integer> point(Problem<PermutationSolution<Integer>> problem,
            Instance in, int family, String[] fields, int offset) {
        double[] objectives = doubles(fields[offset]);
        int[] js = ints(fields[offset + 1]), fa = ints(fields[offset + 2]);
        int[] ma = ints(fields[offset + 3]), wa = ints(fields[offset + 4]);
        if (objectives.length != 3 || js.length != in.jobs() || fa.length != js.length
                || ma.length != js.length || wa.length != js.length) throw new IllegalArgumentException("Malformed paid source point");
        PermutationSolution<Integer> point = problem.createSolution();
        @SuppressWarnings("unchecked") List<Integer> machines = (List<Integer>) point.getAttribute("machine");
        int[] assignment = new int[js.length];
        for (int i = 0; i < js.length; i++) {
            point.setVariableValue(i, js[i]); point.setVariableValueid(i, fa[i]);
            machines.set(i, ma[i]); point.setVariableValueworker(i, wa[i]); assignment[js[i]] = fa[i];
        }
        for (int k = 0; k < 3; k++) point.setObjective(k, objectives[k]);
        point.setAttribute("cooperation.family", family);
        if (family >= 0) point.setAttribute("cooperation.fixedFactoryByJob", assignment);
        if (SchedulingEncoding.repair(point, in) != 0) throw new AssertionError("Imported paid source required repair");
        return point;
    }

    private static int[] fixed(PermutationSolution<Integer> value) {
        return (int[]) value.getAttribute("cooperation.fixedFactoryByJob");
    }

    public Map<String,Object> receipt() {
        Map<String,Object> result = GomRecords.row("sourcePointFullDecodes", restored, "sourcePointQASeconds", restoreNanos / 1e9,
            "importObjectiveMatches", restored, "importedCandidatesOfferedToArchive", 0,
            "sourceCacheRecovery", "Already-paid source vectors only; local metrics restored by full decode");
        result.putAll(pools.importReceipt()); return result;
    }

    public static DynamicSchedule full(Instance in, DynamicParameters params, PermutationSolution<Integer> point) {
        FourVectors v = GomRecords.vectors(point);
        DynamicSchedule full = DynamicDecoder.full(in, params, v.jobs(), v.factories(), v.machines(), v.workers(), () -> {});
        DynamicValidator.validate(in, params, full); return full;
    }

    public static int[] ints(String value) {
        if (value.isEmpty()) return new int[0];
        String[] fields = value.split(","); int[] result = new int[fields.length];
        for (int i = 0; i < result.length; i++) result[i] = Integer.parseInt(fields[i]); return result;
    }

    public static double[] doubles(String value) {
        String[] fields = value.split(","); double[] result = new double[fields.length];
        for (int i = 0; i < result.length; i++) {
            result[i] = Double.parseDouble(fields[i]);
            if (!Double.isFinite(result[i])) throw new IllegalArgumentException("Nonfinite imported value");
        }
        return result;
    }
}
