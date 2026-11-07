package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.*;

/** Import, exact physical QA, and append-only output for the isolated neutral-view probe. */
final class NeutralProbeSupport {
    private NeutralProbeSupport() { }

    static Map<String,Object> row(Object... fields) {
        Map<String,Object> out = new LinkedHashMap<>();
        for (int i = 0; i < fields.length; i += 2) out.put((String) fields[i], fields[i + 1]);
        return out;
    }

    static void append(Path path, Map<String,Object> row) {
        try {
            Files.write(path, Collections.singletonList(DynamicJson.encode(row)), StandardCharsets.UTF_8,
                    StandardOpenOption.CREATE, StandardOpenOption.APPEND);
        } catch (java.io.IOException e) { throw new java.io.UncheckedIOException(e); }
    }

    static DynamicSchedule full(Instance in, DynamicParameters params, PermutationSolution<Integer> value) {
        DynamicSchedule result = DynamicDecoder.full(in, params,
                SchedulingEncoding.integers(value.getVariables()),
                SchedulingEncoding.integers(value.getVariablesid()), SchedulingEncoding.machineIntegers(value),
                SchedulingEncoding.integers(value.getVariablesworker()), null);
        DynamicValidator.validate(in, params, result);
        return result;
    }

    static void sameTimeline(DynamicSchedule a, DynamicSchedule b) {
        if (!Arrays.equals(a.objectives(), b.objectives()) || a.steps().size() != b.steps().size())
            throw new AssertionError("Neutral-view objectives differ");
        for (int i = 0; i < a.steps().size(); i++) {
            DynamicStep x = a.steps().get(i), y = b.steps().get(i);
            if (x.job()!=y.job() || x.factory()!=y.factory() || x.stage()!=y.stage()
                    || x.machine()!=y.machine() || x.worker()!=y.worker() || !Arrays.equals(values(x), values(y)))
                throw new AssertionError("Neutral-view physical timeline differs");
        }
    }

    private static double[] values(DynamicStep x) {
        return new double[]{x.start(),x.base(),x.duration(),x.setupDuration(),x.completion(),
                x.u(),x.v(),x.energy(),x.labor(),x.exposure()};
    }

    static long mixed(long value) {
        value = (value ^ (value >>> 30)) * 0xbf58476d1ce4e5b9L;
        value = (value ^ (value >>> 27)) * 0x94d049bb133111ebL;
        return value ^ (value >>> 31);
    }
}
