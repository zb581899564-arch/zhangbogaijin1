package research.dynamic;

import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.solution.*;
import org.uma.jmetal.util.research.runtime.*;
import org.uma.jmetal.util.research.model.*;

/** Shared checkpoint policy; physics QA after the measured search. */
final class PilotEvidence {
    final AnytimeRecorder recorder;
    final CheckpointGenomes genomes;
    final PddrPaidDigest digest;
    final NaturalRunEvidence last=new NaturalRunEvidence();
    final List<Map<String,Object>> initial=new ArrayList<>();
    long nanos;
    PilotEvidence(long limit,double seconds) throws Exception {
        SortedSet<Long> checks=new TreeSet<>();
        for(long x:new long[]{1,2,100,10000,50000,100000,250000,500000})if(x<=limit)checks.add(x);
        checks.add(limit);long[] points=new long[checks.size()];int i=0;for(long x:checks)points[i++]=x;
        recorder=new AnytimeRecorder(limit,seconds,new double[]{.25,.5,1},points);
        genomes=new CheckpointGenomes(recorder,seconds);digest=new PddrPaidDigest();
    }
    void completed(Solution<?> value,long fe,double seconds,boolean changed,ThreeObjectiveArchive<?> archive) {
        long start=System.nanoTime();
        @SuppressWarnings("unchecked") PermutationSolution<Integer> p=(PermutationSolution<Integer>)value;
        last.observed(archive,fe);digest.update(fe,p);
        if(fe<=100){Map<String,Object> row=ProbeData.encoding(p);row.put("fe",fe);initial.add(row);}
        genomes.completedSolution(value,fe,seconds,changed,archive);nanos+=System.nanoTime()-start;
    }
    void write(Path out,Instance in,DynamicParameters params) throws Exception {
        PaLightEvidence.writeRows(out.resolve("initial-population.jsonl"),initial);
        PaLightEvidence.writeRows(out.resolve("anytime.jsonl"),recorder.finish());
        genomes.validateAndWrite(out,in,params);
    }
}
