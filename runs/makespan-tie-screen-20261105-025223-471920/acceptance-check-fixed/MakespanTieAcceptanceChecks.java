package org.uma.jmetal.util.research.search;

import java.nio.file.*;
import java.util.Collections;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;

/** Objective-only checks of the actual isolated loaded acceptance kernel; no decoder calls. */
public final class MakespanTieAcceptanceChecks {
    private MakespanTieAcceptanceChecks() { }
    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]);
        System.setProperty("dhfsp.dataDir",input.getParent().toString());System.setProperty("dhfsp.setupFile",args[1]);
        System.setProperty("dhfsp.standbyPower","1.0");System.setProperty("research.pddr.mode","LINEAR");
        String[] d=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(d[0]),Integer.parseInt(d[1]),Integer.parseInt(d[2]),Integer.parseInt(d[3]));
        PermutationSolution<Integer> child=raw.createSolution(),parent=raw.createSolution();int checks=0;
        for(String mode:new String[]{"STRICT","COST_LEX","PARETO_SAFE"}) {
            MakespanTiePolicy.configure(mode);
            checks+=check(child,parent,new double[]{9,30,30},new double[]{10,10,10},true);
            checks+=check(child,parent,new double[]{11,1,1},new double[]{10,10,10},false);
            checks+=check(child,parent,new double[]{10,10,10},new double[]{10,10,10},false);
            checks+=check(child,parent,new double[]{10,9,9},new double[]{10,10,10},!mode.equals("STRICT"));
            checks+=check(child,parent,new double[]{10,9,11},new double[]{10,10,10},mode.equals("COST_LEX"));
            checks+=check(child,parent,new double[]{10,10,9},new double[]{10,10,10},!mode.equals("STRICT"));
            checks+=check(child,parent,new double[]{10,11,9},new double[]{10,10,10},false);
        }
        MakespanTiePolicy.configure("COST_LEX");
        set(child,new double[]{10,9,11});set(parent,new double[]{10,10,10});
        if(LocalPddrKernel.better(Direction.CENTER,child,parent,Collections.emptyList()))throw new AssertionError("CENTER tie modified");
        if(!LocalPddrKernel.better(Direction.ENERGY,child,parent,Collections.emptyList()))throw new AssertionError("ENERGY modified");
        if(LocalPddrKernel.better(Direction.WORKER_COST,child,parent,Collections.emptyList()))throw new AssertionError("WORKER modified");
        System.out.println("MAKESPAN_TIE_ACCEPTANCE_CHECK_PASS checks="+(checks+3)+" decoderCalls=0");
    }
    private static int check(PermutationSolution<Integer>c,PermutationSolution<Integer>p,double[] cv,double[]pv,boolean expected) {
        set(c,cv);set(p,pv);
        if(LocalPddrKernel.better(Direction.MAKESPAN,c,p,Collections.emptyList())!=expected)
            throw new AssertionError("Unexpected MAKESPAN acceptance: "+MakespanTiePolicy.diagnostics());
        return 1;
    }
    private static void set(PermutationSolution<Integer>s,double[]v){for(int j=0;j<3;j++)s.setObjective(j,v[j]);}
}
