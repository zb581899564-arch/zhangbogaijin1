package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.util.research.model.Instance;

/** Input-only per-job/factory optimistic costs; independent resource minima, no scheduling decoder. */
public final class FactoryAffinityInputs {
    private FactoryAffinityInputs() { }
    public static void main(String[] args)throws Exception {
        Path input=Paths.get(args[0]),out=Paths.get(args[2]);
        System.setProperty("dhfsp.dataDir",input.getParent().toString());System.setProperty("dhfsp.setupFile",args[1]);
        System.setProperty("dhfsp.standbyPower","1");String[] dims=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW source=new EDHHFSPW(Integer.parseInt(dims[0]),Integer.parseInt(dims[1]),Integer.parseInt(dims[2]),Integer.parseInt(dims[3]));
        Instance in=source.getSchedulingInstance();List<Map<String,Object>> data=new ArrayList<>();
        for(int j=0;j<in.jobs();j++)for(int f=0;f<in.factories();f++) {
            double[] energy=new double[in.stages()],labor=new double[in.stages()];
            for(int k=0;k<in.stages();k++) {
                energy[k]=labor[k]=Double.POSITIVE_INFINITY;
                for(int m=0;m<in.machines(f,k);m++)for(int w=0;w<in.workers(f,k);w++) {
                    double base=(in.processing(j,k)/in.speed(f,k,m)+in.setup(j,k))/in.efficiency(f,k,w);
                    energy[k]=Math.min(energy[k],base*in.power(f,k,m));labor[k]=Math.min(labor[k],base*in.cost(f,k,w));
                }
            }
            data.add(row("job",j,"factory",f,"stageBaseEnergyMin",energy,"stageBaseLaborMin",labor));
        }
        Files.write(out,Collections.singletonList(DynamicJson.encode(row("jobs",in.jobs(),"factories",in.factories(),"stages",in.stages(),
            "searchFE",0,"decoderCalls",0,"data",data,"classIdentity",ClassResolutionProbe.capture(
                "org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW","org.uma.jmetal.util.research.model.Instance")))),
            StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
        System.out.println("FACTORY_AFFINITY_INPUTS_PASS jobs="+in.jobs()+" decoderCalls=0");
    }
    private static Map<String,Object> row(Object...fields) {
        Map<String,Object> result=new LinkedHashMap<>();for(int i=0;i<fields.length;i+=2)result.put((String)fields[i],fields[i+1]);return result;
    }
}
