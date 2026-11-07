package org.uma.jmetal.util.research.search;

import java.util.*;

/** Observer-only numeric mirror, with the actual archive's exact minimization and duplicate rules. */
final class PaidObjectiveMirror {
    private final List<double[]> front=new ArrayList<>();
    void add(double[] value) {
        for(double[] old:front)if(same(old,value)||dominates(old,value))return;
        front.removeIf(old->dominates(value,old));front.add(value.clone());
    }
    double[][] snapshot() {
        double[][] result=new double[front.size()][];
        for(int i=0;i<result.length;i++)result[i]=front.get(i).clone();return result;
    }
    void verify(double[][] actual) {
        if(!Arrays.deepEquals(snapshot(),actual))throw new AssertionError("Paid objective mirror differs from real archive");
    }
    private static boolean same(double[] a,double[] b) {
        for(int k=0;k<3;k++)if(a[k]!=b[k])return false;return true;
    }
    private static boolean dominates(double[] a,double[] b) {
        boolean strict=false;
        for(int k=0;k<3;k++){if(a[k]>b[k])return false;strict|=a[k]<b[k];}return strict;
    }
}
