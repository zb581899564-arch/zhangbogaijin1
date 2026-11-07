package org.uma.jmetal.util.research.model;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/** Loads supplied 45-instance text format; records values absent from that format. */
public final class InstanceLoader {
    private InstanceLoader() { }
    public static Instance loadChapter3(Path path, double standbyPower) throws IOException {
        return load(path, ModelKind.CHAPTER3_FIXED_WORKER, null, standbyPower);
    }
    public static Instance loadChapter4(Path path, SetupTimes setup, double standbyPower) throws IOException {
        if (setup == null) throw new IllegalArgumentException("Author benchmark SUT is absent; supply sourced SetupTimes");
        return load(path, ModelKind.CHAPTER4_DUAL_RESOURCE, setup, standbyPower);
    }
    private static Instance load(Path path, ModelKind kind, SetupTimes setup, double standbyPower) throws IOException {
        List<String> lines = Files.readAllLines(path, StandardCharsets.UTF_8);
        String[] header = lines.get(0).trim().split("\\s+");
        if (header.length != 3) throw new IOException("Bad instance header: " + path);
        int factories = Integer.parseInt(header[0]), stages = Integer.parseInt(header[1]), jobs = Integer.parseInt(header[2]);
        NumericRows rows = new NumericRows(lines.subList(1, lines.size()));
        int[][] machines = new int[factories][stages];
        for (int f = 0; f < factories; f++) machines[f] = rows.nextInts(stages);
        double[][][] speed = readMachines(rows, machines), power = readMachines(rows, machines);
        double[][] processing = new double[jobs][stages];
        for (int j = 0; j < jobs; j++) processing[j] = rows.next(stages);
        int[] totals = rows.nextInts(factories);
        double[][] levels = new double[factories][], costs = new double[factories][];
        for (int f = 0; f < factories; f++) levels[f] = rows.next(totals[f]);
        for (int f = 0; f < factories; f++) costs[f] = rows.next(totals[f]);
        int duplicateBlocks = consumeTrailingWorkerBlocks(rows, totals);
        double[][][] efficiencies = new double[factories][stages][], rates = new double[factories][stages][];
        double[][][] standby = new double[factories][stages][];
        for (int f = 0; f < factories; f++) {
            int offset = 0;
            for (int k = 0; k < stages; k++) {
                standby[f][k] = filled(machines[f][k], standbyPower);
                if (kind == ModelKind.CHAPTER3_FIXED_WORKER) {
                    efficiencies[f][k] = levels[f].clone(); rates[f][k] = costs[f].clone();
                    offset += machines[f][k];
                } else {
                    int count = machines[f][k] > 2 ? machines[f][k] - 1 : machines[f][k];
                    if (offset + count > totals[f]) throw new IOException("Worker pool exceeds supplied total: " + path);
                    efficiencies[f][k] = slice(levels[f], offset, count);
                    rates[f][k] = slice(costs[f], offset, count); offset += count;
                }
            }
            if (offset != totals[f]) throw new IOException("Worker total inconsistent with stage partition: " + path);
        }
        String origin = "benchmark=" + path.toAbsolutePath().normalize()
                + "; standbyPower=" + standbyPower + " (EXPLICIT RECONSTRUCTION ASSUMPTION, absent from instance)";
        if (duplicateBlocks > 0) origin += "; first worker block selected as in original loader; ignored validated trailing worker blocks=" + duplicateBlocks;
        if (kind == ModelKind.CHAPTER4_DUAL_RESOURCE) origin += "; " + setup.provenance()
                + "; stage worker counts: thesis sec4.3, M=2 completed by supplied source code";
        double[][] sut = setup == null ? new double[jobs][stages] : setup.values();
        return new Instance(path.getFileName().toString(), kind, processing, sut, speed, power,
                standby, efficiencies, rates, origin);
    }
    private static double[][][] readMachines(NumericRows rows, int[][] counts) throws IOException {
        double[][][] result = new double[counts.length][][];
        for (int f = 0; f < counts.length; f++) {
            result[f] = new double[counts[f].length][];
            for (int k = 0; k < counts[f].length; k++) result[f][k] = rows.next(counts[f][k]);
        }
        return result;
    }
    private static int consumeTrailingWorkerBlocks(NumericRows rows, int[] counts) throws IOException {
        int blocks = 0;
        while (rows.hasNext()) {
            int[] repeated = rows.nextInts(counts.length);
            if (!java.util.Arrays.equals(repeated, counts)) throw new IOException("Unexpected trailing numeric data");
            for (int count : counts) rows.next(count);
            for (int count : counts) rows.next(count);
            blocks++;
        }
        return blocks;
    }
    private static double[] filled(int count, double value) {
        double[] result = new double[count]; java.util.Arrays.fill(result, value); return result;
    }
    private static double[] slice(double[] values, int start, int count) {
        return java.util.Arrays.copyOfRange(values, start, start + count);
    }
    private static final class NumericRows {
        private final List<String> rows = new ArrayList<String>(); private int cursor;
        NumericRows(List<String> lines) {
            for (String line : lines) if (line.trim().matches("[-+0-9.eE,\\s]+")) rows.add(line.trim());
        }
        boolean hasNext() { return cursor < rows.size(); }
        double[] next(int length) throws IOException {
            if (!hasNext()) throw new IOException("Missing numeric row");
            String[] tokens = rows.get(cursor++).split("[,\\s]+");
            if (tokens.length != length) throw new IOException("Numeric row " + cursor + " has " + tokens.length + ", expected " + length);
            double[] values = new double[length];
            for (int i = 0; i < length; i++) values[i] = Double.parseDouble(tokens[i]);
            return values;
        }
        int[] nextInts(int length) throws IOException {
            double[] values = next(length); int[] result = new int[length];
            for (int i = 0; i < length; i++) {
                if (values[i] != Math.rint(values[i]) || values[i] <= 0) throw new IOException("Invalid count");
                result[i] = (int) values[i];
            }
            return result;
        }
    }
}
