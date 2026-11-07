package org.uma.jmetal.util.research.modelglobal;

import java.util.Arrays;

/** Deterministic shortest-augmenting-path assignment; no cost perturbation or RNG. */
public final class CenterAssignment {
    private CenterAssignment() { }
    public static int[] solve(double[][] cost) {
        int n=cost.length;
        if(n==0)throw new IllegalArgumentException("Nonempty square costs required");
        for(double[] row:cost) {
            if(row.length!=n)throw new IllegalArgumentException("Square costs required");
            for(double v:row)if(!Double.isFinite(v))throw new IllegalArgumentException("Finite cost required");
        }
        double[] u=new double[n],v=new double[n];int[] rowForColumn=new int[n],columnForRow=new int[n];
        Arrays.fill(rowForColumn,-1);Arrays.fill(columnForRow,-1);
        for(int current=0;current<n;current++) {
            Path path=shortest(cost,current,u,v,rowForColumn);
            u[current]+=path.minimum;
            for(int row=0;row<n;row++)if(path.rows[row]&&row!=current)
                u[row]+=path.minimum-path.distances[columnForRow[row]];
            for(int col=0;col<n;col++)if(path.columns[col])v[col]-=path.minimum-path.distances[col];
            int col=path.sink;
            while(true) {
                int row=path.previous[col],old=columnForRow[row];
                rowForColumn[col]=row;columnForRow[row]=col;col=old;
                if(row==current)break;
            }
        }
        return columnForRow;
    }
    private static Path shortest(double[][] cost,int start,double[] u,double[] v,int[] rowForColumn) {
        int n=cost.length,row=start,remainingCount=n;int[] remaining=new int[n];Path path=new Path(n);
        for(int j=0;j<n;j++)remaining[j]=n-j-1;
        while(path.sink<0) {
            path.rows[row]=true;double lowest=Double.POSITIVE_INFINITY;int selected=-1;
            for(int at=0;at<remainingCount;at++) {
                int col=remaining[at];double reduced=path.minimum+cost[row][col]-u[row]-v[col];
                if(reduced<path.distances[col]){path.distances[col]=reduced;path.previous[col]=row;}
                if(path.distances[col]<lowest||(path.distances[col]==lowest&&rowForColumn[col]<0)) {
                    lowest=path.distances[col];selected=at;
                }
            }
            if(selected<0||!Double.isFinite(lowest))throw new IllegalArgumentException("No finite assignment");
            path.minimum=lowest;int col=remaining[selected];
            if(rowForColumn[col]<0)path.sink=col;else row=rowForColumn[col];
            path.columns[col]=true;remaining[selected]=remaining[--remainingCount];
        }
        return path;
    }
    private static final class Path {
        final boolean[] rows,columns;final double[] distances;final int[] previous;
        int sink=-1;double minimum;
        Path(int n){rows=new boolean[n];columns=new boolean[n];distances=new double[n];
            Arrays.fill(distances,Double.POSITIVE_INFINITY);previous=new int[n];}
    }
}
