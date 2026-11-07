package org.uma.jmetal.util.research.modelglobal;

import java.io.*;
import java.lang.reflect.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import org.uma.jmetal.util.research.search.*;
import research.dynamic.*;

/** Actual native partition and pure metadata plans on known states, with objective evaluation forbidden. */
public final class PaRoleSemanticsRun {
    private PaRoleSemanticsRun() { }
    @SuppressWarnings("unchecked")
    private static int[] nativeOrder(GeometryWorld world,List<PaIndividual> states) throws Exception {
        CanonicalHmopso nativeAlgorithm=new CanonicalHmopso(world.guard.problem(),world.in,4,new SearchConfig());
        Class<?> type=Class.forName("org.uma.jmetal.util.research.search.Particle");
        Constructor<?> constructor=type.getDeclaredConstructor(PermutationSolution.class);constructor.setAccessible(true);
        List<Object> particles=new ArrayList<>();IdentityHashMap<Object,Integer> indices=new IdentityHashMap<>();
        for(int i=0;i<100;i++){Object p=constructor.newInstance(states.get(i).point);particles.add(p);indices.put(p,i);}
        Method decompose=CanonicalHmopso.class.getDeclaredMethod("decompose",List.class);decompose.setAccessible(true);
        Map<Direction,List<?>> groups=(Map<Direction,List<?>>)decompose.invoke(nativeAlgorithm,particles);
        int[] result=new int[100];int at=0;for(Direction d:Direction.values())for(Object p:groups.get(d))result[at++]=indices.get(p);
        if(at!=100)throw new AssertionError("Native partition lost members");return result;
    }

    private static String randomHash() throws Exception {
        ByteArrayOutputStream bytes=new ByteArrayOutputStream();new ObjectOutputStream(bytes).writeObject(SeededRandom.current());
        return Base64.getEncoder().encodeToString(MessageDigest.getInstance("SHA-256").digest(bytes.toByteArray()));
    }

    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]),output=Paths.get(args[3]);Files.createDirectories(output);
        System.setProperty("research.qgsAudit.mode","record");System.setProperty("research.qgsAudit.ledger",output.resolve("unused-ledger.csv").toString());
        System.setProperty("dhfsp.dataDir",input.getParent().toString());System.setProperty("dhfsp.setupFile",args[1]);System.setProperty("dhfsp.standbyPower","1");
        String[] d=input.getFileName().toString().replace(".txt","").split("_");
        GeometryWorld world=new GeometryWorld(new EDHHFSPW(Integer.parseInt(d[0]),Integer.parseInt(d[1]),Integer.parseInt(d[2]),Integer.parseInt(d[3])),15530003L);
        Map<String,List<PaIndividual>> populations=new LinkedHashMap<>();
        for(String line:Files.readAllLines(Paths.get(args[2]),java.nio.charset.StandardCharsets.UTF_8)) {
            String[] f=line.split("\t");QpaIndividual known=world.carrier(f);
            TypedScheduleGenome genes=TypedScheduleGenome.of(world.catalog,GeometryWorld.ints(f[10]),Arrays.stream(f[11].split(",")).mapToDouble(Double::parseDouble).toArray());
            PaIndividual p=new PaIndividual(Long.parseLong(f[12]),Long.parseLong(f[3]),Direction.valueOf(f[4]),genes,known.point);
            populations.computeIfAbsent(f[0],unused->new ArrayList<>()).add(p);
        }
        long plans=0;List<String> result=new ArrayList<>();
        for(Map.Entry<String,List<PaIndividual>> cohort:populations.entrySet()) {
            List<PaIndividual> values=cohort.getValue();String rngBefore=randomHash();int[] nativeVisit=nativeOrder(world,values);
            for(String mode:Arrays.asList("NATIVE","TASK_ONLY","ORDER_ONLY","FULL","RANDOM","CENTER_MATCHED")) {
                PaRoleSchedule.Plan p=PaRoleSchedule.make(values,mode,new Random(15530003L));plans++;
                if(mode.equals("FULL")&&!Arrays.equals(p.visit,nativeVisit))throw new AssertionError("Native role order differs");
                Map<String,Object> row=new LinkedHashMap<>();row.put("population",cohort.getKey());row.put("mode",mode);row.put("visit",p.visit);
                row.put("roles",Arrays.stream(p.roles).map(Enum::name).toArray(String[]::new));row.put("nativeVisit",nativeVisit);
                row.put("mainRNGBefore",rngBefore);row.put("mainRNGAfter",randomHash());result.add(DynamicJson.encode(row));
                if(!rngBefore.equals(randomHash()))throw new AssertionError("Metadata planning consumed main RNG");
            }
        }
        world.requireZeroEvaluation();Files.write(output.resolve("plans.jsonl"),result,java.nio.charset.StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
        Map<String,Object> receipt=new LinkedHashMap<>();receipt.put("populations",populations.size());receipt.put("plans",plans);receipt.put("carriers",world.proxies);
        receipt.put("attemptedSearchFE",world.guard.budget().attempted());receipt.put("objectiveBackendCalls",world.objectiveCalls());receipt.put("dynamicDecoderCalls",0);
        receipt.put("identity",ClassResolutionProbe.capture("org.uma.jmetal.util.research.modelglobal.PaRoleSchedule",
            "org.uma.jmetal.util.research.modelglobal.PaRoleSemanticsRun","org.uma.jmetal.util.research.search.CanonicalHmopso",
            "org.uma.jmetal.util.research.search.ParetoTools","org.uma.jmetal.util.research.modelglobal.GeometryWorld"));
        Files.write(output.resolve("receipt.json"),DynamicJson.encode(receipt).getBytes(java.nio.charset.StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
    }
}
