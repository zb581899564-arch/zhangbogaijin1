package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.util.research.modelglobal.CenterTargets;

/** Objective-number fixtures only: no decoder, population search or objective calculation. */
public final class PaRegionalMathRun {
    private PaRegionalMathRun(){ }
    public static void main(String[] args) throws Exception {
        Map<String,List<double[]>> data=new LinkedHashMap<>();Map<String,double[]> scales=new LinkedHashMap<>();
        for(String line:Files.readAllLines(Paths.get(args[0]),StandardCharsets.UTF_8)) {
            String[] f=line.split("\t");data.computeIfAbsent(f[0],unused->new ArrayList<>()).add(vector(f[1]));scales.put(f[0],vector(f[2]));
        }
        List<Map<String,Object>> output=new ArrayList<>();
        for(Map.Entry<String,List<double[]>> entry:data.entrySet()) {
            CenterTargets targets=new CenterTargets(scales.get(entry.getKey()));List<double[]> points=entry.getValue();
            for(int i=0;i<points.size();i++)targets.initial(i,points.get(i));
            Map<String,Object> row=new LinkedHashMap<>();row.put("fixture",entry.getKey());row.put("columns",targets.columns());row.put("directions",CenterTargets.directions());
            row.put("initialIdeal",targets.ideal());row.put("assignmentCost",targets.assignmentCost());List<Map<String,Object>> probes=new ArrayList<>();
            for(int axis=0;axis<3;axis++) {
                double[] point=targets.ideal();point[axis]-=scales.get(entry.getKey())[axis];targets.observe(point);
                for(int slot:new int[]{15,40,69}) {
                    Map<String,Object> probe=new LinkedHashMap<>();probe.put("slot",slot);probe.put("ideal",targets.ideal());probe.put("weight",targets.weight(slot));
                    probe.put("point",points.get(slot));probe.put("score",targets.score(points.get(slot),targets.weight(slot)));probes.add(probe);
                }
            }
            row.put("probes",probes);output.add(row);
        }
        int rejected=0;
        for(double[] scale:new double[][]{{0,1,1},{-1,1,1},{Double.NaN,1,1},{1,1}})
            try{new CenterTargets(scale);}catch(IllegalArgumentException expected){rejected++;}
        if(rejected!=4)throw new AssertionError("Invalid scale accepted");
        Map<String,Object> result=new LinkedHashMap<>();result.put("fixtures",output);result.put("invalidScaleRejections",rejected);
        result.put("newSearchFE",0);result.put("newDecoderCalls",0);
        Files.write(Paths.get(args[1]),DynamicJson.encode(result).getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
    }
    private static double[] vector(String text){String[] f=text.split(",");double[] out=new double[f.length];for(int i=0;i<f.length;i++)out[i]=Double.parseDouble(f[i]);return out;}
}
