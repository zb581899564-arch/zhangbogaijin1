package research.dynamic;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.Instance;

/** Strict numeric TSV interchange; original case metadata remains in the captured JSONL. */
final class ProbeData {
    private ProbeData() { }
    static int[] integers(String value) {
        if (value.equals("-")) return null;
        String[] pieces = value.split(","); int[] out = new int[pieces.length];
        for (int i = 0; i < out.length; i++) out[i] = Integer.parseInt(pieces[i]);
        return out;
    }
    static void fill(PermutationSolution<Integer> s, String[] fields, int offset, int family, int[] fixed) {
        int[][] vectors = new int[4][];
        for (int k = 0; k < 4; k++) vectors[k] = integers(fields[offset + k]);
        for (int i = 0; i < s.getNumberOfVariables(); i++) {
            s.setVariableValue(i, vectors[0][i]); s.setVariableValueid(i, vectors[1][i]);
            machines(s).set(i, vectors[2][i]); s.setVariableValueworker(i, vectors[3][i]);
        }
        if (family >= 0) { s.setAttribute("cooperation.family", family); s.setAttribute("cooperation.fixedFactoryByJob", fixed.clone()); }
    }
    static void expected(PermutationSolution<Integer> s, String text) {
        String[] values = text.split(",");
        for (int k = 0; k < 3; k++) if (Double.doubleToLongBits(s.getObjective(k)) != Double.doubleToLongBits(Double.parseDouble(values[k])))
            throw new AssertionError("Captured parent replay differs at objective " + k);
    }
    static int restore(PermutationSolution<Integer> s, Instance in, int[] fixed) {
        if (fixed == null) return 0;
        int edits = 0;
        for (int i = 0; i < in.jobs(); i++) {
            int f = fixed[s.getVariableValue(i)], m = Math.floorMod(machines(s).get(i), in.machines(f, 0));
            int w = Math.floorMod(s.getVariableValueworker(i), in.workers(f, 0));
            if (s.getVariableValueid(i) != f) edits++;
            if (machines(s).get(i) != m) edits++;
            if (s.getVariableValueworker(i) != w) edits++;
            s.setVariableValueid(i, f); machines(s).set(i, m); s.setVariableValueworker(i, w);
        }
        return edits;
    }
    static String key(PermutationSolution<Integer> s) {
        return s.getVariables() + "|" + s.getVariablesid() + "|" + machines(s) + "|" + s.getVariablesworker() + "|" + Arrays.toString(s.getObjectives());
    }
    static Map<String, Object> encoding(PermutationSolution<Integer> s) {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("JS", new ArrayList<>(s.getVariables())); out.put("FA", new ArrayList<>(s.getVariablesid()));
        out.put("MA", new ArrayList<>(machines(s))); out.put("WA", new ArrayList<>(s.getVariablesworker()));
        out.put("objectives", s.getObjectives().clone()); return out;
    }
    static Map<String, Object> changes(PermutationSolution<Integer> p, PermutationSolution<Integer> c) {
        int n = p.getNumberOfVariables(), sequence = 0;
        int[][] a = byJob(p), b = byJob(c); int[] counts = new int[3];
        for (int i = 0; i < n; i++) {
            if (!p.getVariableValue(i).equals(c.getVariableValue(i))) sequence++;
            for (int k = 0; k < 3; k++) if (a[i][k] != b[i][k]) counts[k]++;
        }
        Map<String, Object> out = new LinkedHashMap<>(); out.put("JS", sequence);
        out.put("FA", counts[0]); out.put("MA", counts[1]); out.put("WA", counts[2]); return out;
    }
    private static int[][] byJob(PermutationSolution<Integer> s) {
        int[][] out = new int[s.getNumberOfVariables()][3];
        for (int i = 0; i < out.length; i++) { int j = s.getVariableValue(i); out[j][0] = s.getVariableValueid(i); out[j][1] = machines(s).get(i); out[j][2] = s.getVariableValueworker(i); }
        return out;
    }
    @SuppressWarnings("unchecked")
    private static List<Integer> machines(PermutationSolution<Integer> s) { return (List<Integer>) s.getAttribute("machine"); }
}
