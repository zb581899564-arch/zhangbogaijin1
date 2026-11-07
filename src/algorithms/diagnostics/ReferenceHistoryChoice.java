package research.dynamic;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;

/** Conventional fixed reference utilities for a bounded personal-history probe, not a new algorithm claim. */
final class ReferenceHistoryChoice {
    static final String[] METHODS={"OLDEST","CURRENT","RANDOM","DIR_SUM","BALANCED","DIR_CHEBY"};
    private ReferenceHistoryChoice() { }

    static double[][] weights() {
        List<double[]> out=new ArrayList<>();
        for(int i=1;i<=10;i++)for(int j=1;j<12-i;j++)out.add(new double[]{i/12.,j/12.,(12-i-j)/12.});
        if(out.size()!=55)throw new AssertionError("Expected55 strictly interior reference directions");
        return out.toArray(new double[0][]);
    }
    static int choose(String method,List<PermutationSolution<Integer>> history,double[] weight,double[] scales,long seed) {
        if(method.equals("OLDEST"))return 0;
        if(method.equals("CURRENT"))return -1;
        if(method.equals("RANDOM"))return new Random(NeutralProbeSupport.mixed(seed^0x5A17B3L)).nextInt(history.size());
        double[] resolved=method.equals("BALANCED")?new double[]{1./3,1./3,1./3}:weight;
        int best=0;double value=Double.POSITIVE_INFINITY;
        for(int i=0;i<history.size();i++) {
            double score=0;
            for(int k=0;k<3;k++) {
                double term=resolved[k]*history.get(i).getObjective(k)/scales[k];
                score=method.equals("DIR_SUM")?score+term:Math.max(score,term);
            }
            if(score<value){best=i;value=score;}
        }
        return best;
    }
}
