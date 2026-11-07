package research.dynamic;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.util.research.runtime.*;

/** Captures the last completed archive at each deadline, never the next future evaluation. */
public final class AnytimeRecorder implements EvaluationObserver {
    private final String kind;
    private final double[] checkpoints;
    private int next;
    private double[][] last = new double[0][3];
    private double lastSeconds;
    private long lastFE;
    private final List<Map<String, Object>> rows = new ArrayList<>();

    public AnytimeRecorder(long fe, double seconds) {
        kind = Double.isFinite(seconds) ? "TIME" : "FE";
        double limit = Double.isFinite(seconds) ? seconds : fe;
        checkpoints = new double[] {limit * .25, limit * .5, limit};
    }
    @Override public void completed(long fe, double seconds, boolean changed, ThreeObjectiveArchive<?> archive) {
        double progress = kind.equals("TIME") ? seconds : fe;
        while (next < checkpoints.length && progress > checkpoints[next]) capture();
        if (changed) last = archive.objectiveSnapshot();
        lastFE = fe; lastSeconds = seconds;
        while (next < checkpoints.length && progress == checkpoints[next]) capture();
    }
    public List<Map<String, Object>> finish() {
        while (next < checkpoints.length) capture();
        return rows;
    }
    private void capture() {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("checkpointKind", kind); row.put("checkpoint", checkpoints[next++]);
        row.put("elapsedSeconds", lastSeconds); row.put("fe", lastFE); row.put("front", last);
        rows.add(row);
    }
}
