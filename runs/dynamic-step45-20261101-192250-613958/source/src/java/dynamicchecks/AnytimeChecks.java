package org.uma.jmetal.util.research.runtime;

import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.joint.JointCheckProblem;
import research.dynamic.AnytimeRecorder;

/** Deterministic timestamps test exclusion of the next evaluation after every time boundary. */
public final class AnytimeChecks {
    private AnytimeChecks() { }
    public static void main(String[] args) {
        SeededRandom.reset(713);
        JointCheckProblem raw = new JointCheckProblem(6);
        ThreeObjectiveArchive<PermutationSolution<Integer>> archive = new ThreeObjectiveArchive<>();
        AnytimeRecorder time = new AnytimeRecorder(100, 10);
        AnytimeRecorder fe = new AnytimeRecorder(4, Double.POSITIVE_INFINITY);
        double[] seconds = {1,3,6,11};
        for (int i = 0; i < 4; i++) {
            PermutationSolution<Integer> s = raw.createSolution();
            for (int k = 0; k < 3; k++) s.setObjective(k, 4-i);
            boolean changed = archive.addEvaluated(s);
            time.completed(i+1, seconds[i], changed, archive); fe.completed(i+1, seconds[i], changed, archive);
        }
        List<Map<String,Object>> t = time.finish(), f = fe.finish();
        for (int i = 0; i < 3; i++) {
            require(((Number) t.get(i).get("fe")).intValue() == i+1, "Future FE entered TIME snapshot");
            double[][] front = (double[][]) t.get(i).get("front");
            require(front[0][0] == 4-i, "Future objective entered TIME snapshot");
        }
        require(((Number) f.get(2).get("fe")).intValue() == 4, "Last acquired FE missing");
        require(((double[][]) f.get(2).get("front"))[0][0] == 1, "Final FE result omitted");
        System.out.println("ANYTIME_CHECKS_PASS no future archive; exact FE endpoints; time boundary exclusion");
    }
    private static void require(boolean ok, String message) { if (!ok) throw new AssertionError(message); }
}
