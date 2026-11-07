package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Pure encoding checks: no evaluator, archive, objective scoring or hidden search FE. */
public final class RelinkingEngineering {
    private RelinkingEngineering() { }
    private static void fixtures() {
        int[][] genes={{0,0,0},{1,0,0},{2,0,0}},target={{1,0,0},{2,0,0},{0,0,0}};
        int aux=FactoryCoverTransfer.apply(genes,target,new boolean[3],0,3);
        if(aux!=2||!Arrays.deepEquals(genes,target))throw new AssertionError("Singleton cycle did not close");
        genes=new int[][]{{0,0,0},{1,0,0},{1,0,0}};target=new int[][]{{1,0,0},{0,0,0},{1,0,0}};
        if(FactoryCoverTransfer.apply(genes,target,new boolean[]{false,false,true},0,2)!=1)throw new AssertionError("Augmenting path failed");
        genes=new int[][]{{0,0,0},{1,0,0}};target=new int[][]{{0,1,0},{1,0,0}};
        if(FactoryCoverTransfer.apply(genes,target,new boolean[2],0,2)!=0||genes[0][1]!=1)throw new AssertionError("Resource-only update failed");
        boolean rejected=false;
        try {FactoryCoverTransfer.apply(new int[][]{{0,0,0},{1,0,0}},new int[][]{{1,0,0},{1,0,0}},new boolean[2],0,2);}
        catch(IllegalArgumentException expected){rejected=true;}
        if(!rejected)throw new AssertionError("Uncoverable target accepted");
    }
    public static void main(String[] args) throws Exception {
        fixtures();Path input=Paths.get(args[0]);
        System.setProperty("dhfsp.dataDir",input.getParent().toString());System.setProperty("dhfsp.setupFile",args[1]);System.setProperty("dhfsp.standbyPower","1");
        String[] dims=input.getFileName().toString().replace(".txt","").split("_");SeededRandom.reset(12060003);
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(dims[0]),Integer.parseInt(dims[1]),Integer.parseInt(dims[2]),Integer.parseInt(dims[3]));
        Instance in=raw.getSchedulingInstance();long steps=0,auxiliary=0,pairs=0;
        for(String line:Files.readAllLines(Paths.get(args[2]),StandardCharsets.UTF_8)) {
            String[] f=line.split("\t",-1);PermutationSolution<Integer> parent=raw.createSolution(),teacher=raw.createSolution();
            ProbeData.fill(parent,f,4,-1,null);ProbeData.fill(teacher,f,9,-1,null);
            String parentKey=ProbeData.key(parent),teacherKey=ProbeData.key(teacher);
            for(String method:new String[]{"COVER_PATH","RANDOM_PATH","REPAIR_PATH"}) {
                CommittedRelinkingPath state=new CommittedRelinkingPath(in,parent,teacher,method,12060003+pairs);
                PermutationSolution<Integer> last=null;
                for(int step=0;step<in.jobs();step++){last=state.next(step);steps++;auxiliary+=state.auxiliaryJobs;}
                if(!CommittedRelinkingPath.sameEncoding(last,teacher))throw new AssertionError("Path did not reach paid teacher");
            }
            if(!parentKey.equals(ProbeData.key(parent))||!teacherKey.equals(ProbeData.key(teacher)))throw new AssertionError("Path mutated source input");pairs++;
        }
        Files.write(Paths.get(args[3]),Collections.singletonList(DynamicJson.encode(NeutralProbeSupport.row("status","PASS",
            "pairs",pairs,"completeEncodingSteps",steps,"auxiliaryCoverJobs",auxiliary,"fixtures",4,"searchFE",0,"decodes",0))),
            StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
        System.out.println("RELINKING_ENGINEERING_PASS steps="+steps);
    }
}
