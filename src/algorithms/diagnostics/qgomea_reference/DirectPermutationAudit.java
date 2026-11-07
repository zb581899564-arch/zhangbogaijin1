package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.util.research.modelglobal.DirectPositionMixing;

/** Compare new independent Java integer operators to unmodified author-generated fixtures. */
public final class DirectPermutationAudit {
    private static int[] parse(String field) {
        int[] values = ProbeData.integers(field);
        for (int i = 0; i < values.length; i++) values[i]--;
        return values;
    }
    private static void same(int[] actual, String expected) {
        if (!Arrays.equals(actual, parse(expected))) throw new AssertionError("Native output mismatch");
    }
    public static void main(String[] args) throws Exception {
        List<String> cases = Files.readAllLines(Paths.get(args[0]), StandardCharsets.UTF_8);
        List<String> results = Files.readAllLines(Paths.get(args[1]), StandardCharsets.UTF_8);
        if (cases.size() != results.size()) throw new AssertionError("Missing native fixture");
        for (int i = 0; i < cases.size(); i++) {
            String[] input = cases.get(i).split("\t"), output = results.get(i).split("\t");
            if (!input[0].equals(output[0])) throw new AssertionError("Case identity");
            int[] parent = parse(input[1]), donor = parse(input[2]), mask = parse(input[3]);
            int reference = Integer.parseInt(input[4]) - 1;
            int[] position = DirectPositionMixing.position(parent, donor, mask, reference);
            same(position, output[3]); same(DirectPositionMixing.order(parent, donor, mask), output[4]);
            same(DirectPositionMixing.order(position, donor, mask), output[5]);
            same(DirectPositionMixing.inverse(parent), output[6]);
            same(parent, input[1]); same(donor, input[2]); same(mask, input[3]);
        }
        NeutralProbeSupport.append(Paths.get(args[2]), NeutralProbeSupport.row("status", "passed", "cases", cases.size(),
            "nativeOutputComparisons", cases.size()*4, "inputArraysUnchanged", true, "newDynamicSearchFE", 0, "dynamicDecoderCalls", 0));
    }
}
