package org.uma.jmetal.util.research.modelglobal;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.Instance;

/** Initial physical-neutral coordinate intervention, independent of the optimizer's RNG. */
public final class NeutralInitialView {
    private static final String MODE=System.getProperty("research.initialView.mode","ORIGINAL");
    private static final Random NOISE=new Random(Long.getLong("research.initialView.seed",15350003L));
    private static long transforms,paid;
    public interface Observer { void paid(PermutationSolution<Integer> point,long fe); }
    private static Observer observer;
    private NeutralInitialView() { }

    public static void observer(Observer value) { if(observer!=null)throw new IllegalStateException("Already attached");observer=value; }

    @SuppressWarnings("unchecked")
    public static void apply(Instance instance,PermutationSolution<Integer> point,int index) {
        if(index!=transforms||transforms>=100)throw new AssertionError("Expected exactly100 initial slots");
        int n=instance.jobs(),factories=instance.factories();
        int[] js=SchedulingEncoding.integers(point.getVariables()),fa=SchedulingEncoding.integers(point.getVariablesid());
        int[] ma=SchedulingEncoding.machineIntegers(point),wa=SchedulingEncoding.integers(point.getVariablesworker());
        List<List<Integer>> chains=new ArrayList<>();for(int f=0;f<factories;f++)chains.add(new ArrayList<>());
        int[][] resources=new int[n][3];
        for(int p=0;p<n;p++){chains.get(fa[p]).add(js[p]);resources[js[p]]=new int[]{fa[p],ma[p],wa[p]};}
        List<Integer> order=new ArrayList<>();
        if(MODE.equals("ORIGINAL")){for(int j:js)order.add(j);}
        else if(MODE.equals("CONCAT")){for(List<Integer> chain:chains)order.addAll(chain);}
        else if(MODE.equals("RANDOM")) {
            int[] labels=fa.clone();
            for(int p=n-1;p>0;p--){int q=NOISE.nextInt(p+1),swap=labels[p];labels[p]=labels[q];labels[q]=swap;}
            int[] ranks=new int[factories];for(int f:labels)order.add(chains.get(f).get(ranks[f]++));
        } else throw new IllegalArgumentException("Unknown neutral view: "+MODE);
        List<Integer> machines=(List<Integer>)point.getAttribute("machine");int[] ranks=new int[factories];
        for(int p=0;p<n;p++){
            int j=order.get(p),f=resources[j][0];
            if(chains.get(f).get(ranks[f]++)!=j)throw new AssertionError("Physical initial chain changed");
            point.setVariableValue(p,j);point.setVariableValueid(p,f);machines.set(p,resources[j][1]);point.setVariableValueworker(p,resources[j][2]);
        }
        transforms++;
    }

    public static void paid(PermutationSolution<Integer> point,long fe) {
        if(fe!=paid+1||observer==null)throw new AssertionError("Missing or out-of-order paid observation");
        paid=fe;observer.paid(point,fe);
    }

    public static Map<String,Object> diagnostics() {
        Map<String,Object> row=new LinkedHashMap<>();row.put("mode",MODE);row.put("transforms",transforms);row.put("paid",paid);
        row.put("privateSeed",Long.getLong("research.initialView.seed",15350003L));row.put("mainRNGCalls",0);return row;
    }
}
