package org.uma.jmetal.util.research.modelglobal;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import research.dynamic.*;

/** Structural-only frozen-model/proposal inspection. Backend calls are forbidden, including on failure. */
public final class QpaNeutralGeometryRun {
    private QpaNeutralGeometryRun() { }
    public static void main(String[] args) throws Exception {
        long start=System.nanoTime();Path input=Paths.get(args[0]),out=Paths.get(args[4]);
        System.setProperty("dhfsp.dataDir",input.getParent().toString());System.setProperty("dhfsp.setupFile",args[1]);System.setProperty("dhfsp.standbyPower","1");
        String[] n=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(n[0]),Integer.parseInt(n[1]),Integer.parseInt(n[2]),Integer.parseInt(n[3]));
        GeometryWorld world=new GeometryWorld(raw,2026110603L);List<int[]> pairs=new ArrayList<>();
        for (String line:Files.readAllLines(Paths.get(args[3]),StandardCharsets.UTF_8)) pairs.add(Arrays.stream(line.split("\t")).mapToInt(Integer::parseInt).toArray());
        GeometryProposals proposals=new GeometryProposals(world,pairs);int models=0;Throwable failure=null;
        String population=null,variant=null;GeometryPopulation original=null;List<QpaIndividual> points=new ArrayList<>();
        try (BufferedReader reader=Files.newBufferedReader(Paths.get(args[2]),StandardCharsets.UTF_8);
             BufferedWriter model=Files.newBufferedWriter(out.resolve("models.jsonl"),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
             BufferedWriter cases=Files.newBufferedWriter(out.resolve("proposal-hashes.tsv"),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW)) {
            cases.write("population\tvariant\tpair\tmask\tkind\treference\tphysicalSHA256\tfallback\n");reader.readLine();String line;
            while ((line=reader.readLine())!=null) {
                String[] fields=line.split("\t",-1);
                if (population!=null&&(!population.equals(fields[0])||!variant.equals(fields[1]))) {
                    GeometryPopulation value=new GeometryPopulation(points,world,2026110601L);models+=2;
                    if (variant.equals("ORIGINAL")) original=value;else value.samePhysicalAndPA(original,world);
                    model.write(value.json(population,variant));model.newLine();proposals.write(population,variant,value,original.qpa.activeSubsets,2026110602L,cases);points=new ArrayList<>();
                }
                if (population!=null&&!population.equals(fields[0])) original=null;
                population=fields[0];variant=fields[1];
                if (Integer.parseInt(fields[2])!=points.size()) throw new AssertionError("Carrier slot order mismatch");points.add(world.carrier(fields));
            }
            if (!points.isEmpty()) {
                GeometryPopulation value=new GeometryPopulation(points,world,2026110601L);models+=2;
                if (variant.equals("ORIGINAL")) original=value;else value.samePhysicalAndPA(original,world);
                model.write(value.json(population,variant));model.newLine();proposals.write(population,variant,value,original.qpa.activeSubsets,2026110602L,cases);
            }
            world.requireZeroEvaluation();
        } catch(Throwable error) {failure=error;}
        Map<String,Object> result=new LinkedHashMap<>();result.put("status",failure==null?"PASS":"FAILED_RETAINED");
        result.put("error",failure==null?null:failure.toString());result.put("modelBuilds",models);result.put("knownPhysicalCarrierInitializations",world.proxies);
        result.put("unscoredCompleteProposalConstructions",proposals.constructions);result.put("attemptedSearchFE",world.guard.budget().attempted());
        result.put("successfulSearchFE",world.guard.budget().successful());result.put("failedSearchFE",world.guard.budget().failed());
        result.put("objectiveBackendCalls",world.objectiveCalls());result.put("dynamicDecoderCalls",0);result.put("seconds",(System.nanoTime()-start)/1e9);
        result.put("identity",ClassResolutionProbe.capture("org.uma.jmetal.util.research.modelglobal.QpaNeutralGeometryRun",
            "org.uma.jmetal.util.research.modelglobal.GeometryPopulation","org.uma.jmetal.util.research.modelglobal.GeometryProposals",
            "org.uma.jmetal.util.research.modelglobal.QpaLinkageModel","org.uma.jmetal.util.research.modelglobal.LinkageHierarchy",
            "org.uma.jmetal.util.research.modelglobal.FactoryKeyReencoder","org.uma.jmetal.util.research.modelglobal.PaDependencyModel",
            "org.uma.jmetal.util.research.modelglobal.DirectJointMove","org.uma.jmetal.util.research.modelglobal.PaMixingMove"));
        Files.write(out.resolve("receipt.json"),(DynamicJson.encode(result)+"\n").getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
        if (failure!=null) throw new AssertionError("Zero-FE neutral geometry audit failed",failure);
    }
}
