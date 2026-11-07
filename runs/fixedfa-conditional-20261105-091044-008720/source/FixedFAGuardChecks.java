package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.*;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;

/** Intentional third-attempt fixed-FA violation, separately billed from all performance runs. */
public final class FixedFAGuardChecks {
    private FixedFAGuardChecks() { }
    public static void main(String[] args)throws Exception {
        Path input=Paths.get(args[0]),out=Paths.get(args[3]);Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir",input.getParent().toString());System.setProperty("dhfsp.setupFile",args[1]);
        System.setProperty("dhfsp.standbyPower","1");String[] dim=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW source=new EDHHFSPW(Integer.parseInt(dim[0]),Integer.parseInt(dim[1]),Integer.parseInt(dim[2]),Integer.parseInt(dim[3]));
        Instance in=source.getSchedulingInstance();DynamicParameters p=DynamicInputs.fatigue(in,Paths.get(args[2]));
        DynamicEvaluation decoder=new DynamicEvaluation(source,in,p,true);FixedFactoryProblem fixed=new FixedFactoryProblem(decoder,in);
        RunContext<PermutationSolution<Integer>> context=new RunContext<>(fixed,3,12790003);decoder.setCheckpoint(context::checkpoint);
        List<PermutationSolution<Integer>> valid=new ArrayList<>();
        Algorithm<Object> fixture=new Algorithm<Object>() {
            public void run() {
                for(int i=0;i<2;i++) {PermutationSolution<Integer> value=context.problem().createSolution();context.problem().evaluate(value);valid.add(value);}
                PermutationSolution<Integer> invalid=context.problem().createSolution();int[] count=new int[in.factories()];
                for(int f:invalid.getVariablesid())count[f]++;
                int pos=0;while(count[invalid.getVariableValueid(pos)]<2)pos++;
                invalid.setVariableValueid(pos,(invalid.getVariableValueid(pos)+1)%in.factories());
                SchedulingEncoding.repair(invalid,in);context.problem().evaluate(invalid);
            }
            public Object getResult(){return null;}
            public String getName(){return "fixedFA-guard-fixture";}
            public String getDescription(){return "Two actual successes, then a deliberately different feasible FA";}
        };
        boolean rejected=false;
        try {context.run(fixture);}catch(IllegalStateException error){rejected=error.getMessage().startsWith("FIXED_FA_DRIFT");}
        if(!rejected || context.budget().attempted()!=3 || context.budget().successful()!=2 || context.budget().failed()!=1)
            throw new AssertionError("Fixed FA failure billing differs");
        for(PermutationSolution<Integer> value:valid) {
            DynamicSchedule paid=(DynamicSchedule)value.getAttribute(DynamicEvaluation.KEY);
            DynamicSchedule full=DynamicDecoder.full(in,p,paid.js(),paid.fa(),paid.ma(),paid.wa(),null);
            DynamicValidator.validate(in,p,full);if(!Arrays.equals(value.getObjectives(),full.objectives()))throw new AssertionError("Fixture objective differs");
        }
        Map<String,Object> result=new LinkedHashMap<>();result.put("status","PASS_EXPECTED_GUARD_FAILURE");
        result.put("attemptedFE",3);result.put("successfulFE",2);result.put("expectedFailures",1);result.put("unexpectedFailures",0);
        result.put("offlineFullDecoderQA",2);result.put("constraint",fixed.diagnostics());
        List<double[]> front=new ArrayList<>();for(PermutationSolution<Integer> value:context.result())front.add(value.getObjectives().clone());
        result.put("lastValidFront",front);
        Files.write(out.resolve("receipt.json"),Collections.singletonList(DynamicJson.encode(result)),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
        System.out.println("FIXED_FA_GUARD_CHECK_PASS attempted=3 successful=2 expectedFailure=1 fullQA=2");
    }
}
