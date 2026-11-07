package research.dynamic;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.search.GomRunScope;

/** Engineering-only append log and independent timeline checks; never feeds decisions back. */
final class GomEngineeringEvidence implements GomRunScope.Evidence, AutoCloseable {
    private final BufferedWriter writer;
    private final PaRunChecks checks;
    GomEngineeringEvidence(Path out, PaRunChecks validation) throws IOException {
        checks = validation; writer = Files.newBufferedWriter(out.resolve("gom-events.jsonl"), StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
    }
    public void record(Map<String,Object> event) {
        try { writer.write(DynamicJson.encode(event)); writer.newLine(); }
        catch (IOException error) { throw new UncheckedIOException(error); }
    }
    public void view(PermutationSolution<Integer> before, PermutationSolution<Integer> after) { checks.neutral(before, after); }
    public void close() throws IOException { writer.close(); }
}
