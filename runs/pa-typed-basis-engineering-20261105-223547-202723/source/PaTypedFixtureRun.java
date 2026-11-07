package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.modelglobal.*;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.util.research.search.Direction;
import static org.uma.jmetal.util.research.modelglobal.PaTypedTrace.*;

/** 100 paid fixed parents and64 deterministic typed proposals, with complete timeline QA. */
public final class PaTypedFixtureRun {
    public static void main(String[] args)throws Exception{
        Path input=Paths.get(args[0]),out=Paths.get(args[4]);Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir",input.getParent().toString());System.setProperty("dhfsp.setupFile",args[1]);
        System.setProperty("dhfsp.standbyPower","1");System.setProperty("research.pa.typedTrace",out.resolve("fixtures.jsonl").toString());
        String[] dims=input.getFileName().toString().replace(".txt", "").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(dims[0]),Integer.parseInt(dims[1]),Integer.parseInt(dims[2]),Integer.parseInt(dims[3]));
        Instance instance=raw.getSchedulingInstance();DynamicParameters fatigue=DynamicInputs.fatigue(instance,Paths.get(args[2]));
        DynamicEvaluation decoder=new DynamicEvaluation(raw,instance,fatigue,true);
        RunContext<PermutationSolution<Integer>> run=new RunContext<>(decoder,164,Long.parseLong(args[5]));decoder.setCheckpoint(run::checkpoint);
        PaRunChecks checks=new PaRunChecks(instance,fatigue);PaPaidEvaluation evaluator=new PaPaidEvaluation(run,instance,checks);
        PaTypedTrace trace=new PaTypedTrace();List<PaIndividual> initial=new ArrayList<>();boolean passed=false;
        try{
            run.run(new Algorithm<Object>(){
                public void run(){
                    try{
                        for(String line:Files.readAllLines(Paths.get(args[3]),StandardCharsets.UTF_8)){
                            String[] f=line.split("\t"),values=f[3].split(",");double[] expected=new double[3];for(int k=0;k<3;k++)expected[k]=Double.parseDouble(values[k]);
                            PaIndividual point=evaluator.initial(new FourVectors(ProbeData.integers(f[4]),ProbeData.integers(f[5]),ProbeData.integers(f[6]),ProbeData.integers(f[7])),Direction.valueOf(f[1]),expected);
                            initial.add(point);trace.emit(row("kind","initial","state",state(point)));
                        }
                    }catch(java.io.IOException error){throw new java.io.UncheckedIOException(error);}
                    if(initial.size()!=100)throw new AssertionError("Expected100sourceparents");
                    for(PaTypedFixtureCases fixture:PaTypedFixtureCases.make(evaluator.catalog(),initial)){
                        PaIndividual parent=initial.get(fixture.receiver),donor=fixture.donor<0?parent:initial.get(fixture.donor);
                        PaTypedMove move=PaTypedMove.apply(evaluator.catalog(),parent.genome,donor.genome,fixture.term,PaTypedTerm.Basis.TYPED,fixture.donor<0);
                        PaIndividual child=evaluator.candidate(move.genome,parent);
                        trace.emit(row("kind","proposal","receiver",fixture.receiver,"donor",fixture.donor,"poolScope",fixture.donor<0?"SINGLE_RECEIVER":"ALL_INITIAL","type",fixture.term.kind.name(),
                            "jobs",fixture.term.jobs(),"fallback",move.fallback,"state",state(child)));
                    }
                    evaluator.checkpoint();throw new AssertionError("Expected exact164FEstop");
                }
                public Object getResult(){return null;}public String getName(){return "TYPED_BASIS_FIXTURES";}public String getDescription(){return getName();}
            });
            if(run.budget().successful()!=164 || run.budget().failed()!=0 || checks.paidQA!=164)throw new AssertionError("Fixtureaccounting");
            passed=true;
        }finally{
            trace.close();NeutralProbeSupport.append(out.resolve("receipt.jsonl"),row("status",passed?"COMPLETE":"INCOMPLETE_RETAINED",
                "successfulFE",run.budget().successful(),"attemptedFE",run.budget().attempted(),"failedFE",run.budget().failed(),
                "paidSHA256",checks.paidDigest.finish(),"fullDecoderQA",checks.paidQA+checks.neutralQA,"decoder",decoder.diagnostics()));decoder.clearPrepared();
        }
    }
}
