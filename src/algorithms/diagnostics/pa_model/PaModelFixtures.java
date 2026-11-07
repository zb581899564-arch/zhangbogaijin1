package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.util.research.modelglobal.*;

/** Small mathematical fixtures are independent of dynamic scheduling and never become search candidates. */
final class PaModelFixtures {
    private PaModelFixtures() { }

    static void write(Path out) throws Exception {
        List<String> lines = new ArrayList<>();
        for (int p : new int[]{1, 2, 5, 15, 55, 80, 100, 400, 1000}) for (int factories = 2; factories <= 5; factories++) {
            BinomialAttraction model = new BinomialAttraction(p, factories);
            for (int x = 0; x <= p; x++) lines.add(p + "\t" + factories + "\t" + x + "\t" + model.value(x));
        }
        Files.write(out.resolve("binomial.tsv"), lines, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        double[][] keys = {{.1, .3}, {.1, .3}};
        PaDependencyModel one = new PaDependencyModel(new int[][]{{0, 0}, {0, 0}}, keys, 1);
        PaDependencyModel repulsion = new PaDependencyModel(new int[][]{{0, 1}, {1, 0}}, keys, 2);
        if (Math.abs(one.components(0, 1)[0] - .96) > 1e-12 || Math.abs(repulsion.components(0, 1)[0] - 2.0 / 3) > 1e-12)
            throw new AssertionError("Degenerate dependency fixture differs");
        List<int[]> zero = new LinkageHierarchy(new double[4][4]).subsets();
        int[][] expected = {{0}, {1}, {2}, {3}, {0, 1}, {0, 1, 2}, {0, 1, 2, 3}};
        for (int i = 0; i < expected.length; i++) if (!Arrays.equals(zero.get(i), expected[i])) throw new AssertionError("Hierarchy tie order differs");
        NeutralProbeSupport.append(out.resolve("fixtures.jsonl"), NeutralProbeSupport.row("singleFactory", one.components(0, 1),
                "repulsion", repulsion.components(0, 1), "zeroMatrixHierarchy", zero, "binomialValues", lines.size()));
    }
}
