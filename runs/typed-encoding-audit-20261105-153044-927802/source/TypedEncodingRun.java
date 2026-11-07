package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Random;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.modelglobal.*;

/** Offline replay of known paid genomes only. No RunContext, objective call, archive or search. */
public final class TypedEncodingRun {
    private final TypedEncodingChecks checks = new TypedEncodingChecks();
    private final Instance instance;
    private final DynamicParameters fatigue;
    private final FirstStageCatalog catalog;
    private long decoderCalls, sources, timelinePairs;

    private TypedEncodingRun(Instance value, DynamicParameters parameters) {
        instance = value; fatigue = parameters; catalog = new FirstStageCatalog(value); checks.catalog(catalog);
    }

    private DynamicSchedule full(FourVectors value) {
        decoderCalls++;
        DynamicSchedule result = DynamicDecoder.full(instance, fatigue, value.jobs(), value.factories(),
                value.machines(), value.workers(), null);
        DynamicValidator.validate(instance, fatigue, result); return result;
    }

    private void replay(Path source, Path out, long seed) throws Exception {
        Random noise = new Random(seed);
        for (String line : Files.readAllLines(source, StandardCharsets.UTF_8)) {
            String[] fields = line.split("\t");
            FourVectors input = new FourVectors(ProbeData.integers(fields[4]), ProbeData.integers(fields[5]),
                    ProbeData.integers(fields[6]), ProbeData.integers(fields[7]));
            TypedScheduleGenome genome = checks.source(catalog, input, noise);
            FourVectors roundtrip = genome.toVectors();
            DynamicSchedule original = full(input), decoded = full(roundtrip);
            String[] expected = fields[3].split(",");
            for (int k = 0; k < 3; k++)
                if (Double.doubleToLongBits(original.objectives()[k])
                        != Double.doubleToLongBits(Double.parseDouble(expected[k])))
                    throw new AssertionError("Captured source objective differs");
            NeutralProbeSupport.sameTimeline(original, decoded); timelinePairs++; sources++;
            NeutralProbeSupport.append(out.resolve("source-checks.jsonl"), NeutralProbeSupport.row(
                "sourceIndex", Integer.parseInt(fields[0]), "role", fields[1], "family", Integer.parseInt(fields[2]),
                "objectives", original.objectives(), "rawFourVectorsEqual", true, "allTimelineFieldsEqual", true,
                "categoricalResourcesByJob", genome.allocations(), "globalKeysByJob", genome.priorities()));
        }
        if (sources != 100 || decoderCalls != 200 || timelinePairs != 100 || checks.rejected != 1300)
            throw new AssertionError("Wrong source or QA count");
    }

    public static void main(String[] args) throws Exception {
        Path input = Paths.get(args[0]), out = Paths.get(args[4]); Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir", input.getParent().toString());
        System.setProperty("dhfsp.setupFile", args[1]); System.setProperty("dhfsp.standbyPower", "1");
        String[] parts = input.getFileName().toString().replace(".txt", "").split("_");
        EDHHFSPW raw = new EDHHFSPW(Integer.parseInt(parts[0]), Integer.parseInt(parts[1]),
                Integer.parseInt(parts[2]), Integer.parseInt(parts[3]));
        Instance instance = raw.getSchedulingInstance();
        TypedEncodingRun audit = new TypedEncodingRun(instance, DynamicInputs.fatigue(instance, Paths.get(args[2])));
        boolean complete = false;
        try {
            NeutralProbeSupport.append(out.resolve("loaded-identity.jsonl"), ClassResolutionProbe.capture(
                "research.dynamic.TypedEncodingRun", "org.uma.jmetal.util.research.modelglobal.TypedScheduleGenome",
                "org.uma.jmetal.util.research.modelglobal.FirstStageCatalog", "org.uma.jmetal.util.research.model.DynamicDecoder",
                "org.uma.jmetal.util.research.model.DynamicValidator"));
            audit.replay(Paths.get(args[3]), out, Long.parseLong(args[5])); complete = true;
        } finally {
            NeutralProbeSupport.append(out.resolve("receipt.jsonl"), NeutralProbeSupport.row(
                "status", complete ? "COMPLETE" : "INCOMPLETE_RETAINED", "optimizationFE", 0,
                "decoderCalls", audit.decoderCalls, "sourceGenomes", audit.sources,
                "exactTimelinePairs", audit.timelinePairs, "pureChecks", audit.checks.checks,
                "expectedMalformedRejections", audit.checks.rejected, "categoricalDomainSize", audit.catalog.size(),
                "jobs", instance.jobs(), "stages", instance.stages(), "factories", instance.factories(),
                "defaultMainlineChanged", false, "goalAchieved", false));
        }
    }
}
