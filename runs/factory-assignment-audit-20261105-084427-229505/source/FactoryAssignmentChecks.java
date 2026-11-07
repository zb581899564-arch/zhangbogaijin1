package org.uma.jmetal.util.research.search;

import java.util.Arrays;

/** Zero-decoder examples distinguish positional identity, physical FA and neutral interleaving. */
public final class FactoryAssignmentChecks {
    private FactoryAssignmentChecks() { }
    private static void expect(int count,int[] a,int[] af,int[] b,int[] bf) {
        if(FactoryAssignmentEncoding.changes(FactoryAssignmentEncoding.byJob(a,af),FactoryAssignmentEncoding.byJob(b,bf))!=count)
            throw new AssertionError("FA identity fixture failed");
    }
    public static void main(String[] args) {
        int[] js={0,1,2,3},fa={0,0,1,1};
        expect(2,js,fa,new int[]{2,1,0,3},fa); // Identical positional FA, two jobs change factories.
        expect(0,js,fa,new int[]{1,0,2,3},fa);
        expect(0,js,fa,new int[]{0,2,1,3},new int[]{0,1,0,1});
        expect(1,js,fa,js,new int[]{0,1,1,1});
        expect(0,js,fa,js,fa);
        boolean rejected=false;try{FactoryAssignmentEncoding.byJob(new int[]{0,0},new int[]{0,1});}
        catch(IllegalArgumentException expected){rejected=true;}
        if(!rejected||!Arrays.equals(FactoryAssignmentEncoding.byJob(js,fa),fa))throw new AssertionError("Invalid permutation fixture failed");
        System.out.println("FACTORY_ASSIGNMENT_CHECKS_PASS fixtures=6 searchFE=0 decodes=0");
    }
}
