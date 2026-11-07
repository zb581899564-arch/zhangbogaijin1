package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.util.research.model.*;

/** No RunContext or optimizer: every call is separately recorded offline physical QA. */
public final class FatigueStageAudit {
    private FatigueStageAudit() { }
    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]),out=Paths.get(args[4]);Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir",input.getParent().toString());System.setProperty("dhfsp.setupFile",args[1]);
        System.setProperty("dhfsp.standbyPower","1");String[] dims=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW source=new EDHHFSPW(Integer.parseInt(dims[0]),Integer.parseInt(dims[1]),Integer.parseInt(dims[2]),Integer.parseInt(dims[3]));
        Instance in=source.getSchedulingInstance();DynamicParameters p=DynamicInputs.fatigue(in,Paths.get(args[2]));
        DynamicParameters zero=FatigueStageStats.beta0(in,p);long dynamicQA=0,zeroCalls=0,operations=0;
        List<String> result=new ArrayList<>();
        try {
            for(String line:Files.readAllLines(Paths.get(args[3]),StandardCharsets.UTF_8)) {
                String[] v=line.split("\t",-1);if(v.length!=6)throw new IllegalArgumentException("Expected6fields");
                int[] js=ints(v[2]),fa=ints(v[3]),ma=ints(v[4]),wa=ints(v[5]);
                DynamicSchedule schedule=DynamicDecoder.full(in,p,js,fa,ma,wa,null);dynamicQA++;
                DynamicValidator.validate(in,p,schedule);
                if(!Arrays.equals(Arrays.stream(v[1].split(",")).mapToDouble(Double::parseDouble).toArray(),schedule.objectives()))
                    throw new AssertionError("Paid genome objective bits differ");
                DynamicSchedule other=DynamicDecoder.full(in,zero,js,fa,ma,wa,null);zeroCalls++;
                DynamicValidator.validate(in,zero,other);operations+=schedule.steps().size()+other.steps().size();
                Map<String,Object> stats=FatigueStageStats.analyze(in,schedule,other);stats.put("case",v[0]);result.add(DynamicJson.encode(stats));
            }
        } catch(RuntimeException|Error failure) {
            write(out.resolve("failure.json"),row("searchFE",0,"dynamicFullQA",dynamicQA,"beta0OfflineDecodes",zeroCalls,
                "completedOperationAccounting",operations,"error",failure.toString()));throw failure;
        }
        Files.write(out.resolve("genome-stats.jsonl"),result,StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
        List<Map<String,Object>> resources=new ArrayList<>();
        for(int f=0;f<in.factories();f++)for(int k=0;k<in.stages();k++)resources.add(row("factory",f,"stage",k,"machines",in.machines(f,k),"workers",in.workers(f,k)));
        write(out.resolve("receipt.json"),row("status","PASS","searchFE",0,"dynamicFullQA",dynamicQA,"beta0OfflineDecodes",zeroCalls,
            "completedOperationAccounting",operations,"resources",resources,"classIdentity",ClassResolutionProbe.capture(
                "org.uma.jmetal.util.research.model.DynamicDecoder","org.uma.jmetal.util.research.model.DynamicPhysics",
                "research.dynamic.FatigueStageStats")));
        System.out.println("FATIGUE_STAGE_AUDIT_PASS dynamicQA="+dynamicQA+" beta0Offline="+zeroCalls);
    }
    private static int[] ints(String value) {return Arrays.stream(value.split(",")).mapToInt(Integer::parseInt).toArray();}
    private static Map<String,Object> row(Object...fields) {
        Map<String,Object> out=new LinkedHashMap<>();for(int i=0;i<fields.length;i+=2)out.put((String)fields[i],fields[i+1]);return out;
    }
    private static void write(Path path,Map<String,Object> record)throws Exception {
        Files.write(path,Collections.singletonList(DynamicJson.encode(record)),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
    }
}
