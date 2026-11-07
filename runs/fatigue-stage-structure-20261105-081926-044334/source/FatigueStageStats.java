package research.dynamic;

import java.util.*;
import org.uma.jmetal.util.research.model.*;

/** Exact accounting on already-paid schedules; beta0 is a physical counterfactual, never search feedback. */
public final class FatigueStageStats {
    private FatigueStageStats() { }
    public static DynamicParameters beta0(Instance in,DynamicParameters p) {
        double[][][][] fields=new double[4][in.factories()][in.stages()][];
        for(int f=0;f<in.factories();f++) for(int k=0;k<in.stages();k++) {
            for(int x=0;x<4;x++) fields[x][f][k]=new double[in.workers(f,k)];
            for(int w=0;w<in.workers(f,k);w++) {
                fields[0][f][k][w]=p.alpha(f,k,w); fields[1][f][k][w]=p.mu(f,k,w);
                fields[3][f][k][w]=p.h0(f,k,w);
            }
        }
        return new DynamicParameters(fields[0],fields[1],fields[2],fields[3],p.source()+"; OFFLINE beta0 diagnostic");
    }
    public static Map<String,Object> analyze(Instance in,DynamicSchedule dynamic,DynamicSchedule beta0) {
        double[][] components=new double[in.stages()][8];
        long[][] counts=new long[in.stages()][3];
        for(DynamicStep op:dynamic.steps()) {
            int f=op.factory(),k=op.stage(),m=op.machine(),w=op.worker();
            double power=in.power(f,k,m),wage=in.cost(f,k,w),extra=op.duration()-op.base();
            double idle=op.energy()-power*op.duration();
            if(extra < -1e-10 || idle < -1e-8) throw new AssertionError("Negative physical component");
            double[] row=components[k];row[0]+=op.base();row[1]+=op.duration();
            row[2]+=power*op.base();row[3]+=power*extra;row[4]+=idle;
            row[5]+=wage*op.base();row[6]+=wage*extra;row[7]+=op.exposure();
            counts[k][0]++;if(op.u()>0)counts[k][1]++;if(extra>=.001*op.base())counts[k][2]++;
        }
        List<Map<String,Object>> stages=new ArrayList<>();double energy=0,labor=0;
        for(int k=0;k<in.stages();k++) {
            double[] s=components[k];energy+=s[2]+s[3]+s[4];labor+=s[5]+s[6];
            stages.add(row("stage",k,"operations",counts[k][0],"positiveStartFatigue",counts[k][1],
                "atLeast0p1PctDurationInflation",counts[k][2],"baseWork",s[0],"dynamicWork",s[1],
                "baseProcessingEnergy",s[2],"fatigueProcessingEnergy",s[3],"idleEnergy",s[4],
                "baseLabor",s[5],"fatigueLabor",s[6],"workExposure",s[7]));
        }
        close(energy,dynamic.objectives()[1]);close(labor,dynamic.objectives()[2]);
        Map<String,Object> result=row("dynamicObjectives",dynamic.objectives(),"beta0Objectives",beta0.objectives(),
            "stageComponents",stages,"policyChanges",policyChanges(in,dynamic,beta0));
        int[] factoryJobs=new int[in.factories()];for(int f:dynamic.fa())factoryJobs[f]++;
        result.put("factoryJobs",factoryJobs);return result;
    }
    private static Map<String,Object> policyChanges(Instance in,DynamicSchedule a,DynamicSchedule b) {
        int n=in.jobs(),s=in.stages();DynamicStep[][] aa=new DynamicStep[n][s],bb=new DynamicStep[n][s];
        int[][] ra=new int[n][s],rb=new int[n][s],positions=new int[in.factories()][s];
        for(DynamicStep op:a.steps()) {aa[op.job()][op.stage()]=op;ra[op.job()][op.stage()]=positions[op.factory()][op.stage()]++;}
        positions=new int[in.factories()][s];
        for(DynamicStep op:b.steps()) {bb[op.job()][op.stage()]=op;rb[op.job()][op.stage()]=positions[op.factory()][op.stage()]++;}
        int[] machine=new int[s],worker=new int[s],order=new int[s];
        for(int j=0;j<n;j++)for(int k=0;k<s;k++) {
            if(aa[j][k].factory()!=bb[j][k].factory())throw new AssertionError("FA counterfactual changed");
            if(aa[j][k].machine()!=bb[j][k].machine())machine[k]++;
            if(aa[j][k].worker()!=bb[j][k].worker())worker[k]++;
            if(ra[j][k]!=rb[j][k])order[k]++;
        }
        if(machine[0]!=0||worker[0]!=0||order[0]!=0)throw new AssertionError("Explicit first-stage encoding changed");
        return row("machineChangedByStage",machine,"workerChangedByStage",worker,"dispatchRankChangedByStage",order,
            "comparisonUnit","same job and stage, dynamic vs beta0 full decode; position change is not pairwise inversion count");
    }
    private static void close(double a,double b) {
        if(Math.abs(a-b)>1e-10*Math.max(1,Math.abs(b)))throw new AssertionError("Physical decomposition does not close");
    }
    private static Map<String,Object> row(Object... fields) {
        Map<String,Object> out=new LinkedHashMap<>();for(int i=0;i<fields.length;i+=2)out.put((String)fields[i],fields[i+1]);return out;
    }
}
