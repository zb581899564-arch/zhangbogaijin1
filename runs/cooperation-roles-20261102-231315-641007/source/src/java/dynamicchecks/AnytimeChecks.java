package org.uma.jmetal.util.research.runtime;

import java.util.List;
import java.util.Map;
import java.util.Random;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.joint.JointCheckProblem;
import research.dynamic.AnytimeRecorder;

/** Deterministic monitor checks, with synthetic timestamps and no performance comparison. */
public final class AnytimeChecks {
    private AnytimeChecks() { }

    public static void main(String[] args) {
        SeededRandom.reset(713);
        legacyDefaults();
        dualExactBoundaries();
        crossingSeveralDeadlines();
        exactSuccessfulFE();
        snapshotsStayIndependent();
        emptyAndInfiniteBudgets();
        invalidInputs();
        monitorDoesNotUseRandom();
        System.out.println("ANYTIME_CHECKS_PASS legacy defaults; dual TIME/FE; no future archive; "
                + "exact successful FE; censored FE; independent numeric snapshots; input validation; RNG unchanged");
    }

    private static void legacyDefaults() {
        Fixture fixture = new Fixture();
        AnytimeRecorder time = new AnytimeRecorder(100, 10);
        AnytimeRecorder fe = new AnytimeRecorder(4, Double.POSITIVE_INFINITY);
        double[] seconds = {1,3,6,11};
        for (int i = 0; i < 4; i++) {
            boolean changed = fixture.add(4-i);
            time.completed(i+1, seconds[i], changed, fixture.archive);
            fe.completed(i+1, seconds[i], changed, fixture.archive);
        }
        List<Map<String,Object>> t = time.finish(), f = fe.finish();
        require(t.size() == 3 && f.size() == 3, "Legacy constructor changed row count");
        for (int i = 0; i < 3; i++) {
            assertRow(t.get(i), "TIME", new double[] {2.5,5,10}[i], i+1, true, 4-i);
        }
        assertRow(f.get(2), "FE", 4, 4, true, 1);
        // The old FE percentages can be fractional and must retain their previous-archive semantics.
        AnytimeRecorder fractional = new AnytimeRecorder(3, Double.POSITIVE_INFINITY);
        fractional.completed(1, 1, true, fixture.archive);
        assertRow(fractional.finish().get(0), "FE", .75, 0, true, null);
    }

    private static void dualExactBoundaries() {
        Fixture fixture = new Fixture();
        AnytimeRecorder monitor = new AnytimeRecorder(100, 10, new double[] {.5,1}, new long[] {2,4,15000});
        double[] times = {1,5,9,10,11};
        for (int i = 0; i < times.length; i++) fixture.complete(monitor, i+1, times[i], 8-i);
        List<Map<String,Object>> rows = monitor.finish();
        require(rows.size() == 5, "Dual checkpoint count");
        assertRow(rows.get(0), "TIME", 5, 2, true, 7);
        assertRow(rows.get(1), "TIME", 10, 4, true, 5);
        assertRow(rows.get(2), "FE", 2, 2, true, 7);
        assertRow(rows.get(3), "FE", 4, 4, true, 5);
        assertRow(rows.get(4), "FE", 15000, 5, false, null);
        require(number(rows.get(4), "elapsedSeconds") == 11, "Censored row lacks last actual time");
        require(monitor.finish() == rows, "finish must be idempotent");
    }

    private static void crossingSeveralDeadlines() {
        Fixture fixture = new Fixture();
        AnytimeRecorder monitor = new AnytimeRecorder(10, 10, new double[] {.25,.5,1}, new long[] {2});
        fixture.complete(monitor, 1, 1, 9);
        fixture.complete(monitor, 2, 12, 1);
        List<Map<String,Object>> rows = monitor.finish();
        for (int i = 0; i < 3; i++) {
            assertRow(rows.get(i), "TIME", new double[] {2.5,5,10}[i], 1, true, 9);
            require(number(rows.get(i), "elapsedSeconds") == 1, "Future timestamp entered crossed deadline");
        }
        assertRow(rows.get(3), "FE", 2, 2, false, null);
        require(number(rows.get(3), "elapsedSeconds") == 12, "Late FE censorship lacks actual time");
    }

    private static void exactSuccessfulFE() {
        Fixture fixture = new Fixture();
        AnytimeRecorder monitor = new AnytimeRecorder(20000, 12, new double[] {.5,1}, new long[] {15000});
        fixture.complete(monitor, 14999, 3, 9);
        fixture.complete(monitor, 15000, 7, 8);
        fixture.complete(monitor, 15001, 9, 7);
        List<Map<String,Object>> rows = monitor.finish();
        assertRow(rows.get(0), "TIME", 6, 14999, true, 9);
        assertRow(rows.get(1), "TIME", 12, 15001, true, 7);
        assertRow(rows.get(2), "FE", 15000, 15000, true, 8);
        require(number(rows.get(2), "elapsedSeconds") == 7, "FE snapshot used a future completion");

        AnytimeRecorder skipped = new AnytimeRecorder(10, 10, new double[0], new long[] {2,3});
        skipped.completed(3, 1, true, fixture.archive);
        assertRow(skipped.finish().get(0), "FE", 2, 3, false, null);
        assertRow(skipped.finish().get(1), "FE", 3, 3, true, 7);
    }

