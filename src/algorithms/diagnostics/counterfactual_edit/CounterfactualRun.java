package research.dynamic;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.modelglobal.*;
import org.uma.jmetal.util.research.runtime.*;

/** Full-decoder-only diagnostic; exactly one paid query for every nonendpoint configuration. */
public final class CounterfactualRun implements Algorithm<Void> {
    private final RunContext<PermutationSolution<Integer>> run;
    private final Instance instance;
    private final DynamicParameters params;
    private final List<CounterfactualInputs.Entry> entries;
    private final BufferedWriter writer;
    private long written;
    private String pending;

    private CounterfactualRun(RunContext<PermutationSolution<Integer>> context, Instance in,
            DynamicParameters fatigue, List<CounterfactualInputs.Entry> cases, BufferedWriter output) {
        run=context; instance=in; params=fatigue; entries=cases; writer=output;
    }

    private void append(Map<String,Object> row) {
        try { writer.write(DynamicJson.encode(row)); writer.newLine(); writer.flush(); written++; }
        catch (IOException error) { throw new UncheckedIOException(error); }
    }

    @Override public void run() {
        for (CounterfactualInputs.Entry e:entries) {
            pending=e.id+":"+e.mask;
            PermutationSolution<Integer> p=CounterfactualInputs.point(run.problem(),e);
            run.problem().evaluate(p);
            DynamicSchedule schedule=(DynamicSchedule)p.getAttribute(DynamicEvaluation.KEY);
            // Validation reads the paid timeline; it performs no additional decoder query.
            DynamicValidator.validate(instance,params,schedule);
            append(CounterfactualInputs.record(e,schedule,run.budget().successful()));
            pending=null;
        }
    }

    @Override public Void getResult() { return null; }
    @Override public String getName() { return "FROZEN_EDIT_COUNTERFACTUAL"; }
    @Override public String getDescription() { return "No search, retention, pool update or adaptive proposal"; }

    private static Map<String,Object> qa(Instance in,DynamicParameters params,
            List<CounterfactualInputs.Entry> entries,BufferedWriter writer) throws IOException {
        long attempts=0,passed=0; String pending=null; Throwable failure=null;
        double[] maximumError=new double[3];
        try {
            for (CounterfactualInputs.Entry e:entries) {
                pending=e.id+":"+e.mask; attempts++;
                FourVectors v=e.vectors;
                DynamicSchedule s=DynamicDecoder.full(in,params,v.jobs(),v.factories(),v.machines(),v.workers(),null);
                DynamicValidator.validate(in,params,s);
                for (int k=0;k<3;k++) {
                    maximumError[k]=Math.max(maximumError[k],Math.abs(s.objectives()[k]-e.expected[k]));
                    if (Double.doubleToLongBits(s.objectives()[k])!=Double.doubleToLongBits(e.expected[k]))
                        throw new AssertionError("Old paid endpoint bits differ: "+pending+" objective "+k);
                }
                writer.write(DynamicJson.encode(CounterfactualInputs.record(e,s,attempts)));
                writer.newLine(); writer.flush(); passed++; pending=null;
            }
        } catch (RuntimeException | Error error) { failure=error; }
        Map<String,Object> r=new LinkedHashMap<>();
        r.put("attemptedQA",attempts); r.put("passedQA",passed); r.put("failedQA",attempts-passed);
        r.put("maxAbsoluteObjectiveError",maximumError); r.put("exactBits",true);
        r.put("pending",pending); r.put("error",failure==null?null:failure.toString());
        return r;
    }

    public static void main(String[] args) throws Exception {
        if(args.length!=7)throw new IllegalArgumentException("INPUT SETUP FATIGUE CASES OUT MODE COUNT");
        Path input=Paths.get(args[0]),out=Paths.get(args[4]); Files.createDirectories(out);
        boolean isQA=args[5].equals("QA");
        if(!isQA&&!args[5].equals("PAID"))throw new IllegalArgumentException("Unknown mode");
        int count=Integer.parseInt(args[6]);
        if(count<1||count>(isQA?52:364))throw new IllegalArgumentException("Hard budget exceeded");
        System.setProperty("dhfsp.dataDir",input.getParent().toString());
        System.setProperty("dhfsp.setupFile",args[1]); System.setProperty("dhfsp.standbyPower","1");
        String[] n=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(n[0]),Integer.parseInt(n[1]),Integer.parseInt(n[2]),Integer.parseInt(n[3]));
        Instance in=raw.getSchedulingInstance();
        if(!in.satisfiesDualResourceCondition())throw new IllegalArgumentException("Unqualified instance");
        DynamicParameters params=DynamicInputs.fatigue(in,Paths.get(args[2]));
        FirstStageCatalog catalog=new FirstStageCatalog(in);
        List<CounterfactualInputs.Entry> cases=new ArrayList<>();
        for(String line:Files.readAllLines(Paths.get(args[3]),StandardCharsets.UTF_8)) {
            if(line.trim().isEmpty())continue;
            CounterfactualInputs.Entry e=new CounterfactualInputs.Entry(line,catalog);
            if(isQA?(e.mask!=0&&e.mask!=15)||e.expected.length!=3:
                    e.mask<1||e.mask>14||e.expected.length!=0)throw new IllegalArgumentException("Wrong mode row");
            cases.add(e);
        }
        if(cases.size()!=count)throw new IllegalArgumentException("Manifest/count mismatch");
        Map<String,Object> receipt; long start=System.nanoTime();
        try(BufferedWriter writer=Files.newBufferedWriter(out.resolve("evaluations.jsonl"),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW)) {
            if(isQA)receipt=qa(in,params,cases,writer);
            else {
                DynamicEvaluation decoder=new DynamicEvaluation(raw,in,params,false);
                RunContext<PermutationSolution<Integer>> run=new RunContext<>(decoder,count,8111009L);
                decoder.setCheckpoint(run::checkpoint);
                CounterfactualRun algorithm=new CounterfactualRun(run,in,params,cases,writer);
                Throwable failure=null;
                try { run.run(algorithm); } catch(RuntimeException | Error error) { failure=error; }
                receipt=new LinkedHashMap<>(); receipt.put("attempted",run.budget().attempted());
                receipt.put("successful",run.budget().successful()); receipt.put("failed",run.budget().failed());
                receipt.put("written",algorithm.written); receipt.put("pending",algorithm.pending);
                receipt.put("decoder",decoder.diagnostics()); receipt.put("stopReason",run.stopReason());
                receipt.put("error",failure==null?null:failure.toString());
            }
        }
        receipt.put("mode",args[5]);receipt.put("limit",count);receipt.put("processBodySeconds",(System.nanoTime()-start)/1e9);
        receipt.put("loaded",ClassResolutionProbe.capture("research.dynamic.CounterfactualRun","research.dynamic.CounterfactualInputs",
            "org.uma.jmetal.util.research.modelglobal.TypedScheduleGenome","org.uma.jmetal.util.research.modelglobal.FirstStageCatalog",
            "org.uma.jmetal.util.research.DynamicEvaluation","org.uma.jmetal.util.research.model.DynamicDecoder",
            "org.uma.jmetal.util.research.model.DynamicValidator","org.uma.jmetal.util.research.runtime.RunContext",
            "org.uma.jmetal.util.research.runtime.BudgetedProblem"));
        Files.write(out.resolve("receipt.json"),(DynamicJson.encode(receipt)+"\n").getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
        if(receipt.get("error")!=null)throw new IllegalStateException("Failure retained: "+receipt.get("error"));
        System.out.println("COUNTERFACTUAL_DONE "+args[5]+" "+count);
    }
}
