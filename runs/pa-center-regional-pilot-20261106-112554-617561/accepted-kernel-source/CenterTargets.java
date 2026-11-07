package org.uma.jmetal.util.research.modelglobal;

import java.util.Arrays;

/** Fixed55 positive directions and a paid-observation ideal; independent of the decoder. */
public final class CenterTargets {
    private final double[] scale,ideal={Double.POSITIVE_INFINITY,Double.POSITIVE_INFINITY,Double.POSITIVE_INFINITY};
    private final double[][] initial=new double[100][];private final int[][] weights=directions();
    private int count;private int[] columns;private double assignmentCost;
    public CenterTargets(double[] values) {
        if(values.length!=3)throw new IllegalArgumentException("Three scales required");
        scale=values.clone();for(double s:scale)if(!Double.isFinite(s)||s<=0)throw new IllegalArgumentException("Positive finite scale required");
    }
    public void initial(int slot,double[] point) {
        if(slot!=count||count>=100)throw new IllegalArgumentException("Initial slots must be0..99 once");
        observe(point);initial[count++]=point.clone();
        if(count==100) {
            double[][] cost=new double[55][55];
            for(int row=0;row<55;row++)for(int col=0;col<55;col++)cost[row][col]=score(initial[row+15],weights[col]);
            columns=CenterAssignment.solve(cost);
            for(int row=0;row<55;row++)assignmentCost+=cost[row][columns[row]];
        }
    }
    public void observe(double[] point) {
        if(point.length!=3)throw new IllegalArgumentException("Three objectives required");
        for(int k=0;k<3;k++) {
            if(!Double.isFinite(point[k]))throw new IllegalArgumentException("Finite objectives required");
            ideal[k]=Math.min(ideal[k],point[k]);
        }
    }
    public boolean ready(){return columns!=null;}
    public double[] ideal(){return ideal.clone();}
    public int[] columns(){if(!ready())throw new IllegalStateException("Targets not ready");return columns.clone();}
    public double assignmentCost(){return assignmentCost;}
    public int[] weight(int slot) {
        if(!ready()||slot<15||slot>=70)throw new IllegalArgumentException("Initialized CENTER slot required");
        return weights[columns[slot-15]].clone();
    }
    public double score(double[] point,int[] weight) {
        if(point.length!=3||weight.length!=3)throw new IllegalArgumentException("Three-dimensional score required");
        double score=Double.NEGATIVE_INFINITY;
        for(int k=0;k<3;k++)score=Math.max(score,weight[k]*((point[k]-ideal[k])/scale[k]));
        if(!Double.isFinite(score))throw new IllegalStateException("Finite initialized score required");return score;
    }
    public static int[][] directions() {
        int[][] result=new int[55][3];int at=0;
        for(int a=0;a<10;a++)for(int b=0;b<10-a;b++)result[at++]=new int[]{a+1,b+1,10-a-b};
        return result;
    }
}
