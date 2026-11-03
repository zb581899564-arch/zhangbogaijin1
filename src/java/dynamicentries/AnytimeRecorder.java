package research.dynamic;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.util.research.runtime.*;

/** Captures the last completed archive at each deadline, never the next future evaluation. */
public final class AnytimeRecorder implements EvaluationObserver {
    private final List<Checkpoint> timePoints = new ArrayList<>();
    private final List<Checkpoint> fePoints = new ArrayList<>();
    private final boolean exactFE;
    private final double timeLimit;
    private int nextTime;
    private int nextFE;
    private double[][] last = new double[0][3];
    private double lastSeconds;
    private long lastFE;
    private List<Map<String, Object>> finished;

    /** Retains the original single-budget 25/50/100 percent checkpoints. */
    public AnytimeRecorder(long fe, double seconds) {
        exactFE = false;
        timeLimit = seconds;
        List<Checkpoint> points = Double.isFinite(seconds) ? timePoints : fePoints;
        double limit = Double.isFinite(seconds) ? seconds : fe;
        for (double fraction : new double[] {.25, .5, 1}) {
            points.add(new Checkpoint(Double.valueOf(limit * fraction)));
        }
    }

    /** Records TIME fractions and absolute successful-FE checkpoints in the same run. */
    public AnytimeRecorder(long fe, double seconds, double[] timeFractions, long[] feCheckpoints) {
        validate(fe, seconds, timeFractions, feCheckpoints);
        exactFE = true;
        timeLimit = seconds;
        if (Double.isFinite(seconds)) {
            double previous = -1;
            for (double fraction : timeFractions) {
                double deadline = seconds * fraction;
                if (!Double.isFinite(deadline) || deadline <= previous) {
                    throw new IllegalArgumentException("TIME deadlines must be finite and strictly increasing");
                }
                timePoints.add(new Checkpoint(Double.valueOf(deadline)));
                previous = deadline;
            }
        }
        for (long checkpoint : feCheckpoints) fePoints.add(new Checkpoint(Long.valueOf(checkpoint)));
    }

    @Override public void completed(long fe, double seconds, boolean changed, ThreeObjectiveArchive<?> archive) {
        if (finished != null) throw new IllegalStateException("Recorder has finished");
        // A completion beyond a deadline must close that deadline before admitting its archive.
        while (nextTime < timePoints.size() && seconds > timePoints.get(nextTime).value.doubleValue()) {
            timePoints.get(nextTime++).capture("TIME", lastFE, lastSeconds, last, true);
        }
        advancePastFE(fe);
        // Archive admission itself can cross T after the evaluator's final clock checkpoint.
        boolean withinTime = !exactFE || seconds <= timeLimit;
        if (changed && withinTime) last = archive.objectiveSnapshot();
        lastFE = fe; lastSeconds = seconds;
        while (nextTime < timePoints.size() && seconds == timePoints.get(nextTime).value.doubleValue()) {
            timePoints.get(nextTime++).capture("TIME", lastFE, lastSeconds, last, true);
        }
        while (nextFE < fePoints.size() && fePoints.get(nextFE).compareFE(fe) == 0) {
            Checkpoint point = fePoints.get(nextFE++);
            if (withinTime) point.capture("FE", lastFE, lastSeconds, last, true);
        }
    }

    /** TIME rows precede FE rows; both groups retain ascending checkpoint order. */
    public List<Map<String, Object>> finish() {
        if (finished != null) return finished;
        for (Checkpoint point : timePoints) {
            if (point.row == null) point.capture("TIME", lastFE, lastSeconds, last, true);
        }
        for (Checkpoint point : fePoints) {
            if (point.row != null) continue;
            if (!exactFE) point.capture("FE", lastFE, lastSeconds, last, true);
            else if (point.value.longValue() == 0) point.capture("FE", 0, 0, new double[0][3], true);
            else point.capture("FE", lastFE, lastSeconds, new double[0][3], false);
        }
        List<Map<String, Object>> rows = new ArrayList<>(timePoints.size() + fePoints.size());
        for (Checkpoint point : timePoints) rows.add(point.row);
        for (Checkpoint point : fePoints) rows.add(point.row);
        finished = Collections.unmodifiableList(rows);
        return finished;
    }

    private void advancePastFE(long fe) {
        while (nextFE < fePoints.size() && fePoints.get(nextFE).compareFE(fe) > 0) {
            Checkpoint point = fePoints.get(nextFE++);
            if (!exactFE) point.capture("FE", lastFE, lastSeconds, last, true);
            else if (point.value.longValue() == 0) point.capture("FE", 0, 0, new double[0][3], true);
            // A skipped exact FE is censored at finish, never filled with a later archive.
        }
    }

    private static void validate(long fe, double seconds, double[] fractions, long[] checkpoints) {
        if (fe < 0 || Double.isNaN(seconds) || seconds < 0) {
            throw new IllegalArgumentException("Nonnegative FE and time limits required");
        }
        if (fractions == null || checkpoints == null) throw new IllegalArgumentException("Checkpoint arrays required");
        double previousFraction = -1;
        for (double fraction : fractions) {
            if (!Double.isFinite(fraction) || fraction < 0 || fraction > 1 || fraction <= previousFraction) {
                throw new IllegalArgumentException("TIME fractions must be finite, in [0,1], and strictly increasing");
            }
            previousFraction = fraction;
        }
        long previousFE = -1;
        for (long checkpoint : checkpoints) {
            if (checkpoint < 0 || checkpoint <= previousFE) {
                throw new IllegalArgumentException("FE checkpoints must be nonnegative and strictly increasing");
            }
            previousFE = checkpoint;
        }
    }

    private static final class Checkpoint {
        private final Number value;
        private Map<String, Object> row;

        private Checkpoint(Number value) { this.value = value; }

        private int compareFE(long fe) {
            return value instanceof Long ? Long.compare(fe, value.longValue()) : Double.compare(fe, value.doubleValue());
        }

        private void capture(String kind, long fe, double seconds, double[][] front, boolean reached) {
            Map<String, Object> values = new LinkedHashMap<>();
            values.put("checkpointKind", kind); values.put("checkpoint", value);
            values.put("elapsedSeconds", seconds); values.put("fe", fe); values.put("front", front);
            values.put("reached", reached); values.put("censored", !reached);
            row = Collections.unmodifiableMap(values);
        }
    }
}
