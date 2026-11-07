package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.*;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;
import org.uma.jmetal.util.research.search.*;

/** True deadline observer: reported fronts and their genomes must have completed by the deadline. */
public final class ProgramExitRun {
    private ProgramExitRun() { }
    private static final long[] CHECKS={100,5100,15000,50000,100000,250000,500000};

    private static final class Evidence implements EvaluationObserver {
        final AnytimeRecorder recorder; final CheckpointGenomes genomes;
        final PddrPaidDigest digest; final List<Map<String,Object>> initial=new ArrayList<>();
        final NaturalRunEvidence lastPaid=new NaturalRunEvidence();
        Evidence(long limit,double seconds) throws Exception {
            recorder=new AnytimeRecorder(limit,seconds,seconds==0?new double[]{1}:new double[]{.5,1},NaturalRunEvidence.checkpoints(limit));
            genomes=new CheckpointGenomes(recorder,seconds);
            digest=Boolean.getBoolean("research.memory.audit") ? new PddrPaidDigest() : null;
        }
        public void completed(long fe,double seconds,boolean changed,ThreeObjectiveArchive<?> archive) {
            throw new IllegalStateException("Paid solution evidence required");
        }
        public void completedSolution(Solution<?> value,long fe,double seconds,boolean changed,ThreeObjectiveArchive<?> archive) {
            lastPaid.observed(archive,fe);
            if(digest!=null)digest.update(fe,(PermutationSolution<?>)value);
            if(fe<=100) {
                Map<String,Object> point=row("fe",fe);point.putAll(genome((PermutationSolution<?>)value));initial.add(point);
            }
            genomes.completedSolution(value,fe,seconds,changed,archive);
            lastPaid.maybeInject(fe);
        }
        void write(Path out,Instance in,DynamicParameters params) throws Exception {
            lines(out.resolve("initial-population.jsonl"),initial);
            lines(out.resolve("anytime.jsonl"),recorder.finish());
            genomes.validateAndWrite(out,in,params);
        }
    }

    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]),out=Paths.get(args[3]);Files.createDirectories(out);
        String mode=args[4];long limit=Long.parseLong(args[5]),seed=Long.parseLong(args[6]);
        double seconds=Double.parseDouble(args[7]);
        System.setProperty("dhfsp.dataDir",input.getParent().toString());System.setProperty("dhfsp.setupFile",args[1]);
        System.setProperty("dhfsp.standbyPower","1");System.setProperty("research.pddr.mode","LINEAR");
        String regime=args[9];if(!Arrays.asList("record","replay").contains(regime))throw new IllegalArgumentException("Unknown local regime");
        System.setProperty("research.qgsAudit.mode",regime);System.setProperty("research.qgsAudit.ledger",args[8]);
        String[] d=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW source=new EDHHFSPW(Integer.parseInt(d[0]),Integer.parseInt(d[1]),Integer.parseInt(d[2]),Integer.parseInt(d[3]));
        Instance in=source.getSchedulingInstance();DynamicParameters params=DynamicInputs.fatigue(in,Paths.get(args[2]));
        ProgramExitPolicy.initialize();
        DynamicEvaluation decoder=new DynamicEvaluation(source,in,params,true);
        RunContext<PermutationSolution<Integer>> context=new RunContext<>(decoder,limit,seed,seconds);
        decoder.setCheckpoint(context::checkpoint);
        QgsLocalLedger.allowDeadlinePrefix(()->context.clock().elapsedSeconds()>=seconds);
        SearchConfig config=new SearchConfig();config.mergeGlobalLocal=config.paperResourceOperators=
                !DynamicSearch.isClassic(mode)&&!Boolean.getBoolean("research.li.v2");
        DynamicSearch search=DynamicSearch.create(mode,in,params,decoder,context,config,false,0,0);
        Evidence evidence=new Evidence(limit,seconds);context.problem().setObserver(evidence);
        NaturalRunEvidence.identity(out);
        lines(out.resolve("program-exit-loaded-identity.jsonl"),Collections.singletonList(ClassResolutionProbe.capture(
            "org.uma.jmetal.util.research.search.LocalSearch", "org.uma.jmetal.util.research.search.ProgramExitPolicy",
            "org.uma.jmetal.util.research.search.ProgramExitHv3D", "org.uma.jmetal.util.research.search.LocalPddrKernel")));
        Throwable failure=null;
        try {SnapshotCopyMetrics.searchStarted();context.run(search.algorithm);}
        catch(RuntimeException|Error error){failure=error;}
        finally {SnapshotCopyMetrics.searchEnded();decoder.clearPrepared();}
        Map<String,Object> receipt=row("mode",mode,"seed",seed,"localLedgerMode",regime,"searchConfiguration",search.configuration,"stopReason",context.stopReason(),
                "feLimit",limit,"timeLimitSeconds",Double.isFinite(seconds)?seconds:null,
                "attempted",context.budget().attempted(),"successful",context.budget().successful(),"failed",context.budget().failed(),
                "timeInterruptedAttempts",context.budget().timeInterruptedAttempts(),"searchSeconds",context.clock().elapsedSeconds(),
                "search",search.diagnostics(),"decoder",decoder.diagnostics(),"paidSHA256",evidence.digest==null?null:evidence.digest.finish(),
                "error",failure==null?null:failure.toString());
        ProgramExitPolicy.write(out);
        lines(out.resolve("run-receipt.jsonl"),Collections.singletonList(receipt));
        if(failure!=null) {
            evidence.lastPaid.writeFailure(out,failure.toString(),context.budget().attempted(),context.budget().successful(),context.budget().failed());
            throw new IllegalStateException("Natural/replay run failed; receipt and available front retained",failure);
        }
        QgsLocalLedger.finish(out);evidence.write(out,in,params);
        lines(out.resolve("copy-metrics.jsonl"),Collections.singletonList(SnapshotCopyMetrics.snapshot()));
        // No raw post-deadline context.result() is offered as the deadline result.
        System.out.println("SNAPSHOT_TIME_PASS "+mode+" successful="+context.budget().successful()+" stop="+context.stopReason());
    }

    private static Map<String,Object> genome(PermutationSolution<?> s) {
        return row("JS",new ArrayList<>(s.getVariables()),"FA",new ArrayList<>(s.getVariablesid()),
                "MA",new ArrayList<>((List<?>)s.getAttribute("machine")),"WA",new ArrayList<>(s.getVariablesworker()),
                "objectives",s.getObjectives().clone());
    }
    private static Map<String,Object> row(Object...fields) {
        Map<String,Object> out=new LinkedHashMap<>();for(int i=0;i<fields.length;i+=2)out.put((String)fields[i],fields[i+1]);return out;
    }
    private static void lines(Path path,List<Map<String,Object>> rows) throws Exception {
        List<String> text=new ArrayList<>();for(Map<String,Object> r:rows)text.add(DynamicJson.encode(r));
        Files.write(path,text,StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
    }
}
