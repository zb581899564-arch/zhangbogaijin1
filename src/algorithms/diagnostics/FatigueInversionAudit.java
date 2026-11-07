package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.util.research.model.*;

/** Full physical replay of known paid genomes; no search evaluator and no archive feedback. */
public final class FatigueInversionAudit {
    private FatigueInversionAudit() { }
    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]),out=Paths.get(args[4]);Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir",input.getParent().toString());System.setProperty("dhfsp.setupFile",args[1]);
        System.setProperty("dhfsp.standbyPower","1");String[] dims=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW source=new EDHHFSPW(Integer.parseInt(dims[0]),Integer.parseInt(dims[1]),Integer.parseInt(dims[2]),Integer.parseInt(dims[3]));
        Instance in=source.getSchedulingInstance();DynamicParameters p=DynamicInputs.fatigue(in,Paths.get(args[2]));
        FatigueInversionStats.analyticChecks();long qa=0,transitions=0;List<String> results=new ArrayList<>();
        try {
            for(String line:Files.readAllLines(Paths.get(args[3]),StandardCharsets.UTF_8)) {
                String[] fields=line.split("\t",-1);if(fields.length!=6)throw new IllegalArgumentException("Expected6fields");
                DynamicSchedule schedule=DynamicDecoder.full(in,p,ints(fields[2]),ints(fields[3]),ints(fields[4]),ints(fields[5]),null);qa++;
                DynamicValidator.validate(in,p,schedule);
                double[] expected=Arrays.stream(fields[1].split(",")).mapToDouble(Double::parseDouble).toArray();
                if(!Arrays.equals(expected,schedule.objectives()))throw new AssertionError("Paid genome objectives differ");
                Map<String,Object> result=FatigueInversionStats.analyze(in,p,schedule);transitions+=((Number)result.get("offlineTransitionPreviews")).longValue();
                result.put("case",fields[0]);results.add(DynamicJson.encode(result));
            }
        } catch(RuntimeException|Error failure) {
            Files.write(out.resolve("failure.jsonl"),Collections.singletonList(DynamicJson.encode(row("offlineFullDecodes",qa,
                    "offlineTransitionPreviews",transitions,"searchFE",0,"error",failure.toString()))),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
            throw failure;
        }
        Files.write(out.resolve("genome-stats.jsonl"),results,StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
        Map<String,Object> receipt=row("status","PASS","searchFE",0,"offlineFullDecoderQA",qa,"offlineTransitionPreviews",transitions,
                "analyticFixtures",4,"classIdentity",ClassResolutionProbe.capture("org.uma.jmetal.util.research.model.DynamicDecoder",
                "org.uma.jmetal.util.research.model.DynamicPhysics","org.uma.jmetal.util.research.model.FatigueInversionStats"));
        Files.write(out.resolve("receipt.json"),Collections.singletonList(DynamicJson.encode(receipt)),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
        System.out.println("FATIGUE_INVERSION_PASS fullQA="+qa+" transitions="+transitions);
    }
    private static int[] ints(String value){return Arrays.stream(value.split(",")).mapToInt(Integer::parseInt).toArray();}
    private static Map<String,Object> row(Object...fields){Map<String,Object> out=new LinkedHashMap<>();for(int i=0;i<fields.length;i+=2)out.put((String)fields[i],fields[i+1]);return out;}
}
