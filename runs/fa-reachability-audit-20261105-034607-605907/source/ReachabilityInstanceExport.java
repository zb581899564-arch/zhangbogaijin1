package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.util.research.model.*;

/** Export the loaded physical coefficients, without constructing/evaluating a candidate schedule. */
public final class ReachabilityInstanceExport {
    private ReachabilityInstanceExport() { }
    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]);System.setProperty("dhfsp.dataDir",input.getParent().toString());
        System.setProperty("dhfsp.setupFile",args[1]);System.setProperty("dhfsp.standbyPower","1.0");
        String[] dims=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(dims[0]),Integer.parseInt(dims[1]),Integer.parseInt(dims[2]),Integer.parseInt(dims[3]));
        Instance in=raw.getSchedulingInstance();DynamicParameters p=DynamicInputs.fatigue(in,Paths.get(args[2]));
        List<List<Map<String,Object>>> factories=new ArrayList<>();boolean initialFatigue=false;
        for(int f=0;f<in.factories();f++) {
            List<Map<String,Object>> stages=new ArrayList<>();
            for(int k=0;k<in.stages();k++) {
                int mCount=in.machines(f,k),wCount=in.workers(f,k);int pairs=mCount*wCount;
                double[][] base=new double[in.jobs()][pairs],energy=new double[in.jobs()][pairs],labor=new double[in.jobs()][pairs];
                for(int j=0;j<in.jobs();j++)for(int m=0;m<mCount;m++)for(int w=0;w<wCount;w++) {
                    int at=m*wCount+w;
                    // Match DynamicPhysics's arithmetic order, including worker-scaled setup.
                    double b=(in.processing(j,k)/in.speed(f,k,m)+in.setup(j,k))/in.efficiency(f,k,w);
                    base[j][at]=b;energy[j][at]=in.power(f,k,m)*b;labor[j][at]=in.cost(f,k,w)*b;
                }
                double[] alpha=new double[wCount],mu=new double[wCount],beta=new double[wCount],h0=new double[wCount];
                for(int w=0;w<wCount;w++) {
                    alpha[w]=p.alpha(f,k,w);mu[w]=p.mu(f,k,w);beta[w]=p.beta(f,k,w);h0[w]=p.h0(f,k,w);
                    initialFatigue|=h0[w]>0;
                }
                stages.add(row("machines",mCount,"workers",wCount,"base",base,"energy",energy,"labor",labor,
                    "alpha",alpha,"mu",mu,"beta",beta,"h0",h0));
            }
            factories.add(stages);
        }
        Map<String,Object> out=row("instance",in.name(),"jobs",in.jobs(),"stages",in.stages(),"factories",factories,
            "provenance",in.provenance(),"fatigueSource",p.source(),"anyInitialFatigue",initialFatigue,
            "decoderCalls",0,"candidateEvaluations",0,"baseFormula","(p/v+setup)/workerEfficiency",
            "classIdentity",ClassResolutionProbe.capture("org.uma.jmetal.util.research.model.Instance",
                "org.uma.jmetal.util.research.model.DynamicPhysics","org.uma.jmetal.util.research.model.DynamicParameters"));
        Files.write(Paths.get(args[3]),(DynamicJson.encode(out)+"\n").getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
    }
    private static Map<String,Object> row(Object... entries) {
        Map<String,Object> out=new LinkedHashMap<>();for(int i=0;i<entries.length;i+=2)out.put((String)entries[i],entries[i+1]);return out;
    }
}
