package org.uma.jmetal.util.research.search;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;

/** Numeric checks use independent Python HV expectations, not duplicated Java code. */
public final class ProgramExitMetricChecks {
    private ProgramExitMetricChecks() { }
    public static void main(String[] args) throws Exception {
        long checked = 0;double worst = 0;
        for (String line : Files.readAllLines(Paths.get(args[0]), StandardCharsets.UTF_8)) {
            String[] fields = line.split("\t");double reference = Double.parseDouble(fields[0]);
            double expected = Double.parseDouble(fields[1]);
            double[][] points = Arrays.stream(fields[2].split(";")).map(row ->
                Arrays.stream(row.split(",")).mapToDouble(Double::parseDouble).toArray()).toArray(double[][]::new);
            double actual = ProgramExitHv3D.volume(points, reference);
            double filtered = ProgramExitHv3D.volume(ProgramExitHv3D.nondominated(points), reference);
            worst = Math.max(worst, Math.max(Math.abs(actual - expected), Math.abs(filtered - expected)));
            if (Math.abs(actual - expected) > 1e-11 || Math.abs(filtered - expected) > 1e-11)
                throw new AssertionError("Independent 3D HV differs at fixture " + checked);
            checked++;
        }
        System.out.println("PROGRAM_EXIT_HV_NUMERIC_PASS fixtures=" + checked + " worst=" + worst + " searchFE=0 decoderCalls=0");
    }
}
