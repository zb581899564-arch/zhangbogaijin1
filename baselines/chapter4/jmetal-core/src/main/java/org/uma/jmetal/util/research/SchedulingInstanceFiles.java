package org.uma.jmetal.util.research;

import java.io.BufferedReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

/** Resolves local instances and rejects mismatched dimensions before decoding. */
public final class SchedulingInstanceFiles {
    private SchedulingInstanceFiles() { }

    public static String resolve(int jobs, int stages, int factories, int instanceId) throws IOException {
        String directory = System.getProperty("dhfsp.dataDir");
        if (directory == null || directory.trim().isEmpty()) {
            throw new IllegalArgumentException("Specify -Ddhfsp.dataDir=<chapter instance directory>");
        }
        Path file = Paths.get(directory, jobs + "_" + stages + "_" + factories + "_" + instanceId + ".txt")
                .toAbsolutePath().normalize();
        try (BufferedReader reader = Files.newBufferedReader(file, StandardCharsets.UTF_8)) {
            String header = reader.readLine();
            String[] dimensions = header == null ? new String[0] : header.trim().split("\\s+");
            if (dimensions.length != 3 || Integer.parseInt(dimensions[0]) != factories
                    || Integer.parseInt(dimensions[1]) != stages || Integer.parseInt(dimensions[2]) != jobs) {
                throw new IOException("Instance dimensions do not match requested problem: " + file);
            }
        }
        return file.toString();
    }

    public static String forProblem(Object problem) {
        if (!(problem instanceof InstanceFileProvider)) {
            throw new IllegalArgumentException("Scheduling solution requires an InstanceFileProvider problem: "
                    + problem.getClass().getName());
        }
        return ((InstanceFileProvider) problem).getInstanceFile();
    }
}
