package org.uma.jmetal.util.research.cooperation;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.util.research.model.*;
import research.dynamic.*;

/** Full replay of registered, already-paid source points; no search is run or updated. */
public final class FactoryValueRun {
    private FactoryValueRun() { }
    private static int[] ints(String text) {return Arrays.stream(text.split(",")).mapToInt(Integer::parseInt).toArray();}
    private static double[] doubles(String text) {return Arrays.stream(text.split(",")).mapToDouble(Double::parseDouble).toArray();}

    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]),out=Paths.get(args[5]); long started=System.nanoTime();
        System.setProperty("dhfsp.dataDir",input.getParent().toString()); System.setProperty("dhfsp.setupFile",args[1]);
        System.setProperty("dhfsp.standbyPower","1"); String[] n=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(n[0]),Integer.parseInt(n[1]),Integer.parseInt(n[2]),Integer.parseInt(n[3]));
        Instance in=raw.getSchedulingInstance(); DynamicParameters params=DynamicInputs.fatigue(in,Paths.get(args[2]));
        FactoryValueRecords records=new FactoryValueRecords(); Map<String,double[]> values=new LinkedHashMap<>();
        int attempts=0,passed=0; Throwable failure=null; Map<String,Object> result=new LinkedHashMap<>();
        try (BufferedWriter writer=Files.newBufferedWriter(out.resolve("factory-records.jsonl"),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW)) {
            for (String line:Files.readAllLines(Paths.get(args[3]),StandardCharsets.UTF_8)) {
                if (line.startsWith("id\t")) continue; String[] c=line.split("\t",-1); double[] expected=doubles(c[1]); attempts++;
                if (attempts>4200) throw new AssertionError("Known-source bound exceeded");
                DynamicSchedule schedule=DynamicDecoder.full(in,params,ints(c[2]),ints(c[3]),ints(c[4]),ints(c[5]),null);
                DynamicValidator.validate(in,params,schedule); double[] actual=schedule.objectives();
                for (int k=0; k<3; k++) if (Double.doubleToLongBits(expected[k])!=Double.doubleToLongBits(actual[k]))
                    throw new AssertionError("Known point objectives differ: "+c[0]+" objective "+k);
                records.add(c[0],schedule,writer,in.factories()); values.put(c[0],actual); passed++;
            }
        } catch (Throwable error) {failure=error;}
        if (failure==null) try {result.putAll(new FactoryValuePools(records,raw,in,values).process(Paths.get(args[4]),out.resolve("query-pools.jsonl")));}
        catch (Throwable error) {failure=error;}
        result.put("attemptedKnownSourceFullDecodes",attempts); result.put("passedKnownSourceFullDecodes",passed);
        result.put("repeatedPhysicalChainsTimelineVerified",records.repeatedChains); result.put("extraSearchFE",0);
        result.put("seconds",(System.nanoTime()-started)/1e9); result.put("status",failure==null?"PASS":"FAILED_RETAINED");
        result.put("error",failure==null?null:failure.toString());
        result.put("classIdentity",ClassResolutionProbe.capture("org.uma.jmetal.util.research.cooperation.FactoryValueRun",
            "org.uma.jmetal.util.research.cooperation.FactoryValuePools","org.uma.jmetal.util.research.cooperation.FactoryValueRecords",
            "org.uma.jmetal.util.research.cooperation.FactoryPool","org.uma.jmetal.util.research.cooperation.FactoryRecord",
            "org.uma.jmetal.util.research.cooperation.FamilyContexts","org.uma.jmetal.util.research.search.ParetoTools",
            "org.uma.jmetal.util.research.model.DynamicDecoder","org.uma.jmetal.util.research.model.DynamicPhysics",
            "org.uma.jmetal.util.research.model.DynamicSchedule","org.uma.jmetal.util.research.model.DynamicValidator"));
        Files.write(out.resolve("physics-acceptance.json"),(DynamicJson.encode(result)+"\n").getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
        if (failure!=null) throw new AssertionError("Offline factory value engineering failed",failure);
    }
}