    private static void snapshotsStayIndependent() {
        Fixture fixture = new Fixture();
        double[] fractions = {.5,1};
        long[] checkpoints = {1};
        AnytimeRecorder monitor = new AnytimeRecorder(10, 10, fractions, checkpoints);
        fractions[0] = .9; checkpoints[0] = 9;
        fixture.complete(monitor, 1, 5, 9);
        fixture.complete(monitor, 2, 8, 8);
        monitor.completed(3, 9, false, fixture.archive);
        List<Map<String,Object>> rows = monitor.finish();
        fixture.add(1);
        double[][] unrelated = fixture.archive.objectiveSnapshot();
        unrelated[0][0] = -100;
        assertRow(rows.get(0), "TIME", 5, 1, true, 9);
        assertRow(rows.get(1), "TIME", 10, 3, true, 8);
        assertRow(rows.get(2), "FE", 1, 1, true, 9);
    }

    private static void emptyAndInfiniteBudgets() {
        AnytimeRecorder empty = new AnytimeRecorder(0, 10, new double[] {0,.5,1}, new long[] {0,1});
        List<Map<String,Object>> rows = empty.finish();
        for (int i = 0; i < 3; i++) assertRow(rows.get(i), "TIME", new double[] {0,5,10}[i], 0, true, null);
        assertRow(rows.get(3), "FE", 0, 0, true, null);
        assertRow(rows.get(4), "FE", 1, 0, false, null);
        require(new AnytimeRecorder(10, 10, new double[0], new long[0]).finish().isEmpty(), "Empty arrays rejected");

        Fixture fixture = new Fixture();
        AnytimeRecorder unlimited = new AnytimeRecorder(10, Double.POSITIVE_INFINITY, new double[] {.5,1}, new long[] {1});
        fixture.complete(unlimited, 1, 1, 9);
        require(unlimited.finish().size() == 1, "Infinite time generated TIME rows");
        assertRow(unlimited.finish().get(0), "FE", 1, 1, true, 9);
    }

    private static void invalidInputs() {
        for (double[] fractions : new double[][] {{.5,.5}, {1,.5}, {-.1}, {1.1}, {Double.NaN},
                {Double.POSITIVE_INFINITY}, {Double.NEGATIVE_INFINITY}}) {
            rejects(() -> new AnytimeRecorder(10, Double.POSITIVE_INFINITY, fractions, new long[0]));
        }
        for (long[] checkpoints : new long[][] {{-1}, {1,1}, {2,1}}) {
            rejects(() -> new AnytimeRecorder(10, Double.POSITIVE_INFINITY, new double[0], checkpoints));
        }
        rejects(() -> new AnytimeRecorder(-1, 10, new double[0], new long[0]));
        for (double seconds : new double[] {-1, Double.NaN, Double.NEGATIVE_INFINITY}) {
            rejects(() -> new AnytimeRecorder(10, seconds, new double[0], new long[0]));
        }
        rejects(() -> new AnytimeRecorder(10, 0, new double[] {.5,1}, new long[0]));
        rejects(() -> new AnytimeRecorder(10, 10, null, new long[0]));
        rejects(() -> new AnytimeRecorder(10, 10, new double[0], null));
    }

    private static void monitorDoesNotUseRandom() {
        Fixture fixture = new Fixture();
        fixture.add(9);
        SeededRandom.reset(911);
        AnytimeRecorder monitor = new AnytimeRecorder(10, 10, new double[] {.5,1}, new long[] {1,2});
        monitor.completed(1, 5, true, fixture.archive);
        monitor.completed(2, 10, false, fixture.archive);
        monitor.finish();
        require(SeededRandom.current().nextLong() == new Random(911).nextLong(), "Monitor consumed search RNG");
    }

    private static void assertRow(Map<String,Object> row, String kind, double checkpoint,
                                  long fe, boolean reached, Integer objective) {
        require(kind.equals(row.get("checkpointKind")), "Checkpoint kind/order changed");
        require(number(row, "checkpoint") == checkpoint, "Wrong checkpoint");
        require(((Number) row.get("fe")).longValue() == fe, "Future or wrong FE entered snapshot");
        require(Boolean.valueOf(reached).equals(row.get("reached")), "Wrong reached status");
        require(Boolean.valueOf(!reached).equals(row.get("censored")), "Wrong censored status");
        double[][] front = (double[][]) row.get("front");
        if (objective == null) require(front.length == 0, "Unreached FE contains a fabricated front");
        else {
            require(front.length == 1 && front[0].length == 3, "Non-numeric or malformed snapshot");
            for (double value : front[0]) require(value == objective, "Future objective entered snapshot");
        }
    }

    private static double number(Map<String,Object> row, String key) { return ((Number) row.get(key)).doubleValue(); }

    private static void rejects(Runnable action) {
        try { action.run(); } catch (IllegalArgumentException expected) { return; }
        throw new AssertionError("Invalid monitor input accepted");
    }

    private static final class Fixture {
        private final JointCheckProblem raw = new JointCheckProblem(6);
        private final ThreeObjectiveArchive<PermutationSolution<Integer>> archive = new ThreeObjectiveArchive<>();

        private boolean add(int objective) {
            PermutationSolution<Integer> solution = raw.createSolution();
            for (int k = 0; k < 3; k++) solution.setObjective(k, objective);
            return archive.addEvaluated(solution);
        }

        private void complete(AnytimeRecorder monitor, long fe, double seconds, int objective) {
            boolean changed = add(objective);
            monitor.completed(fe, seconds, changed, archive);
        }
    }

    private static void require(boolean ok, String message) { if (!ok) throw new AssertionError(message); }
}
