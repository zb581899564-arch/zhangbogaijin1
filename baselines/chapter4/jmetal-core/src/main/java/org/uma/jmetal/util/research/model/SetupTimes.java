package org.uma.jmetal.util.research.model;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/** Setup is independent input, with mandatory origin; never inferred from processing time. */
public final class SetupTimes implements java.io.Serializable {
    private static final long serialVersionUID = 1L;
    private final double[][] values;
    private final String provenance;
    public SetupTimes(double[][] values, String provenance) {
        if (provenance == null || provenance.trim().isEmpty()) throw new IllegalArgumentException("Missing setup source");
        this.values = new double[values.length][];
        for (int i = 0; i < values.length; i++) this.values[i] = values[i].clone();
        this.provenance = provenance;
    }
    public static SetupTimes generatedSupplement(int jobs, int stages, long seed) {
        Random random = new Random(seed);
        double[][] values = new double[jobs][stages];
        for (int j = 0; j < jobs; j++) for (int k = 0; k < stages; k++) values[j][k] = 1 + random.nextInt(9);
        return new SetupTimes(values, "RECONSTRUCTED-NOT-AUTHOR-DATA; discrete U[1,9]; java.util.Random seed=" + seed);
    }
    public static SetupTimes fromFile(Path path, int jobs, int stages) throws IOException {
        List<String> lines = Files.readAllLines(path, StandardCharsets.UTF_8);
        if (lines.isEmpty() || !lines.get(0).startsWith("# source=")) {
            throw new IOException("Setup file requires first line # source=<origin>: " + path);
        }
        if (lines.get(0).substring(9).trim().isEmpty()) throw new IOException("Empty setup source: " + path);
        List<double[]> rows = new ArrayList<double[]>();
        for (int i = 1; i < lines.size(); i++) {
            String line = lines.get(i).trim();
            if (line.isEmpty() || line.startsWith("#")) continue;
            String[] tokens = line.split("[,\\s]+");
            if (tokens.length != stages) throw new IOException("Wrong setup stage count at line " + (i + 1));
            double[] row = new double[stages];
            for (int k = 0; k < stages; k++) row[k] = Double.parseDouble(tokens[k]);
            rows.add(row);
        }
        if (rows.size() != jobs) throw new IOException("Wrong setup job count: " + path);
        return new SetupTimes(rows.toArray(new double[rows.size()][]), lines.get(0).substring(9) + "; file=" + path);
    }
    public void write(Path path) throws IOException {
        List<String> lines = new ArrayList<String>();
        lines.add("# source=" + provenance);
        for (double[] row : values) {
            StringBuilder line = new StringBuilder();
            for (double value : row) { if (line.length() > 0) line.append(','); line.append(value); }
            lines.add(line.toString());
        }
        Files.write(path, lines, StandardCharsets.UTF_8, java.nio.file.StandardOpenOption.CREATE_NEW);
    }
    public String provenance() { return provenance; }
    double[][] values() {
        double[][] result = new double[values.length][];
        for (int i = 0; i < values.length; i++) result[i] = values[i].clone();
        return result;
    }
}
