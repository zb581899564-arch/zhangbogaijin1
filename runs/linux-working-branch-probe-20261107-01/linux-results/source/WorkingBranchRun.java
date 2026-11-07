package research.dynamic;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.modelglobal.*;
import org.uma.jmetal.util.research.runtime.*;

/** One bounded JVM. No engineering rerun or extra decoding is performed here. */
public final class WorkingBranchRun {
    static EDHHFSPW problem(Path input,String setup) {
        System.setProperty("dhfsp.dataDir",input.getParent().toString());System.setProperty("dhfsp.setupFile",setup);
        System.setProperty("dhfsp.standbyPower","1");String[] n=input.getFileName().toString().replace(".txt","").split("_");
        return new EDHHFSPW(Integer.parseInt(n[0]),Integer.parseInt(n[1]),Integer.parseInt(n[2]),Integer.parseInt(n[3]));
    }
    public static void main(String[] args)throws Exception {
        if(args.length!=5)throw new IllegalArgumentException("INPUT SETUP FATIGUE PREPARED OUT");
        Path input=Paths.get(args[0]),out=Paths.get(args[4]);Files.createDirectories(out);
        EDHHFSPW raw=problem(input,args[1]);Instance in=raw.getSchedulingInstance();
        if(!in.satisfiesDualResourceCondition())throw new AssertionError("Unqualified instance");
        DynamicParameters params=DynamicInputs.fatigue(in,Paths.get(args[2]));
        WorkingBranchData data=new WorkingBranchData(Paths.get(args[3]),new FirstStageCatalog(in));
        DynamicEvaluation decoder=new DynamicEvaluation(raw,in,params,false);
        RunContext<PermutationSolution<Integer>> run=new RunContext<>(decoder,1536,14910003L);decoder.setCheckpoint(run::checkpoint);
        Map<String,Object> receipt=new LinkedHashMap<>();long start=System.nanoTime();Throwable failure=null;
        try(BufferedWriter paid=Files.newBufferedWriter(out.resolve("evaluations.jsonl"),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
            BufferedWriter ends=Files.newBufferedWriter(out.resolve("endpoints.jsonl"),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW)) {
            WorkingBranchSearch search=new WorkingBranchSearch(run,in,params,data,paid,ends);
            try{run.run(search);}catch(RuntimeException|Error error){failure=error;}
            receipt.put("written",search.written);receipt.put("programs",search.programs);receipt.put("pending",search.pending);
        }
        receipt.put("attempted",run.budget().attempted());receipt.put("successful",run.budget().successful());receipt.put("failed",run.budget().failed());
        receipt.put("decoder",decoder.diagnostics());receipt.put("stopReason",run.stopReason());receipt.put("limit",1536);
        receipt.put("processBodySeconds",(System.nanoTime()-start)/1e9);receipt.put("error",failure==null?null:failure.toString());
        receipt.put("loaded",ClassResolutionProbe.capture("research.dynamic.WorkingBranchRun","research.dynamic.WorkingBranchData",
            "research.dynamic.WorkingBranchSearch","research.dynamic.WorkingBranchRules","research.dynamic.CounterfactualInputs",
            "org.uma.jmetal.util.research.modelglobal.PaMixingMove","org.uma.jmetal.util.research.modelglobal.PaInternalArchive",
            "org.uma.jmetal.util.research.modelglobal.TypedScheduleGenome","org.uma.jmetal.util.research.DynamicEvaluation",
            "org.uma.jmetal.util.research.model.DynamicDecoder","org.uma.jmetal.util.research.model.DynamicValidator",
            "org.uma.jmetal.util.research.runtime.RunContext","org.uma.jmetal.util.research.runtime.BudgetedProblem"));
        Files.write(out.resolve("receipt.json"),(DynamicJson.encode(receipt)+"\n").getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
        if(failure!=null)throw new IllegalStateException("Failure retained",failure);
        if(run.budget().successful()!=1536 || !receipt.get("written").equals(1536L) || !receipt.get("programs").equals(84L))
            throw new AssertionError("Incomplete paid programs; do not refill");
        System.out.println("WORKING_BRANCH_DONE 1536 programs=84");
    }
}
