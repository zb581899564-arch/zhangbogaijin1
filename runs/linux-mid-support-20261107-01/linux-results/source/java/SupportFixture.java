package research.dynamic;

import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.util.research.modelglobal.*;

/** Unscored native generator equivalence: independent Java PaMixingMove versus frozen Python rows. */
public final class SupportFixture {
    private static int[] ints(String s){return Arrays.stream(s.split(",")).mapToInt(Integer::parseInt).toArray();}
    private static double[] doubles(String s){return Arrays.stream(s.split(",")).mapToDouble(Double::parseDouble).toArray();}
    public static void main(String[] args)throws Exception {
        Path input=Paths.get(args[0]);System.setProperty("dhfsp.dataDir",input.getParent().toString());
        System.setProperty("dhfsp.setupFile",args[1]);System.setProperty("dhfsp.standbyPower","1");
        String[] n=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(n[0]),Integer.parseInt(n[1]),Integer.parseInt(n[2]),Integer.parseInt(n[3]));
        FirstStageCatalog c=new FirstStageCatalog(raw.getSchedulingInstance());int count=0;
        for(String line:Files.readAllLines(Paths.get(args[2]),StandardCharsets.UTF_8)) {
            String[] f=line.split("\t");TypedScheduleGenome a=TypedScheduleGenome.of(c,ints(f[1]),doubles(f[2]));
            TypedScheduleGenome b=TypedScheduleGenome.of(c,ints(f[3]),doubles(f[4]));
            PaMixingMove move=PaMixingMove.apply(c,a,b,ints(f[5]));
            if(!Arrays.equals(move.genome.allocations(),ints(f[6])) || !Arrays.equals(move.genome.priorities(),doubles(f[7]))
                    || move.fallback!=Boolean.parseBoolean(f[8]))throw new AssertionError("Native mixing differs: "+f[0]);
            count++;
        }
        System.out.println("SUPPORT_FIXTURE_PASSED "+count+" evaluations=0");
    }
}
