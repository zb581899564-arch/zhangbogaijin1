package org.uma.jmetal.util.research.runtime;

import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.*;
import org.uma.jmetal.util.research.model.*;
import research.dynamic.DynamicInputs;
import research.dynamic.DynamicJson;

/** Engineering-only full decode and deep-copy contracts; zero search or performance evaluation FE. */
public final class SnapshotContractChecks {
    private SnapshotContractChecks() { }

    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]);
        System.setProperty("dhfsp.dataDir",input.getParent().toString());
        System.setProperty("dhfsp.setupFile",args[1]); System.setProperty("dhfsp.standbyPower","1");
        String[] d=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(d[0]),Integer.parseInt(d[1]),Integer.parseInt(d[2]),Integer.parseInt(d[3]));
        Instance in=raw.getSchedulingInstance(); DynamicParameters params=DynamicInputs.fatigue(in,Paths.get(args[2]));
        SeededRandom.reset(11600009L); PermutationSolution<Integer> source=raw.createSolution();
        SchedulingEncoding.repair(source,in);
        DynamicSchedule schedule=DynamicDecoder.full(in,params,SchedulingEncoding.integers(source.getVariables()),
                SchedulingEncoding.integers(source.getVariablesid()),SchedulingEncoding.machineIntegers(source),
                SchedulingEncoding.integers(source.getVariablesworker()),null);
        DynamicValidator.validate(in,params,schedule);
        for (int k=0;k<3;k++) source.setObjective(k,schedule.objectives()[k]);
        source.setAttribute(DynamicEvaluation.KEY,schedule);
        source.setAttribute(SchedulingMetadata.KEY,new SchedulingMetadata(schedule.factoryMakespan(),schedule.factoryEnergy(),schedule.factoryCost()));
        DynamicPrefix prefix=new DynamicPrefix(in,params); SnapshotContractData.installGraph(source,prefix);
        List<String> audited=SnapshotContractData.auditImmutableClasses(); immutableGetters(schedule,(SchedulingMetadata)source.getAttribute(SchedulingMetadata.KEY));
        String expected=SnapshotContractData.key(source);
        PermutationSolution<Integer> a=SolutionSnapshots.copy(source), b=SolutionSnapshots.copy(source);
        SnapshotContractData.independent(source,a); SnapshotContractData.independent(source,b); SnapshotContractData.independent(a,b);
        if (!expected.equals(SnapshotContractData.key(a)) || !expected.equals(SnapshotContractData.key(b)))
            throw new AssertionError("Copy changed source values");
        boolean anchored=System.getProperty("research.snapshot.mode","SERIAL").equals("ANCHOR");
        if ((a.getAttribute(DynamicEvaluation.KEY)==schedule)!=anchored) throw new AssertionError("Wrong immutable sharing mode");
        prefixIsolation(source,a,b);
        archiveIsolation(source,expected);
        SnapshotContractData.mutate(a);
        if (!expected.equals(SnapshotContractData.key(source)) || !expected.equals(SnapshotContractData.key(b)))
            throw new AssertionError("Copied vectors contaminated source or another copy");
        if (((SnapshotContractData.Payload)b.getAttribute("snapshot.payload")).array[0]!=3)
            throw new AssertionError("Nested mutable state contaminated");
        SnapshotContractData.mutate(source);
        if (!expected.equals(SnapshotContractData.key(b))) throw new AssertionError("Source contaminated copy");
        Map<String,Object> result=new LinkedHashMap<>(); result.put("status","PASS"); result.put("mode",anchored?"ANCHOR":"SERIAL");
        result.put("searchFE",0); result.put("engineeringFullDecoderCalls",1); result.put("auditedImmutableTypes",audited);
        result.put("mutableGraphAndCyclesIndependent",true); result.put("unknownPayloadDeepCopied",true);
        result.put("prefixAndVectorAliasesIndependent",true); result.put("failedSnapshotPreservesArchive",true);
        result.put("metrics",SnapshotCopyMetrics.snapshot());
        Files.write(Paths.get(args[3]),Collections.singletonList(DynamicJson.encode(result)),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
        System.out.println("SNAPSHOT_CONTRACT_PASS "+result.get("mode"));
    }

    private static void prefixIsolation(PermutationSolution<Integer> source,PermutationSolution<Integer>a,PermutationSolution<Integer>b) {
        DynamicPrefix prefix=(DynamicPrefix)a.getAttribute("snapshot.mutablePrefix");
        prefix.append(source.getVariableValue(0),source.getVariableValueid(0),SchedulingEncoding.machineIntegers(source)[0],source.getVariableValueworker(0));
        if (prefix.size()!=1 || ((DynamicPrefix)source.getAttribute("snapshot.mutablePrefix")).size()!=0
                || ((DynamicPrefix)b.getAttribute("snapshot.mutablePrefix")).size()!=0)
            throw new AssertionError("Prefix copy not independent");
    }

    private static void archiveIsolation(PermutationSolution<Integer> source,String expected) {
        ThreeObjectiveArchive<PermutationSolution<Integer>> archive=new ThreeObjectiveArchive<>();
        if (!archive.addEvaluated(source)) throw new AssertionError("Initial archive rejected");
        PermutationSolution<Integer>a=archive.snapshot().get(0), b=archive.snapshot().get(0);
        SnapshotContractData.independent(a,b); SnapshotContractData.mutate(a);
        if (!expected.equals(SnapshotContractData.key(b)) || !expected.equals(SnapshotContractData.key(archive.snapshot().get(0))))
            throw new AssertionError("Returned snapshot mutated archive");
        PermutationSolution<Integer> bad=SolutionSnapshots.copy(source);
        for(int k=0;k<3;k++)bad.setObjective(k,source.getObjective(k)-1);
        bad.setAttribute("snapshot.nonserializable",new Object()); boolean failed=false;
        try { archive.addEvaluated(bad); } catch(IllegalStateException expectedFailure) { failed=true; }
        if (!failed || archive.size()!=1 || !expected.equals(SnapshotContractData.key(archive.snapshot().get(0))))
            throw new AssertionError("Snapshot failure damaged archive");
    }

    private static void immutableGetters(DynamicSchedule schedule,SchedulingMetadata metadata) throws Exception {
        for (Method method:DynamicSchedule.class.getDeclaredMethods()) if (java.lang.reflect.Modifier.isPublic(method.getModifiers())
                && method.getParameterTypes().length==0 && method.getReturnType().isArray()) {
            Object first=method.invoke(schedule), second=method.invoke(schedule);
            if (first==second) throw new AssertionError("Exposed schedule array: "+method);
            if(first instanceof int[]){int old=((int[])second)[0];((int[])first)[0]=-1;
                if(((int[])method.invoke(schedule))[0]!=old)throw new AssertionError("Mutable schedule getter");}
            if(first instanceof double[]){double old=((double[])second)[0];((double[])first)[0]=-1;
                if(((double[])method.invoke(schedule))[0]!=old)throw new AssertionError("Mutable schedule getter");}
        }
        for(int k=0;k<3;k++){double[] a=metadata.values(k), b=metadata.values(k);a[0]=-1;
            if(metadata.values(k)[0]!=b[0])throw new AssertionError("Mutable metadata getter");}
        boolean denied=false;try{schedule.steps().clear();}catch(UnsupportedOperationException expected){denied=true;}
        if(!denied)throw new AssertionError("Schedule step list mutable");
    }
}
