package research.dynamic;

import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.util.research.model.*;

/** Exact half-JS stage-zero commitments; later stages are not falsely frozen. */
public final class PrefixReachabilityExport {
    private PrefixReachabilityExport() { }
    private static int[] ints(String text){return Arrays.stream(text.split(",")).mapToInt(Integer::parseInt).toArray();}
    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]);System.setProperty("dhfsp.dataDir",input.getParent().toString());
        System.setProperty("dhfsp.setupFile",args[1]);System.setProperty("dhfsp.standbyPower","1.0");
        String[] d=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(d[0]),Integer.parseInt(d[1]),Integer.parseInt(d[2]),Integer.parseInt(d[3]));
        Instance in=raw.getSchedulingInstance();DynamicParameters p=DynamicInputs.fatigue(in,Paths.get(args[2]));
        int prefixCalls=0,decodeAttempts=0,successfulDecodes=0,completed=0;Throwable failure=null;
        try(BufferedWriter writer=Files.newBufferedWriter(Paths.get(args[4]),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW)) {
            for(String line:Files.readAllLines(Paths.get(args[3]),StandardCharsets.UTF_8)) {
                String[] f=line.split("\t");double[] expected=Arrays.stream(f[1].split(",")).mapToDouble(Double::parseDouble).toArray();
                int[] js=ints(f[2]),fa=ints(f[3]),ma=ints(f[4]),wa=ints(f[5]);DynamicPrefix prefix=new DynamicPrefix(in,p);
                for(int i=0;i<in.jobs()/2;i++){prefix.append(js[i],fa[i],ma[i],wa[i]);prefixCalls++;}
                decodeAttempts++;DynamicSchedule full=DynamicDecoder.full(in,p,js,fa,ma,wa,null);successfulDecodes++;
                DynamicValidator.validate(in,p,full);
                if(!Arrays.equals(full.objectives(),expected))throw new AssertionError("Old paid objectives differ: "+f[0]);
                decodeAttempts++;DynamicSchedule constructed=DynamicDecoder.incremental(in,p,js,fa,ma,wa,null,prefix,null);successfulDecodes++;
                DynamicValidator.validate(in,p,constructed);sameTimeline(full,constructed);
                Map<String,Object> row=state(f[0],in,prefix,full);writer.write(DynamicJson.encode(row));writer.newLine();writer.flush();completed++;
            }
        }catch(Throwable error){failure=error;}
        Files.write(Paths.get(args[5]),(DynamicJson.encode(row("status",failure==null?"PASS":"FAILED_RETAINED",
            "completedProfiles",completed,"fullDecodeAttempts",decodeAttempts,"successfulFullDecodes",successfulDecodes,
            "prefixAppendTransitions",prefixCalls,"searchFE",0,"error",failure==null?null:failure.toString()))+"\n").getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
        if(failure!=null)throw new AssertionError("Prefix export failed",failure);
    }

    private static Map<String,Object> state(String id,Instance in,DynamicPrefix prefix,DynamicSchedule full) {
        boolean[] completed=new boolean[in.jobs()];double[] ready=new double[in.jobs()];
        for(int j=0;j<in.jobs();j++){completed[j]=prefix.completed(j);ready[j]=prefix.firstCompletion(j);}
        List<double[]> machines=new ArrayList<>(),workers=new ArrayList<>(),fatigue=new ArrayList<>();
        for(int f=0;f<in.factories();f++) {
            double[] m=new double[in.machines(f,0)],w=new double[in.workers(f,0)],h=new double[w.length];
            for(int i=0;i<m.length;i++)m[i]=prefix.machineEnd(f,i);
            for(int i=0;i<w.length;i++){w[i]=prefix.workerEnd(f,i);h[i]=prefix.workerFatigue(f,i);}
            machines.add(m);workers.add(w);fatigue.add(h);
        }
        List<Map<String,Object>> firstStage=new ArrayList<>();
        for(DynamicStep op:full.steps())if(op.stage()==0)firstStage.add(row("job",op.job(),"factory",op.factory(),
            "machine",op.machine(),"worker",op.worker(),"u",op.u(),"duration",op.duration(),"start",op.start()));
        return row("id",id,"prefixSize",prefix.size(),"completedJobs",completed,"firstCompletion",ready,
            "partialObjectives",prefix.partialObjectives(),"machineEnd",machines,"workerEnd",workers,
            "workerFatigue",fatigue,"firstStageOperations",firstStage,"objectives",full.objectives(),"timelineIdentical",true);
    }

    private static void sameTimeline(DynamicSchedule a,DynamicSchedule b) {
        if(!Arrays.equals(a.objectives(),b.objectives())||a.steps().size()!=b.steps().size())throw new AssertionError("Prefix objective mismatch");
        for(int i=0;i<a.steps().size();i++) {
            DynamicStep x=a.steps().get(i),y=b.steps().get(i);
            if(x.job()!=y.job()||x.factory()!=y.factory()||x.stage()!=y.stage()||x.machine()!=y.machine()||x.worker()!=y.worker()
                ||!Arrays.equals(values(x),values(y)))throw new AssertionError("Prefix timeline mismatch at "+i);
        }
    }
    private static double[] values(DynamicStep x){return new double[]{x.start(),x.base(),x.duration(),x.setupDuration(),x.completion(),x.u(),x.v(),x.energy(),x.labor(),x.exposure()};}
    private static Map<String,Object> row(Object...entries){Map<String,Object> out=new LinkedHashMap<>();for(int i=0;i<entries.length;i+=2)out.put((String)entries[i],entries[i+1]);return out;}
}
