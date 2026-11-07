package research.dynamic;

import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.uma.jmetal.util.research.modelglobal.*;

/** Algebraic source-component probe only: no problem construction, genome mixing or decoding. */
public final class HistoryLinkage {
    private static int[] ints(String s){return Arrays.stream(s.split(",")).mapToInt(Integer::parseInt).toArray();}
    private static double[] doubles(String s){return Arrays.stream(s.split(",")).mapToDouble(Double::parseDouble).toArray();}
    public static void main(String[] args)throws Exception {
        Map<String,List<String[]>> groups=new LinkedHashMap<>();
        for(String line:Files.readAllLines(Paths.get(args[0]),StandardCharsets.UTF_8)) {
            String[] f=line.split("\t");groups.computeIfAbsent(f[0],k->new ArrayList<>()).add(f);
        }
        List<Object> results=new ArrayList<>();int factories=Integer.parseInt(args[2]);
        for(Map.Entry<String,List<String[]>> entry:groups.entrySet()) {
            List<String[]> rows=entry.getValue();if(rows.size()!=80)throw new AssertionError("free80 required");
            int[][] before=new int[80][],after=new int[80][];double[][] keys=new double[80][];
            for(int i=0;i<80;i++){before[i]=ints(rows.get(i)[1]);after[i]=ints(rows.get(i)[2]);keys[i]=doubles(rows.get(i)[3]);}
            PaDependencyModel pre=new PaDependencyModel(before,keys,factories),post=new PaDependencyModel(after,keys,factories);
            int jobs=after[0].length;double[][] nativeMatrix=post.matrix(),hybrid=new double[jobs][jobs];
            BinomialAttraction tail=new BinomialAttraction(80,factories);
            for(int a=0;a<jobs;a++)for(int b=a+1;b<jobs;b++) {
                double[] p=pre.components(a,b),q=post.components(a,b);
                double value=p[1]*(PaDependencyModel.WEIGHT+(1-PaDependencyModel.WEIGHT)*
                    (tail.attracts((int)p[4])?q[2]:p[3]));
                hybrid[a][b]=hybrid[b][a]=value;
            }
            Map<String,Object> result=new LinkedHashMap<>();result.put("context",entry.getKey());
            result.put("nativeMatrix",nativeMatrix);result.put("hybridMatrix",hybrid);
            result.put("nativeFOS",new LinkageHierarchy(nativeMatrix).subsets());
            result.put("hybridFOS",new LinkageHierarchy(hybrid).subsets());results.add(result);
        }
        Map<String,Object> output=new LinkedHashMap<>();output.put("contexts",results);output.put("evaluations",0);
        output.put("decoderCalls",0);output.put("candidateConstructions",0);
        output.put("loaded",ClassResolutionProbe.capture("org.uma.jmetal.util.research.modelglobal.PaDependencyModel",
            "org.uma.jmetal.util.research.modelglobal.BinomialAttraction","org.uma.jmetal.util.research.modelglobal.LinkageHierarchy"));
        Files.write(Paths.get(args[1]),(DynamicJson.encode(output)+"\n").getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
    }
}
