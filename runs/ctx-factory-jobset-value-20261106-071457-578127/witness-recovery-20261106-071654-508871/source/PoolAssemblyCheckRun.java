package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.util.research.model.*;

/** Offline full decoding of every distinct nine-policy assembly, with explicit diagnostic accounting. */
public final class PoolAssemblyCheckRun {
    private PoolAssemblyCheckRun() { }
    private static int[] ints(String text) {return Arrays.stream(text.split(",")).mapToInt(Integer::parseInt).toArray();}
    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]);System.setProperty("dhfsp.dataDir",input.getParent().toString());
        System.setProperty("dhfsp.setupFile",args[1]);System.setProperty("dhfsp.standbyPower","1");
        String[] n=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW problem=new EDHHFSPW(Integer.parseInt(n[0]),Integer.parseInt(n[1]),Integer.parseInt(n[2]),Integer.parseInt(n[3]));
        Instance in=problem.getSchedulingInstance();DynamicParameters params=DynamicInputs.fatigue(in,Paths.get(args[2]));
        boolean exact=args.length>5&&args[5].equals("EXACT");
        int attempted=0,passed=0;double[] maxError=new double[3];Throwable failure=null;
        try {
            for(String line:Files.readAllLines(Paths.get(args[3]),StandardCharsets.UTF_8)) {
                if(line.startsWith("id\t"))continue;
                String[] c=line.split("\t",-1);if(c.length!=6)throw new IllegalArgumentException("Bad diagnostic case");
                double[] expected=Arrays.stream(c[1].split(",")).mapToDouble(Double::parseDouble).toArray();attempted++;
                DynamicSchedule schedule=DynamicDecoder.full(in,params,ints(c[2]),ints(c[3]),ints(c[4]),ints(c[5]),null);
                DynamicValidator.validate(in,params,schedule);double[] actual=schedule.objectives();
                for(int k=0;k<3;k++) {
                    maxError[k]=Math.max(maxError[k],Math.abs(actual[k]-expected[k]));
                    if(exact?Double.doubleToLongBits(actual[k])!=Double.doubleToLongBits(expected[k]):
                            Math.abs(actual[k]-expected[k])>1e-9*Math.max(1,Math.abs(expected[k])))
                        throw new AssertionError("Assembly objectives disagree for "+c[0]+" objective "+k);
                }
                passed++;
            }
        } catch(Throwable error) {failure=error;}
        Map<String,Object> result=new LinkedHashMap<>();result.put("attemptedOfflineDecodes",attempted);
        result.put("passedOfflineDecodes",passed);result.put("maxAbsoluteObjectiveError",maxError);
        result.put("status",failure==null?"PASS":"FAILED_RETAINED");result.put("error",failure==null?null:failure.toString());
        if(exact)result.put("exactObjectiveBitsRequired",true);
        Files.write(Paths.get(args[4]),(DynamicJson.encode(result)+"\n").getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
        if(failure!=null)throw new AssertionError("Offline assembly QA failed",failure);
    }
}
