package org.uma.jmetal.util.research.search;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;
import research.dynamic.DynamicInputs;
import research.dynamic.DynamicJson;

/** Matched finite-slot continuations of already-paid parents; every replay/evaluation is charged. */
public final class MakespanContinuationProbe {
    private MakespanContinuationProbe() { }

    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]),out=Paths.get(args[4]);
        System.setProperty("dhfsp.dataDir",input.getParent().toString());System.setProperty("dhfsp.setupFile",args[1]);
        System.setProperty("dhfsp.standbyPower","1.0");System.setProperty("research.pddr.mode","LINEAR");
        String[] dims=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(dims[0]),Integer.parseInt(dims[1]),Integer.parseInt(dims[2]),Integer.parseInt(dims[3]));
        Instance in=raw.getSchedulingInstance();DynamicParameters pars=DynamicInputs.fatigue(in,Paths.get(args[2]));
        long total=0,qa=0;SeededRandom.reset(0);
        for(String line:Files.readAllLines(Paths.get(args[3]),StandardCharsets.UTF_8)) {
            String[] f=line.split("\t");String id=f[0];long seed=Long.parseLong(f[2]);int paid=Integer.parseInt(f[3]);
            MakespanTiePolicy.configure(f[1]);QgsLocalLedger.resetForProbe();
            System.setProperty("research.qgsAudit.mode","replay");
            System.setProperty("research.qgsAudit.ledger",out.resolve("ledgers").resolve(id+".csv").toString());
            DynamicEvaluation decoder=new DynamicEvaluation(raw,in,pars,true);
            RunContext<PermutationSolution<Integer>> context=new RunContext<>(decoder,paid+1,seed);decoder.setCheckpoint(context::checkpoint);
            SearchState state=new SearchState(context.problem(),in,null);state.observationGroup(Direction.MAKESPAN);
            LocalSearch local=new LocalSearch(in,4,new SearchConfig().resolved(4),state);
            List<PermutationSolution<Integer>> retained=new ArrayList<>();
            context.run(new Algorithm<Object>() {
                private static final long serialVersionUID=1L;
                public void run() {
                    PermutationSolution<Integer> parent=context.problem().createSolution();fill(parent,f,4);
                    if(SchedulingEncoding.repair(parent,in)!=0)throw new AssertionError("Illegal stored parent");
                    context.problem().evaluate(parent);
                    double[] expected=Arrays.stream(f[4].split(",")).mapToDouble(Double::parseDouble).toArray();
                    if(!Arrays.equals(expected,parent.getObjectives()))throw new AssertionError("Parent replay differs");
                    SeededRandom.reset(seed);
                    Particle result=local.improve(new Particle(parent),Direction.MAKESPAN,Collections.emptyList());
                    retained.add(result.current);
                }
                public Object getResult(){return null;}
                public String getName(){return "MAKESPAN_TIE_CONTINUATION";}
                public String getDescription(){return getName();}
            });
            if(context.budget().successful()!=paid+1||context.budget().failed()!=0||retained.size()!=1)
                throw new AssertionError("Incomplete finite local slot");
            Path ledgerOut=out.resolve("actual-ledgers").resolve(id);Files.createDirectories(ledgerOut);QgsLocalLedger.finish(ledgerOut);
            decoder.clearPrepared();List<Map<String,Object>> front=new ArrayList<>();
            for(PermutationSolution<Integer> solution:context.result()){validate(in,pars,solution);qa++;front.add(encoding(solution));}
            validate(in,pars,retained.get(0));qa++;
            append(out.resolve("trials.jsonl"),row("id",id,"mode",f[1],"seed",seed,"successful",context.budget().successful(),
                "attempted",context.budget().attempted(),"failed",context.budget().failed(),"front",front,
                "retained",encoding(retained.get(0)),"tiePolicy",MakespanTiePolicy.diagnostics(),
                "decoder",decoder.diagnostics(),"search",state.diagnostics(),"searchSeconds",context.clock().elapsedSeconds()));
            total+=context.budget().successful();
        }
        append(out.resolve("receipt.jsonl"),row("successfulFE",total,"failedFE",0,"fullDecoderQA",qa));
    }

    private static void validate(Instance in,DynamicParameters pars,PermutationSolution<Integer>s) {
        DynamicSchedule cached=(DynamicSchedule)s.getAttribute(DynamicEvaluation.KEY);DynamicValidator.validate(in,pars,cached);
        DynamicSchedule full=DynamicDecoder.full(in,pars,SchedulingEncoding.integers(s.getVariables()),
            SchedulingEncoding.integers(s.getVariablesid()),SchedulingEncoding.machineIntegers(s),SchedulingEncoding.integers(s.getVariablesworker()),null);
        if(!Arrays.equals(full.objectives(),s.getObjectives())||!Arrays.equals(full.factoryMakespan(),cached.factoryMakespan()))
            throw new AssertionError("Full decoder QA differs");
    }

    @SuppressWarnings("unchecked")
    private static void fill(PermutationSolution<Integer>s,String[]f,int offset) {
        List<Integer> machines=(List<Integer>)s.getAttribute("machine");
        for(int k=0;k<4;k++) {
            int[]v=Arrays.stream(f[offset+1+k].split(",")).mapToInt(Integer::parseInt).toArray();
            for(int j=0;j<v.length;j++) {
                if(k==0)s.setVariableValue(j,v[j]);else if(k==1)s.setVariableValueid(j,v[j]);
                else if(k==2)machines.set(j,v[j]);else s.setVariableValueworker(j,v[j]);
            }
        }
    }

    private static Map<String,Object> encoding(PermutationSolution<Integer>s) {
        return row("JS",s.getVariables(),"FA",s.getVariablesid(),"MA",s.getAttribute("machine"),
            "WA",s.getVariablesworker(),"objectives",s.getObjectives().clone(),
            "factoryMakespan",((DynamicSchedule)s.getAttribute(DynamicEvaluation.KEY)).factoryMakespan());
    }
    private static Map<String,Object> row(Object...pairs) {
        Map<String,Object>out=new LinkedHashMap<>();for(int j=0;j<pairs.length;j+=2)out.put((String)pairs[j],pairs[j+1]);return out;
    }
    private static void append(Path path,Map<String,Object>row) throws Exception {
        Files.write(path,Collections.singletonList(DynamicJson.encode(row)),StandardCharsets.UTF_8,StandardOpenOption.CREATE,StandardOpenOption.APPEND);
    }
}
