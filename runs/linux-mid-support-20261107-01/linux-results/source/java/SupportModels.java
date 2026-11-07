package research.dynamic;

import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.util.research.modelglobal.*;

/** Reconstruct the unchanged free-domain model from paid snapshots, with zero decoding. */
public final class SupportModels {
    private static int[] ints(String s){return Arrays.stream(s.split(",")).mapToInt(Integer::parseInt).toArray();}
    private static double[] doubles(String s){return Arrays.stream(s.split(",")).mapToDouble(Double::parseDouble).toArray();}
    public static void main(String[] args)throws Exception {
        Path input=Paths.get(args[0]);System.setProperty("dhfsp.dataDir",input.getParent().toString());
        System.setProperty("dhfsp.setupFile",args[1]);System.setProperty("dhfsp.standbyPower","1");
        String[] n=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(n[0]),Integer.parseInt(n[1]),Integer.parseInt(n[2]),Integer.parseInt(n[3]));
        FirstStageCatalog c=new FirstStageCatalog(raw.getSchedulingInstance());
        Map<String,List<TypedScheduleGenome>> groups=new LinkedHashMap<>();
        for(String line:Files.readAllLines(Paths.get(args[2]),StandardCharsets.UTF_8)) {
            String[] f=line.split("\t");
            groups.computeIfAbsent(f[0],k->new ArrayList<>()).add(TypedScheduleGenome.of(c,ints(f[1]),doubles(f[2])));
        }
        List<Object> output=new ArrayList<>();
        for(Map.Entry<String,List<TypedScheduleGenome>> entry:groups.entrySet()) {
            List<TypedScheduleGenome> rows=entry.getValue();if(rows.size()!=80)throw new AssertionError("free80 required");
            int[][] factories=new int[80][c.jobs()];double[][] keys=new double[80][];
            for(int i=0;i<80;i++){int[] r=rows.get(i).allocations();keys[i]=rows.get(i).priorities();
                for(int j=0;j<c.jobs();j++)factories[i][j]=c.factory(r[j]);}
            double[][] matrix=new PaDependencyModel(factories,keys,c.factories()).matrix();
            Map<String,Object> model=new LinkedHashMap<>();model.put("context",entry.getKey());model.put("dependency",matrix);
            model.put("subsets",new LinkageHierarchy(matrix).subsets());output.add(model);
        }
        List<int[]> catalog=new ArrayList<>();for(int i=0;i<c.size();i++)catalog.add(c.tuple(i));
        Map<String,Object> result=new LinkedHashMap<>();result.put("catalog",catalog);result.put("models",output);
        result.put("jobs",c.jobs());result.put("factories",c.factories());result.put("evaluations",0);
        result.put("loaded",ClassResolutionProbe.capture("org.uma.jmetal.util.research.modelglobal.PaDependencyModel",
            "org.uma.jmetal.util.research.modelglobal.LinkageHierarchy","org.uma.jmetal.util.research.modelglobal.FirstStageCatalog"));
        Files.write(Paths.get(args[3]),(DynamicJson.encode(result)+"\n").getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
    }
}
