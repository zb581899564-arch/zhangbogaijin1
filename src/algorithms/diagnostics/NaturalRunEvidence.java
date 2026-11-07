package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.util.research.runtime.ThreeObjectiveArchive;

/** Boundary evidence only; no candidate decisions or default search changes. */
public final class NaturalRunEvidence {
    private static final long[] CHECKS={1,2,100,5100,15000,50000,100000,250000,500000};
    private final long failAfter=Long.getLong("research.natural.failAfterFE",-1L);
    private ThreeObjectiveArchive<?> archive;private long paid;

    public static long[] checkpoints(long limit) {
        if(limit<0)throw new IllegalArgumentException("Negative FE limit");
        SortedSet<Long> values=new TreeSet<>();for(long value:CHECKS)if(value<=limit)values.add(value);values.add(limit);
        long[] result=new long[values.size()];int p=0;for(long value:values)result[p++]=value;return result;
    }
    public void observed(ThreeObjectiveArchive<?> value,long fe) {archive=value;paid=fe;}
    public void maybeInject(long fe) {
        if(fe==failAfter)throw new IllegalStateException("NATURAL_FAILURE_FIXTURE_AFTER_FE="+fe);
    }
    public void writeFailure(Path out,String error,long attempted,long successful,long failed) {
        try {
            Map<String,Object> record=row("error",error,"attempted",attempted,"successful",successful,"failed",failed,
                "lastObservedPaidFE",paid,"front",archive==null?new double[0][3]:archive.objectiveSnapshot(),
                "diagnosticOnly",true,"scope","Raw last successful archive at exception, not a deadline quality result");
            write(out.resolve("failure-last-front.jsonl"),record);
        }catch(Exception failure){System.err.println("NATURAL_FAILURE_EVIDENCE_WRITE_FAILED "+failure);}
    }
    public static void identity(Path out) throws Exception {
        write(out.resolve("loaded-identity.json"),ClassResolutionProbe.capture(
            "research.dynamic.DynamicSearch","org.uma.jmetal.util.research.search.CanonicalHmopso",
            "org.uma.jmetal.util.research.search.LocalSearch","org.uma.jmetal.util.research.search.SearchState",
            "org.uma.jmetal.util.research.search.QgsLocalLedger","org.uma.jmetal.util.research.search.DeepLocalVisits",
            "org.uma.jmetal.util.research.search.GlobalGroupPolicy","org.uma.jmetal.util.research.search.LocalPddrKernel",
            "org.uma.jmetal.util.research.classic.ClassicAlgorithm","org.uma.jmetal.util.research.DynamicEvaluation"));
    }
    private static Map<String,Object> row(Object...fields) {
        Map<String,Object> result=new LinkedHashMap<>();for(int i=0;i<fields.length;i+=2)result.put((String)fields[i],fields[i+1]);return result;
    }
    private static void write(Path path,Map<String,Object> row) throws Exception {
        Files.write(path,Collections.singletonList(DynamicJson.encode(row)),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
    }
}
