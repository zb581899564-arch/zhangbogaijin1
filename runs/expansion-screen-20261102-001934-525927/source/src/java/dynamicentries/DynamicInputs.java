package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.uma.jmetal.util.research.model.DynamicParameters;
import org.uma.jmetal.util.research.model.Instance;

/** Explicit worker-indexed numerical input, shared with the Python reference. */
public final class DynamicInputs {
    private DynamicInputs() { }
    public static DynamicParameters fatigue(Instance in, Path path) throws Exception {
        List<String> lines = Files.readAllLines(path, StandardCharsets.UTF_8);
        if (lines.isEmpty() || !lines.get(0).startsWith("# source=")) throw new IllegalArgumentException("Missing fatigue source");
        double[][][][] all = new double[4][in.factories()][in.stages()][];
        boolean[][][] seen = new boolean[in.factories()][in.stages()][];
        int count = 0, expected = 0;
        for (int f = 0; f < in.factories(); f++) for (int k = 0; k < in.stages(); k++) {
            seen[f][k] = new boolean[in.workers(f, k)]; expected += in.workers(f, k);
            for (int q = 0; q < 4; q++) all[q][f][k] = new double[in.workers(f, k)];
        }
        for (String line : lines.subList(1, lines.size())) {
            if (line.trim().isEmpty() || line.startsWith("#")) continue;
            String[] x = line.trim().split("[,\\s]+");
            if (x.length != 7) throw new IllegalArgumentException("Expected f,k,w,alpha,mu,beta,h0");
            int f = Integer.parseInt(x[0]), k = Integer.parseInt(x[1]), w = Integer.parseInt(x[2]);
            if (seen[f][k][w]) throw new IllegalArgumentException("Duplicate fatigue worker");
            seen[f][k][w] = true; count++;
            for (int q = 0; q < 4; q++) all[q][f][k][w] = Double.parseDouble(x[q + 3]);
        }
        if (count != expected) throw new IllegalArgumentException("Missing fatigue workers");
        return new DynamicParameters(all[0], all[1], all[2], all[3], lines.get(0).substring(9));
    }
}
