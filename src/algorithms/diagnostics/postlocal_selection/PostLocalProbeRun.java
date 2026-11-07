package research.dynamic;

import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.*;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;
import org.uma.jmetal.util.research.search.*;

/** Separate JVM entry point; source extraction and Linux execution belong to the controller. */
public final class PostLocalProbeRun {
    private static final long PROBE_SEED_XOR=0x6c8e9cf5L;
    private PostLocalProbeRun(){ }
    public static void main(String[] args)throws Exception {
        if(args.length!=7)throw new IllegalArgumentException("Expected instance setup fatigue output extractedInput mode sourceSeed");
        Path input=Paths.get(args[0]),out=Paths.get(args[3]),imported=Paths.get(args[4]);Files.createDirectories(out);
        String mode=args[5];long sourceSeed=Long.parseLong(args[6]),seed=sourceSeed^PROBE_SEED_XOR;
        if(!Arrays.asList("RAW_ROLE","POST_ROLE","POST_PARETO").contains(mode))throw new IllegalArgumentException(mode);
        configure(input,args,mode);
        String[] name=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(name[0]),Integer.parseInt(name[1]),Integer.parseInt(name[2]),Integer.parseInt(name[3]));
        Instance in=raw.getSchedulingInstance();if(!in.satisfiesDualResourceCondition())throw new IllegalArgumentException("Unqualified instance");
        DynamicParameters params=DynamicInputs.fatigue(in,Paths.get(args[2]));
        DynamicEvaluation decoder=new DynamicEvaluation(raw,in,params,true);
        long passFE=PostLocalReplay.passBudget(in),full=3*passFE,limit=Long.getLong("research.postlocal.limit",full);
        if(limit<0||limit>full)throw new IllegalArgumentException("Probe FE limit must be between zero and three complete passes");
        configurePrefixes(passFE);
        RunContext<PermutationSolution<Integer>> run=new RunContext<>(PilotPhysics.delegate(decoder),limit,seed);
        decoder.setCheckpoint(run::checkpoint);
        long prepareStart=System.nanoTime();PostLocalReplay probe=new PostLocalReplay(run,raw,in,imported,out,mode,seed);
        double prepareSeconds=(System.nanoTime()-prepareStart)/1e9;
        GomPrefixDigest digest=new GomPrefixDigest();PilotPhysics physics=new PilotPhysics(in,params);
        run.problem().setObserver(new EvaluationObserver(){
            public void completed(long fe,double time,boolean admitted,ThreeObjectiveArchive<?> archive){throw new AssertionError("Paid solution required");}
            @SuppressWarnings("unchecked") public void completedSolution(Solution<?> value,long fe,double time,boolean admitted,ThreeObjectiveArchive<?> archive) {
                PermutationSolution<Integer> point=(PermutationSolution<Integer>)value;
                probe.observed(point,fe);digest.update(point,fe);physics.check(point);
            }
        });
        Throwable failure=null;Map<String,Object> imports=null,details=null;
        try {imports=probe.validateImports(params);run.run(probe);}
        catch(RuntimeException|Error error){failure=error;}
        finally {decoder.clearPrepared();}
        try {details=probe.finish();}
        catch(Exception|Error error){if(failure==null)failure=error;else failure.addSuppressed(error);}
        Map<String,Object> receipt=GomRecords.row("mode",mode,"sourceSeed",sourceSeed,"seed",seed,"seedPlan",seedPlan(seed),
            "nativeObserver",Boolean.getBoolean("research.postlocal.nativeObserver"),"attempted",run.budget().attempted(),
            "successful",run.budget().successful(),"failed",run.budget().failed(),"searchSeconds",run.clock().elapsedSeconds(),
            "prepareSeconds",prepareSeconds,"expectedFE",full,"passFE",passFE,"feLimit",limit,
            "failAt",Long.getLong("research.pilot.failAt",-1L),"stopReason",run.stopReason(),"paidSHA256",digest.snapshot(),
            "paidPrefixes",digest.prefixes,"prefix2BSHA256",digest.prefixes.get(Long.toString(2*passFE)),
            "physicsQA",physics.receipt(),"importQA",imports,"decoder",decoder.diagnostics(),"probe",details,
            "error",failure==null?null:failure.toString(),"loaded",loaded());
        PostLocalReplay.write(out.resolve("receipt.json"),receipt);
        if(failure!=null)throw new IllegalStateException("Preserved post-local probe failure",failure);
        System.out.println("POSTLOCAL_PROBE_DONE "+mode+" "+run.budget().successful());
    }
    private static void configure(Path input,String[] args,String mode) {
        System.setProperty("research.ctxGom.enabled","true");
        System.setProperty("research.group.mode",mode.equals("POST_PARETO")?"FULL_ALL":"FULL_ROLE");
        System.setProperty("dhfsp.dataDir",input.getParent().toString());
        System.setProperty("dhfsp.setupFile",args[1]);System.setProperty("dhfsp.standbyPower","1");
    }
    private static void configurePrefixes(long passFE) {
        Set<String> prefixes=new LinkedHashSet<>();String requested=System.getProperty("research.ctxGom.prefixFE","");
        if(!requested.isEmpty())prefixes.addAll(Arrays.asList(requested.split(",")));
        for(int pass=1;pass<=3;pass++)prefixes.add(Long.toString(passFE*pass));
        System.setProperty("research.ctxGom.prefixFE",String.join(",",prefixes));
    }
    private static Map<String,Object> seedPlan(long seed) {
        return GomRecords.row("probeSeedXor",PROBE_SEED_XOR,"polish",seed^PostLocalReplay.POLISH_SEED_XOR,
            "rawFirst",seed^PostLocalReplay.RAW_FIRST_SEED_XOR,"rawSecond",seed^PostLocalReplay.RAW_SECOND_SEED_XOR,
            "final",seed^PostLocalReplay.FINAL_SEED_XOR,"rng","SeededRandom/ResearchSharedJavaRandom");
    }
    private static Object loaded()throws Exception {
        return ClassResolutionProbe.capture("research.dynamic.PostLocalProbeRun","org.uma.jmetal.util.research.search.PostLocalReplay",
            "org.uma.jmetal.util.research.search.PostLocalData","org.uma.jmetal.util.research.search.PostLocalArchives",
            "org.uma.jmetal.util.research.search.PostLocalPass","org.uma.jmetal.util.research.search.PostLocalSelection",
            "org.uma.jmetal.util.research.search.PostLocalEvidence","org.uma.jmetal.util.research.search.GomRunScope",
            "org.uma.jmetal.util.research.search.GomWorkspace","org.uma.jmetal.util.research.search.GomLocalProgram",
            "org.uma.jmetal.util.research.search.GlobalGroupPolicy","org.uma.jmetal.util.research.modelglobal.PaMixingMove",
            "org.uma.jmetal.util.research.DynamicEvaluation","org.uma.jmetal.util.research.runtime.BudgetedProblem");
    }
}
