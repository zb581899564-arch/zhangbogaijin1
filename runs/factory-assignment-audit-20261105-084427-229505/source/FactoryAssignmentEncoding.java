package org.uma.jmetal.util.research.search;

import org.uma.jmetal.solution.PermutationSolution;

/** Position-indexed FA must be compared by job identity, including JS-only cross-factory swaps. */
public final class FactoryAssignmentEncoding {
    private FactoryAssignmentEncoding() { }
    public static int[] byJob(int[] js,int[] fa) {
        if(js.length!=fa.length)throw new IllegalArgumentException("Different vector lengths");
        int[] result=new int[js.length];boolean[] seen=new boolean[js.length];
        for(int i=0;i<js.length;i++) {
            int j=js[i];if(j<0||j>=js.length||seen[j])throw new IllegalArgumentException("Invalid job permutation");
            seen[j]=true;result[j]=fa[i];
        }
        return result;
    }
    static int[] byJob(PermutationSolution<Integer> value) {
        int n=value.getNumberOfVariables();int[] js=new int[n],fa=new int[n];
        for(int i=0;i<n;i++){js[i]=value.getVariableValue(i);fa[i]=value.getVariableValueid(i);}
        return byJob(js,fa);
    }
    public static int changes(int[] before,int[] after) {
        if(before.length!=after.length)throw new IllegalArgumentException("Different job counts");
        int count=0;for(int j=0;j<before.length;j++)if(before[j]!=after[j])count++;return count;
    }
}
